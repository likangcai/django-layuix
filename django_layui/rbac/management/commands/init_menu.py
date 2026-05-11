# -*- coding: utf-8 -*-
"""
初始化默认菜单数据
用法:
  python manage.py init_menu             # 初始化菜单、角色、系统配置（已存在则跳过）
  python manage.py init_menu --force     # 强制清空后重新初始化
  python manage.py init_menu --fix-icons # 修复数据库中可能存在的无效 Layui 图标

"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django_layui.rbac.models import Menu, Role, SystemConfig


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

        # 如果已有菜单数据且不强制重新初始化，则跳过
        if Menu.objects.exists() and not force:
            self._init_default_configs()
            self.stdout.write(self.style.WARNING('菜单数据已存在，跳过初始化。如需重新初始化，请使用 --force 参数。'))
            return
        
        # 如果强制重新初始化，更新现有菜单而不是删除
        if force and Menu.objects.exists():
            self.stdout.write(self.style.WARNING('使用 --force 模式，将更新现有菜单数据（保留角色权限关联）'))

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

            # ---- 系统管理 ----
            ('系统管理', 'System', '系统管理', 'layui-icon-set', '', 1, 2, None),
            ('个人中心', 'Profile', '个人中心', 'layui-icon-user', '/static/layui/pages/profile.html', 2, 1, '系统管理'),
            ('操作日志', 'Log', '操作日志', 'layui-icon-log', '/system/log', 2, 2, '系统管理'),
            ('系统配置', 'Config', '系统配置', 'layui-icon-set-sm', '/system/config', 2, 3, '系统管理'),

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
            # 服务器管理下：新增、编辑、删除、查看日志、终端
            ('新增服务器', 'Add Server', '新增服务器', created['服务器管理'], 'server:add', 1),
            ('编辑服务器', 'Edit Server', '编辑服务器', created['服务器管理'], 'server:edit', 2),
            ('删除服务器', 'Delete Server', '删除服务器', created['服务器管理'], 'server:delete', 3),
            ('查看日志', 'View Log', '查看日志', created['服务器管理'], 'server:view_log', 4),
            ('终端连接', 'Terminal', '终端连接', created['服务器管理'], 'server:terminal', 5),
            # AI 配置下：新增、编辑、删除、测试连接、设默认
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
            self.stdout.write(f'  角色已存在: 普通用户')

        # 创建默认系统配置
        self._init_default_configs()

        self.stdout.write(self.style.SUCCESS('\n初始化完成！'))

    def _init_default_configs(self):
        """初始化默认系统配置项"""
        self.stdout.write(self.style.MIGRATE_HEADING('\n  初始化系统配置:'))
        configs = [
            ('system_name', 'Django Layui Admin', '系统名称，显示在浏览器标题栏和侧边栏', 'string', 1),
            ('system_version', '1.0.0', '系统版本号', 'string', 2),
            ('system_description', '', '系统描述信息（显示在管理后台底部）', 'text', 3),
            ('logo_icon', 'layui-icon-code-circle', 'Logo图标（layui图标类名）', 'string', 4),
            ('logo_url', '', 'Logo图片URL（设置后替换图标，支持本地上传）', 'image', 5),
            ('favicon_url', '', '浏览器标签页图标URL（支持ICO/PNG/SVG，支持本地上传）', 'image', 6),
            ('copyright', '', '版权信息（显示在登录页和管理后台底部）', 'string', 7),
            ('frontend_url', '', '前端页面地址（顶部"查看站点"按钮跳转地址）', 'url', 8),
            ('webssh_url', '/webssh/', 'WebSSH 服务地址（用于服务器终端功能，默认 /webssh/）', 'url', 9),
            ('login_bg_type', 'gradient', '登录页背景类型：gradient(渐变)/color(纯色)/image(图片)', 'string', 10),
            ('login_bg_value', 'linear-gradient(135deg, #2d3a4b 0%, #1a1a2e 100%)', '登录页背景渐变/颜色值（当type为gradient或color时生效）', 'color', 11),
            ('login_bg_image', '', '登录页背景图片URL（当type为image时生效，支持本地上传）', 'image', 12),
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
