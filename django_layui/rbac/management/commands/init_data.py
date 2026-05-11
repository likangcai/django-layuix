# -*- coding: utf-8 -*-
"""
数据初始化管理命令
用法: python manage.py init_data

功能：在 init_menu 的基础上增加创建超级管理员功能
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django_layui.rbac.models import Role, UserProfile


class Command(BaseCommand):
    help = '初始化系统数据：创建超级管理员 + 执行 init_menu（角色、菜单、系统配置）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            default=False,
            help='强制重新初始化所有数据（包括重置配置为默认值）',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        
        self.stdout.write(self.style.SUCCESS('开始初始化系统数据...'))

        # 1. 先执行 init_menu 创建角色、菜单和系统配置
        self.stdout.write('  执行 init_menu...')
        if force:
            call_command('init_menu', force=True)
        else:
            call_command('init_menu')

        # 2. 创建超级管理员用户
        self._create_admin()

        # 3. 绑定超级管理员角色给 admin 用户
        self._bind_admin_role()

        self.stdout.write(self.style.SUCCESS('系统数据初始化完成!'))
        self.stdout.write(self.style.SUCCESS('超级管理员账号: admin / admin123'))
        self.stdout.write(self.style.SUCCESS('已创建角色: 管理员、注册用户、普通用户'))

    def _create_admin(self):
        """创建超级管理员用户"""
        self.stdout.write('  创建超级管理员...')
        if UserProfile.objects.filter(username='admin').exists():
            self.stdout.write(self.style.WARNING('    超级管理员已存在，跳过'))
            return

        # 创建超级管理员（is_active默认为True）
        admin = UserProfile.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123',
            nickname='超级管理员',
        )
        
        self.stdout.write(self.style.SUCCESS('    超级管理员创建成功'))

    def _bind_admin_role(self):
        """绑定超级管理员角色给 admin 用户"""
        self.stdout.write('  绑定超级管理员角色...')
        try:
            admin_user = UserProfile.objects.get(username='admin')
            admin_role = Role.objects.get(code='admin')
            
            if admin_role in admin_user.roles.all():
                self.stdout.write(self.style.WARNING('    超级管理员角色已绑定，跳过'))
                return
            
            admin_user.roles.add(admin_role)
            self.stdout.write(self.style.SUCCESS('    超级管理员角色绑定成功'))
        except UserProfile.DoesNotExist:
            self.stdout.write(self.style.WARNING('    未找到 admin 用户'))
        except Role.DoesNotExist:
            self.stdout.write(self.style.WARNING('    未找到超级管理员角色'))
