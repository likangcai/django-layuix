# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-26 22:19
# @FileName  : views_api.py
# -----------------------------
"""
store/views_api.py - 商品管理 REST API 视图
提供 Category / Product / Order 的 CRUD 接口
"""
import json
from decimal import Decimal
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import localtime
from django_layuix.rbac.views import api_login_required, get_request_body, success_response, error_response
from django_layuix.rbac.serializers import field_whitelisted
from .models import Category, Product, Order, OrderItem


def fmt_time(dt, format_str='%Y-%m-%d %H:%M:%S'):
    """将 timezone-aware datetime 转为当前时区后格式化"""
    if dt is None:
        return ''
    return localtime(dt).strftime(format_str)


# ============================================================
# 分类 API
# ============================================================

@csrf_exempt
@api_login_required
@field_whitelisted('store.Category')
def category_list(request):
    """GET /admin/api/store/categories/ - 分类列表"""
    queryset = Category.objects.all().order_by('sort', 'id')

    # 搜索
    keyword = request.GET.get('keyword', '').strip()
    if keyword:
        queryset = queryset.filter(
            Q(name__icontains=keyword) | Q(description__icontains=keyword)
        )

    total = queryset.count()

    # 分页
    try:
        page = int(request.GET.get('page', 1))
    except (ValueError, TypeError):
        page = 1
    try:
        page_size = int(request.GET.get('page_size', 10))
    except (ValueError, TypeError):
        page_size = 10
    page_size = max(1, min(page_size, 100))
    offset = (page - 1) * page_size
    items = queryset[offset:offset + page_size]

    data = []
    for cat in items:
        data.append({
            'id': cat.id,
            'name': cat.name,
            'description': cat.description,
            'sort': cat.sort,
            'product_count': cat.products.count(),
            'create_time': fmt_time(cat.create_time),
        })
    return success_response({'list': data, 'total': total})


@csrf_exempt
@api_login_required
def category_create(request):
    """POST /admin/api/store/categories/create/ - 创建分类"""
    if request.method != 'POST':
        return error_response('Method not allowed', 405)

    body = get_request_body(request)
    name = body.get('name', '').strip()
    if not name:
        return error_response('分类名称不能为空', 400)
    if Category.objects.filter(name=name).exists():
        return error_response('分类名称已存在', 400)

    cat = Category.objects.create(
        name=name,
        description=body.get('description', ''),
        sort=int(body.get('sort', 0)),
    )
    return success_response({'id': cat.id}, msg='创建成功')


@csrf_exempt
@api_login_required
@field_whitelisted('store.Category')
def category_detail(request, pk):
    """GET/PUT/DELETE /admin/api/store/categories/<pk>/ - 分类详情/更新/删除"""
    try:
        cat = Category.objects.get(pk=pk)
    except Category.DoesNotExist:
        return error_response('分类不存在', 404)

    if request.method == 'GET':
        data = {
            'id': cat.id,
            'name': cat.name,
            'description': cat.description,
            'sort': cat.sort,
            'product_count': cat.products.count(),
            'create_time': fmt_time(cat.create_time),
        }
        from django_layuix.rbac.serializers import serialize_instance

        return success_response(serialize_instance(data, request, 'store.Category'))

    elif request.method == 'PUT':
        body = get_request_body(request)
        if 'name' in body:
            new_name = body['name'].strip()
            if not new_name:
                return error_response('分类名称不能为空', 400)
            if Category.objects.filter(name=new_name).exclude(pk=pk).exists():
                return error_response('分类名称已存在', 400)
            cat.name = new_name
        if 'description' in body:
            cat.description = body.get('description', '')
        if 'sort' in body:
            try:
                cat.sort = int(body['sort'])
            except (ValueError, TypeError):
                pass
        cat.save()
        return success_response(msg='更新成功')

    elif request.method == 'DELETE':
        # 检查是否有商品关联
        if cat.products.exists():
            return error_response('该分类下存在商品，无法删除', 400)
        cat.delete()
        return success_response(msg='删除成功')

    return error_response('Method not allowed', 405)


# ============================================================
# 商品 API
# ============================================================

