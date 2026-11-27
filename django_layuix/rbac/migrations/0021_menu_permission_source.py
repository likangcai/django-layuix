# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-27
# @FileName  : 0021_menu_permission_source.py
# -----------------------------
from django.db import migrations, models


def backfill_permission_source(apps, schema_editor):
    Menu = apps.get_model('django_layuix_rbac', 'Menu')
    Menu.objects.filter(plugin_key='permission_catalog').update(permission_source='builtin')
    Menu.objects.exclude(plugin_key='permission_catalog').update(permission_source='business')


def noop_reverse(apps, schema_editor):
    return None


class Migration(migrations.Migration):

    dependencies = [
        ('django_layuix_rbac', '0020_region_level_index'),
    ]

    operations = [
        migrations.AddField(
            model_name='menu',
            name='permission_source',
            field=models.CharField(choices=[('builtin', '内置'), ('business', '业务')], default='business', max_length=20, verbose_name='权限来源'),
        ),
        migrations.RunPython(backfill_permission_source, noop_reverse),
    ]
