# -*- coding: utf-8 -*-
"""
django-layui 菜单注册工具
允许外部应用动态注册菜单，无需修改库源码

支持两种方式：
1. 手动注册：通过 register_menus() 显式定义菜单结构
2. 自动扫描：通过 auto_register_admin_apps() 自动识别已注册到 Admin 的应用
"""


def auto_register_admin_apps(exclude_apps=None, menu_sort_order=None):
    """
    自动扫描并注册所有已在 Django Admin 中注册的应用和模型
    
    这是推荐的方式，类似于 django-simpleui 的行为。
    在 AppConfig.ready() 中调用即可，无需手动维护菜单。
    
    Args:
        exclude_apps: 要排除的 app 标签列表（如 ['auth', 'contenttypes']）
                     默认会排除: auth, contenttypes, sessions,
                                django_layui.rbac, django_layui.ops
                                (因为这些已有专门的菜单管理)
        menu_sort_order: 自定义菜单排序（app_label: sort_number 字典）
    
    Example:
        # 在 myapp/apps.py 的 ready() 方法中调用
        from django_layui.rbac import auto_register_admin_apps
        
        # 使用默认排除列表(推荐)
        auto_register_admin_apps()
        
        # 或自定义排除列表
        auto_register_admin_apps(
            exclude_apps=['auth', 'contenttypes', 'sessions'],
            menu_sort_order={
                'store': 1,
                'myapp': 2,
            }
        )
    """
    from django.apps import apps
    from django.contrib import admin
    from django_layui.rbac.models import Menu, Role
    
    # 默认排除的 app 标签
    # 注意: django_layui.rbac 和 django_layui.ops 已有专门的菜单管理
    # (权限管理、系统管理、运维管理)，不应重复生成
    # 重要: app_label 使用下划线而非点! (django_layui_rbac 而非 django_layui.rbac)
    if exclude_apps is None:
        exclude_apps = [
            'auth',               # Django 认证系统
            'contenttypes',       # Django 内容类型
            'sessions',           # Django 会话
            'django_layui_rbac',  # RBAC权限管理(已有权限管理菜单) - 注意使用下划线!
            'django_layui_ops',   # 运维管理(已有运维管理菜单) - 注意使用下划线!
        ]
    
    if menu_sort_order is None:
        menu_sort_order = {}
    
    created = {}
    sort_counter = 10
    
    # 获取所有已注册的模型
    for model, model_admin in admin.site._registry.items():
        app_label = model._meta.app_label
        model_name = model._meta.model_name
        
        # 跳过排除的 app
        if app_label in exclude_apps:
            continue
        
        # 获取 app 的 verbose_name
        try:
            app_config = apps.get_app_config(app_label)
            app_verbose_name = str(app_config.verbose_name) if app_config.verbose_name else app_label
        except LookupError:
            app_verbose_name = app_label
        
        # 创建或获取父菜单（目录类型）
        if app_label not in created:
            parent_menu, is_new = Menu.objects.get_or_create(
                name=app_verbose_name,
                defaults={
                    'icon': 'layui-icon-app',
                    'path': '',
                    'menu_type': 1,  # 目录
                    'sort': menu_sort_order.get(app_label, sort_counter),
                    'parent': None,
                    'status': True,
                    'visible': True,
                }
            )
            created[app_label] = parent_menu
            sort_counter += 1
            
            # 给管理员角色分配权限
            if is_new:
                admin_role = Role.objects.filter(code='admin').first()
                if admin_role:
                    admin_role.menus.add(parent_menu)
        
        parent_menu = created[app_label]
        
        # 获取模型的 verbose_name
        model_verbose_name = str(model._meta.verbose_name) if model._meta.verbose_name else model_name
        
        # 构建模型的管理 URL
        model_url = f'/admin/{app_label}/{model_name}/'
        
        # 创建子菜单（菜单类型）
        child_menu, is_new = Menu.objects.get_or_create(
            name=model_verbose_name,
            parent=parent_menu,
            defaults={
                'icon': 'layui-icon-template-1',
                'path': model_url,
                'menu_type': 2,  # 菜单
                'sort': 1,
                'status': True,
                'visible': True,
            }
        )
        
        # 给管理员角色分配权限
        if is_new:
            admin_role = Role.objects.filter(code='admin').first()
            if admin_role:
                admin_role.menus.add(child_menu)
        
        # 创建按钮权限（增删改查）
        buttons = [
            (f'新增{model_verbose_name}', child_menu, f'{app_label}.add_{model_name}', 1),
            (f'编辑{model_verbose_name}', child_menu, f'{app_label}.change_{model_name}', 2),
            (f'删除{model_verbose_name}', child_menu, f'{app_label}.delete_{model_name}', 3),
        ]
        
        for btn_name, btn_parent, permission, btn_sort in buttons:
            btn, btn_is_new = Menu.objects.get_or_create(
                name=btn_name,
                parent=btn_parent,
                defaults={
                    'icon': '',
                    'path': '',
                    'menu_type': 3,  # 按钮
                    'permission': permission,
                    'sort': btn_sort,
                    'status': True,
                    'visible': True,
                }
            )
            
            if btn_is_new:
                admin_role = Role.objects.filter(code='admin').first()
                if admin_role:
                    admin_role.menus.add(btn)