@csrf_exempt
@api_login_required
@field_whitelisted('store.Product')
def product_list(request):
    """GET /admin/api/store/products/ - 商品列表"""
    queryset = Product.objects.select_related('category').all().order_by('-create_time')

    # 搜索
    keyword = request.GET.get('keyword', '').strip()
    if keyword:
        queryset = queryset.filter(
            Q(name__icontains=keyword) |
            Q(sku__icontains=keyword) |
            Q(description__icontains=keyword)
        )

    # 分类过滤
    category_id = request.GET.get('category_id', '').strip()
    if category_id and category_id.isdigit():
        queryset = queryset.filter(category_id=int(category_id))

    # 状态过滤
    status = request.GET.get('status', '').strip()
    if status and status.isdigit():
        queryset = queryset.filter(status=int(status))

    total = queryset.count()

    # 分页
    try:
        page = int(request.GET.get('page', 1))
    except (ValueError, TypeError):
        page = 1
    try:
        page_size = int(request.GET.get('page_size', 10))
    except (ValueError, TypeError):
        page_size = 10
    page_size = max(1, min(page_size, 100))
    offset = (page - 1) * page_size
    items = queryset[offset:offset + page_size]

    status_labels = {1: '上架', 0: '下架', 2: '售罄'}
    data = []
    for p in items:
        data.append({
            'id': p.id,
            'name': p.name,
            'sku': p.sku,
            'category_id': p.category_id,
            'category_name': p.category.name if p.category else '',
            'description': p.description,
            'price': str(p.price),
            'cost_price': str(p.cost_price),
            'stock': p.stock,
            'sales': p.sales,
            'status': p.status,
            'status_label': status_labels.get(p.status, '未知'),
            'is_featured': p.is_featured,
            'create_time': fmt_time(p.create_time),
            'update_time': fmt_time(p.update_time),
        })
    return success_response({'list': data, 'total': total})


@csrf_exempt
@api_login_required
def product_create(request):
    """POST /admin/api/store/products/create/ - 创建商品"""
    if request.method != 'POST':
        return error_response('Method not allowed', 405)

    body = get_request_body(request)
    name = body.get('name', '').strip()
    sku = body.get('sku', '').strip()
    if not name:
        return error_response('商品名称不能为空', 400)
    if not sku:
        return error_response('商品编码不能为空', 400)
    if Product.objects.filter(sku=sku).exists():
        return error_response('商品编码已存在', 400)

    try:
        price = Decimal(str(body.get('price', 0)))
    except Exception:
        return error_response('售价格式不正确', 400)

    category_id = body.get('category_id')
    category = None
    if category_id:
        try:
            category = Category.objects.get(pk=int(category_id))
        except (Category.DoesNotExist, ValueError, TypeError):
            pass

    product = Product(
        name=name,
        sku=sku,
        category=category,
        description=body.get('description', ''),
        price=price,
        cost_price=Decimal(str(body.get('cost_price', 0))),
        stock=int(body.get('stock', 0)),
        status=int(body.get('status', 1)),
        is_featured=body.get('is_featured') in (True, 'true', 'on', 1, '1'),
    )
    product.save()
    return success_response({'id': product.id}, msg='创建成功')


