# -*- coding: utf-8 -*-
"""
修复 AI 配置菜单的按钮权限
用法: python manage.py fix_ai_config_permissions
"""
from django.core.management.base import BaseCommand
from django_layui.rbac.models import Menu


class Command(BaseCommand):
    help = '修复 AI 配置菜单的按钮权限（新增、编辑、删除、设默认）'

    def handle(self, *args, **options):
        # 查找 AI 配置菜单
        ai_menu = Menu.objects.filter(name='AI 配置').first()
        if not ai_menu:
            self.stdout.write(self.style.ERROR('错误：找不到 "AI 配置" 菜单，请先运行 init_menu'))
            return

        self.stdout.write(self.style.MIGRATE_HEADING('\n修复 AI 配置按钮权限:'))
        
        buttons_data = [
            ('新增 AI 配置', ai_menu, 'ai_config:add', 1),
            ('编辑 AI 配置', ai_menu, 'ai_config:edit', 2),
            ('删除 AI 配置', ai_menu, 'ai_config:delete', 3),
            ('设为默认', ai_menu, 'ai_config:set_default', 4),
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
                self.stdout.write(self.style.SUCCESS(f'  ✓ 创建按钮权限: {btn_name} ({permission})'))
            else:
                self.stdout.write(f'  - 按钮权限已存在: {btn_name}')

        self.stdout.write(self.style.SUCCESS('\n修复完成！请刷新页面或重新登录后生效。'))
