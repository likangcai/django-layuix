# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-26 22:19
# @FileName  : 0007_sod_compat.py
# -----------------------------
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('django_layuix_rbac', '0006_scope_and_parent'),
    ]

    operations = [
        migrations.CreateModel(
            name='SoDConstraint',
            fields=[],
            options={
                'proxy': True,
                'verbose_name': 'SSD 互斥约束',
                'verbose_name_plural': 'SSD 互斥约束',
            },
            bases=('django_layuix_rbac.rolemutex',),
        ),
    ]