@csrf_exempt
@api_login_required
@field_whitelisted('store.Product')
def product_detail(request, pk):
    """GET/PUT/DELETE /admin/api/store/products/<pk>/ - 商品详情/更新/删除"""
    try:
        product = Product.objects.select_related('category').get(pk=pk)
    except Product.DoesNotExist:
        return error_response('商品不存在', 404)

    if request.method == 'GET':
        status_labels = {1: '上架', 0: '下架', 2: '售罄'}
        data = {
            'id': product.id,
            'name': product.name,
            'sku': product.sku,
            'category_id': product.category_id,
            'category_name': product.category.name if product.category else '',
            'description': product.description,
            'price': str(product.price),
            'cost_price': str(product.cost_price),
            'stock': product.stock,
            'sales': product.sales,
            'status': product.status,
            'status_label': status_labels.get(product.status, '未知'),
            'is_featured': product.is_featured,
            'create_time': fmt_time(product.create_time),
            'update_time': fmt_time(product.update_time),
        }
        return success_response(data)

    elif request.method == 'PUT':
        body = get_request_body(request)
        if 'name' in body:
            name = body['name'].strip()
            if not name:
                return error_response('商品名称不能为空', 400)
            product.name = name
        if 'sku' in body:
            sku = body['sku'].strip()
            if not sku:
                return error_response('商品编码不能为空', 400)
            if Product.objects.filter(sku=sku).exclude(pk=pk).exists():
                return error_response('商品编码已存在', 400)
            product.sku = sku
        if 'category_id' in body:
            try:
                cat = Category.objects.get(pk=int(body['category_id']))
                product.category = cat
            except (Category.DoesNotExist, ValueError, TypeError):
                product.category = None
        if 'description' in body:
            product.description = body.get('description', '')
        if 'price' in body:
            try:
                product.price = Decimal(str(body['price']))
            except Exception:
                return error_response('售价格式不正确', 400)
        if 'cost_price' in body:
            try:
                product.cost_price = Decimal(str(body['cost_price']))
            except Exception:
                return error_response('成本价格式不正确', 400)
        if 'stock' in body:
            try:
                product.stock = int(body['stock'])
            except (ValueError, TypeError):
                pass
        if 'status' in body:
            try:
                product.status = int(body['status'])
            except (ValueError, TypeError):
                pass
        if 'is_featured' in body:
            product.is_featured = body['is_featured'] in (True, 'true', 'on', 1, '1')
        product.save()
        return success_response(msg='更新成功')

    elif request.method == 'DELETE':
        product.delete()
        return success_response(msg='删除成功')

    return error_response('Method not allowed', 405)


# ============================================================
# 订单 API
# ============================================================

STATUS_LABELS = {
    'pending': '待付款', 'paid': '已付款', 'shipped': '已发货',
    'completed': '已完成', 'cancelled': '已取消', 'refunded': '已退款',
}


@csrf_exempt
@api_login_required
@field_whitelisted('store.Order')
def order_list(request):
    """GET /admin/api/store/orders/ - 订单列表"""
    queryset = Order.objects.all().order_by('-create_time')

    keyword = request.GET.get('keyword', '').strip()
    if keyword:
        queryset = queryset.filter(
            Q(order_no__icontains=keyword) |
            Q(customer_name__icontains=keyword) |
            Q(customer_phone__icontains=keyword)
        )

    status = request.GET.get('status', '').strip()
    if status:
        queryset = queryset.filter(status=status)

    total = queryset.count()

    try:
        page = int(request.GET.get('page', 1))
    except (ValueError, TypeError):
        page = 1
    try:
        page_size = int(request.GET.get('page_size', 10))
    except (ValueError, TypeError):
        page_size = 10
    page_size = max(1, min(page_size, 100))
    offset = (page - 1) * page_size
    items = queryset[offset:offset + page_size]

    data = []
    for o in items:
        items_list = []
        for item in o.items.all():
            items_list.append({
                'id': item.id,
                'product_name': item.product_name,
                'product_sku': item.product_sku,
                'unit_price': str(item.unit_price),
                'quantity': item.quantity,
                'subtotal': str(item.subtotal),
            })
        data.append({
            'id': o.id,
            'order_no': o.order_no,
            'customer_name': o.customer_name,
            'customer_phone': o.customer_phone,
            'shipping_address': o.shipping_address,
            'total_amount': str(o.total_amount),
            'status': o.status,
            'status_label': STATUS_LABELS.get(o.status, '未知'),
            'remark': o.remark,
            'items': items_list,
            'create_time': fmt_time(o.create_time),
            'update_time': fmt_time(o.update_time),
        })
    return success_response({'list': data, 'total': total})


