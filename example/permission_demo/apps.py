from django.apps import AppConfig
from django.db.models.signals import post_migrate

from django_layuix.rbac.demo_specs import BUTTON_SPECS, DEMO_PARENT_MENU, MENU_SPECS


class PermissionDemoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'permission_demo'
    verbose_name = '权限示例'

    def ready(self):
        self._register_api_urls()
        post_migrate.connect(
            self._register_menus,
            sender=self,
            dispatch_uid='permission_demo_register_menus',
        )

    def _register_menus(self, sender=None, **kwargs):
        from django_layuix.rbac.menu_registry import register_menus
        from django_layuix.rbac.models import Menu

        Menu.objects.get_or_create(**DEMO_PARENT_MENU)
        register_menus(menus_data=MENU_SPECS, buttons_data=BUTTON_SPECS)
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
