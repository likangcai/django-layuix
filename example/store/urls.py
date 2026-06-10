# -*- coding: utf-8 -*-
"""
store/urls.py - 商品管理 REST API 路由
"""
from django.urls import path
from . import views_api

urlpatterns = [
    # Category
    path('categories/', views_api.category_list, name='store_category_list'),
    path('categories/create/', views_api.category_create, name='store_category_create'),
    path('categories/<int:pk>/', views_api.category_detail, name='store_category_detail'),

    # Product
    path('products/', views_api.product_list, name='store_product_list'),
    path('products/select/', views_api.product_select_list, name='store_product_select'),
    path('products/create/', views_api.product_create, name='store_product_create'),
    path('products/<int:pk>/', views_api.product_detail, name='store_product_detail'),

    # Order
    path('orders/', views_api.order_list, name='store_order_list'),
    path('orders/create/', views_api.order_create, name='store_order_create'),
    path('orders/<int:pk>/', views_api.order_detail, name='store_order_detail'),
]
