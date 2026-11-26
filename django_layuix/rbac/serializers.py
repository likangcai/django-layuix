# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-26 22:19
# @FileName  : serializers.py
# -----------------------------
"""Field-whitelist serializer for business API responses."""
import json
from datetime import date, datetime, time
from functools import wraps

from django.http import JsonResponse
from django.utils import timezone

from .abac import (
    _SENSITIVE_FIELD_TOKENS, _policies_for, evaluate_policies,
    load_field_policies, user_context,
)


API_FIELD_REGISTRY = {
    'rbac.User': (
        'id', 'username', 'nickname', 'phone', 'email', 'avatar',
        'is_active', 'is_superuser', 'is_staff', 'is_tester', 'roles',
        'department_id', 'department_name', 'position_id', 'position_name',
        'position_ids', 'position_names',
        'last_login', 'date_joined',
    ),
    'rbac.OperationLog': (
        'id', 'user', 'user_id', 'module', 'action', 'ip', 'method',
        'url', 'status', 'status_display', 'create_time',
    ),
    'rbac.SystemConfig': (
        'id', 'key', 'value', 'description', 'config_type', 'sort',
        'create_time', 'update_time',
    ),
    'rbac.Role': (
        'id', 'name', 'code', 'description', 'is_system', 'status',
        'menu_ids', 'parent_ids', 'parent_id', 'children_ids',
        'max_users', 'scope_node', 'scope_depth', 'create_time',
        'update_time',
    ),
    'rbac.Dictionary': (
        'id', 'code', 'name', 'description', 'sort', 'status',
        'is_system', 'item_count', 'create_time', 'update_time',
    ),
    'rbac.DictionaryItem': (
        'id', 'dictionary_id', 'label', 'value', 'sort', 'status',
        'is_default', 'css_class', 'remark', 'create_time', 'update_time',
    ),
    'ops.Server': (
        'id', 'name', 'host', 'port', 'username', 'auth_type',
        'description', 'is_active', 'create_time',
    ),
    'store.Category': (
        'id', 'name', 'description', 'sort', 'product_count',
        'create_time', 'update_time',
    ),
    'store.Product': (
        'id', 'name', 'sku', 'category_id', 'category_name',
        'description', 'price', 'cost_price', 'stock', 'sales',
        'status', 'status_label', 'is_featured', 'create_time',
        'update_time',
    ),
    'store.Order': (
        'id', 'order_no', 'customer_name', 'customer_phone',
        'shipping_address', 'total_amount', 'status', 'status_label',
        'remark', 'items', 'create_time', 'update_time',
    ),
    'rbac.Department': (
        'id', 'name', 'code', 'type', 'type_display', 'parent_id',
        'parent_name', 'leader', 'phone', 'email', 'sort', 'status',
        'note', 'create_time', 'update_time',
    ),
    'rbac.Position': (
        'id', 'name', 'code', 'sort', 'status', 'note',
        'create_time', 'update_time',
    ),
    'rbac.Region': (
        'id', 'name', 'code', 'area_code', 'zip_code', 'pinyin', 'level',
        'level_display', 'parent_id', 'parent_name', 'sort', 'status',
        'note', 'create_time', 'update_time',
    ),
    'rbac.MemberLevel': (
        'id', 'name', 'code', 'min_points', 'discount', 'icon', 'sort',
        'status', 'description', 'create_time', 'update_time',
    ),
    'rbac.UserRole': (
        'id', 'name', 'code',
    ),
    'store.OrderItem': (
        'id', 'product_id', 'product_name', 'product_sku',
        'unit_price', 'quantity', 'subtotal',
    ),
}

API_NESTED_FIELD_REGISTRY = {
    'rbac.User.roles': 'rbac.UserRole',
    'store.Order.items': 'store.OrderItem',
}


def _clean_value(value):
    if isinstance(value, datetime):
        return timezone.localtime(value).strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, time):
        return value.isoformat()
    if hasattr(value, 'pk') and not isinstance(value, (dict, list, tuple, str, int, float, bool)):
        return value.pk
    return value


def _safe_fields(fields, resource):
    """Unknown resources fail closed; explicit fields may only narrow a registry."""
    registered = API_FIELD_REGISTRY.get(resource or '', ())
    if not registered:
        return []
    return [field for field in (fields or registered) if field in registered]


def _is_sensitive(field):
    lower = str(field).lower()
    return any(token in lower for token in _SENSITIVE_FIELD_TOKENS)


def _load_nested_policy_maps(resource, action, safe):
    result = {}
    for field, child_resource in API_NESTED_FIELD_REGISTRY.items():
        if field not in safe:
            continue
        result[field] = load_field_policies(
            child_resource, action, API_FIELD_REGISTRY.get(child_resource, ())
        )
    return result


