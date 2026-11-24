# -*- coding: utf-8 -*-
"""
Django-Layuix Theme System
Simplified to Dark/Light dual mode only
"""

DJANGO_LAYUIX_THEMES = [
    {
        'name': '默认深色',
        'file': 'default-dark.css',
        'colors': {
            'primary': '#1E9FFF',
            'menu_bg': '#232935',
            'menu_text': '#BFCBD9',
            'header_bg': '#232935',
            'logo_color': '#FFFFFF',
        }
    },
    {
        'name': '默认浅色',
        'file': 'default-light.css',
        'colors': {
            'primary': '#1E9FFF',
            'menu_bg': '#FFFFFF',
            'menu_text': '#646a73',
            'header_bg': '#FFFFFF',
            'logo_color': '#1E9FFF',
        }
    },
]

# 兼容旧版本导入名
DJANGO_LAYUI_THEMES = DJANGO_LAYUIX_THEMES


def get_theme_by_name(name):
    """Get theme configuration by display name"""
    for theme in DJANGO_LAYUIX_THEMES:
        if theme['name'] == name:
            return theme
    return None


def get_all_themes():
    """Get all available themes (dark/light only)"""
    return DJANGO_LAYUIX_THEMES


def get_theme_names():
    """Get all theme display names"""
    return [theme['name'] for theme in DJANGO_LAYUIX_THEMES]


def get_theme_colors(name):
    """Get color configuration for a specific theme"""
    theme = get_theme_by_name(name)
    if theme:
        return theme.get('colors', {})
    return {}


# ==================== Theme Normalization ====================
THEME_ALIAS_MAP = {
    'dark': '默认深色',
    'light': '默认浅色',
}

REVERSE_THEME_MAP = {v: k for k, v in THEME_ALIAS_MAP.items()}


def normalize_theme(theme_value):
    """
    Normalize theme value to standard format.
    Supports:
    - New format: 'dark', 'light'
    - Legacy format: '默认深色', '默认浅色'
    - Other legacy themes: fallback to dark mode
    """
    if not theme_value:
        return '默认深色'

    if theme_value in THEME_ALIAS_MAP:
        return THEME_ALIAS_MAP[theme_value]

    valid_names = get_theme_names()
    if theme_value in valid_names:
        return theme_value

    return '默认深色'


def get_display_theme(theme_value):
    """
    Convert stored theme value to frontend display format.
    Returns 'dark'/'light' for standard themes.
    """
    if theme_value in REVERSE_THEME_MAP:
        return REVERSE_THEME_MAP[theme_value]
    return theme_value


def is_dark_mode(theme_value):
    """Check if theme is dark mode"""
    normalized = normalize_theme(theme_value)
    return normalized == '默认深色'
