from django.apps import AppConfig
from django.db.models.signals import post_migrate


class StoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'store'
    verbose_name = '商品管理'

    def ready(self):
        """Register URL bridges only; never query the database at startup."""
        self._register_store_api_urls()
        post_migrate.connect(
            self._on_post_migrate,
            sender=self,
            dispatch_uid='store.register_menus_post_migrate',
        )

    def _on_post_migrate(self, sender, **kwargs):
        self._register_store_menus()

    def _register_store_menus(self):
        """Register demo menus after migrations, when RBAC tables exist."""
        try:
            from django_layuix.rbac.menu_registry import register_menus
            from django_layuix.rbac.models import Menu

            register_menus(
                menus_data=[
                    ('演示应用', 'layui-icon-app', '', 1, 4, None),
                    ('商品分类', 'layui-icon-template-1', '/static/store/pages/category.html', 2, 1, '演示应用'),
                    ('商品管理', 'layui-icon-cart-simple', '/static/store/pages/product.html', 2, 2, '演示应用'),
                    ('订单管理', 'layui-icon-form', '/static/store/pages/order.html', 2, 3, '演示应用'),
                ],
                buttons_data=[
                    ('新增分类', '商品分类', 'category:add', 1),
                    ('编辑分类', '商品分类', 'category:edit', 2),
                    ('删除分类', '商品分类', 'category:delete', 3),
                    ('新增商品', '商品管理', 'product:add', 1),
                    ('编辑商品', '商品管理', 'product:edit', 2),
                    ('删除商品', '商品管理', 'product:delete', 3),
                    ('查看订单', '订单管理', 'order:view', 1),
                    ('新增订单', '订单管理', 'order:add', 2),
                    ('编辑订单', '订单管理', 'order:edit', 3),
                    ('订单发货', '订单管理', 'order:ship', 4),
                    ('取消订单', '订单管理', 'order:cancel', 5),
                    ('删除订单', '订单管理', 'order:delete', 6),
                ],
            )
            translations = {
                '演示应用': ('Demo App', '演示应用'),
                '商品分类': ('Categories', '商品分类'),
                '商品管理': ('Products', '商品管理'),
                '订单管理': ('Orders', '订单管理'),
            }
            for menu_name, (name_en, name_zh_hans) in translations.items():
                Menu.objects.filter(name=menu_name).update(
                    name_en=name_en, name_zh_hans=name_zh_hans,
                )
        except Exception as exc:
            # A migrate of an unrelated app can fire before RBAC tables exist.
            print('[StoreConfig] Menu registration skipped: %s' % exc)

    def _register_store_api_urls(self):
        """Register store API URLs under the admin site."""
        from django.contrib.admin import site
        from django.urls import include, path

        from . import urls as store_urls

        original_get_urls = site.get_urls

        def patched_get_urls():
            urls = original_get_urls()
            custom_urls = [
                path('api/store/', include((store_urls.urlpatterns, 'store'))),
            ]
            return custom_urls + urls

        site.get_urls = patched_get_urls
