# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-26 22:19
# @FileName  : 0002_rbac3.py
# -----------------------------
"""RBAC3：角色继承、互斥组、前置角色和基数约束。"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_layuix_rbac', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='role',
            name='parent_roles',
            field=models.ManyToManyField(
                blank=True,
                related_name='child_roles',
                symmetrical=False,
                to='django_layuix_rbac.role',
                verbose_name='继承角色',
            ),
        ),
        migrations.AddField(
            model_name='role',
            name='max_users',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='人数上限'),
        ),
        migrations.CreateModel(
            name='RoleMutex',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='互斥组名称')),
                ('kind', models.CharField(choices=[('ssd', '静态职责分离(SSD)'), ('dsd', '动态职责分离(DSD)')], default='ssd', max_length=3, verbose_name='互斥类型')),
                ('description', models.TextField(blank=True, default='', verbose_name='说明')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('roles', models.ManyToManyField(blank=True, related_name='mutex_groups', to='django_layuix_rbac.role', verbose_name='互斥角色')),
            ],
            options={
                'db_table': 'sys_role_mutex',
                'verbose_name': '角色互斥组',
                'verbose_name_plural': '角色互斥组',
                'ordering': ['id'],
                'indexes': [models.Index(fields=['kind', 'is_active'], name='idx_role_mutex_kind_active')],
            },
        ),
        migrations.CreateModel(
            name='RolePrerequisite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('prerequisite', models.ForeignKey(on_delete=models.CASCADE, related_name='prerequisite_for', to='django_layuix_rbac.role', verbose_name='前置角色')),
                ('role', models.ForeignKey(on_delete=models.CASCADE, related_name='required_by', to='django_layuix_rbac.role', verbose_name='角色')),
            ],
            options={
                'db_table': 'sys_role_prerequisite',
                'verbose_name': '前置角色',
                'verbose_name_plural': '前置角色',
                'ordering': ['id'],
                'unique_together': {('role', 'prerequisite')},
            },
        ),
    ]
