from django import template
from django.conf import settings

from datetime import datetime

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
    """Get configuration value: database first, settings second, default last."""
    return _get_db_config(key, default)


@register.simple_tag
def layui_version():
    """Return layui version"""
    return getattr(settings, 'LAYUI_VERSION', '2.13.5')


@register.simple_tag
def layui_cdn():
    """Return layui resource URL (defaults to local bundled files)"""
    return getattr(settings, 'LAYUI_CDN', '/static/layui/lib/')


@register.simple_tag
def system_name():
    """Return system name from config (database first, settings fallback)"""
    return _get_db_config('system_name', 'Django Layuix Admin')


@register.simple_tag
def static_version():
    """Return static resource version string for cache busting"""
    return _STATIC_VERSION


@register.simple_tag
def system_version():
    """Return system version"""
    return _get_db_config('system_version', '1.4.2')


@register.simple_tag
def system_description():
    """Return system description"""
    return _get_db_config('system_description', '')


@register.simple_tag
def frontend_url():
    """Return frontend URL"""
    return _get_db_config('frontend_url', '')


@register.simple_tag
def logo_url():
    """Return logo URL"""
    return _get_db_config('logo_url', '')


@register.simple_tag
def logo_icon():
    """Return logo icon class"""
    return _get_db_config('logo_icon', 'layui-icon-code-circle')


@register.simple_tag
def favicon_url():
    """Return favicon URL"""
    return _get_db_config('favicon_url', '')


@register.simple_tag
def login_bg_type():
    """Return login background type"""
    return _get_db_config('login_bg_type', 'gradient')


@register.simple_tag
def login_bg_value():
    """Return login background value"""
    return _get_db_config('login_bg_value', 'linear-gradient(135deg, #2d3a4b 0%, #1a1a2e 100%)')


@register.simple_tag
def login_bg_image():
    """Return login background image URL"""
    return _get_db_config('login_bg_image', '')


@register.simple_tag
def copyright_text():
    """Return copyright text"""
    return _get_db_config('copyright', '')


@register.simple_tag
def supported_languages():
    """Return supported languages"""
    return getattr(settings, 'LAYUI_LANGUAGES',
                   [('zh-hans', '简体中文'), ('en', 'English')])


@register.simple_tag
def webssh_url():
    """Return webssh service URL"""
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
