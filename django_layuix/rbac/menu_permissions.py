# -*- coding: utf-8 -*-
"""Stable permission codes assigned to built-in menus.

Read-only management APIs use these codes so authorization follows role/menu
assignment instead of relying on login-only checks.
"""

MENU_VIEW_PERMISSIONS = {
    '仪表盘': 'dashboard:view',
    '菜单管理': 'menu:view',
    '角色管理': 'role:view',
    '用户管理': 'user:view',
    '操作日志': 'log:view',
    '系统配置': 'config:view',
    '字典管理': 'dict:view',
    '服务器管理': 'server:view',
    'AI 配置': 'ai_config:view',
    'ABAC 策略': 'abac:view',
    '数据范围': 'scope:view',
    '约束管理': 'constraint:view',
}
