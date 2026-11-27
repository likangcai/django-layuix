# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-26 22:19
# @FileName  : layui_tags.py
# -----------------------------
from django import template
from django.conf import settings

from datetime import datetime

import django_layuix

register = template.Library()

# 静态资源版本号：与 iframe 缓存参数保持同一量级（分钟级），避免两套口径
_STATIC_VERSION = datetime.now().strftime('%Y%m%d%H%M')


def _get_db_config(key, default=''):
    """从数据库读取配置，settings 作为兜底"""
    config = getattr(settings, 'LAYUI_CONFIG', {})
    settings_value = config.get(key, default)
    try:
        from django_layuix.rbac.models import SystemConfig
        db_config = SystemConfig.objects.filter(key=key).first()
        if db_config:
            return db_config.value
    except Exception:
        pass
    return settings_value


@register.simple_tag
def layui_config(key, default=''):
    """获取配置值：优先数据库，其次 settings，最后使用默认值。"""
    return _get_db_config(key, default)


@register.simple_tag
def layui_version():
    """返回 Layui 版本。"""
    return getattr(settings, 'LAYUI_VERSION', '2.13.9')


@register.simple_tag
def layui_cdn():
    """返回 Layui 资源地址（默认使用本地内置文件）。"""
    return getattr(settings, 'LAYUI_CDN', '/static/layui/lib/')


@register.simple_tag
def system_name():
    """从配置返回系统名称（优先数据库，settings 回退）。"""
    return _get_db_config('system_name', 'Django Layuix Admin')


@register.simple_tag
def static_version():
    """返回用于缓存刷新的静态资源版本号。"""
    return _STATIC_VERSION


@register.simple_tag
def system_version():
    """返回系统版本。"""
    return _get_db_config('system_version', django_layuix.__version__)


@register.simple_tag
def system_description():
    """返回系统描述。"""
    return _get_db_config('system_description', '')


@register.simple_tag
def frontend_url():
    """返回前端站点地址。"""
    return _get_db_config('frontend_url', '')


@register.simple_tag
def logo_url():
    """返回 Logo 地址。"""
    return _get_db_config('logo_url', '')


@register.simple_tag
def logo_icon():
    """返回 Logo 图标类名。"""
    return _get_db_config('logo_icon', 'layui-icon-code-circle')


@register.simple_tag
def favicon_url():
    """返回 Favicon 地址。"""
    return _get_db_config('favicon_url', '')


@register.simple_tag
def login_bg_type():
    """返回登录背景类型。"""
    return _get_db_config('login_bg_type', 'gradient')


@register.simple_tag
def login_bg_value():
    """返回登录背景值。"""
    return _get_db_config('login_bg_value', 'linear-gradient(135deg, #2d3a4b 0%, #1a1a2e 100%)')


@register.simple_tag
def login_bg_image():
    """返回登录背景图片地址。"""
    return _get_db_config('login_bg_image', '')


@register.simple_tag
def copyright_text():
    """返回版权文本。"""
    return _get_db_config('copyright', '')


@register.simple_tag
def supported_languages():
    """返回支持的语言。"""
    return getattr(settings, 'LAYUI_LANGUAGES',
                   [('zh-hans', '简体中文'), ('en', 'English')])


@register.simple_tag
def webssh_url():
    """返回 WebSSH 服务地址。"""
    # 优先从数据库读取（系统配置）
    try:
        from django_layuix.rbac.models import SystemConfig
        db_config = SystemConfig.objects.filter(key='webssh_url').first()
        if db_config and db_config.value:
            return db_config.value
    except Exception:
        pass
    
    # 回退到 settings.py 中的 LAYUI_CONFIG
    config = getattr(settings, 'LAYUI_CONFIG', {})
    return config.get('webssh_url', '/webssh/')
