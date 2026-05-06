# -*- coding: utf-8 -*-
"""
Django-Layui Theme System
Supports 26+ theme colors including:
- Classic themes (dark/light)
- Element UI style
- Ant Design style
- Admin LTE style
- Custom gradient themes
"""

DJANGO_LAYUI_THEMES = [
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
    {
        'name': 'Element蓝',
        'file': 'element-blue.css',
        'colors': {
            'primary': '#409EFF',
            'menu_bg': '#FFFFFF',
            'menu_text': '#606266',
            'header_bg': '#409EFF',
            'logo_color': '#FFFFFF',
        }
    },
    {
        'name': 'Ant Design黑',
        'file': 'ant-design-black.css',
        'colors': {
            'primary': '#1890FF',
            'menu_bg': '#001529',
            'menu_text': 'rgba(255,255,255,0.65)',
            'header_bg': '#001529',
            'logo_color': '#FFFFFF',
        }
    },
    {
        'name': 'AdminLTE蓝',
        'file': 'adminlte-blue.css',
        'colors': {
            'primary': '#3C8DBC',
            'menu_bg': '#2B3539',
            'menu_text': '#B7C0CE',
            'header_bg': '#3C8DBC',
            'logo_color': '#FFFFFF',
        }
    },
    {
        'name': '企业紫',
        'file': 'enterprise-purple.css',
        'colors': {
            'primary': '#8263B1',
            'menu_bg': '#263238',
            'menu_text': '#B0BEC5',
            'header_bg': '#8263B1',
            'logo_color': '#FFFFFF',
        }
    },
    {
        'name': '企业红',
        'file': 'enterprise-red.css',
        'colors': {
            'primary': '#C9333E',
            'menu_bg': '#1a1a1a',
            'menu_text': '#B0BEC5',
            'header_bg': '#C9333E',
            'logo_color': '#FFFFFF',
        }
    },
    {
        'name': '清新绿',
        'file': 'fresh-green.css',
        'colors': {
            'primary': '#27AD60',
            'menu_bg': '#FFFFFF',
            'menu_text': '#5F5F5F',
            'header_bg': '#27AD60',
            'logo_color': '#FFFFFF',
        }
    },
    {
        'name': '科技橙',
        'file': 'tech-orange.css',
        'colors': {
            'primary': '#FF6B35',
            'menu_bg': '#F7F7F7',
            'menu_text': '#333333',
            'header_bg': 'linear-gradient(to right, #DA8342, #E45131)',
            'logo_color': '#FFFFFF',
        }
    },
    {
        'name': '深邃黑',
        'file': 'deep-black.css',
        'colors': {
            'primary': '#00BCD4',
            'menu_bg': '#333333',
            'menu_text': '#B0BEC5',
            'header_bg': '#333333',
            'logo_color': '#E0F7FA',
        }
    },
    {
        'name': '优雅灰',
        'file': 'elegant-gray.css',
        'colors': {
            'primary': '#213A53',
            'menu_bg': '#E0E0E0',
            'menu_text': '#666666',
            'header_bg': '#213A53',
            'logo_color': '#FFFFFF',
        }
    },
    {
        'name': '天空蓝',
        'file': 'sky-blue.css',
        'colors': {
            'primary': '#02C0CE',
            'menu_bg': '#E0E0E0',
            'menu_text': '#666666',
            'header_bg': '#02C0CE',
            'logo_color': '#FFFFFF',
        }
    },
    {
        'name': '樱花粉',
        'file': 'sakura-pink.css',
        'colors': {
            'primary': '#FF6B9D',
            'menu_bg': '#FFF5F7',
            'menu_text': '#666666',
            'header_bg': '#FF6B9D',
            'logo_color': '#FFFFFF',
        }
    },
    {
        'name': '极光紫',
        'file': 'aurora-purple.css',
        'colors': {
            'primary': '#667eea',
            'menu_bg': '#1a1a2e',
            'menu_text': '#a0a0b0',
            'header_bg': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            'logo_color': '#FFFFFF',
        }
    },
    {
        'name': '暗夜蓝',
        'file': 'midnight-blue.css',
        'colors': {
            'primary': '#3E4295',
            'menu_bg': '#E0E0E0',
            'menu_text': '#666666',
            'header_bg': '#FFFFFF',
            'logo_color': '#3E4295',
        }
    },
    {
        'name': '薄荷青',
        'file': 'mint-cyan.css',
        'colors': {
            'primary': '#2F9688',
            'menu_bg': '#263238',
            'menu_text': '#B0BEC5',
            'header_bg': '#2F9688',
            'logo_color': '#FFFFFF',
        }
    },
    {
        'name': '烈焰红',
        'file': 'flame-red.css',
        'colors': {
            'primary': '#AA3130',
            'menu_bg': '#263238',
            'menu_text': '#B0BEC5',
            'header_bg': '#AA3130',
            'logo_color': '#FFFFFF',
        }
    },
    {
        'name': '商务蓝',
        'file': 'business-blue.css',
        'colors': {
            'primary': '#3BA1DF',
            'menu_bg': '#FFFFFF',
            'menu_text': '#666666',
            'header_bg': '#3BA1DF',
            'logo_color': '#FFFFFF',
        }
    },
    {
        'name': '高端黑',
        'file': 'premium-black.css',
        'colors': {
            'primary': '#1F2C39',
            'menu_bg': '#FFFFFF',
            'menu_text': '#666666',
            'header_bg': '#1F2C39',
            'logo_color': '#FFFFFF',
        }
    },
    {
        'name': '活力橙',
        'file': 'vibrant-orange.css',
        'colors': {
            'primary': '#F57C00',
            'menu_bg': '#FAFAFA',
            'menu_text': '#424242',
            'header_bg': '#F57C00',
            'logo_color': '#FFFFFF',
        }
    },
    {
        'name': '森林绿',
        'file': 'forest-green.css',
        'colors': {
            'primary': '#19A97B',
            'menu_bg': '#FFFFFF',
            'menu_text': '#666666',
            'header_bg': '#19A97B',
            'logo_color': '#FFFFFF',
        }
    },
    {
        'name': '深海蓝',
        'file': 'deep-sea.css',
        'colors': {
            'primary': '#00695C',
            'menu_bg': '#263238',
            'menu_text': '#B0BEC5',
            'header_bg': '#00695C',
            'logo_color': '#FFFFFF',
        }
    },
    {
        'name': '玫瑰金',
        'file': 'rose-gold.css',
        'colors': {
            'primary': '#B76E79',
            'menu_bg': '#FFF8F0',
            'menu_text': '#666666',
            'header_bg': '#B76E79',
            'logo_color': '#FFFFFF',
        }
    },
    {
        'name': '极客绿',
        'file': 'geek-green.css',
        'colors': {
            'primary': '#00FF00',
            'menu_bg': '#0D0D0D',
            'menu_text': '#00FF00',
            'header_bg': '#000000',
            'logo_color': '#00FF00',
        }
    },
    {
        'name': '赛博朋克',
        'file': 'cyberpunk.css',
        'colors': {
            'primary': '#FCEE0A',
            'menu_bg': '#000000',
            'menu_text': '#00F0FF',
            'header_bg': 'linear-gradient(90deg, #FCEE0A 0%, #00F0FF 100%)',
            'logo_color': '#000000',
        }
    },
]


def get_theme_by_name(name):
    """Get theme configuration by display name"""
    for theme in DJANGO_LAYUI_THEMES:
        if theme['name'] == name:
            return theme
    return None


def get_all_themes():
    """Get all available themes"""
    return DJANGO_LAYUI_THEMES


def get_theme_names():
    """Get all theme display names"""
    return [theme['name'] for theme in DJANGO_LAYUI_THEMES]


def get_theme_colors(name):
    """Get color configuration for a specific theme"""
    theme = get_theme_by_name(name)
    if theme:
        return theme.get('colors', {})
    return {}