@csrf_exempt
@api_login_required
def order_create(request):
    """POST /admin/api/store/orders/create/ - 创建订单"""
    if request.method != 'POST':
        return error_response('Method not allowed', 405)

    body = get_request_body(request)
    customer_name = body.get('customer_name', '').strip()
    customer_phone = body.get('customer_phone', '').strip()
    shipping_address = body.get('shipping_address', '').strip()
    if not customer_name:
        return error_response('客户姓名不能为空', 400)
    if not customer_phone:
        return error_response('联系电话不能为空', 400)

    # 生成订单号
    from datetime import datetime
    import random
    order_no = f'ORD{datetime.now().strftime("%Y%m%d%H%M%S")}{random.randint(10, 99)}'

    try:
        total_amount = Decimal(str(body.get('total_amount', 0)))
    except Exception:
        total_amount = Decimal('0')

    order = Order.objects.create(
        order_no=order_no,
        customer_name=customer_name,
        customer_phone=customer_phone,
        shipping_address=shipping_address,
        total_amount=total_amount,
        status=body.get('status', 'pending'),
        remark=body.get('remark', ''),
    )

    # 处理订单明细
    items_data = body.get('items', [])
    if isinstance(items_data, str):
        try:
            items_data = json.loads(items_data)
        except (json.JSONDecodeError, TypeError):
            items_data = []

    for item_data in items_data:
        product_id = item_data.get('product_id')
        product = None
        if product_id:
            try:
                product = Product.objects.get(pk=int(product_id))
            except (Product.DoesNotExist, ValueError, TypeError):
                pass

        qty = int(item_data.get('quantity', 1))
        unit_price = Decimal(str(item_data.get('unit_price', 0)))
        subtotal = unit_price * qty

        OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name if product else (item_data.get('product_name', '')),
            product_sku=product.sku if product else (item_data.get('product_sku', '')),
            unit_price=unit_price,
            quantity=qty,
            subtotal=subtotal,
        )

    return success_response({'id': order.id, 'order_no': order.order_no}, msg='创建成功')


@csrf_exempt
@api_login_required
@field_whitelisted('store.Order')
def order_detail(request, pk):
    """GET/PUT/DELETE /admin/api/store/orders/<pk>/ - 订单详情/更新/删除"""
    try:
        order = Order.objects.prefetch_related('items').get(pk=pk)
    except Order.DoesNotExist:
        return error_response('订单不存在', 404)

    if request.method == 'GET':
        items_list = []
        for item in order.items.all():
            items_list.append({
                'id': item.id,
                'product_id': item.product_id,
                'product_name': item.product_name,
                'product_sku': item.product_sku,
                'unit_price': str(item.unit_price),
                'quantity': item.quantity,
                'subtotal': str(item.subtotal),
            })
        data = {
            'id': order.id,
            'order_no': order.order_no,
            'customer_name': order.customer_name,
            'customer_phone': order.customer_phone,
            'shipping_address': order.shipping_address,
            'total_amount': str(order.total_amount),
            'status': order.status,
            'status_label': STATUS_LABELS.get(order.status, '未知'),
            'remark': order.remark,
            'items': items_list,
            'create_time': fmt_time(order.create_time),
            'update_time': fmt_time(order.update_time),
        }
        return success_response(data)

    elif request.method == 'PUT':
        body = get_request_body(request)
        if 'customer_name' in body:
            order.customer_name = body['customer_name'].strip()
        if 'customer_phone' in body:
            order.customer_phone = body['customer_phone'].strip()
        if 'shipping_address' in body:
            order.shipping_address = body['shipping_address'].strip()
        if 'status' in body:
            order.status = body['status']
        if 'remark' in body:
            order.remark = body.get('remark', '')
        if 'total_amount' in body:
            try:
                order.total_amount = Decimal(str(body['total_amount']))
            except Exception:
                pass
        order.save()
        return success_response(msg='更新成功')

    elif request.method == 'DELETE':
        order.delete()
        return success_response(msg='删除成功')

    return error_response('Method not allowed', 405)


# ============================================================
# Products list for select (无分页，用于新建订单时选择商品)
# ============================================================

@csrf_exempt
@api_login_required
def product_select_list(request):
    """GET /admin/api/store/products/select/ - 商品下拉选择列表"""
    products = Product.objects.filter(status=1).order_by('name')
    data = [{
        'id': p.id,
        'name': p.name,
        'sku': p.sku,
        'price': str(p.price),
        'stock': p.stock,
    } for p in products]
    return success_response(data)
