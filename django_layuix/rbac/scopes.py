# -*- coding: utf-8 -*-
"""1.4.1 optional data-scope layer.

No database query is filtered unless a business model explicitly declares
``SCOPE_FIELD`` and a role has ``scope_node`` configured.
"""
from django.conf import settings
from django.db import models


def get_scope_hierarchy():
    return list(getattr(settings, 'LAYUIX_SCOPE_HIERARCHY', []) or [])


def visible_scope_nodes(node, depth=0):
    """Expand a scope node to its descendants according to optional config."""
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
    """Return visible scope nodes, or None when scope filtering is disabled."""
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
    """Manager that filters by ``SCOPE_FIELD`` only when scope is configured."""

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
    """Optional mixin for business models that want data-scope filtering."""

    SCOPE_FIELD = ''
    objects = ScopedManager()

    class Meta:
        abstract = True
