# -*- coding: utf-8 -*-
"""
store/admin.py - 商品管理 Admin 注册
展示 django-layui 主题在各种 Admin 配置下的效果
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, Order, OrderItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """商品分类管理"""
    list_display = ['id', 'name', 'description', 'sort', 'product_count', 'create_time']
    search_fields = ['name']
    list_editable = ['sort']
    ordering = ['sort', 'id']

    def product_count(self, obj):
        count = obj.products.count()
        return format_html('<span style="color:#1890ff;font-weight:bold">{}</span>', count)
    product_count.short_description = '商品数量'


class OrderItemInline(admin.TabularInline):
    """订单明细内联"""
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'product_sku', 'unit_price', 'quantity', 'subtotal']
    fields = ['product_name', 'product_sku', 'unit_price', 'quantity', 'subtotal']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """商品管理"""
    list_display = ['id', 'name', 'sku', 'category', 'price_display', 'stock',
                    'sales', 'status_display', 'is_featured', 'create_time']
    list_filter = ['status', 'is_featured', 'category']
    search_fields = ['name', 'sku', 'description']
    list_editable = ['is_featured']
    list_select_related = ['category']
    date_hierarchy = 'create_time'
    ordering = ['-create_time']
    readonly_fields = ['sales', 'create_time', 'update_time']

    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'sku', 'category', 'description')
        }),
        ('价格库存', {
            'fields': ('price', 'cost_price', 'stock', 'sales')
        }),
        ('状态设置', {
            'fields': ('status', 'is_featured')
        }),
        ('时间信息', {
            'classes': ('collapse',),
            'fields': ('create_time', 'update_time')
        }),
    )

    def price_display(self, obj):
        return format_html('¥<strong>{}</strong>', obj.price)
    price_display.short_description = '售价'
    price_display.admin_order_field = 'price'

    def status_display(self, obj):
        colors = {1: '#52c41a', 0: '#ff4d4f', 2: '#faad14'}
        labels = {1: '上架', 0: '下架', 2: '售罄'}
        color = colors.get(obj.status, '#999')
        label = labels.get(obj.status, '未知')
        return format_html(
            '<span style="color:{};font-weight:bold">{}</span>', color, label
        )
    status_display.short_description = '状态'
    status_display.admin_order_field = 'status'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """订单管理"""
    list_display = ['order_no', 'customer_name', 'customer_phone',
                    'total_amount_display', 'status_badge', 'create_time']
    list_filter = ['status', 'create_time']
    search_fields = ['order_no', 'customer_name', 'customer_phone']
    readonly_fields = ['order_no', 'create_time', 'update_time']
    date_hierarchy = 'create_time'
    ordering = ['-create_time']
    inlines = [OrderItemInline]

    fieldsets = (
        ('订单信息', {
            'fields': ('order_no', 'status', 'total_amount', 'remark')
        }),
        ('客户信息', {
            'fields': ('customer_name', 'customer_phone', 'shipping_address')
        }),
        ('时间信息', {
            'classes': ('collapse',),
            'fields': ('create_time', 'update_time')
        }),
    )

    def total_amount_display(self, obj):
        return format_html('¥<strong style="color:#1890ff">{}</strong>', obj.total_amount)
    total_amount_display.short_description = '订单金额'
    total_amount_display.admin_order_field = 'total_amount'

    def status_badge(self, obj):
        color_map = {
            'pending': ('#faad14', '待付款'),
            'paid': ('#1890ff', '已付款'),
            'shipped': ('#722ed1', '已发货'),
            'completed': ('#52c41a', '已完成'),
            'cancelled': ('#ff4d4f', '已取消'),
            'refunded': ('#fa8c16', '已退款'),
        }
        color, label = color_map.get(obj.status, ('#999', '未知'))
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:10px;font-size:12px">{}</span>',
            color, label
        )
    status_badge.short_description = '订单状态'
    status_badge.admin_order_field = 'status'


# 自定义 Admin Site 标题
admin.site.site_header = 'Layui Admin 演示系统'
admin.site.site_title = 'Layui Admin'
admin.site.index_title = '欢迎使用 Layui Admin'
