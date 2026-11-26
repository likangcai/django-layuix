# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-26 22:19
# @FileName  : themes.py
# -----------------------------
"""Django-Layuix 主题系统，简化为深色/浅色双模式。"""

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
    """按显示名称获取主题配置。"""
    for theme in DJANGO_LAYUIX_THEMES:
        if theme['name'] == name:
            return theme
    return None


def get_all_themes():
    """获取全部可用主题（仅深色/浅色）。"""
    return DJANGO_LAYUIX_THEMES


def get_theme_names():
    """获取全部主题显示名称。"""
    return [theme['name'] for theme in DJANGO_LAYUIX_THEMES]


def get_theme_colors(name):
    """获取指定主题的颜色配置。"""
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
        return '默认浅色'

    if theme_value in THEME_ALIAS_MAP:
        return THEME_ALIAS_MAP[theme_value]

    valid_names = get_theme_names()
    if theme_value in valid_names:
        return theme_value

    return '默认深色'


def get_display_theme(theme_value):
    """将存储的主题值转换为前端展示格式。标准主题返回 'dark'/'light'。"""
    if theme_value in REVERSE_THEME_MAP:
        return REVERSE_THEME_MAP[theme_value]
    return theme_value


def is_dark_mode(theme_value):
    """判断主题是否为深色模式。"""
    normalized = normalize_theme(theme_value)
    return normalized == '默认深色'
