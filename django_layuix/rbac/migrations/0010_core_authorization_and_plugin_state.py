from django.db import migrations, models


MENU_VIEW_PERMISSIONS = {
    '仪表盘': 'dashboard:view',
    '菜单管理': 'menu:view',
    '角色管理': 'role:view',
    '用户管理': 'user:view',
    '操作日志': 'log:view',
    '系统配置': 'config:view',
    '服务器管理': 'server:view',
    'AI 配置': 'ai_config:view',
    'ABAC 策略': 'abac:view',
    '数据范围': 'scope:view',
    '约束管理': 'constraint:view',
}


def set_view_permissions(apps, schema_editor):
    Menu = apps.get_model('django_layuix_rbac', 'Menu')
    for name, permission in MENU_VIEW_PERMISSIONS.items():
        Menu.objects.filter(name=name).exclude(permission=permission).update(permission=permission)


def clear_view_permissions(apps, schema_editor):
    Menu = apps.get_model('django_layuix_rbac', 'Menu')
    Menu.objects.filter(permission__in=MENU_VIEW_PERMISSIONS.values()).update(permission='')


class Migration(migrations.Migration):

    dependencies = [
        ('django_layuix_rbac', '0009_move_scope_menu'),
    ]

    operations = [
        migrations.AddField(
            model_name='pluginregistry',
            name='desired_active',
            field=models.BooleanField(default=True, verbose_name='用户期望启用'),
        ),
        migrations.RunPython(set_view_permissions, clear_view_permissions),
    ]
