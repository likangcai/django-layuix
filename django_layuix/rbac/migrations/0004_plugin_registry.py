# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-26 22:19
# @FileName  : 0004_plugin_registry.py
# -----------------------------
"""Persist plugin registry metadata."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_layuix_rbac', '0003_rbac4_extensions'),
    ]

    operations = [
        migrations.CreateModel(
            name='PluginRegistry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=100, unique=True, verbose_name='插件标识')),
                ('name', models.CharField(max_length=100, verbose_name='插件名称')),
                ('version', models.CharField(default='1.0.0', max_length=30, verbose_name='版本')),
                ('description', models.TextField(blank=True, default='', verbose_name='说明')),
                ('api_prefix', models.CharField(blank=True, default='', max_length=200, verbose_name='API 前缀')),
                ('menu_path', models.CharField(blank=True, default='', max_length=200, verbose_name='菜单路径')),
                ('app_label', models.CharField(blank=True, default='', max_length=100, verbose_name='Django App Label')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
            options={
                'db_table': 'sys_plugin_registry',
                'verbose_name': '插件注册',
                'verbose_name_plural': '插件注册',
                'ordering': ['key'],
            },
        ),
    ]
