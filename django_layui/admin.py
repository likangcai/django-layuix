"""
自定义 Django Admin Site
用于传递 LAYUI_CONFIG 到模板上下文
"""
from django.contrib.admin import AdminSite, site
from django.conf import settings
from .rbac.themes import get_all_themes


class LayuiAdminSite(AdminSite):
    """自定义 AdminSite，传递 Layui 配置到模板"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 共享默认 admin.site 的注册表
        self._registry = site._registry
    
    def get_urls(self):
        """每次获取 URL 时同步注册表，确保包含所有最新注册的模型"""
        # 重新同步注册表（解决菜单丢失问题）
        self._registry = site._registry
        return super().get_urls()
    
    def each_context(self, request):
        """扩展模板上下文，添加 layui 配置"""
        context = super().each_context(request)
        
        # 从 settings 获取 LAYUI_CONFIG
        layui_config = getattr(settings, 'LAYUI_CONFIG', {})
        
        # 将配置添加到上下文（不做任何默认值处理）
        context['layui_config'] = layui_config
        
        # 添加可用主题列表（深色/浅色双模式）
        context['available_themes'] = get_all_themes()
        
        return context


# 创建全局实例
layui_admin_site = LayuiAdminSite(name='layui_admin')
