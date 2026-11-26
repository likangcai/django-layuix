# -*- coding: utf-8 -*-
"""django-layuix sidebar menu template tag"""
from django import template
from django.utils.safestring import mark_safe
register = template.Library()

_LT = chr(60)
_GT = chr(62)

# 与 SPA 外壳 index.html 的 menuPathMap 保持一致：
# 数据库种子中的前端路由 path 需要映射到静态功能页，否则服务端渲染外壳会 404。
MENU_PATH_MAP = {
    "/permission/menu": "/static/layui/pages/menu.html",
    "/permission/role": "/static/layui/pages/role.html",
    "/permission/user": "/static/layui/pages/user.html",
    "/system/rbac-constraints": "/static/layui/pages/constraints.html",
    "/permission/abac": "/static/layui/pages/abac.html",
    "/permission/data-scope": "/static/layui/pages/scope.html",
    "/system/scope-nodes": "/static/layui/pages/scope.html",
    "/permission-demo/orders": "/static/permission_demo/pages/order.html",
    "/static/permission_demo/pages/order.html": "/static/permission_demo/pages/order.html",
    "/profile": "/static/layui/pages/profile.html",
    "/system/log": "/static/layui/pages/log.html",
    "/system/info": "/static/layui/pages/dashboard.html",
    "/system/config": "/static/layui/pages/config.html",
    "/ops/server": "/static/layui/pages/server.html",
    "/ops/ai-config": "/static/layui/pages/ai-config.html",
}

def _build_menu_tree(menus, parent_id=None):
    tree = []
    for menu in menus:
        if menu.parent_id == parent_id or (menu.parent_id is None and parent_id is None):
            children = _build_menu_tree(menus, menu.id)
            tree.append({
                "id": menu.id, "parent_id": menu.parent_id,
                "name": menu.name, "name_zh_hans": menu.name_zh_hans, "name_en": menu.name_en,
                "icon": menu.icon or "layui-icon-app",
                "path": menu.path or "", "component": menu.component or "",
                "menu_type": menu.menu_type, "sort": menu.sort, "children": children,
            })
    tree.sort(key=lambda x: (x["sort"], x["id"]))
    return tree

@register.simple_tag(takes_context=True)
def render_sidebar_menu(context):
    request = context.get("request")
    if not request or not request.user.is_authenticated:
        return mark_safe("")
    user = request.user
    lang = getattr(user, "language", "zh-hans") if hasattr(user, "language") else "zh-hans"
    from django_layuix.rbac.engine import visible_menu_queryset
    qs = visible_menu_queryset(user, 'backend').order_by("sort", "id")
    tree = _build_menu_tree(qs)
    if not tree:
        return mark_safe("")
    return mark_safe(_render_tree(tree, lang, request.path))

def _render_tree(items, lang, current_path=""):
    parts = []
    for item in items:
        name = item["name"]
        if lang == "en" and item.get("name_en"):
            name = item["name_en"]
        elif lang == "zh-hans" and item.get("name_zh_hans"):
            name = item["name_zh_hans"]
        children = item.get("children", [])
        if item["menu_type"] == 1:
            parts.append(_render_dir(item, name, children, lang, current_path))
        elif item["menu_type"] == 2:
            parts.append(_render_item(item, name, current_path))
    return chr(10).join(parts)
def _render_dir(item, name, children, lang, current_path=""):
    icon = item.get("icon", "layui-icon-app")
    child_html = _render_tree(children, lang, current_path) if children else ""
    return (
        _LT + 'div class="menu-group has-children" data-menu-id="%s"' + _GT +
        _LT + 'div class="menu-group-title"' + _GT +
        _LT + 'i class="layui-icon %s menu-dir-icon"' + _GT + _LT + '/i' + _GT +
        _LT + 'i class="menu-arrow"' + _GT + _LT + '/i' + _GT +
        _LT + 'span' + _GT + '%s' + _LT + '/span' + _GT +
        _LT + '/div' + _GT +
        _LT + 'div class="sub-menu open"' + _GT + '%s' + _LT + '/div' + _GT +
        _LT + '/div' + _GT
    ) % (str(item["id"]), _ea(icon), _e(name), child_html)

def _render_item(item, name, current_path=""):
    icon = item.get("icon", "layui-icon-app")
    raw_url = item.get("path") or item.get("component") or ""
    url = MENU_PATH_MAP.get(raw_url, raw_url)
    active = ' active' if current_path and current_path.rstrip('/') == url.rstrip('/') else ''
    return (
        _LT + 'div class="menu-item' + active + '" data-url="%s" data-title="%s"' + _GT +
        _LT + 'i class="layui-icon %s menu-icon"' + _GT + _LT + '/i' + _GT +
        _LT + 'span class="menu-text"' + _GT + '%s' + _LT + '/span' + _GT +
        _LT + '/div' + _GT
    ) % (_ea(url), _ea(name), _ea(icon), _e(name))

def _e(text):
    if not text: return ""
    return (str(text)
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace('\'', '&#39;'))

def _ea(text):
    return _e(text)
