# -*- coding: utf-8 -*-
"""
Theme CSS Generator
动态生成主题CSS文件

使用方式:
    python manage.py generate_themes
"""
import os
from django.conf import settings


def generate_theme_css(theme_config, output_dir):
    """
    根据主题配置生成CSS文件
    
    Args:
        theme_config: 主题配置字典
        output_dir: 输出目录
    """
    name = theme_config['name']
    file_name = theme_config['file']
    colors = theme_config['colors']
    
    # 提取颜色变量
    primary = colors.get('primary', '#1E9FFF')
    menu_bg = colors.get('menu_bg', '#232935')
    menu_text = colors.get('menu_text', '#BFCBD9')
    header_bg = colors.get('header_bg', '#232935')
    logo_color = colors.get('logo_color', '#FFFFFF')
    
    # 处理渐变色(如果是渐变,取第一个颜色作为备选)
    if 'linear-gradient' in header_bg:
        header_bg_solid = header_bg.split(',')[-1].strip().rstrip(')')
    else:
        header_bg_solid = header_bg
    
    # CSS模板
    css_template = f"""/* 
 * Django-Layui Theme: {name}
 * Auto-generated theme CSS
 */

:root {{
    --theme-primary: {primary};
    --theme-menu-bg: {menu_bg};
    --theme-menu-text: {menu_text};
    --theme-header-bg: {header_bg};
    --theme-logo-color: {logo_color};
}}

/* ---- 顶部导航栏 ---- */
.layui-layout-admin .layui-header {{
    background: {header_bg} !important;
}}

.layui-layout-admin .layui-header .layui-logo {{
    color: {logo_color} !important;
    background: {menu_bg} !important;
}}

.layui-layout-admin .layui-header .layui-nav .layui-nav-item a {{
    color: {logo_color} !important;
}}

.layui-layout-admin .layui-header .layui-nav .layui-nav-item a:hover {{
    color: rgba(255,255,255,0.8) !important;
}}

/* ---- 侧边菜单 ---- */
.layui-layout-admin .layui-side {{
    background-color: {menu_bg} !important;
}}

.layui-side-menu .layui-nav .layui-nav-item a {{
    color: {menu_text} !important;
}}

.layui-side-menu .layui-nav .layui-nav-item a:hover {{
    color: {primary} !important;
}}

.layui-side-menu .layui-nav .layui-nav-item.layui-this a {{
    color: {primary} !important;
    background-color: rgba(30, 159, 255, 0.1) !important;
}}

.layui-side-menu .layui-nav .layui-nav-child dd.layui-this {{
    background-color: rgba(30, 159, 255, 0.15) !important;
}}

.layui-side-menu .layui-nav .layui-nav-child dd.layui-this a {{
    color: {primary} !important;
}}

.layui-nav-tree .layui-nav-bar {{
    background-color: {primary} !important;
}}

/* ---- 按钮样式 ---- */
.layui-btn-primary {{
    border-color: {primary} !important;
    color: {primary} !important;
}}

.layui-btn-primary:hover {{
    border-color: {primary} !important;
    color: {primary} !important;
    opacity: 0.8;
}}

.layui-btn-normal {{
    background-color: {primary} !important;
}}

/* ---- 表单元素 ---- */
.layui-input:focus,
.layui-textarea:focus {{
    border-color: {primary} !important;
}}

.layui-form-select dl dd.layui-this {{
    background-color: rgba(30, 159, 255, 0.1) !important;
    color: {primary} !important;
}}

/* ---- 表格样式 ---- */
.layui-table-view .layui-table-body tr:hover {{
    background-color: rgba(30, 159, 255, 0.05) !important;
}}

.layui-table-page .layui-laypage .layui-laypage-curr .layui-laypage-em {{
    background-color: {primary} !important;
}}

/* ---- Tab标签页 ---- */
.layui-tab-title li.layui-this {{
    color: {primary} !important;
}}

.layui-tab-title li.layui-this::after {{
    border-bottom-color: {primary} !important;
}}

/* ---- 面包屑导航 ---- */
.layui-breadcrumb a:hover {{
    color: {primary} !important;
}}

/* ---- 链接样式 ---- */
a {{
    color: {primary} !important;
}}

a:hover {{
    color: {primary} !important;
    opacity: 0.8;
}}

/* ---- 徽章样式 ---- */
.layui-badge-dot {{
    background-color: {primary} !important;
}}

/* ---- 时间线 ---- */
.layui-timeline-axis {{
    color: {primary} !important;
}}

/* ---- 进度条 ---- */
.layui-progress-bar {{
    background-color: {primary} !important;
}}

/* ---- 开关按钮 ---- */
.layui-form-onswitch {{
    background-color: {primary} !important;
    border-color: {primary} !important;
}}

/* ---- 复选框 ---- */
.layui-form-checked span,
.layui-form-checked:hover span {{
    background-color: {primary} !important;
}}

/* ---- 单选框 ---- */
.layui-form-radioed>i,
.layui-form-radioed>span {{
    color: {primary} !important;
}}

/* ---- 滑块 ---- */
.layui-slider-bar {{
    background-color: {primary} !important;
}}

.layui-slider-step.layui-slider-active {{
    background-color: {primary} !important;
}}

/* ---- 评分 ---- */
.layui-rate li i.layui-icon-rate-solid {{
    color: {primary} !important;
}}

/* ---- 树组件 ---- */
.layui-tree-set .layui-tree-entry .layui-tree-txt a {{
    color: {primary} !important;
}}

/* ---- 轮播图指示器 ---- */
.layui-carousel-ind ul.layui-this {{
    background-color: {primary} !important;
}}

/* ---- 流加载按钮 ---- */
.layui-flow-more a {{
    background-color: {primary} !important;
}}

/* ---- 代码高亮 ---- */
pre code .layui-code-h3 {{
    border-left-color: {primary} !important;
}}

/* ---- 分割线 ---- */
.layui-divider.layui-bg-primary {{
    background-color: {primary} !important;
}}

/* ---- 动画效果 ---- */
@keyframes layui-rotate {{
    from {{ transform: rotate(0deg); }}
    to {{ transform: rotate(360deg); }}
}}

.layui-icon-loading {{
    animation: layui-rotate 1s linear infinite;
}}

/* ---- 响应式适配 ---- */
@media screen and (max-width: 768px) {{
    .layui-layout-admin .layui-header .layui-logo {{
        font-size: 14px;
    }}
}}

/* ---- 深色模式优化 ---- */
@media (prefers-color-scheme: dark) {{
    body {{
        background-color: #1a1a1a;
    }}
}}

/* ---- 打印样式 ---- */
@media print {{
    .layui-header,
    .layui-side,
    .layui-footer {{
        display: none !important;
    }}
}}
"""
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 写入CSS文件
    css_path = os.path.join(output_dir, file_name)
    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(css_template)
    
    return css_path


def generate_all_themes():
    """
    生成所有主题CSS文件
    """
    from django_layui.rbac.themes import DJANGO_LAYUI_THEMES
    
    # 获取输出目录
    static_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(static_dir, 'layui', 'css', 'themes')
    
    print(f"🎨 开始生成主题CSS文件...")
    print(f"📁 输出目录: {output_dir}")
    
    generated = []
    for theme in DJANGO_LAYUI_THEMES:
        try:
            css_path = generate_theme_css(theme, output_dir)
            generated.append(css_path)
            print(f"✅ {theme['name']} -> {theme['file']}")
        except Exception as e:
            print(f"❌ {theme['name']} 失败: {e}")
    
    print(f"\n✨ 成功生成 {len(generated)} 个主题CSS文件!")
    return generated


if __name__ == '__main__':
    # 独立运行时使用
    import sys
    import django
    
    # 配置Django
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            INSTALLED_APPS=[
                'django.contrib.contenttypes',
                'django.contrib.auth',
            ],
        )
        django.setup()
    
    generate_all_themes()
