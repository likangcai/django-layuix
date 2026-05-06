# -*- coding: utf-8 -*-
"""
数据初始化管理命令
用法: python manage.py init_data
"""
from django.core.management.base import BaseCommand
from django_layui.rbac.models import Menu, Role, UserProfile


class Command(BaseCommand):
    help = '初始化系统数据：创建超级管理员、内置角色、基础菜单树'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('开始初始化系统数据...'))

        # 1. 创建超级管理员
        self._create_admin()
        # 2. 创建系统内置角色
        admin_role, registered_role = self._create_roles()
        # 3. 创建基础菜单树
        menus = self._create_menus()
        # 4. 关联角色和菜单
        self._bind_role_menus(admin_role, registered_role, menus)

        self.stdout.write(self.style.SUCCESS('系统数据初始化完成!'))
        self.stdout.write(self.style.SUCCESS('超级管理员账号: admin / admin123'))

    def _create_admin(self):
        """创建超级管理员"""
        self.stdout.write('  创建超级管理员...')
        if UserProfile.objects.filter(username='admin').exists():
            self.stdout.write(self.style.WARNING('    超级管理员已存在，跳过'))
            admin = UserProfile.objects.get(username='admin')
        else:
            admin = UserProfile.objects.create_superuser(
                username='admin',
                password='admin123',
                nickname='超级管理员',
                email='admin@example.com',
            )
            self.stdout.write(self.style.SUCCESS('    超级管理员创建成功'))
        return admin

    def _create_roles(self):
        """创建系统内置角色"""
        self.stdout.write('  创建系统内置角色...')

        # 超级管理员角色
        if Role.objects.filter(code='admin').exists():
            self.stdout.write(self.style.WARNING('    超级管理员角色已存在，跳过'))
            admin_role = Role.objects.get(code='admin')
        else:
            admin_role = Role.objects.create(
                name='超级管理员',
                code='admin',
                description='拥有系统所有权限',
                is_system=True,
                status=True,
            )
            self.stdout.write(self.style.SUCCESS('    超级管理员角色创建成功'))

        # 注册用户角色
        if Role.objects.filter(code='registered').exists():
            self.stdout.write(self.style.WARNING('    注册用户角色已存在，跳过'))
            registered_role = Role.objects.get(code='registered')
        else:
            registered_role = Role.objects.create(
                name='注册用户',
                code='registered',
                description='注册用户默认角色',
                is_system=True,
                status=True,
            )
            self.stdout.write(self.style.SUCCESS('    注册用户角色创建成功'))

        return admin_role, registered_role

    def _create_menus(self):
        """创建基础菜单树"""
        self.stdout.write('  创建基础菜单树...')

        menus = {}

        # === 权限管理（目录） ===
        perm_dir, created = Menu.objects.get_or_create(
            name='权限管理',
            defaults={
                'icon': 'layui-icon-auz',
                'path': '/permission',
                'menu_type': 1,
                'permission': '',
                'sort': 1,
                'visible': True,
                'status': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('    菜单创建: 权限管理'))
        menus['perm_dir'] = perm_dir

        # 菜单管理
        menu_mgmt, created = Menu.objects.get_or_create(
            name='菜单管理',
            defaults={
                'parent': perm_dir,
                'icon': 'layui-icon-menu-fill',
                'path': '/permission/menu',
                'component': 'permission/menu/index',
                'menu_type': 2,
                'permission': 'menu:list',
                'sort': 1,
                'visible': True,
                'status': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('    菜单创建: 菜单管理'))
        menus['menu_mgmt'] = menu_mgmt

        # 菜单管理 - 按钮权限
        menu_add, _ = Menu.objects.get_or_create(
            name='菜单新增',
            defaults={
                'parent': menu_mgmt,
                'menu_type': 3,
                'permission': 'menu:add',
                'sort': 1,
                'status': True,
            }
        )
        menu_edit, _ = Menu.objects.get_or_create(
            name='菜单编辑',
            defaults={
                'parent': menu_mgmt,
                'menu_type': 3,
                'permission': 'menu:edit',
                'sort': 2,
                'status': True,
            }
        )
        menu_del, _ = Menu.objects.get_or_create(
            name='菜单删除',
            defaults={
                'parent': menu_mgmt,
                'menu_type': 3,
                'permission': 'menu:delete',
                'sort': 3,
                'status': True,
            }
        )

        # 角色管理
        role_mgmt, created = Menu.objects.get_or_create(
            name='角色管理',
            defaults={
                'parent': perm_dir,
                'icon': 'layui-icon-group',
                'path': '/permission/role',
                'component': 'permission/role/index',
                'menu_type': 2,
                'permission': 'role:list',
                'sort': 2,
                'visible': True,
                'status': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('    菜单创建: 角色管理'))
        menus['role_mgmt'] = role_mgmt

        # 角色管理 - 按钮权限
        role_add, _ = Menu.objects.get_or_create(
            name='角色新增',
            defaults={
                'parent': role_mgmt,
                'menu_type': 3,
                'permission': 'role:add',
                'sort': 1,
                'status': True,
            }
        )
        role_edit, _ = Menu.objects.get_or_create(
            name='角色编辑',
            defaults={
                'parent': role_mgmt,
                'menu_type': 3,
                'permission': 'role:edit',
                'sort': 2,
                'status': True,
            }
        )
        role_del, _ = Menu.objects.get_or_create(
            name='角色删除',
            defaults={
                'parent': role_mgmt,
                'menu_type': 3,
                'permission': 'role:delete',
                'sort': 3,
                'status': True,
            }
        )

        # 用户管理
        user_mgmt, created = Menu.objects.get_or_create(
            name='用户管理',
            defaults={
                'parent': perm_dir,
                'icon': 'layui-icon-username',
                'path': '/permission/user',
                'component': 'permission/user/index',
                'menu_type': 2,
                'permission': 'user:list',
                'sort': 3,
                'visible': True,
                'status': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('    菜单创建: 用户管理'))
        menus['user_mgmt'] = user_mgmt

        # 用户管理 - 按钮权限
        user_add, _ = Menu.objects.get_or_create(
            name='用户新增',
            defaults={
                'parent': user_mgmt,
                'menu_type': 3,
                'permission': 'user:add',
                'sort': 1,
                'status': True,
            }
        )
        user_edit, _ = Menu.objects.get_or_create(
            name='用户编辑',
            defaults={
                'parent': user_mgmt,
                'menu_type': 3,
                'permission': 'user:edit',
                'sort': 2,
                'status': True,
            }
        )
        user_del, _ = Menu.objects.get_or_create(
            name='用户删除',
            defaults={
                'parent': user_mgmt,
                'menu_type': 3,
                'permission': 'user:delete',
                'sort': 3,
                'status': True,
            }
        )

        # === 个人中心（目录） ===
        profile_dir, created = Menu.objects.get_or_create(
            name='个人中心',
            defaults={
                'icon': 'layui-icon-user',
                'path': '/profile',
                'menu_type': 1,
                'permission': '',
                'sort': 2,
                'visible': True,
                'status': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('    菜单创建: 个人中心'))
        menus['profile_dir'] = profile_dir

        # === 系统监控（目录） ===
        sys_dir, created = Menu.objects.get_or_create(
            name='系统监控',
            defaults={
                'icon': 'layui-icon-set',
                'path': '/system',
                'menu_type': 1,
                'permission': '',
                'sort': 3,
                'visible': True,
                'status': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('    菜单创建: 系统监控'))
        menus['sys_dir'] = sys_dir

        # 操作日志
        log_mgmt, created = Menu.objects.get_or_create(
            name='操作日志',
            defaults={
                'parent': sys_dir,
                'icon': 'layui-icon-log',
                'path': '/system/log',
                'component': 'system/log/index',
                'menu_type': 2,
                'permission': 'log:list',
                'sort': 1,
                'visible': True,
                'status': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('    菜单创建: 操作日志'))
        menus['log_mgmt'] = log_mgmt

        # 系统信息
        sys_info, created = Menu.objects.get_or_create(
            name='系统信息',
            defaults={
                'parent': sys_dir,
                'icon': 'layui-icon-about',
                'path': '/system/info',
                'component': 'system/info/index',
                'menu_type': 2,
                'permission': 'system:info',
                'sort': 2,
                'visible': True,
                'status': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('    菜单创建: 系统信息'))
        menus['sys_info'] = sys_info

        # 系统配置菜单（在系统监控下）
        config_menu, created = Menu.objects.get_or_create(
            name='系统配置',
            defaults={
                'parent': sys_dir,
                'icon': 'layui-icon-set-fill',
                'path': '/system/config',
                'component': 'system/config/index',
                'menu_type': 2,
                'permission': 'system:config',
                'sort': 3,
                'visible': True,
                'status': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('    菜单创建: 系统配置'))
        menus['config_menu'] = config_menu

        # === 运维管理（目录） ===
        ops_dir, created = Menu.objects.get_or_create(
            name='运维管理',
            defaults={
                'icon': 'layui-icon-engine',
                'path': '/ops',
                'menu_type': 1,
                'permission': '',
                'sort': 4,
                'visible': True,
                'status': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('    菜单创建: 运维管理'))
        menus['ops_dir'] = ops_dir

        # 服务器管理菜单
        server_mgmt, created = Menu.objects.get_or_create(
            name='服务器管理',
            defaults={
                'parent': ops_dir,
                'icon': 'layui-icon-console',
                'path': '/ops/server',
                'component': 'ops/server/index',
                'menu_type': 2,
                'permission': 'server:list',
                'sort': 1,
                'visible': True,
                'status': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('    菜单创建: 服务器管理'))
        menus['server_mgmt'] = server_mgmt

        # 服务器管理 - 按钮权限
        Menu.objects.get_or_create(
            name='服务器新增',
            defaults={
                'parent': server_mgmt,
                'menu_type': 3,
                'permission': 'server:add',
                'sort': 1,
                'status': True,
            }
        )
        Menu.objects.get_or_create(
            name='服务器编辑',
            defaults={
                'parent': server_mgmt,
                'menu_type': 3,
                'permission': 'server:edit',
                'sort': 2,
                'status': True,
            }
        )
        Menu.objects.get_or_create(
            name='服务器删除',
            defaults={
                'parent': server_mgmt,
                'menu_type': 3,
                'permission': 'server:delete',
                'sort': 3,
                'status': True,
            }
        )
        Menu.objects.get_or_create(
            name='服务器连接',
            defaults={
                'parent': server_mgmt,
                'menu_type': 3,
                'permission': 'server:connect',
                'sort': 4,
                'status': True,
            }
        )
        Menu.objects.get_or_create(
            name='日志查看',
            defaults={
                'parent': server_mgmt,
                'menu_type': 3,
                'permission': 'server:log',
                'sort': 5,
                'status': True,
            }
        )
        Menu.objects.get_or_create(
            name='命令执行',
            defaults={
                'parent': server_mgmt,
                'menu_type': 3,
                'permission': 'server:exec',
                'sort': 6,
                'status': True,
            }
        )

        return menus

    def _bind_role_menus(self, admin_role, registered_role, menus):
        """关联角色和菜单"""
        self.stdout.write('  关联角色菜单权限...')

        # 超级管理员角色关联所有菜单
        all_menus = Menu.objects.all()
        admin_role.menus.set(all_menus)
        self.stdout.write(self.style.SUCCESS('    超级管理员角色已关联所有菜单'))

        # 注册用户角色关联个人中心
        registered_role.menus.set([menus['profile_dir']])
        self.stdout.write(self.style.SUCCESS('    注册用户角色已关联个人中心'))

        # 将超级管理员角色绑定给admin用户
        try:
            admin_user = UserProfile.objects.get(username='admin')
            admin_user.roles.add(admin_role)
            self.stdout.write(self.style.SUCCESS('    超级管理员已绑定超级管理员角色'))
        except UserProfile.DoesNotExist:
            self.stdout.write(self.style.WARNING('    未找到admin用户'))
