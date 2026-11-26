# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-26 22:19
# @FileName  : dictionary_views.py
# -----------------------------
"""Data dictionary management APIs."""
import math
import re

from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.views.decorators.csrf import csrf_exempt

from .models import Dictionary, DictionaryItem
from .permissions import api_login_required, api_permission_required, has_permission
from .serializers import field_whitelisted
from .views import error_response, fmt_time, get_request_body, success_response


_DICT_CODE_RE = re.compile(r'^[a-z][a-z0-9_.-]{1,63}$')


def _as_bool(value, default=False):
    if value is None or value == '':
        return default
    if isinstance(value, bool):
        return value
    return str(value).lower() in ('1', 'true', 'yes', 'on', 'active')


def _page_args(request, default_size=20):
    try:
        page = max(1, int(request.GET.get('page') or 1))
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = int(request.GET.get('page_size') or default_size)
    except (TypeError, ValueError):
        page_size = default_size
    page_size = max(1, min(200, page_size))
    return page, page_size


def _dict_payload(obj, item_count=None):
    data = {
        'id': obj.pk,
        'code': obj.code,
        'name': obj.name,
        'description': obj.description,
        'sort': obj.sort,
        'status': obj.status,
        'is_system': obj.is_system,
        'item_count': getattr(obj, 'item_count', item_count or 0),
        'create_time': fmt_time(obj.create_time),
        'update_time': fmt_time(obj.update_time),
    }
    return data


def _item_payload(obj):
    return {
        'id': obj.pk,
        'dictionary_id': obj.dictionary_id,
        'label': obj.label,
        'value': obj.value,
        'sort': obj.sort,
        'status': obj.status,
        'is_default': obj.is_default,
        'css_class': obj.css_class,
        'remark': obj.remark,
        'create_time': fmt_time(obj.create_time),
        'update_time': fmt_time(obj.update_time),
    }


@csrf_exempt
@api_login_required
@api_permission_required('dict:view')
@field_whitelisted('rbac.Dictionary')
def dictionary_list(request):
    """GET /api/rbac/dictionaries/ - list dictionaries."""
    queryset = Dictionary.objects.annotate(item_count=Count('items'))
    keyword = str(request.GET.get('keyword') or '').strip()
    if keyword:
        queryset = queryset.filter(
            Q(name__icontains=keyword) | Q(code__icontains=keyword)
            | Q(description__icontains=keyword)
        )
    status = request.GET.get('status')
    if status not in (None, ''):
        queryset = queryset.filter(status=_as_bool(status))
    page, page_size = _page_args(request)
    total = queryset.count()
    start = (page - 1) * page_size
    rows = queryset.order_by('sort', 'id')[start:start + page_size]
    return success_response({
        'list': [_dict_payload(row) for row in rows],
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': max(1, math.ceil(total / page_size)),
    })


@csrf_exempt
@api_login_required
@api_permission_required('dict:add')
def dictionary_create(request):
    """POST /api/rbac/dictionaries/create/ - create a dictionary."""
    if request.method != 'POST':
        return error_response('Method not allowed', 405)
    body = get_request_body(request)
    code = str(body.get('code') or '').strip().lower()
    name = str(body.get('name') or '').strip()
    if not _DICT_CODE_RE.match(code):
        return error_response('字典编码需以小写字母开头，仅支持字母、数字、点、下划线和短横线', 400)
    if not name:
        return error_response('字典名称不能为空', 400)
    try:
        with transaction.atomic():
            obj = Dictionary.objects.create(
                code=code,
                name=name,
                description=str(body.get('description') or '')[:200],
                sort=int(body.get('sort') or 0),
                status=_as_bool(body.get('status'), True),
                is_system=False,
            )
    except IntegrityError:
        return error_response('字典编码已存在', 400)
    except (TypeError, ValueError):
        return error_response('排序必须是整数', 400)
    return success_response({'id': obj.pk}, msg='创建成功')


@csrf_exempt
@api_login_required
@api_permission_required('dict:view')
@field_whitelisted('rbac.Dictionary')
def dictionary_detail(request, pk):
    """GET/PUT/DELETE /api/rbac/dictionaries/<id>/."""
    try:
        obj = Dictionary.objects.get(pk=pk)
    except Dictionary.DoesNotExist:
        return error_response('字典不存在', 404)

    if request.method == 'GET':
        return success_response(_dict_payload(obj))

    if request.method == 'PUT':
        if not has_permission(request.user, 'dict:edit', request):
            return error_response('无权限', 403)
        body = get_request_body(request)
        code = str(body.get('code') or obj.code).strip().lower()
        name = str(body.get('name') or '').strip()
        if not _DICT_CODE_RE.match(code):
            return error_response('字典编码格式不正确', 400)
        if not name:
            return error_response('字典名称不能为空', 400)
        if obj.is_system and code != obj.code:
            return error_response('系统内置字典不允许修改编码', 400)
        try:
            with transaction.atomic():
                obj.code = code
                obj.name = name
                obj.description = str(body.get('description') or '')[:200]
                obj.sort = int(body.get('sort') or 0)
                obj.status = _as_bool(body.get('status'), True)
                obj.save()
        except IntegrityError:
            return error_response('字典编码已存在', 400)
        except (TypeError, ValueError):
            return error_response('排序必须是整数', 400)
        return success_response(msg='更新成功')

    if request.method == 'DELETE':
        if not has_permission(request.user, 'dict:delete', request):
            return error_response('无权限', 403)
        if obj.is_system:
            return error_response('系统内置字典不可删除', 400)
        obj.delete()
        return success_response(msg='删除成功')

    return error_response('Method not allowed', 405)


