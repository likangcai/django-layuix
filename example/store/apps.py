from django.apps import AppConfig


class StoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'store'
    verbose_name = '商品管理'
    
    def ready(self):
        """
        应用启动时注册菜单
        使用 register_menus 手动注册，菜单指向 Layui 前端静态页面（如 /static/store/pages/category.html）
        取代原有的 Django admin 原生页面
        """
        try:
            from django_layuix.rbac.menu_registry import register_menus
            from django_layuix.rbac.models import Menu

            # 检查是否已经存在完整的菜单结构
            if Menu.objects.filter(name='权限管理').exists():
                # 已存在完整菜单结构，用 register_menus 更新 store 菜单
                pass

            import store.admin  # noqa: F401

            # 使用 register_menus 手动注册，菜单路径指向 Layui 前端页面
            # 新增模板中仅包含"返回"和"保存"按钮
            register_menus(
                menus_data=[
                    # 目录：演示应用
                    ('演示应用', 'layui-icon-app', '', 1, 4, None),
                    # 子菜单：商品分类 -> 指向 Layui 前端页面
                    ('商品分类', 'layui-icon-template-1', '/static/store/pages/category.html', 2, 1, '演示应用'),
                    # 子菜单：商品管理 -> 指向 Layui 前端页面
                    ('商品管理', 'layui-icon-cart-simple', '/static/store/pages/product.html', 2, 2, '演示应用'),
                    # 子菜单：订单管理 -> 指向 Layui 前端页面
                    ('订单管理', 'layui-icon-form', '/static/store/pages/order.html', 2, 3, '演示应用'),
                ],
                buttons_data=[
                    # 商品分类按钮权限
                    ('新增分类', '商品分类', 'category:add', 1),
                    ('编辑分类', '商品分类', 'category:edit', 2),
                    ('删除分类', '商品分类', 'category:delete', 3),
                    # 商品管理按钮权限
                    ('新增商品', '商品管理', 'product:add', 1),
                    ('编辑商品', '商品管理', 'product:edit', 2),
                    ('删除商品', '商品管理', 'product:delete', 3),
                    # 订单管理按钮权限
                    ('查看订单', '订单管理', 'order:view', 1),
                    ('新增订单', '订单管理', 'order:add', 2),
                    ('编辑订单', '订单管理', 'order:edit', 3),
                    ('订单发货', '订单管理', 'order:ship', 4),
                    ('取消订单', '订单管理', 'order:cancel', 5),
                    ('删除订单', '订单管理', 'order:delete', 6),
                ]
            )
            # 补齐演示菜单的多语言字段，配合后台语言切换验证菜单本地化。
            translations = {
                '演示应用': ('Demo App', '演示应用'),
                '商品分类': ('Categories', '商品分类'),
                '商品管理': ('Products', '商品管理'),
                '订单管理': ('Orders', '订单管理'),
            }
            for menu_name, (name_en, name_zh_hans) in translations.items():
                Menu.objects.filter(name=menu_name).update(
                    name_en=name_en, name_zh_hans=name_zh_hans
                )

            print(f"[StoreConfig.ready] Menu registration completed successfully.")

            # 注册 store API 路由到 admin site 内部（与 rbac 方式一致）
            self._register_store_api_urls()

        except Exception as e:
            # 如果数据库还未迁移或 rbac 未安装，忽略错误
            print(f"Warning: Could not register menus: {e}")

    def _register_store_api_urls(self):
        """Register store API URLs under admin site (same approach as rbac)"""
        from django.contrib.admin import site
        from django.urls import path, include
        from . import urls as store_urls

        original_get_urls = site.get_urls

        def patched_get_urls():
            urls = original_get_urls()
            custom_urls = [
                path('api/store/', include((store_urls.urlpatterns, 'store'))),
            ]
            return custom_urls + urls

        site.get_urls = patched_get_urls
