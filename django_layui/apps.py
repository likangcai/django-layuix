from django.apps import AppConfig
from django.contrib import admin


class DjangoLayuiConfig(AppConfig):
    name = 'django_layui'
    verbose_name = 'Django Layui Admin'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        # 替换默认的 admin.site 为自定义的 LayuiAdminSite
        # 这样可以传递 LAYUI_CONFIG 到模板上下文
        from .admin import layui_admin_site
        
        # 保存原始的 admin.site 引用
        original_site = admin.site
        
        # 替换为自定义站点
        admin.site = layui_admin_site
        
        # 迁移所有已注册的模型
        for model, model_admin in original_site._registry.items():
            admin.site.register(model, model_admin.__class__)
        
        # BUG-05 FIX: 不直接修改 settings.MIDDLEWARE（线程不安全且可能无效）
        # 改为通过文档告知用户手动移除 XFrameOptionsMiddleware
        # 或者在模板中通过 django.middleware.common.BreakPathMiddleware 处理
        pass
