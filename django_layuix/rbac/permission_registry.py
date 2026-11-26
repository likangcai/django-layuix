# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-26 22:19
# @FileName  : permission_registry.py
# -----------------------------
"""Central permission catalog for built-in pages, buttons and fields.

A permission is usable only after it is registered as an active ``Menu`` row
with a non-empty ``permission`` code. Role assignment then controls whether a
user can use the registered permission.
"""
from django.conf import settings


PAGE_PERMISSIONS = {
    '/static/layui/pages/dashboard.html': 'dashboard:view',
    '/static/layui/pages/menu.html': 'menu:view',
    '/static/layui/pages/role.html': 'role:view',
    '/static/layui/pages/user.html': 'user:view',
    '/static/layui/pages/log.html': 'log:view',
    '/static/layui/pages/config.html': 'config:view',
    '/static/layui/pages/dict.html': 'dict:view',
    '/static/layui/pages/permission.html': 'permission:view',
    '/static/layui/pages/dept.html': 'dept:view',
    '/static/layui/pages/position.html': 'position:view',
    '/static/layui/pages/region.html': 'region:view',
    '/static/layui/pages/member-level.html': 'member_level:view',
    '/static/layui/pages/ai-config.html': 'ai_config:view',
    '/static/layui/pages/server.html': 'server:view',
    '/static/layui/pages/abac.html': 'abac:view',
    '/static/layui/pages/scope.html': 'scope:view',
    '/static/layui/pages/constraints.html': 'constraint:view',
    '/static/layui/pages/profile.html': 'profile:view',
    '/static/layui/pages/frontend.html': 'frontend:view',
    '/static/permission_demo/pages/order.html': 'permission_demo:view',
    '/static/store/pages/product.html': 'product:view',
    '/static/store/pages/category.html': 'category:view',
    '/static/store/pages/order.html': 'store_order:view',
}

BUTTON_ACTIONS = {
    'view': ('查看', 'View'),
    'add': ('新增', 'Add'),
    'edit': ('编辑', 'Edit'),
    'delete': ('删除', 'Delete'),
    'copy': ('复制', 'Copy'),
    'export': ('导出', 'Export'),
    'import': ('导入', 'Import'),
    'assign': ('分配', 'Assign'),
    'reset_password': ('重置密码', 'Reset password'),
    'toggle_status': ('启用/禁用', 'Toggle status'),
    'test': ('测试连接', 'Test connection'),
    'set_default': ('设为默认', 'Set default'),
    'view_log': ('查看日志', 'View log'),
    'terminal': ('终端连接', 'Terminal'),
}


def _allow_unregistered():
    return bool(getattr(settings, 'LAYUI_RBAC_ALLOW_UNREGISTERED_PERMISSIONS', False))


def is_registered_permission(permission_code):
    """Whether a permission code exists as an active registered Menu entry.

    Built-in codes are available before initialization through the central
    catalog. Once a matching ``sys_menu`` row exists, its active/visible state
    is authoritative, so disabling a registered permission takes effect
    immediately. Custom codes must be registered as active Menu rows.
    """
    if not permission_code:
        return False
    if _allow_unregistered():
        return True
    from django.db import connection

    builtin = permission_code in permission_catalog()
    if 'sys_menu' not in connection.introspection.table_names():
        return builtin
    from .models import Menu

    rows = Menu.objects.filter(permission=permission_code)
    if not builtin:
        return rows.filter(status=True, visible=True).exists()
    if not rows.exists():
        return True
    catalog_rows = rows.filter(plugin_key='permission_catalog')
    if catalog_rows.exists():
        return catalog_rows.filter(status=True, visible=True).exists()
    business_rows = rows.exclude(plugin_key='permission_catalog')
    if business_rows.exists():
        return business_rows.filter(status=True, visible=True).exists()
    return builtin


def permission_for_path(path):
    """Resolve the required permission code for a frontend page path."""
    if not path:
        return ''
    clean = str(path).split('?', 1)[0].split('#', 1)[0]
    if clean in PAGE_PERMISSIONS:
        return PAGE_PERMISSIONS[clean]
    for prefix, code in PAGE_PERMISSIONS.items():
        if clean.endswith(prefix.split('/')[-1]):
            return code
    return ''


