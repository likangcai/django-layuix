from django.db import migrations


def move_scope_menu(apps, schema_editor):
    Menu = apps.get_model('django_layuix_rbac', 'Menu')
    parent = Menu.objects.filter(name='权限管理').first()
    if not parent:
        return

    menus = list(Menu.objects.filter(name__in=['组织节点', '数据范围']).order_by('id'))
    if not menus:
        return

    menu = menus[0]
    menu.name = '数据范围'
    menu.name_en = 'Data Scope'
    menu.name_zh_hans = '数据范围'
    menu.icon = 'layui-icon-tree'
    menu.path = '/permission/data-scope'
    menu.parent = parent
    menu.sort = 6
    menu.save()

    for duplicate in menus[1:]:
        duplicate.delete()


def restore_scope_menu(apps, schema_editor):
    Menu = apps.get_model('django_layuix_rbac', 'Menu')
    parent = Menu.objects.filter(name='系统管理').first()
    if not parent:
        return
    menu = Menu.objects.filter(name='数据范围').first()
    if not menu:
        return
    menu.name = '组织节点'
    menu.name_en = 'Scope Nodes'
    menu.name_zh_hans = '组织节点'
    menu.path = '/system/scope-nodes'
    menu.parent = parent
    menu.sort = 5
    menu.save()


class Migration(migrations.Migration):

    dependencies = [
        ('django_layuix_rbac', '0008_abac_and_scope_nodes'),
    ]

    operations = [
        migrations.RunPython(move_scope_menu, restore_scope_menu),
    ]
