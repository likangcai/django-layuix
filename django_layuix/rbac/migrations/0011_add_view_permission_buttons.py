# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-26 22:19
# @FileName  : 0011_add_view_permission_buttons.py
# -----------------------------
from django.db import migrations


BUTTONS = [
    ('查看服务器', 'View Servers', '查看服务器', '服务器管理', 'server:view', 0),
    ('查看 AI 配置', 'View AI Config', '查看 AI 配置', 'AI 配置', 'ai_config:view', 0),
]


def add_buttons(apps, schema_editor):
    Menu = apps.get_model('django_layuix_rbac', 'Menu')
    Role = apps.get_model('django_layuix_rbac', 'Role')
    admin_role = Role.objects.filter(code='admin').first()
    for name, name_en, name_zh, parent_name, permission, sort in BUTTONS:
        parent = Menu.objects.filter(name=parent_name).first()
        if not parent:
            continue
        menu, created = Menu.objects.get_or_create(
            name=name,
            parent=parent,
            defaults={
                'name_en': name_en,
                'name_zh_hans': name_zh,
                'icon': '',
                'path': '',
                'component': '',
                'menu_type': 3,
                'permission': permission,
                'sort': sort,
                'status': True,
                'visible': True,
            },
        )
        if not created and menu.permission != permission:
            menu.permission = permission
            menu.save(update_fields=['permission'])
        if created and admin_role:
            admin_role.menus.add(menu)


def remove_buttons(apps, schema_editor):
    Menu = apps.get_model('django_layuix_rbac', 'Menu')
    Menu.objects.filter(
        name__in=[row[0] for row in BUTTONS],
        permission__in=[row[4] for row in BUTTONS],
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('django_layuix_rbac', '0010_core_authorization_and_plugin_state'),
    ]

    operations = [
        migrations.RunPython(add_buttons, remove_buttons),
    ]
