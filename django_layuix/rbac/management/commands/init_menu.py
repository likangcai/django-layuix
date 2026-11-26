# -*- coding: utf-8 -*-
"""
初始化默认菜单数据
用法:
  python manage.py init_menu             # 初始化菜单、角色、系统配置（已存在则跳过）
  python manage.py init_menu --force     # 强制更新所有菜单、角色权限、系统配置（重置为默认值）
  python manage.py init_menu --fix-icons # 修复数据库中可能存在的无效 Layui 图标

"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django_layuix.rbac.defaults import get_default_configs
from django_layuix.rbac.models import Menu, Role, SystemConfig


class Command(BaseCommand):
    help = '初始化默认菜单和角色数据（包含图标修复功能）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            default=False,
            help='强制更新菜单数据（保留角色权限关联）',
        )
        parser.add_argument(
            '--fix-icons',
            action='store_true',
            dest='fix_icons',
            default=False,
            help='修复数据库中无效的 Layui 图标（原 fix_icons 命令功能）',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        fix_icons = options.get('fix_icons', False)

        # --fix-icons 模式：仅修复图标，不初始化菜单
        if fix_icons:
            self._fix_icons()
            return

        # 检查 rbac 核心菜单是否已存在（通过检查'权限管理'目录菜单）
        # 不使用 Menu.objects.exists()，因为其他 app（如 store）可能已通过 auto_register_admin_apps 创建了菜单
        try:
            rbac_menu_exists = Menu.objects.filter(name='权限管理').exists()
        except Exception:
            # 如果表不存在（例如首次迁移前），则视为不存在
            rbac_menu_exists = False
            
        if rbac_menu_exists and not force:
            self.stdout.write(self.style.WARNING('rbac 菜单数据已存在，跳过菜单初始化。'))
            self._ensure_rbac3_menu()
            self._ensure_142_menus()
        else:
            if force and rbac_menu_exists:
                self.stdout.write(self.style.WARNING('使用 --force 模式，将更新现有 rbac 菜单数据（保留角色权限关联）'))
            self._init_menus(force)
            
        # 无论菜单是否已存在，都继续执行角色和配置的初始化
        # 这确保了即使其他 app 抢跑了菜单注册，角色和配置也能正确创建
        from django_layuix.rbac.permission_registry import register_page_permissions
        created_permissions = register_page_permissions()
        if created_permissions:
            self.stdout.write(self.style.SUCCESS('  注册权限目录 %s 项' % len(created_permissions)))

        self._init_roles(force)
        self._init_default_configs(force)
        self.stdout.write(self.style.SUCCESS('\n初始化完成！'))

    def _ensure_rbac3_menu(self):
        """Add the constraint-management menu to installations created before RBAC3."""
        parent = Menu.objects.filter(name='权限管理').first()
        if not parent:
            return
        menu, created = Menu.objects.get_or_create(
            name='约束管理',
            defaults={
                'name_en': 'Constraints',
                'name_zh_hans': '约束管理',
                'icon': 'layui-icon-auz',
                'path': '/system/rbac-constraints',
                'menu_type': 2,
                'sort': 4,
                'parent': parent,
                'status': True,
                'visible': True,
                'backend_visible': True,
                'frontend_visible': True,
            },
        )
        if created:
            admin_role = Role.objects.filter(code='admin').first()
            if admin_role:
                admin_role.menus.add(menu)
            self.stdout.write(self.style.SUCCESS('  创建菜单: 约束管理 (RBAC3)'))

    def _migrate_scope_menu(self):
        """Move legacy 组织节点 menu to 权限管理 → 数据范围."""
        parent = Menu.objects.filter(name='权限管理').first()
        if not parent:
            return
        legacy = list(Menu.objects.filter(name__in=['组织节点', '数据范围']).order_by('id'))
        if not legacy:
            return
        menu = legacy[0]
        menu.name = '数据范围'
        menu.name_en = 'Data Scope'
        menu.name_zh_hans = '数据范围'
        menu.icon = 'layui-icon-tree'
        menu.path = '/permission/data-scope'
        menu.parent = parent
        menu.sort = 6
        menu.save()
        for duplicate in legacy[1:]:
            duplicate.delete()

    def _ensure_142_menus(self):
        """Add ABAC policy and data scope menus to pre-1.4.2 installations."""
        specs = [
            ('ABAC 策略', 'ABAC Policies', 'ABAC 策略', 'layui-icon-auz', '/permission/abac', 5, '权限管理'),
            ('数据范围', 'Data Scope', '数据范围', 'layui-icon-tree', '/permission/data-scope', 6, '权限管理'),
        ]
        self._migrate_scope_menu()
        for name, name_en, name_zh, icon, path, sort, parent_name in specs:
            parent = Menu.objects.filter(name=parent_name).first()
            if not parent:
                continue
            menu, created = Menu.objects.get_or_create(
                name=name,
                defaults={
                    'name_en': name_en, 'name_zh_hans': name_zh, 'icon': icon,
                    'path': path, 'menu_type': 2, 'sort': sort, 'parent': parent,
                    'status': True, 'visible': True,
                    'backend_visible': True, 'frontend_visible': True,
                },
            )
            if created:
                admin_role = Role.objects.filter(code='admin').first()
                if admin_role:
                    admin_role.menus.add(menu)

    def _init_menus(self, force=False):
        """初始化菜单数据"""
        # 创建菜单
        # (name, name_en, name_zh_hans, icon, path, menu_type, sort, parent_name_or_None)
        # menu_type: 1=目录, 2=菜单
        menus_data = [
            # ---- 仪表盘 ----
            ('仪表盘', 'Dashboard', '仪表盘', 'layui-icon-chart', '/static/layui/pages/dashboard.html', 2, 0, None),

            # ---- 权限管理 ----
            ('权限管理', 'Permission', '权限管理', 'layui-icon-auz', '', 1, 1, None),
            ('菜单管理', 'Menu', '菜单管理', 'layui-icon-menu-fill', '/permission/menu', 2, 1, '权限管理'),
            ('角色管理', 'Role', '角色管理', 'layui-icon-group', '/permission/role', 2, 2, '权限管理'),
            ('用户管理', 'User', '用户管理', 'layui-icon-username', '/permission/user', 2, 3, '权限管理'),
            ('约束管理', 'Constraints', '约束管理', 'layui-icon-auz', '/system/rbac-constraints', 2, 4, '权限管理'),
            ('ABAC 策略', 'ABAC Policies', 'ABAC 策略', 'layui-icon-auz', '/permission/abac', 2, 5, '权限管理'),

            # ---- 系统管理 ----
            ('系统管理', 'System', '系统管理', 'layui-icon-set', '', 1, 2, None),
            ('个人中心', 'Profile', '个人中心', 'layui-icon-user', '/static/layui/pages/profile.html', 2, 1, '系统管理'),
            ('操作日志', 'Log', '操作日志', 'layui-icon-log', '/system/log', 2, 2, '系统管理'),
            ('系统配置', 'Config', '系统配置', 'layui-icon-set-sm', '/system/config', 2, 3, '系统管理'),
            ('数据范围', 'Data Scope', '数据范围', 'layui-icon-tree', '/permission/data-scope', 2, 6, '权限管理'),

            # ---- 运维管理 ----
            ('运维管理', 'Operations', '运维管理', 'layui-icon-console', '', 1, 3, None),
            ('服务器管理', 'Server', '服务器管理', 'layui-icon-console', '/ops/server', 2, 1, '运维管理'),
            ('AI 配置', 'AI Config', 'AI 配置', 'layui-icon-light', '/ops/ai-config', 2, 2, '运维管理'),
        ]

        created = {}
        for name, name_en, name_zh_hans, icon, path, menu_type, sort, parent_name in menus_data:
            parent = created.get(parent_name) if parent_name else None
            menu, is_new = Menu.objects.get_or_create(
                name=name,
                defaults={
                    'name_en': name_en,
                    'name_zh_hans': name_zh_hans,
                    'icon': icon,
                    'path': path,
                    'menu_type': menu_type,
                    'sort': sort,
                    'parent': parent,
                    'status': True,
                    'visible': True,
                    'backend_visible': True,
                    'frontend_visible': True,
                }
            )
            # 如果菜单已存在，在 --force 模式下更新所有字段，否则只更新名称
            if not is_new:
                updated = False
                if force:
                    # --force 模式：更新所有字段（但保留角色关联）
                    if menu.name_en != name_en:
                        menu.name_en = name_en
                        updated = True
                    if menu.name_zh_hans != name_zh_hans:
                        menu.name_zh_hans = name_zh_hans
                        updated = True
                    if menu.icon != icon:
                        menu.icon = icon
                        updated = True
                    if menu.path != path:
                        menu.path = path
                        updated = True
                    if menu.menu_type != menu_type:
                        menu.menu_type = menu_type
                        updated = True
                    if menu.sort != sort:
                        menu.sort = sort
                        updated = True
                    if parent and menu.parent_id != parent.id:
                        menu.parent = parent
                        updated = True
                    if menu.backend_visible != True:
                        menu.backend_visible = True
                        updated = True
                    if menu.frontend_visible != True:
                        menu.frontend_visible = True
                        updated = True
                else:
                    # 非 --force 模式：只更新名称字段
                    if menu.name_en != name_en:
                        menu.name_en = name_en
                        updated = True
                    if menu.name_zh_hans != name_zh_hans:
                        menu.name_zh_hans = name_zh_hans
                        updated = True
                if updated:
                    menu.save()
                    if force:
                        self.stdout.write(f'  更新菜单: {name} (所有字段)')
                    else:
                        self.stdout.write(f'  更新菜单: {name} (name_en, name_zh_hans)')
            created[name] = menu
            if is_new:
                self.stdout.write(self.style.SUCCESS(f'  创建菜单: {name}'))
            elif not updated:
                self.stdout.write(f'  菜单已存在: {name}')

        from django_layuix.rbac.menu_permissions import MENU_VIEW_PERMISSIONS
        for menu_name, permission in MENU_VIEW_PERMISSIONS.items():
            menu = Menu.objects.filter(name=menu_name).first()
            if menu and menu.permission != permission:
                menu.permission = permission
                menu.save(update_fields=['permission'])

        # 创建按钮级权限（menu_type=3）
        # (name, name_en, name_zh_hans, parent_menu, permission, sort)
        buttons_data = [
            # 菜单管理下：新增菜单、编辑菜单、删除菜单
            ('新增菜单', 'Add Menu', '新增菜单', created['菜单管理'], 'menu:add', 1),
            ('编辑菜单', 'Edit Menu', '编辑菜单', created['菜单管理'], 'menu:edit', 2),
            ('删除菜单', 'Delete Menu', '删除菜单', created['菜单管理'], 'menu:delete', 3),
            # 角色管理下：新增角色、编辑角色、删除角色、复制角色
            ('新增角色', 'Add Role', '新增角色', created['角色管理'], 'role:add', 1),
            ('编辑角色', 'Edit Role', '编辑角色', created['角色管理'], 'role:edit', 2),
            ('删除角色', 'Delete Role', '删除角色', created['角色管理'], 'role:delete', 3),
            ('复制角色', 'Copy Role', '复制角色', created['角色管理'], 'role:copy', 4),
            # 用户管理下：新增用户、编辑用户、删除用户、重置密码、启用/禁用
            ('新增用户', 'Add User', '新增用户', created['用户管理'], 'user:add', 1),
            ('编辑用户', 'Edit User', '编辑用户', created['用户管理'], 'user:edit', 2),
            ('删除用户', 'Delete User', '删除用户', created['用户管理'], 'user:delete', 3),
            ('重置密码', 'Reset Password', '重置密码', created['用户管理'], 'user:reset_password', 4),
            ('启用/禁用', 'Toggle Status', '启用/禁用', created['用户管理'], 'user:toggle_status', 5),
            # 操作日志下：（只读，无按钮权限）
            # 个人中心下：（只读，无按钮权限）
            # 系统配置下：新增配置、编辑配置、删除配置
            ('新增配置', 'Add Config', '新增配置', created['系统配置'], 'config:add', 1),
            ('编辑配置', 'Edit Config', '编辑配置', created['系统配置'], 'config:edit', 2),
            ('删除配置', 'Delete Config', '删除配置', created['系统配置'], 'config:delete', 3),
            # 服务器管理下：查看、新增、编辑、删除、查看日志、终端
            ('查看服务器', 'View Servers', '查看服务器', created['服务器管理'], 'server:view', 0),
            ('新增服务器', 'Add Server', '新增服务器', created['服务器管理'], 'server:add', 1),
            ('编辑服务器', 'Edit Server', '编辑服务器', created['服务器管理'], 'server:edit', 2),
            ('删除服务器', 'Delete Server', '删除服务器', created['服务器管理'], 'server:delete', 3),
            ('查看日志', 'View Log', '查看日志', created['服务器管理'], 'server:view_log', 4),
            ('终端连接', 'Terminal', '终端连接', created['服务器管理'], 'server:terminal', 5),
            # AI 配置下：查看、新增、编辑、删除、测试连接、设默认
            ('查看 AI 配置', 'View AI Config', '查看 AI 配置', created['AI 配置'], 'ai_config:view', 0),
            ('新增 AI 配置', 'Add AI Config', '新增 AI 配置', created['AI 配置'], 'ai_config:add', 1),
            ('编辑 AI 配置', 'Edit AI Config', '编辑 AI 配置', created['AI 配置'], 'ai_config:edit', 2),
            ('删除 AI 配置', 'Delete AI Config', '删除 AI 配置', created['AI 配置'], 'ai_config:delete', 3),
            ('测试连接', 'Test Connection', '测试连接', created['AI 配置'], 'ai_config:test', 4),
            ('设为默认', 'Set Default', '设为默认', created['AI 配置'], 'ai_config:set_default', 5),
        ]
        for btn_name, btn_name_en, btn_name_zh_hans, parent_menu, permission, sort in buttons_data:
            btn, is_new = Menu.objects.get_or_create(
                name=btn_name,
                defaults={
                    'name_en': btn_name_en,
                    'name_zh_hans': btn_name_zh_hans,
                    'parent': parent_menu,
                    'icon': '',
                    'path': '',
                    'component': '',
                    'menu_type': 3,
                    'permission': permission,
                    'sort': sort,
                    'status': True,
                    'visible': True,
                    'backend_visible': True,
                    'frontend_visible': True,
                }
            )
            # 如果按钮已存在，在 --force 模式下更新所有字段，否则只更新名称
            if not is_new:
                updated = False
                if force:
                    # --force 模式：更新所有字段
                    if btn.name_en != btn_name_en:
                        btn.name_en = btn_name_en
                        updated = True
                    if btn.name_zh_hans != btn_name_zh_hans:
                        btn.name_zh_hans = btn_name_zh_hans
                        updated = True
                    if btn.parent_id != parent_menu.id:
                        btn.parent = parent_menu
                        updated = True
                    if btn.permission != permission:
                        btn.permission = permission
                        updated = True
                    if btn.sort != sort:
                        btn.sort = sort
                        updated = True
                    if btn.backend_visible != True:
                        btn.backend_visible = True
                        updated = True
                    if btn.frontend_visible != True:
                        btn.frontend_visible = True
                        updated = True
                else:
                    # 非 --force 模式：只更新名称字段
                    if btn.name_en != btn_name_en:
                        btn.name_en = btn_name_en
                        updated = True
                    if btn.name_zh_hans != btn_name_zh_hans:
                        btn.name_zh_hans = btn_name_zh_hans
                        updated = True
                if updated:
                    btn.save()
                    if force:
                        self.stdout.write(f'  更新按钮权限: {btn_name} (所有字段)')
                    else:
                        self.stdout.write(f'  更新按钮权限: {btn_name} (name_en, name_zh_hans)')
            if is_new:
                self.stdout.write(self.style.SUCCESS(f'  创建按钮权限: {btn_name} ({permission})'))
            else:
                self.stdout.write(f'  按钮权限已存在: {btn_name}')

    def _init_roles(self, force=False):
        """初始化默认角色"""
        # 创建默认角色
        admin_role, created = Role.objects.get_or_create(
            name='管理员',
            defaults={
                'code': 'admin',
                'description': '系统管理员，拥有所有权限',
                'is_system': True,
                'status': True,
            }
        )
        if created:
            # 给管理员角色分配所有菜单
            admin_role.menus.set(Menu.objects.all())
            # 把 admin 超级用户加入管理员角色
            User = get_user_model()
            admin_user = User.objects.filter(is_superuser=True).first()
            if admin_user:
                admin_user.roles.add(admin_role)
            self.stdout.write(self.style.SUCCESS(f'  创建角色: 管理员'))
        else:
            # --force 模式下，重新同步管理员角色的所有菜单权限
            if force:
                admin_role.menus.set(Menu.objects.all())
                self.stdout.write(self.style.SUCCESS(f'  已同步管理员角色权限（共 {Menu.objects.count()} 个菜单）'))
            else:
                self.stdout.write(f'  角色已存在: 管理员')

        # 创建注册用户角色
        registered_role, created = Role.objects.get_or_create(
            name='注册用户',
            defaults={
                'code': 'registered',
                'description': '前端注册用户，默认权限',
                'is_system': True,
                'status': True,
            }
        )
        if created:
            # 注册用户默认只能访问仪表盘和个人中心（需要同时绑定父目录和子菜单）
            dashboard = Menu.objects.filter(name='仪表盘').first()
            system_management = Menu.objects.filter(name='系统管理').first()
            personal_center = Menu.objects.filter(name='个人中心').first()
            menus_to_bind = []
            if dashboard:
                menus_to_bind.append(dashboard)
            if system_management:
                menus_to_bind.append(system_management)
            if personal_center:
                menus_to_bind.append(personal_center)
            if menus_to_bind:
                registered_role.menus.set(menus_to_bind)
            self.stdout.write(self.style.SUCCESS(f'  创建角色: 注册用户'))
        else:
            # --force 模式下，重新同步注册用户的默认权限
            if force:
                dashboard = Menu.objects.filter(name='仪表盘').first()
                system_management = Menu.objects.filter(name='系统管理').first()
                personal_center = Menu.objects.filter(name='个人中心').first()
                menus_to_bind = []
                if dashboard:
                    menus_to_bind.append(dashboard)
                if system_management:
                    menus_to_bind.append(system_management)
                if personal_center:
                    menus_to_bind.append(personal_center)
                if menus_to_bind:
                    registered_role.menus.set(menus_to_bind)
                self.stdout.write(self.style.WARNING(f'  已重置注册用户权限'))
            else:
                self.stdout.write(f'  角色已存在: 注册用户')

        # 创建普通用户角色
        normal_user_role, created = Role.objects.get_or_create(
            name='普通用户',
            defaults={
                'code': 'normal_user',
                'description': '普通用户，拥有基本功能权限',
                'is_system': True,
                'status': True,
            }
        )
        if created:
            # 普通用户可以访问：仪表盘、用户管理及其按钮权限、个人中心、操作日志
            dashboard = Menu.objects.filter(name='仪表盘').first()
            permission_management = Menu.objects.filter(name='权限管理').first()
            user_management = Menu.objects.filter(name='用户管理').first()
            system_management = Menu.objects.filter(name='系统管理').first()
            personal_center = Menu.objects.filter(name='个人中心').first()
            operation_log = Menu.objects.filter(name='操作日志').first()
            
            # 获取用户管理下的按钮权限
            add_user_btn = Menu.objects.filter(name='新增用户', parent=user_management).first() if user_management else None
            edit_user_btn = Menu.objects.filter(name='编辑用户', parent=user_management).first() if user_management else None
            delete_user_btn = Menu.objects.filter(name='删除用户', parent=user_management).first() if user_management else None
            toggle_status_btn = Menu.objects.filter(name='启用/禁用', parent=user_management).first() if user_management else None
            
            menus_to_bind = []
            if dashboard:
                menus_to_bind.append(dashboard)
            if permission_management:
                menus_to_bind.append(permission_management)
            if user_management:
                menus_to_bind.append(user_management)
            if system_management:
                menus_to_bind.append(system_management)
            if personal_center:
                menus_to_bind.append(personal_center)
            if operation_log:
                menus_to_bind.append(operation_log)
            
            # 添加按钮权限
            if add_user_btn:
                menus_to_bind.append(add_user_btn)
            if edit_user_btn:
                menus_to_bind.append(edit_user_btn)
            if delete_user_btn:
                menus_to_bind.append(delete_user_btn)
            if toggle_status_btn:
                menus_to_bind.append(toggle_status_btn)
            
            if menus_to_bind:
                normal_user_role.menus.set(menus_to_bind)
            self.stdout.write(self.style.SUCCESS(f'  创建角色: 普通用户'))
        else:
            # --force 模式下，重新同步普通用户的默认权限
            if force:
                dashboard = Menu.objects.filter(name='仪表盘').first()
                permission_management = Menu.objects.filter(name='权限管理').first()
                user_management = Menu.objects.filter(name='用户管理').first()
                system_management = Menu.objects.filter(name='系统管理').first()
                personal_center = Menu.objects.filter(name='个人中心').first()
                operation_log = Menu.objects.filter(name='操作日志').first()
                
                # 获取用户管理下的按钮权限
                add_user_btn = Menu.objects.filter(name='新增用户', parent=user_management).first() if user_management else None
                edit_user_btn = Menu.objects.filter(name='编辑用户', parent=user_management).first() if user_management else None
                delete_user_btn = Menu.objects.filter(name='删除用户', parent=user_management).first() if user_management else None
                toggle_status_btn = Menu.objects.filter(name='启用/禁用', parent=user_management).first() if user_management else None
                
                menus_to_bind = []
                if dashboard:
                    menus_to_bind.append(dashboard)
                if permission_management:
                    menus_to_bind.append(permission_management)
                if user_management:
                    menus_to_bind.append(user_management)
                if system_management:
                    menus_to_bind.append(system_management)
                if personal_center:
                    menus_to_bind.append(personal_center)
                if operation_log:
                    menus_to_bind.append(operation_log)
                
                # 添加按钮权限
                if add_user_btn:
                    menus_to_bind.append(add_user_btn)
                if edit_user_btn:
                    menus_to_bind.append(edit_user_btn)
                if delete_user_btn:
                    menus_to_bind.append(delete_user_btn)
                if toggle_status_btn:
                    menus_to_bind.append(toggle_status_btn)
                
                if menus_to_bind:
                    normal_user_role.menus.set(menus_to_bind)
                self.stdout.write(self.style.WARNING(f'  已重置普通用户权限'))
            else:
                self.stdout.write(f'  角色已存在: 普通用户')

    def _init_default_configs(self, force=False):
        """初始化默认系统配置项"""
        self.stdout.write(self.style.MIGRATE_HEADING('\n  初始化系统配置:'))
        configs = [
            (cfg['key'], cfg['value'], cfg['description'], cfg['config_type'], cfg['sort'])
            for cfg in get_default_configs()
        ]
        created_count = 0
        updated_count = 0
        skipped_count = 0
        for key, value, desc, config_type, sort in configs:
            try:
                cfg = SystemConfig.objects.get(key=key)
                if key == 'system_version' and cfg.value != value:
                    cfg.value = value
                    cfg.save(update_fields=['value'])
                    self.stdout.write(self.style.SUCCESS(f'  同步配置: {key} -> {value}'))
                if force:
                    # --force 模式：更新为默认值
                    cfg.value = value
                    cfg.description = desc
                    cfg.config_type = config_type
                    cfg.sort = sort
                    cfg.save()
                    updated_count += 1
                    self.stdout.write(self.style.WARNING(f'  更新配置: {key} (重置为默认值)'))
                else:
                    skipped_count += 1
                    self.stdout.write(f'  配置已存在: {key}')
            except SystemConfig.DoesNotExist:
                # 配置不存在，创建新的
                SystemConfig.objects.create(
                    key=key,
                    value=value,
                    description=desc,
                    config_type=config_type,
                    sort=sort,
                )
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  创建配置: {key}'))
        
        if force:
            if updated_count > 0:
                self.stdout.write(self.style.SUCCESS(f'  已更新 {updated_count} 个系统配置为默认值。'))
        elif created_count > 0:
            self.stdout.write(self.style.SUCCESS(f'  成功创建 {created_count} 个系统配置。'))
        elif skipped_count > 0:
            self.stdout.write(self.style.WARNING(f'  提示：{skipped_count} 个系统配置已存在，未作修改。如需重置为默认值，请使用 --force 参数。'))

    def _fix_icons(self):
        """修复数据库中无效的 Layui 图标（原 fix_icons 命令功能）"""
        # 图标映射：错误图标 -> 正确图标
        icon_mapping = {
            'layui-icon-menu': 'layui-icon-menu-fill',      # 菜单
            'layui-icon-template': 'layui-icon-menu-fill', # 菜单(init_data.py错误)
            'layui-icon-server': 'layui-icon-console',     # 服务器->控制台
            'layui-icon-website': 'layui-icon-console',    # 服务器(init_data.py错误)
            'layui-icon-brain': 'layui-icon-light',         # AI/大脑 -> 太阳/智能
            'layui-icon-checkin': 'layui-icon-form',        # 签到 -> 表单
        }
        self.stdout.write(self.style.MIGRATE_HEADING('\n修复 Layui 图标:'))
        updated_count = 0
        for old_icon, new_icon in icon_mapping.items():
            menus = Menu.objects.filter(icon=old_icon)
            count = menus.count()
            if count > 0:
                menus.update(icon=new_icon)
                self.stdout.write(self.style.SUCCESS(
                    f'  ✓ 更新 {count} 个菜单: {old_icon} → {new_icon}'
                ))
                updated_count += count
            else:
                self.stdout.write(f'  跳过 {old_icon} (未找到使用该图标的菜单)')

        if updated_count > 0:
            self.stdout.write(self.style.SUCCESS(f'\n总计更新 {updated_count} 个菜单图标'))
        else:
            self.stdout.write(self.style.WARNING('\n没有需要更新的图标'))
