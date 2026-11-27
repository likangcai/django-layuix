# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-26 22:19
# @FileName  : menu_permissions.py
# -----------------------------
"""分配给内置菜单的稳定权限码。只读管理 API 使用这些权限码，使授权遵循角色/菜单分配，而不是仅依赖登录状态。"""

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