def _serialize_instance(
    data, request, resource, action='view', fields=None,
    policy_map=None, cached_user_context=None, nested_policy_maps=None,
):
    safe = _safe_fields(fields, resource)
    if not safe or not isinstance(data, dict):
        return {}
    user = getattr(request, 'user', None)
    visible = []
    for field in safe:
        if policy_map is None:
            policies = _policies_for(resource, action, field)
        else:
            policies = policy_map.get(field, [])
        if not policies:
            visible.append(field)
            continue
        has_allow_whitelist = any(policy.effect == 'allow' for policy in policies)
        extra_context = {'resource': data}
        if cached_user_context is not None:
            extra_context['user'] = cached_user_context
        decision = evaluate_policies(
            user, action, resource, field, policies=policies,
            extra_context=extra_context,
        )
        if decision.allowed and has_allow_whitelist and decision.matched:
            visible.append(field)

    result = {}
    for key in safe:
        if key not in data or key not in visible or _is_sensitive(key):
            continue
        value = _clean_value(data[key])
        child_resource = API_NESTED_FIELD_REGISTRY.get('%s.%s' % (resource, key))
        if child_resource and isinstance(value, (list, tuple)):
            child_policy_map = (nested_policy_maps or {}).get(key)
            if child_policy_map is None:
                child_policy_map = load_field_policies(
                    child_resource, action, API_FIELD_REGISTRY.get(child_resource, ())
                )
            row_user_context = cached_user_context
            if row_user_context is None and any(child_policy_map.values()) and user is not None:
                if getattr(user, 'is_authenticated', False):
                    row_user_context = user_context(user)
            value = [
                _serialize_instance(
                    row, request, child_resource, action,
                    None, child_policy_map, row_user_context,
                )
                for row in value
            ]
        result[key] = value
    return result


def serialize_instance(data, request, resource, action='view', fields=None):
    """Serialize a dict-like row using the registered API field whitelist.

    Explicit ``fields`` narrow the built-in registry; they cannot widen it.
    ABAC field policies override the default registry visibility.
    """
    safe = _safe_fields(fields, resource)
    if not safe or not isinstance(data, dict):
        return {}
    policy_map = load_field_policies(resource, action, safe)
    nested_policy_maps = _load_nested_policy_maps(resource, action, safe)
    user = getattr(request, 'user', None)
    cached_user_context = None
    has_policies = any(policy_map.values()) or any(
        any(policy_map.values()) for policy_map in nested_policy_maps.values()
    )
    if has_policies and user is not None and getattr(user, 'is_authenticated', False):
        cached_user_context = user_context(user)
    return _serialize_instance(
        data, request, resource, action, safe,
        policy_map, cached_user_context, nested_policy_maps,
    )


def serialize_rows(rows, request, resource, action='view', fields=None):
    if not isinstance(rows, (list, tuple)):
        return rows
    safe = _safe_fields(fields, resource)
    policy_map = load_field_policies(resource, action, safe)
    nested_policy_maps = _load_nested_policy_maps(resource, action, safe)
    user = getattr(request, 'user', None)
    has_policies = any(policy_map.values()) or any(
        any(policy_map.values()) for policy_map in nested_policy_maps.values()
    )
    cached_user_context = None
    if has_policies and user is not None and getattr(user, 'is_authenticated', False):
        cached_user_context = user_context(user)
    return [
        _serialize_instance(
            row, request, resource, action, safe,
            policy_map, cached_user_context, nested_policy_maps,
        )
        for row in rows
    ]


def serialize_payload(payload, request, resource, action='view', keys=('list', 'data')):
    if isinstance(payload, (list, tuple)):
        return serialize_rows(payload, request, resource, action)
    if not isinstance(payload, dict):
        return payload
    result = dict(payload)
    serialized_list = False
    for key in keys:
        if key in result and isinstance(result[key], (list, tuple)):
            result[key] = serialize_rows(result[key], request, resource, action)
            serialized_list = True
    if not serialized_list:
        return serialize_instance(result, request, resource, action)
    return result


def field_whitelisted(resource, action='view', keys=('list', 'data')):
    """Automatically apply the registered field whitelist to a successful view."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            response = view_func(request, *args, **kwargs)
            if not isinstance(response, JsonResponse) or response.status_code != 200:
                return response
            try:
                payload = json.loads(response.content.decode(response.charset or 'utf-8'))
            except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
                return response
            if not isinstance(payload, dict) or payload.get('code') != 200:
                return response
            payload['data'] = serialize_payload(payload.get('data'), request, resource, action, keys)
            safe = not isinstance(payload['data'], (list, tuple))
            return JsonResponse(payload, status=response.status_code, safe=safe)
        return wrapper
    return decorator
