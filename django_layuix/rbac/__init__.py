# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-26 22:19
# @FileName  : __init__.py
# -----------------------------
"""django-layuix RBAC 模块。"""

from django_layuix.rbac.menu_registry import (
    register_menus, 
    unregister_menus,
    auto_register_admin_apps
)
from django_layuix.rbac.ajax_admin import LayuiAjaxAdmin, layer
from django_layuix.rbac.themes import (
    get_theme_by_name,
    get_all_themes,
    get_theme_colors
)

__all__ = [
    'register_menus', 
    'unregister_menus', 
    'auto_register_admin_apps',
    'LayuiAjaxAdmin',
    'layer',
    'get_theme_by_name',
    'get_all_themes',
    'get_theme_colors',
]
