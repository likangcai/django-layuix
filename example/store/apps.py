from django.apps import AppConfig


class StoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'store'
    verbose_name = '商品管理'
    
    def ready(self):
        """
        应用启动时注册菜单
        
        django-layui 提供两种菜单注册方式：
        1. 自动扫描（推荐）：auto_register_admin_apps() - 类似 django-simpleui
        2. 手动注册：register_menus() - 完全自定义菜单结构
        """
        try:
            from django_layui.rbac import auto_register_admin_apps, register_menus
            from django_layui.rbac.models import Menu
            
            # 检查是否已经存在完整的菜单结构（如权限管理）
            # 如果已存在，则跳过自动注册，避免覆盖 init_menu 创建的完整菜单
            if Menu.objects.filter(name='权限管理').exists():
                print(f"[StoreConfig.ready] Full menu structure exists, skipping auto registration.")
                return
            
            # 重要：在调用 auto_register_admin_apps 之前，必须先导入 admin.py
            # 否则 @admin.register 装饰器不会生效，模型不会被注册到 Admin
            import store.admin  # noqa: F401
            
            # 方式一：自动扫描所有已在 Admin 中注册的模型（推荐）
            # 默认会排除: auth, contenttypes, sessions, django_layui.rbac, django_layui.ops
            # 因为这些模块已有专门的菜单管理（权限管理、系统管理、运维管理）
            auto_register_admin_apps(
                menu_sort_order={
                    'store': 1,  # 演示应用排第一
                }
            )
            print(f"[StoreConfig.ready] Menu registration completed successfully.")
            
            # 方式二：如果需要更精细的控制，可以手动注册
            # 适用于需要自定义图标、路径、排序等场景
            # register_menus(
            #     menus_data=[
            #         # 目录：演示应用
            #         ('演示应用', 'layui-icon-app', '', 1, 4, None),
            #         # 子菜单：商品分类
            #         ('商品分类', 'layui-icon-template-1', '/store/category', 2, 1, '演示应用'),
            #         # 子菜单：商品管理
            #         ('商品管理', 'layui-icon-cart-simple', '/store/product', 2, 2, '演示应用'),
            #         # 子菜单：订单管理
            #         ('订单管理', 'layui-icon-form', '/store/order', 2, 3, '演示应用'),
            #     ],
            #     buttons_data=[
            #         # 商品分类按钮权限
            #         ('新增分类', '商品分类', 'category:add', 1),
            #         ('编辑分类', '商品分类', 'category:edit', 2),
            #         ('删除分类', '商品分类', 'category:delete', 3),
            #         # 商品管理按钮权限
            #         ('新增商品', '商品管理', 'product:add', 1),
            #         ('编辑商品', '商品管理', 'product:edit', 2),
            #         ('删除商品', '商品管理', 'product:delete', 3),
            #         # 订单管理按钮权限
            #         ('查看订单', '订单管理', 'order:view', 1),
            #         ('订单发货', '订单管理', 'order:ship', 2),
            #         ('取消订单', '订单管理', 'order:cancel', 3),
            #     ]
            # )
        except Exception as e:
            # 如果数据库还未迁移或 rbac 未安装，忽略错误
            print(f"Warning: Could not register menus: {e}")
