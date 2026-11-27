# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-26 22:19
# @FileName  : urls.py
# -----------------------------
from django.urls import path

from . import views_api

urlpatterns = [
    path('orders/', views_api.order_list, name='permission_demo_order_list'),
]
