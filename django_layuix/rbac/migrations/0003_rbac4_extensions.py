# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-26 22:19
# @FileName  : 0003_rbac4_extensions.py
# -----------------------------
"""RBAC4 extensions: permission-level mutex and strategy defaults."""
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