def register_menus(menus_data, buttons_data=None, skip_existing=False):
    """
    注册菜单和按钮权限（在项目的 AppConfig.ready() 中调用）
    
    Args:
        menus_data: 菜单列表，每个元素为元组：
            (name, icon, path, menu_type, sort, parent_name_or_None)
            - name: 菜单名称
            - icon: Layui图标类名（如 'layui-icon-app'）
            - path: 路由地址（如 '/store/product'）
            - menu_type: 1=目录, 2=菜单, 3=按钮
            - sort: 排序号
            - parent_name: 父菜单名称，顶级菜单为None
            
        buttons_data: 按钮权限列表（可选），每个元素为元组：
            (btn_name, parent_menu_name, permission, sort)
            - btn_name: 按钮名称
            - parent_menu_name: 所属菜单名称
            - permission: 权限标识（如 'product:add'）
            - sort: 排序号
        
        skip_existing: 是否跳过已存在的菜单/按钮
            - False（默认）：如果已存在则更新属性
            - True：跳过已存在的菜单/按钮，不更新
    
    Example:
        # 在 myapp/apps.py 的 ready() 方法中调用
        from django_layui.rbac.menu_registry import register_menus
        
        register_menus(
            menus_data=[
                ('演示应用', 'layui-icon-app', '', 1, 4, None),
                ('商品管理', 'layui-icon-cart-simple', '/store/product', 2, 1, '演示应用'),
            ],
            buttons_data=[
                ('新增商品', '商品管理', 'product:add', 1),
                ('编辑商品', '商品管理', 'product:edit', 2),
                ('删除商品', '商品管理', 'product:delete', 3),
            ],
            skip_existing=True  # 跳过已存在的菜单
        )
    """
    from django_layui.rbac.models import Menu, Role
    
    created = {}
    
    # 创建菜单
    for menu_item in menus_data:
        if len(menu_item) == 6:
            name, icon, path, menu_type, sort, parent_name = menu_item
        else:
            continue
            
        parent = None
        if parent_name:
            # 先查找已存在的父菜单
            try:
                parent = Menu.objects.get(name=parent_name)
            except Menu.DoesNotExist:
                # 如果父菜单在当前批次中已创建
                parent = created.get(parent_name)
        
        menu, is_new = Menu.objects.get_or_create(
            name=name,
            defaults={
                'icon': icon,
                'path': path,
                'menu_type': menu_type,
                'sort': sort,
                'parent': parent,
                'status': True,
                'visible': True,
            }
        )
        created[name] = menu
        
        # 如果是新创建的菜单，给管理员角色分配权限
        if is_new:
            admin_role = Role.objects.filter(code='admin').first()
            if admin_role:
                admin_role.menus.add(menu)
    
    # 创建按钮权限
    if buttons_data:
        for btn_item in buttons_data:
            if len(btn_item) != 4:
                continue
                
            btn_name, parent_menu_name, permission, sort = btn_item
            
            # 查找父菜单
            parent_menu = None
            try:
                parent_menu = Menu.objects.get(name=parent_menu_name)
            except Menu.DoesNotExist:
                parent_menu = created.get(parent_menu_name)
            
            if not parent_menu:
                continue
            
            btn, is_new = Menu.objects.get_or_create(
                name=btn_name,
                defaults={
                    'parent': parent_menu,
                    'icon': '',
                    'path': '',
                    'component': '',
                    'menu_type': 3,
                    'permission': permission,
                    'sort': sort,
                    'status': True,
                    'visible': True,
                }
            )
            
            # 如果是新创建的按钮，给管理员角色分配权限
            if is_new:
                admin_role = Role.objects.filter(code='admin').first()
                if admin_role:
                    admin_role.menus.add(btn)


def unregister_menus(menu_names):
    """
    注销菜单（谨慎使用，会删除菜单及其子菜单）
    
    Args:
        menu_names: 要删除的菜单名称列表
    """
    from django_layui.rbac.models import Menu
    
    for name in menu_names:
        try:
            menu = Menu.objects.get(name=name)
            menu.delete()
        except Menu.DoesNotExist:
            pass
