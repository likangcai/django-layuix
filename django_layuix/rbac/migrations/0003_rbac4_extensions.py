# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-26 22:19
# @FileName  : 0003_rbac4_extensions.py
# -----------------------------
"""RBAC4 扩展：权限级互斥与策略默认值。"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_layuix_rbac', '0002_rbac3'),
    ]

    operations = [
        migrations.AddField(
            model_name='rolemutex',
            name='permissions',
            field=models.ManyToManyField(
                blank=True,
                related_name='permission_mutex_groups',
                to='django_layuix_rbac.menu',
                verbose_name='互斥权限',
            ),
        ),
    ]
