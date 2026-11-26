# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-26 22:19
# @FileName  : defaults.py
# -----------------------------
"""SystemConfig 默认值的唯一来源。"""
import json

import django_layuix


def _json(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


HOME_STATS_CARDS = [
    {'title': '系统用户', 'icon': 'layui-icon-user', 'color': '#1E9FFF', 'api_field': 'user_count'},
    {'title': '系统角色', 'icon': 'layui-icon-template-1', 'color': '#5FB878', 'api_field': 'role_count'},
    {'title': '菜单数量', 'icon': 'layui-icon-app', 'color': '#FFB800', 'api_field': 'menu_count'},
    {'title': '操作日志', 'icon': 'layui-icon-log', 'color': '#FF5722', 'api_field': 'log_count'},
]

HOME_QUICK_LINKS = [
    {'name': 'Django官网', 'icon': 'layui-icon-website', 'url': 'https://www.djangoproject.com/'},
    {'name': 'Layui文档', 'icon': 'layui-icon-template', 'url': 'https://www.layui.dev/'},
    {'name': 'GitHub', 'icon': 'layui-icon-github', 'url': 'https://github.com/likangcai/django-layuix'},
    {'name': 'Gitee', 'icon': 'layui-icon-gitee', 'url': 'https://gitee.com/yingzi_shadow/django-layuix'},
]


def get_default_configs():
    """按稳定顺序返回全部 SystemConfig 行。"""
    return [
        {'key': 'system_name', 'value': 'Django Layuix Admin', 'description': '系统名称，显示在浏览器标题栏和侧边栏', 'config_type': 'string', 'sort': 1},
        {'key': 'system_version', 'value': django_layuix.__version__, 'description': '系统版本号', 'config_type': 'string', 'sort': 2},
        {'key': 'system_description', 'value': '', 'description': '系统描述信息（显示在管理后台底部）', 'config_type': 'text', 'sort': 3},
        {'key': 'logo_icon', 'value': 'layui-icon-code-circle', 'description': 'Logo图标（layui图标类名）', 'config_type': 'string', 'sort': 4},
        {'key': 'logo_url', 'value': '', 'description': 'Logo图片URL（设置后替换图标，支持本地上传）', 'config_type': 'image', 'sort': 5},
        {'key': 'favicon_url', 'value': '', 'description': '浏览器标签页图标URL（支持ICO/PNG/SVG，支持本地上传）', 'config_type': 'image', 'sort': 6},
        {'key': 'copyright', 'value': '', 'description': '版权信息（显示在登录页和管理后台底部）', 'config_type': 'string', 'sort': 7},
        {'key': 'frontend_url', 'value': '', 'description': '前端页面地址（顶部"查看站点"按钮跳转地址）', 'config_type': 'url', 'sort': 8},
        {'key': 'webssh_url', 'value': '/webssh/', 'description': 'WebSSH 服务地址（用于服务器终端功能）', 'config_type': 'url', 'sort': 9},
        {'key': 'login_bg_type', 'value': 'gradient', 'description': '登录页背景类型：gradient(渐变)/color(纯色)/image(图片)', 'config_type': 'string', 'sort': 10},
        {'key': 'login_bg_value', 'value': 'linear-gradient(135deg, #2d3a4b 0%, #1a1a2e 100%)', 'description': '登录页背景渐变/颜色值（当type为gradient或color时生效）', 'config_type': 'color', 'sort': 11},
        {'key': 'login_bg_image', 'value': '', 'description': '登录页背景图片URL（当type为image时生效，支持本地上传）', 'config_type': 'image', 'sort': 12},
        {'key': 'home_stats_cards', 'value': _json(HOME_STATS_CARDS), 'description': '首页统计卡片配置（JSON 格式）', 'config_type': 'json', 'sort': 13},
        {'key': 'home_quick_links', 'value': _json(HOME_QUICK_LINKS), 'description': '首页快速链接配置（JSON 格式）', 'config_type': 'json', 'sort': 14},
        {'key': 'rbac_max_roles_per_user', 'value': '0', 'description': 'RBAC2：每个用户最多可分配角色数，0表示不限', 'config_type': 'integer', 'sort': 15},
        {'key': 'rbac_prerequisite_strategy', 'value': 'auto_grant', 'description': 'RBAC4：前置角色策略 auto_grant/reject', 'config_type': 'string', 'sort': 16},
        {'key': 'rbac_dsd_strategy', 'value': 'greedy', 'description': 'RBAC4：DSD 激活策略 greedy/explicit', 'config_type': 'string', 'sort': 17},
    ]
