from django.apps import AppConfig


class PermissionDemoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'permission_demo'
    verbose_name = '权限示例'

    def ready(self):
        self._register_api_urls()
        try:
            self._register_menus()
        except Exception as exc:
            print('Warning: Could not register permission demo menus: %s' % exc)

    def _register_menus(self):
        from django_layuix.rbac.menu_registry import register_menus
        from django_layuix.rbac.models import Menu

        Menu.objects.get_or_create(
            name='演示应用',
            defaults={
                'name_en': 'Demo App', 'name_zh_hans': '演示应用',
                'icon': 'layui-icon-app', 'path': '', 'menu_type': 1, 'sort': 4,
                'status': True, 'visible': True, 'backend_visible': True,
                'frontend_visible': False,
            },
        )
        register_menus(
            menus_data=[
                ('示例订单', 'layui-icon-form', '/static/permission_demo/pages/order.html', 2, 6, '演示应用'),
            ],
            buttons_data=[
                ('查看示例订单', '示例订单', 'demo:order:view', 1),
                ('查看成本字段', '示例订单', 'demo:order:cost:view', 2),
            ],
        )
        Menu.objects.filter(name='示例订单').update(
            name_en='Demo Orders', name_zh_hans='示例订单'
        )
        Menu.objects.filter(permission__in=['demo:order:view', 'demo:order:cost:view']).update(
            name_en='Demo Order Permissions', name_zh_hans='示例订单权限'
        )

    def _register_api_urls(self):
        from django.contrib.admin import site
        from django.urls import include, path

        if getattr(site, '_permission_demo_urls_registered', False):
            return
        original_get_urls = site.get_urls

        def patched_get_urls():
            from . import urls as demo_urls

            return [
                path('api/permission-demo/', include((demo_urls.urlpatterns, 'permission_demo'))),
            ] + original_get_urls()

        site.get_urls = patched_get_urls
        site._permission_demo_urls_registered = True
