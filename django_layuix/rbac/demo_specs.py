# -*- coding: utf-8 -*-
"""Shared declarations for the one-command permission demo."""

DEMO_PARENT_MENU = {
    'name': '演示应用',
    'defaults': {
        'name_en': 'Demo App', 'name_zh_hans': '演示应用',
        'icon': 'layui-icon-app', 'path': '', 'menu_type': 1, 'sort': 4,
        'status': True, 'visible': True, 'backend_visible': True,
        'frontend_visible': False,
    },
}

ROLE_SPECS = [
    ('demo_base', '示例基础角色', ['menu:view', 'role:view', 'user:view']),
    ('demo_manager', '示例区域经理', ['demo:order:view']),
    ('demo_maker', '示例制单员', ['demo:order:view']),
    ('demo_checker', '示例审核员', ['demo:order:view']),
    ('demo_finance', '示例财务', ['demo:order:view', 'demo:order:cost:view']),
    ('demo_sales', '示例销售', ['demo:order:view']),
]

MENU_SPECS = [
    ('示例订单', 'layui-icon-form', '/static/permission_demo/pages/order.html', 2, 6, '演示应用'),
]

BUTTON_SPECS = [
    ('查看示例订单', '示例订单', 'demo:order:view', 1),
    ('查看成本字段', '示例订单', 'demo:order:cost:view', 2),
]
