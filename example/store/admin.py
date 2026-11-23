# -*- coding: utf-8 -*-
"""
store/admin.py - 商品管理 Admin 注册
改为使用 django-layuix 的 LayuiAjaxAdmin，支持 AJAX 批量操作
前端使用 Layui 静态页面进行 CRUD，不再依赖 Django 原生 admin 页面
"""
from django.contrib import admin
from django_layuix.rbac.ajax_admin import LayuiAjaxAdmin
from .models import Category, Product, Order


@admin.register(Category)
class CategoryAdmin(LayuiAjaxAdmin):
    """商品分类管理"""
    list_display = ['id', 'name', 'description', 'sort']
    search_fields = ['name']
    ordering = ['sort', 'id']


@admin.register(Product)
class ProductAdmin(LayuiAjaxAdmin):
    """商品管理"""
    list_display = ['id', 'name', 'sku', 'category', 'price', 'stock', 'status']
    search_fields = ['name', 'sku']
    list_filter = ['status', 'category']
    ordering = ['-create_time']


@admin.register(Order)
class OrderAdmin(LayuiAjaxAdmin):
    """订单管理"""
    list_display = ['order_no', 'customer_name', 'customer_phone', 'status', 'create_time']
    search_fields = ['order_no', 'customer_name', 'customer_phone']
    list_filter = ['status']
    ordering = ['-create_time']


# 自定义 Admin Site 标题
admin.site.site_header = 'Layui Admin 演示系统'
admin.site.site_title = 'Layui Admin'
admin.site.index_title = '欢迎使用 Layui Admin'
