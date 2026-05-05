# -*- coding: utf-8 -*-
"""
初始化默认菜单数据
用法: python manage.py init_menu
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django_layui.rbac.models import Menu, Role, SystemConfig


class Command(BaseCommand):
    help = '初始化默认菜单和角色数据'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            default=False,
            help='强制重新初始化菜单数据（会删除现有菜单）',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        
        # 如果已有菜单数据且不强制重新初始化，则跳过
        if Menu.objects.exists() and not force:
            self._init_default_configs()
            self.stdout.write(self.style.WARNING('菜单数据已存在，跳过初始化。如需重新初始化，请使用 --force 参数。'))
            return
        
        # 如果强制重新初始化，清空现有菜单
        if force and Menu.objects.exists():
            Menu.objects.all().delete()
            self.stdout.write(self.style.WARNING('已清空现有菜单数据'))

        # 创建菜单
        # (name, icon, path, menu_type, sort, parent_name_or_None)
        # menu_type: 1=目录, 2=菜单
        menus_data = [
            # ---- 仪表盘 ----
            ('仪表盘', 'layui-icon-chart', '/static/layui/pages/dashboard.html', 2, 0, None),

            # ---- 权限管理 ----
            ('权限管理', 'layui-icon-auz', '', 1, 1, None),
            ('菜单管理', 'layui-icon-menu-fill', '/permission/menu', 2, 1, '权限管理'),
            ('角色管理', 'layui-icon-group', '/permission/role', 2, 2, '权限管理'),
            ('用户管理', 'layui-icon-username', '/permission/user', 2, 3, '权限管理'),

            # ---- 系统管理 ----
            ('系统管理', 'layui-icon-set', '', 1, 2, None),
            ('个人中心', 'layui-icon-user', '/static/layui/pages/profile.html', 2, 1, '系统管理'),
            ('操作日志', 'layui-icon-log', '/system/log', 2, 2, '系统管理'),
            ('系统配置', 'layui-icon-set-sm', '/system/config', 2, 3, '系统管理'),

            # ---- 运维管理 ----
            ('运维管理', 'layui-icon-console', '', 1, 3, None),
            ('服务器管理', 'layui-icon-console', '/ops/server', 2, 1, '运维管理'),
            ('AI 配置', 'layui-icon-light', '/ops/ai-config', 2, 2, '运维管理'),

            # ---- 业务示例 ----
            ('业务示例', 'layui-icon-cart', '', 1, 4, None),
            ('商品管理', 'layui-icon-file', '/admin/store/product/', 2, 1, '业务示例'),
            ('订单管理', 'layui-icon-form', '/admin/store/order/', 2, 2, '业务示例'),
            ('分类管理', 'layui-icon-folder', '/admin/store/category/', 2, 3, '业务示例'),
        ]

        created = {}
        for name, icon, path, menu_type, sort, parent_name in menus_data:
            parent = created.get(parent_name) if parent_name else None
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
            if is_new:
                self.stdout.write(self.style.SUCCESS(f'  创建菜单: {name}'))
            else:
                self.stdout.write(f'  菜单已存在: {name}')

        # 创建按钮级权限（menu_type=3）
        buttons_data = [
            # 菜单管理下：新增菜单、编辑菜单、删除菜单
            ('新增菜单', created['菜单管理'], 'menu:add', 1),
            ('编辑菜单', created['菜单管理'], 'menu:edit', 2),
            ('删除菜单', created['菜单管理'], 'menu:delete', 3),
            # 角色管理下：新增角色、编辑角色、删除角色、复制角色
            ('新增角色', created['角色管理'], 'role:add', 1),
            ('编辑角色', created['角色管理'], 'role:edit', 2),
            ('删除角色', created['角色管理'], 'role:delete', 3),
            ('复制角色', created['角色管理'], 'role:copy', 4),
            # 用户管理下：新增用户、编辑用户、删除用户、重置密码、启用/禁用
            ('新增用户', created['用户管理'], 'user:add', 1),
            ('编辑用户', created['用户管理'], 'user:edit', 2),
            ('删除用户', created['用户管理'], 'user:delete', 3),
            ('重置密码', created['用户管理'], 'user:reset_password', 4),
            ('启用/禁用', created['用户管理'], 'user:toggle_status', 5),
            # 操作日志下：（只读，无按钮权限）
            # 个人中心下：（只读，无按钮权限）
            # 系统配置下：新增配置、编辑配置、删除配置
            ('新增配置', created['系统配置'], 'config:add', 1),
            ('编辑配置', created['系统配置'], 'config:edit', 2),
            ('删除配置', created['系统配置'], 'config:delete', 3),
            # 服务器管理下：新增、编辑、删除
            ('新增服务器', created['服务器管理'], 'server:add', 1),
            ('编辑服务器', created['服务器管理'], 'server:edit', 2),
            ('删除服务器', created['服务器管理'], 'server:delete', 3),
             # AI 配置下：新增、编辑、删除、设默认
            ('新增 AI 配置', created['AI 配置'], 'ai_config:add', 1),
            ('编辑 AI 配置', created['AI 配置'], 'ai_config:edit', 2),
            ('删除 AI 配置', created['AI 配置'], 'ai_config:delete', 3),
            ('设为默认', created['AI 配置'], 'ai_config:set_default', 4),
        ]
        for btn_name, parent_menu, permission, sort in buttons_data:
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
            if is_new:
                self.stdout.write(self.style.SUCCESS(f'  创建按钮权限: {btn_name} ({permission})'))
            else:
                self.stdout.write(f'  按钮权限已存在: {btn_name}')

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
            # 注册用户默认只能访问个人中心
            personal_center = Menu.objects.filter(name='个人中心').first()
            if personal_center:
                registered_role.menus.set([personal_center])
            self.stdout.write(self.style.SUCCESS(f'  创建角色: 注册用户'))
        else:
            self.stdout.write(f'  角色已存在: 注册用户')

        # 创建默认系统配置
        self._init_default_configs()

        self.stdout.write(self.style.SUCCESS('\n初始化完成！'))

    def _init_default_configs(self):
        """初始化默认系统配置项"""
        self.stdout.write(self.style.MIGRATE_HEADING('\n  初始化系统配置:'))
        configs = [
            ('system_name', 'Django Layui Admin', '系统名称，显示在浏览器标题栏和侧边栏', 'string', 1),
            ('system_version', '1.0.0', '系统版本号', 'string', 2),
            ('system_description', '', '系统描述信息', 'string', 3),
            ('logo_icon', 'layui-icon-code-circle', '侧边栏Logo图标（layui图标类名）', 'string', 4),
            ('logo_url', '', '侧边栏Logo图片URL（设置后替换图标，支持本地上传）', 'url', 5),
            ('favicon_url', '', '浏览器标签页图标URL（支持ICO/PNG/SVG，支持本地上传）', 'url', 6),
            ('frontend_url', '', '前端页面地址（顶部"查看站点"按钮跳转地址）', 'url', 7),
            ('copyright', '', '版权信息', 'string', 8),
            ('webssh_url', '/webssh/', 'WebSSH 服务地址（用于服务器终端功能，默认 /webssh/）', 'url', 9),
        ]
        for key, value, desc, config_type, sort in configs:
            _, is_new = SystemConfig.objects.get_or_create(
                key=key,
                defaults={
                    'value': value,
                    'description': desc,
                    'config_type': config_type,
                    'sort': sort,
                }
            )
            if is_new:
                self.stdout.write(self.style.SUCCESS(f'  创建配置: {key}'))
            else:
                self.stdout.write(f'  配置已存在: {key}')
