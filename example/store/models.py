# -*- coding: utf-8 -*-
"""
store/models.py - 商品管理示例模型
演示 django-layui 主题在普通 Django Admin 模型上的效果
"""
from django.db import models


class Category(models.Model):
    """商品分类"""
    name = models.CharField(max_length=50, unique=True, verbose_name='分类名称')
    description = models.CharField(max_length=200, blank=True, default='', verbose_name='描述')
    sort = models.IntegerField(default=0, verbose_name='排序')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'store_category'
        verbose_name = '商品分类'
        verbose_name_plural = verbose_name
        ordering = ['sort', 'id']

    def __str__(self):
        return self.name


class Product(models.Model):
    """商品"""
    STATUS_CHOICES = (
        (1, '上架'),
        (0, '下架'),
        (2, '售罄'),
    )
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='products', verbose_name='分类')
    name = models.CharField(max_length=100, verbose_name='商品名称')
    sku = models.CharField(max_length=50, unique=True, verbose_name='商品编码')
    description = models.TextField(blank=True, default='', verbose_name='商品描述')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='售价(元)')
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='成本价(元)')
    stock = models.IntegerField(default=0, verbose_name='库存')
    sales = models.IntegerField(default=0, verbose_name='销量')
    status = models.IntegerField(choices=STATUS_CHOICES, default=1, verbose_name='状态')
    is_featured = models.BooleanField(default=False, verbose_name='是否推荐')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'store_product'
        verbose_name = '商品'
        verbose_name_plural = verbose_name
        ordering = ['-create_time']

    def __str__(self):
        return self.name


class Order(models.Model):
    """订单"""
    STATUS_CHOICES = (
        ('pending', '待付款'),
        ('paid', '已付款'),
        ('shipped', '已发货'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
        ('refunded', '已退款'),
    )
    order_no = models.CharField(max_length=32, unique=True, verbose_name='订单号')
    customer_name = models.CharField(max_length=50, verbose_name='客户姓名')
    customer_phone = models.CharField(max_length=20, verbose_name='联系电话')
    shipping_address = models.CharField(max_length=300, verbose_name='收货地址')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='订单金额(元)')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='订单状态')
    remark = models.CharField(max_length=300, blank=True, default='', verbose_name='备注')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='下单时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'store_order'
        verbose_name = '订单'
        verbose_name_plural = verbose_name
        ordering = ['-create_time']

    def __str__(self):
        return self.order_no


class OrderItem(models.Model):
    """订单明细"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='订单')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, verbose_name='商品')
    product_name = models.CharField(max_length=100, verbose_name='商品名称')  # 快照
    product_sku = models.CharField(max_length=50, verbose_name='商品编码')     # 快照
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='单价')
    quantity = models.IntegerField(default=1, verbose_name='数量')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='小计')

    class Meta:
        db_table = 'store_order_item'
        verbose_name = '订单明细'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.order_id} - {self.product_name}'