@csrf_exempt
@api_login_required
@api_permission_required('dict:view')
def dictionary_items(request, pk):
    """GET /api/rbac/dictionaries/<id>/items/ - list dictionary items."""
    if request.method != 'GET':
        return error_response('Method not allowed', 405)
    try:
        dictionary = Dictionary.objects.get(pk=pk)
    except Dictionary.DoesNotExist:
        return error_response('字典不存在', 404)
    queryset = dictionary.items.all()
    keyword = str(request.GET.get('keyword') or '').strip()
    if keyword:
        queryset = queryset.filter(
            Q(label__icontains=keyword) | Q(value__icontains=keyword)
            | Q(remark__icontains=keyword)
        )
    status = request.GET.get('status')
    if status not in (None, ''):
        queryset = queryset.filter(status=_as_bool(status))
    page, page_size = _page_args(request)
    total = queryset.count()
    start = (page - 1) * page_size
    rows = queryset.order_by('sort', 'id')[start:start + page_size]
    return success_response({
        'list': [_item_payload(row) for row in rows],
        'total': total,
        'page': page,
        'page_size': page_size,
        'dictionary': {
            'id': dictionary.pk,
            'code': dictionary.code,
            'name': dictionary.name,
            'status': dictionary.status,
            'is_system': dictionary.is_system,
        },
        'total_pages': max(1, math.ceil(total / page_size)),
    })


@csrf_exempt
@api_login_required
@api_permission_required('dict:edit')
def dictionary_item_create(request, pk):
    """POST /api/rbac/dictionaries/<id>/items/create/."""
    if request.method != 'POST':
        return error_response('Method not allowed', 405)
    try:
        dictionary = Dictionary.objects.get(pk=pk)
    except Dictionary.DoesNotExist:
        return error_response('字典不存在', 404)
    body = get_request_body(request)
    label = str(body.get('label') or '').strip()
    value = str(body.get('value') or '').strip()
    if not label or not value:
        return error_response('显示名称和数据值不能为空', 400)
    is_default = _as_bool(body.get('is_default'), False)
    try:
        with transaction.atomic():
            if is_default:
                dictionary.items.update(is_default=False)
            item = DictionaryItem.objects.create(
                dictionary=dictionary,
                label=label[:100],
                value=value[:100],
                sort=int(body.get('sort') or 0),
                status=_as_bool(body.get('status'), True),
                is_default=is_default,
                css_class=str(body.get('css_class') or '')[:50],
                remark=str(body.get('remark') or '')[:200],
            )
    except IntegrityError:
        return error_response('同一字典下的数据值不能重复', 400)
    except (TypeError, ValueError):
        return error_response('排序必须是整数', 400)
    return success_response({'id': item.pk}, msg='创建成功')


@csrf_exempt
@api_login_required
@api_permission_required('dict:view')
def dictionary_item_detail(request, pk):
    """PUT/DELETE /api/rbac/dictionary-items/<id>/."""
    try:
        item = DictionaryItem.objects.select_related('dictionary').get(pk=pk)
    except DictionaryItem.DoesNotExist:
        return error_response('字典项不存在', 404)

    if request.method == 'PUT':
        if not has_permission(request.user, 'dict:edit', request):
            return error_response('无权限', 403)
        body = get_request_body(request)
        label = str(body.get('label') or '').strip()
        value = str(body.get('value') or '').strip()
        if not label or not value:
            return error_response('显示名称和数据值不能为空', 400)
        is_default = _as_bool(body.get('is_default'), False)
        try:
            with transaction.atomic():
                if is_default:
                    item.dictionary.items.exclude(pk=item.pk).update(is_default=False)
                item.label = label[:100]
                item.value = value[:100]
                item.sort = int(body.get('sort') or 0)
                item.status = _as_bool(body.get('status'), True)
                item.is_default = is_default
                item.css_class = str(body.get('css_class') or '')[:50]
                item.remark = str(body.get('remark') or '')[:200]
                item.save()
        except IntegrityError:
            return error_response('同一字典下的数据值不能重复', 400)
        except (TypeError, ValueError):
            return error_response('排序必须是整数', 400)
        return success_response(msg='更新成功')

    if request.method == 'DELETE':
        if not has_permission(request.user, 'dict:delete', request):
            return error_response('无权限', 403)
        item.delete()
        return success_response(msg='删除成功')

    return error_response('Method not allowed', 405)


@csrf_exempt
@api_login_required
@api_permission_required('dict:view')
def dictionary_options(request, code):
    """GET /api/rbac/dictionaries/options/<code>/ - active options for consumers."""
    dictionary = Dictionary.objects.filter(code=code, status=True).first()
    if not dictionary:
        return error_response('字典不存在或已停用', 404)
    rows = dictionary.items.filter(status=True).order_by('sort', 'id')
    return success_response([
        {
            'label': item.label,
            'value': item.value,
            'sort': item.sort,
            'is_default': item.is_default,
            'css_class': item.css_class,
        }
        for item in rows
    ])
