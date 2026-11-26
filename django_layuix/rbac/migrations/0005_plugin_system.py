# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-26 22:19
# @FileName  : 0005_plugin_system.py
# -----------------------------
"""第三方插件系统：清单、校验元数据和菜单归属。"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_layuix_rbac', '0004_plugin_registry'),
    ]

    operations = [
        migrations.AddField(
            model_name='menu',
            name='plugin_key',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='所属插件'),
        ),
        migrations.AddField(
            model_name='pluginregistry',
            name='dependencies',
            field=models.TextField(blank=True, default='', verbose_name='依赖声明'),
        ),
        migrations.AddField(
            model_name='pluginregistry',
            name='source',
            field=models.CharField(default='app', max_length=20, verbose_name='来源'),
        ),
        migrations.AddField(
            model_name='pluginregistry',
            name='validation_error',
            field=models.TextField(blank=True, default='', verbose_name='校验错误'),
        ),
    ]
