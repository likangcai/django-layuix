# -*- coding: utf-8 -*-
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
    return rows.filter(status=True, visible=True).exists()


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
        'menu', 'role', 'user', 'config', 'server', 'ai_config',
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


def register_page_permissions():
    """Register built-in page codes as hidden permission nodes."""
    from .models import Menu, Role

    parent, _ = Menu.objects.get_or_create(
        name='权限目录',
        defaults={
            'icon': 'layui-icon-vercode',
            'menu_type': 1,
            'sort': 9999,
            'status': True,
            'visible': True,
            'backend_visible': False,
            'frontend_visible': False,
        },
    )
    created = []
    for path, code in sorted(PAGE_PERMISSIONS.items()):
        menu, is_new = Menu.objects.get_or_create(
            parent=parent, name=code,
            defaults={
                'menu_type': 3,
                'permission': code,
                'sort': 1,
                'status': True,
                'visible': True,
                'backend_visible': False,
                'frontend_visible': False,
                'path': path,
            },
        )
        if is_new:
            created.append(code)
    admin_role = Role.objects.filter(code='admin').first()
    if admin_role:
        admin_role.menus.add(parent)
        for menu in Menu.objects.filter(parent=parent, permission__in=PAGE_PERMISSIONS.values()):
            admin_role.menus.add(menu)
    return created
