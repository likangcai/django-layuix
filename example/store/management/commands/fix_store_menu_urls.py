# -*- coding: utf-8 -*-
"""
清理无效菜单的管理命令

用法: python manage.py fix_store_menu_urls
"""
from django.core.management.base import BaseCommand
from django_layui.rbac.models import Menu


class Command(BaseCommand):
    help = '修复 store 应用的菜单 URL 路径'

    def handle(self, *args, **options):
        self.stdout.write('开始修复 store 应用菜单...\n')
        
        # 查找所有 store 应用下的菜单
        store_menus = Menu.objects.filter(
            name__in=['商品分类', '商品管理', '订单管理']
        )
        
        fixed_count = 0
        for menu in store_menus:
            old_path = menu.path
            new_path = f'/admin/store/{menu.name}/'
            
            # 标准化模型名称到 URL 路径
            url_map = {
                '商品分类': '/admin/store/category/',
                '商品管理': '/admin/store/product/',
                '订单管理': '/admin/store/order/',
            }
            
            correct_path = url_map.get(menu.name)
            if correct_path and old_path != correct_path:
                menu.path = correct_path
                menu.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ 修复: {menu.name}\n'
                        f'  旧路径: {old_path}\n'
                        f'  新路径: {correct_path}'
                    )
                )
                fixed_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f'- 跳过: {menu.name} (路径已是 {menu.path})')
                )
        
        self.stdout.write(f'\n修复完成！共修复 {fixed_count} 个菜单。\n')
        self.stdout.write('请刷新页面查看效果。\n')
