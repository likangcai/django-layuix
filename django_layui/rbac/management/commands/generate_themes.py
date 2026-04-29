# -*- coding: utf-8 -*-
"""
管理命令: 生成所有主题CSS文件

使用方式:
    python manage.py generate_themes
"""
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = '生成Django-Layui多主题CSS文件'

    def add_arguments(self, parser):
        parser.add_argument(
            '--theme',
            type=str,
            help='指定生成某个主题(可选)',
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='列出所有可用主题',
        )

    def handle(self, *args, **options):
        from django_layui.rbac.themes import get_all_themes, get_theme_by_name
        from django_layui.rbac.theme_generator import generate_theme_css, generate_all_themes
        import os
        
        if options['list']:
            # 列出所有主题
            themes = get_all_themes()
            self.stdout.write(self.style.SUCCESS(f'\n📋 可用的 {len(themes)} 个主题:\n'))
            
            for i, theme in enumerate(themes, 1):
                colors = theme['colors']
                self.stdout.write(
                    f"  {i:2d}. {theme['name']:20s} "
                    f"[主色:{colors['primary']} "
                    f"菜单:{colors['menu_bg']}]"
                )
            
            self.stdout.write('\n')
            return
        
        if options['theme']:
            # 生成指定主题
            theme = get_theme_by_name(options['theme'])
            if not theme:
                raise CommandError(f'主题 "{options["theme"]}" 不存在')
            
            static_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            output_dir = os.path.join(static_dir, 'layui', 'css', 'themes')
            
            css_path = generate_theme_css(theme, output_dir)
            self.stdout.write(self.style.SUCCESS(f'✅ 已生成主题: {theme["name"]}'))
            self.stdout.write(self.style.SUCCESS(f'📁 文件路径: {css_path}\n'))
        else:
            # 生成所有主题
            try:
                generated = generate_all_themes()
                self.stdout.write(self.style.SUCCESS(f'\n🎉 主题生成完成!'))
                self.stdout.write(self.style.SUCCESS(f'📊 共生成 {len(generated)} 个CSS文件\n'))
                
                # 提示如何使用
                self.stdout.write(self.style.WARNING('💡 使用方法:'))
                self.stdout.write('在 UserProfile 模型中设置 theme 字段即可:\n')
                self.stdout.write('   user.theme = "Element蓝"\n')
                self.stdout.write('   user.save()\n\n')
                
            except Exception as e:
                raise CommandError(f'生成主题失败: {e}')
