# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-26 22:19
# @FileName  : scopes.py
# -----------------------------
"""1.4.1 可选数据范围层。除非业务模型显式声明 ``SCOPE_FIELD`` 且角色配置了 ``scope_node``，否则不会过滤任何数据库查询。"""
from django.conf import settings
from django.db import models


def get_scope_hierarchy():
    return list(getattr(settings, 'LAYUIX_SCOPE_HIERARCHY', []) or [])


def visible_scope_nodes(node, depth=0):
    """根据可选配置将数据范围节点展开为其后代节点。"""
    node = str(node or '').strip()
    if not node:
        return set()

    result = {node}
    tree = getattr(settings, 'LAYUIX_SCOPE_TREE', {}) or {}
    hierarchy = get_scope_hierarchy()
    frontier = [node]

    for _ in range(max(0, int(depth or 0))):
        children = []
        for current in frontier:
            current_children = list(tree.get(current, []) or [])
            try:
                from .models import ScopeNode
                current_children.extend(
                    ScopeNode.objects.filter(
                        parent__code=current, is_active=True
                    ).values_list('code', flat=True)
                )
            except Exception:
                pass
            if not current_children and current in hierarchy:
                index = hierarchy.index(current)
                if index + 1 < len(hierarchy):
                    current_children.append(hierarchy[index + 1])
            children.extend(current_children)
        if not children:
            break
        children = [str(item) for item in children if item]
        result.update(children)
        frontier = children
    return result


def get_user_scope_nodes(user):
    """返回可见的数据范围节点；范围过滤未启用时返回 None。"""
    if user is None or not getattr(user, 'is_authenticated', False):
        return set()
    if getattr(user, 'is_superuser', False):
        return None

    roles = getattr(user, 'roles', None)
    if roles is None:
        return None
    configured = list(roles.filter(scope_node__gt='').values_list('scope_node', 'scope_depth'))
    if not configured:
        return None

    nodes = set()
    for node, depth in configured:
        nodes.update(visible_scope_nodes(node, depth))
    return nodes


class ScopedManager(models.Manager):
    """仅在配置数据范围时按 ``SCOPE_FIELD`` 过滤的 Manager。"""

    def for_user(self, user):
        queryset = self.get_queryset()
        scope_field = getattr(self.model, 'SCOPE_FIELD', '')
        if not scope_field:
            return queryset
        nodes = get_user_scope_nodes(user)
        if nodes is None:
            return queryset
        if not nodes:
            return queryset.none()
        return queryset.filter(**{'%s__in' % scope_field: list(nodes)})


class ScopedModelMixin(models.Model):
    """为需要数据范围过滤的业务模型提供的可选 mixin。"""

    SCOPE_FIELD = ''
    objects = ScopedManager()

    class Meta:
        abstract = True
