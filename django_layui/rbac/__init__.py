# -*- coding: utf-8 -*-
"""
django-layui RBAC module
"""

from django_layui.rbac.menu_registry import (
    register_menus, 
    unregister_menus,
    auto_register_admin_apps
)
from django_layui.rbac.ajax_admin import LayuiAjaxAdmin, layer
from django_layui.rbac.themes import (
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
