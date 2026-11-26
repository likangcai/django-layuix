# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-26 22:19
# @FileName  : 0012_auth_token_state.py
# -----------------------------
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('django_layuix_rbac', '0011_add_view_permission_buttons'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuthToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('jti', models.CharField(max_length=64, unique=True, verbose_name='Token ID')),
                ('token_type', models.CharField(default='access', max_length=20, verbose_name='Token 类型')),
                ('status', models.PositiveSmallIntegerField(default=1, verbose_name='状态')),
                ('issued_at', models.DateTimeField(verbose_name='签发时间')),
                ('expires_at', models.DateTimeField(verbose_name='过期时间')),
                ('revoked_at', models.DateTimeField(blank=True, null=True, verbose_name='撤销时间')),
                ('revoke_reason', models.CharField(blank=True, default='', max_length=64, verbose_name='撤销原因')),
                ('client_ip', models.CharField(blank=True, default='', max_length=64, verbose_name='客户端 IP')),
                ('user_agent', models.CharField(blank=True, default='', max_length=255, verbose_name='User Agent')),
                ('last_used_at', models.DateTimeField(blank=True, null=True, verbose_name='最后使用时间')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='auth_tokens', to=settings.AUTH_USER_MODEL, verbose_name='用户')),
            ],
            options={
                'db_table': 'sys_auth_token',
                'verbose_name': '访问令牌',
                'verbose_name_plural': '访问令牌',
                'ordering': ['-issued_at'],
            },
        ),
        migrations.AddIndex(
            model_name='authtoken',
            index=models.Index(fields=['user', 'status', 'expires_at'], name='idx_auth_token_user_status_exp'),
        ),
        migrations.AddIndex(
            model_name='authtoken',
            index=models.Index(fields=['expires_at'], name='idx_auth_token_expires_at'),
        ),
    ]
