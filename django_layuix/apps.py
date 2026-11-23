from django.apps import AppConfig
from django.contrib import admin


class DjangoLayuiConfig(AppConfig):
    name = 'django_layuix'
    verbose_name = 'Django Layuix Admin'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        # 替换默认的 admin.site 为自定义的 LayuiAdminSite
        # 这样可以传递 LAYUI_CONFIG 到模板上下文
        from django.contrib.admin.options import ModelAdmin
        from .admin import layui_admin_site

        # 直接 patch ModelAdmin.get_changelist_instance
        # 使其在实例化 ChangeList 前读取 ?per_page= 参数动态更新 list_per_page
        original_get_changelist_instance = ModelAdmin.get_changelist_instance
        
        def patched_get_changelist_instance(self, request):
            # 优先调用自定义 get_list_per_page（如果定义了）
            if hasattr(self, 'get_list_per_page'):
                self.list_per_page = self.get_list_per_page(request)
            else:
                # 通用处理：读取 ?per_page= 参数
                per_page = request.GET.get('per_page')
                if per_page and per_page.isdigit():
                    self.list_per_page = int(per_page)
            return original_get_changelist_instance(self, request)
        
        ModelAdmin.get_changelist_instance = patched_get_changelist_instance
        
        # 保存原始的 admin.site 引用
        original_site = admin.site
        
        # 替换为自定义站点
        admin.site = layui_admin_site
        
        # 加载通用认证桥接与第三方框架适配器
        from .integrations.auth import load_configured_authenticators
        load_configured_authenticators()
        try:
            from .integrations import drf  # noqa: F401
        except ImportError:
            pass
        try:
            from .integrations import ninja  # noqa: F401
        except ImportError:
            pass

        # 发现通过 entry_points 安装的第三方插件
        from .rbac.plugins import discover_entry_point_plugins
        try:
            discover_entry_point_plugins()
        except Exception:
            pass
