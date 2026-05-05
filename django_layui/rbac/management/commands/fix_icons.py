# -*- coding: utf-8 -*-
"""
修复无效的 Layui 图标
用法: python manage.py fix_icons
"""
from django.core.management.base import BaseCommand
from django_layui.rbac.models import Menu


class Command(BaseCommand):
    help = '修复数据库中无效的 Layui 图标'

    def handle(self, *args, **options):
        # 图标映射：错误图标 -> 正确图标
        icon_mapping = {
            'layui-icon-menu': 'layui-icon-menu-fill',      # 菜单
            'layui-icon-server': 'layui-icon-console',      # 服务器 -> 控制台
            'layui-icon-brain': 'layui-icon-light',         # AI/大脑 -> 太阳/智能
            'layui-icon-checkin': 'layui-icon-form',        # 签到 -> 表单
        }

        updated_count = 0
        for old_icon, new_icon in icon_mapping.items():
            menus = Menu.objects.filter(icon=old_icon)
            count = menus.count()
            if count > 0:
                menus.update(icon=new_icon)
                self.stdout.write(self.style.SUCCESS(
                    f'✓ 更新 {count} 个菜单: {old_icon} → {new_icon}'
                ))
                updated_count += count
            else:
                self.stdout.write(f'  跳过 {old_icon} (未找到使用该图标的菜单)')

        if updated_count > 0:
            self.stdout.write(self.style.SUCCESS(
                f'\n总计更新 {updated_count} 个菜单图标'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                '\n没有需要更新的图标'
            ))