def permission_catalog():
    """Return all built-in permission codes from the central catalog."""
    codes = set(PAGE_PERMISSIONS.values())
    for prefix in _button_prefixes():
        for action in BUTTON_ACTIONS:
            codes.add('%s:%s' % (prefix, action))
    return sorted(codes)


def _button_prefixes():
    prefixes = set()
    for code in PAGE_PERMISSIONS.values():
        if ':' in code:
            prefixes.add(code.split(':', 1)[0])
    prefixes.update([
        'menu', 'role', 'user', 'config', 'dict', 'server', 'ai_config',
        'abac', 'scope', 'constraint', 'profile', 'product',
        'category', 'store_order', 'permission_demo',
    ])
    return prefixes


def build_permission_code(prefix, action):
    """Build a canonical permission code for a menu/action pair."""
    prefix = str(prefix or '').strip().strip(':').lower()
    action = str(action or '').strip().lower()
    if not prefix or action not in BUTTON_ACTIONS:
        return ''
    return '%s:%s' % (prefix, action)


def _catalog_node(parent, code, defaults):
    """Return one catalog row per parent/code and merge legacy duplicates."""
    from .models import Menu

    rows = list(Menu.objects.filter(parent=parent, permission=code).order_by('id'))
    if rows:
        keeper = rows[0]
        for duplicate in rows[1:]:
            keeper.roles.add(*duplicate.roles.all())
            duplicate.delete()
        return keeper, False
    try:
        return Menu.objects.get_or_create(
            parent=parent, permission=code, defaults=defaults,
        )
    except Exception:
        row = Menu.objects.filter(parent=parent, permission=code).order_by('id').first()
        return row, False


def register_page_permissions():
    """Register all built-in page and button codes as permission nodes."""
    from .models import Menu, Role

    parent = Menu.objects.filter(name='权限目录').order_by('id').first()
    if parent is None:
        parent = Menu.objects.create(
            name='权限目录',
            icon='layui-icon-vercode',
            menu_type=1,
            plugin_key='permission_catalog',
            sort=9999,
            status=True,
            visible=True,
            backend_visible=False,
            frontend_visible=False,
        )
    button_parent = Menu.objects.filter(
        parent=parent, name='按钮权限目录'
    ).order_by('id').first()
    if button_parent is None:
        button_parent = Menu.objects.create(
            parent=parent,
            name='按钮权限目录',
            icon='layui-icon-vercode',
            menu_type=1,
            plugin_key='permission_catalog',
            sort=2,
            status=True,
            visible=True,
            backend_visible=False,
            frontend_visible=False,
        )
    created = []
    page_codes = set(PAGE_PERMISSIONS.values())
    for path, code in sorted(PAGE_PERMISSIONS.items()):
        menu, is_new = _catalog_node(parent, code, {
            'name': code,
            'menu_type': 3,
            'plugin_key': 'permission_catalog',
            'sort': 1,
            'status': True,
            'visible': True,
            'backend_visible': False,
            'frontend_visible': False,
            'path': path,
        })
        if is_new:
            created.append(code)

    for code in permission_catalog():
        if code in page_codes:
            continue
        menu, is_new = _catalog_node(button_parent, code, {
            'name': code,
            'menu_type': 3,
            'plugin_key': 'permission_catalog',
            'sort': 2,
            'status': True,
            'visible': True,
            'backend_visible': False,
            'frontend_visible': False,
            'path': '',
        })
        if is_new:
            created.append(code)
    Menu.objects.filter(pk__in=[parent.pk, button_parent.pk]).update(
        plugin_key='permission_catalog'
    )
    Menu.objects.filter(parent_id__in=[parent.pk, button_parent.pk]).update(
        plugin_key='permission_catalog'
    )
    from django.db import IntegrityError

    for menu in Menu.objects.filter(
        plugin_key='permission_catalog', permission__gt='', catalog_key__isnull=True
    ).order_by('id'):
        try:
            menu.save(update_fields=['catalog_key'])
        except IntegrityError:
            # 保留历史重复记录可读；第一条记录持有唯一键。
            continue
    admin_role = Role.objects.filter(code='admin').first()
    if admin_role:
        admin_role.menus.add(parent)
        admin_role.menus.add(button_parent)
        catalog_codes = permission_catalog()
        for menu in Menu.objects.filter(permission__in=catalog_codes):
            admin_role.menus.add(menu)
    return created
