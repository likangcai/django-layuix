# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-26 22:19
# @FileName  : init_demo_data.py
# -----------------------------
"""
初始化演示数据
用法: python manage.py init_demo_data
"""
import random
import uuid
from decimal import Decimal
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from store.models import Category, Product, Order, OrderItem


class Command(BaseCommand):
    help = '初始化商品管理演示数据（分类/商品/订单）'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('初始化演示数据...'))

        self._create_categories()
        self._create_products()
        self._create_orders()

        self.stdout.write(self.style.SUCCESS('\n[OK] 演示数据初始化完成！'))
        self.stdout.write('')
        self.stdout.write(f'  分类: {Category.objects.count()} 条')
        self.stdout.write(f'  商品: {Product.objects.count()} 条')
        self.stdout.write(f'  订单: {Order.objects.count()} 条')

    def _create_categories(self):
        self.stdout.write('  创建商品分类...')
        cats = [
            ('手机数码', 1),
            ('电脑办公', 2),
            ('家用电器', 3),
            ('运动户外', 4),
            ('食品生鲜', 5),
            ('服装鞋帽', 6),
        ]
        for name, sort in cats:
            Category.objects.get_or_create(name=name, defaults={'sort': sort})

    def _create_products(self):
        self.stdout.write('  创建商品数据...')
        if Product.objects.count() >= 20:
            self.stdout.write('  商品已存在，跳过')
            return

        categories = {c.name: c for c in Category.objects.all()}

        products = [
            # 手机数码
            ('iPhone 16 Pro Max 512G', 'IP16PROMAX512', categories.get('手机数码'), 9999, 7500, 50, 1),
            ('小米 15 Ultra 16+512G', 'MI15U512', categories.get('手机数码'), 5999, 4200, 120, 1),
            ('华为 Mate 70 Pro 256G', 'HW70PRO256', categories.get('手机数码'), 6999, 5100, 80, 1),
            ('iPad Pro 11寸 M4 256G', 'IPADPROM4256', categories.get('手机数码'), 7499, 5600, 30, 1),
            ('AirPods Pro 2代', 'AIRPODSPRO2', categories.get('手机数码'), 1799, 1100, 200, 1),
            # 电脑办公
            ('MacBook Pro 14寸 M4', 'MBP14M4', categories.get('电脑办公'), 14999, 11000, 25, 1),
            ('联想 ThinkPad X1 Carbon', 'X1C2024', categories.get('电脑办公'), 9888, 7200, 40, 1),
            ('戴尔 U2724D 显示器', 'DELLU2724D', categories.get('电脑办公'), 3299, 2300, 60, 0),
            ('罗技 MX Master 3S 鼠标', 'LGTIMXM3S', categories.get('电脑办公'), 699, 380, 300, 1),
            # 家用电器
            ('格力 KFR-35 空调套机', 'GRIYKFR35', categories.get('家用电器'), 3599, 2500, 45, 1),
            ('美的 BCD-215 冰箱', 'MDBCD215', categories.get('家用电器'), 2199, 1500, 30, 2),
            ('戴森 V15s Detect 吸尘器', 'DYSONV15S', categories.get('家用电器'), 5490, 3900, 15, 1),
            # 运动户外
            ('耐克 Air Max 270 跑鞋 42码', 'NIKEAM27042', categories.get('运动户外'), 999, 550, 100, 1),
            ('迪卡侬 登山包 45L', 'DKL45L', categories.get('运动户外'), 299, 160, 200, 1),
            # 食品生鲜
            ('新疆阿克苏苹果 5斤装', 'AKS5', categories.get('食品生鲜'), 59, 30, 500, 1),
            ('进口帝王蟹 3-4斤/只', 'DIWANGXIE', categories.get('食品生鲜'), 688, 380, 20, 2),
            # 服装鞋帽
            ('优衣库男款羽绒服 XL', 'UQRDN XL', categories.get('服装鞋帽'), 799, 420, 80, 1),
            ('李宁韦德之道7 篮球鞋 42', 'LNWD7-42', categories.get('服装鞋帽'), 899, 500, 60, 1),
        ]

        for i, (name, sku, category, price, cost, stock, status) in enumerate(products):
            Product.objects.get_or_create(
                sku=sku,
                defaults={
                    'name': name,
                    'category': category,
                    'price': Decimal(str(price)),
                    'cost_price': Decimal(str(cost)),
                    'stock': stock,
                    'sales': random.randint(5, 500),
                    'status': status,
                    'is_featured': i % 3 == 0,
                    'description': f'{name} - 高品质精选商品，品质保证',
                }
            )

    def _create_orders(self):
        self.stdout.write('  创建订单数据...')
        if Order.objects.count() >= 15:
            self.stdout.write('  订单已存在，跳过')
            return

        products = list(Product.objects.filter(status=1))
        if not products:
            return

        customers = [
            ('张伟', '13800001001', '北京市朝阳区建国路88号'),
            ('李娜', '13900002002', '上海市浦东新区张江高科技园区'),
            ('王磊', '15600003003', '广东省广州市天河区珠江新城'),
            ('刘洋', '13700004004', '浙江省杭州市西湖区文三路'),
            ('陈婷', '18800005005', '四川省成都市高新区天府大道'),
            ('赵强', '13600006006', '湖北省武汉市武昌区珞珈山路'),
            ('孙丽', '15200007007', '江苏省南京市鼓楼区汉中路'),
            ('周鑫', '17700008008', '陕西省西安市雁塔区科技路'),
        ]

        statuses = ['pending', 'paid', 'paid', 'shipped', 'shipped', 'completed',
                    'completed', 'completed', 'cancelled', 'refunded']

        for i in range(20):
            name, phone, addr = random.choice(customers)
            status = statuses[i % len(statuses)]
            order_no = f'ORD{datetime.now().strftime("%Y%m%d")}{str(i+1).zfill(4)}{random.randint(10,99)}'

            # 随机选 1-3 个商品
            order_products = random.sample(products, min(random.randint(1, 3), len(products)))
            total = Decimal('0')
            items_data = []
            for p in order_products:
                qty = random.randint(1, 3)
                subtotal = p.price * qty
                total += subtotal
                items_data.append((p, qty, subtotal))

            order, created = Order.objects.get_or_create(
                order_no=order_no,
                defaults={
                    'customer_name': name,
                    'customer_phone': phone,
                    'shipping_address': addr,
                    'total_amount': total,
                    'status': status,
                    'remark': '' if i % 3 != 0 else '请尽快发货',
                }
            )
            if created:
                for p, qty, subtotal in items_data:
                    OrderItem.objects.create(
                        order=order,
                        product=p,
                        product_name=p.name,
                        product_sku=p.sku,
                        unit_price=p.price,
                        quantity=qty,
                        subtotal=subtotal,
                    )
