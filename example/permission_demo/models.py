# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-26 22:19
# @FileName  : models.py
# -----------------------------
from django.conf import settings
from django.db import models

from django_layuix.rbac.scopes import ScopedModelMixin


class DemoOrder(ScopedModelMixin, models.Model):
    """Copyable example model showing Scope + ABAC field filtering."""

    SCOPE_FIELD = 'department'

    title = models.CharField(max_length=100, verbose_name='标题')
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='demo_orders', verbose_name='负责人'
    )
    department = models.CharField(max_length=100, default='demo_global', verbose_name='作用域节点')
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='金额')
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='成本')
    status = models.CharField(max_length=20, default='pending', verbose_name='状态')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'demo_permission_order'
        verbose_name = '示例订单'
        verbose_name_plural = verbose_name
        ordering = ['-id']

    def __str__(self):
        return self.title
