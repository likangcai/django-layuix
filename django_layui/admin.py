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
        
        # 从 settings 获取 LAYUI_CONFIG 作为默认值
        layui_config = getattr(settings, 'LAYUI_CONFIG', {})
        
        # 从数据库读取系统配置，优先级高于 settings.py
        try:
            from .rbac.models import SystemConfig
            db_configs = SystemConfig.objects.all()
            for cfg in db_configs:
                # 对于 home_quick_links 和 home_stats_cards，始终尝试解析为 JSON
                if cfg.key in ('home_quick_links', 'home_stats_cards'):
                    import json
                    try:
                        layui_config[cfg.key] = json.loads(cfg.value)
                    except (json.JSONDecodeError, TypeError):
                        # 如果解析失败，使用原始字符串值
                        layui_config[cfg.key] = cfg.value
                # 对于其他 json 类型的配置，也尝试解析
                elif cfg.config_type == 'json':
                    import json
                    try:
                        layui_config[cfg.key] = json.loads(cfg.value)
                    except (json.JSONDecodeError, TypeError):
                        layui_config[cfg.key] = cfg.value
                else:
                    layui_config[cfg.key] = cfg.value
        except Exception:
            # 数据库查询失败时忽略，使用 settings.py 中的默认值
            pass
        
        # 将配置添加到上下文
        context['layui_config'] = layui_config
        
        # 添加可用主题列表（深色/浅色双模式）
        context['available_themes'] = get_all_themes()
        
        return context


# 创建全局实例
layui_admin_site = LayuiAdminSite(name='layui_admin')
