# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-26 22:19
# @FileName  : data_admin_views.py
# -----------------------------
"""Department, position, region and member-level management APIs."""
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt

from .models import Department, MemberLevel, Position, Region
from .permissions import api_login_required, api_permission_required, has_permission
from .serializers import field_whitelisted
from .views import error_response, fmt_time, get_request_body, success_response


def _as_bool(value, default=False):
    if value is None or value == '':
        return default
    if isinstance(value, bool):
        return value
    return str(value).lower() in ('1', 'true', 'yes', 'on', 'active')


def _int_value(value, default=0, minimum=None, maximum=None):
    try:
        result = int(value if value not in (None, '') else default)
    except (TypeError, ValueError):
        raise ValueError('必须是整数')
    if minimum is not None and result < minimum:
        raise ValueError('不能小于 %s' % minimum)
    if maximum is not None and result > maximum:
        raise ValueError('不能大于 %s' % maximum)
    return result


def _parent_for(model, instance, parent_id):
    if parent_id in (None, ''):
        return None
    try:
        parent = model.objects.select_related('parent').get(pk=int(parent_id))
    except (TypeError, ValueError, model.DoesNotExist):
        raise ValueError('上级记录不存在')
    cursor = parent
    while cursor is not None:
        if instance is not None and cursor.pk == instance.pk:
            raise ValueError('上级不能是自身或其子级')
        cursor = cursor.parent
    return parent


def _department_payload(obj):
    return {
        'id': obj.pk,
        'name': obj.name,
        'code': obj.code,
        'type': obj.type,
        'type_display': obj.get_type_display(),
        'parent_id': obj.parent_id,
        'parent_name': obj.parent.name if obj.parent_id else '',
        'leader': obj.leader,
        'phone': obj.phone,
        'email': obj.email,
        'sort': obj.sort,
        'status': obj.status,
        'note': obj.note,
        'create_time': fmt_time(obj.create_time),
        'update_time': fmt_time(obj.update_time),
    }


def _position_payload(obj):
    return {
        'id': obj.pk,
        'name': obj.name,
        'code': obj.code,
        'sort': obj.sort,
        'status': obj.status,
        'note': obj.note,
        'create_time': fmt_time(obj.create_time),
        'update_time': fmt_time(obj.update_time),
    }


def _region_payload(obj):
    return {
        'id': obj.pk,
        'name': obj.name,
        'code': obj.code,
        'area_code': obj.area_code,
        'zip_code': obj.zip_code,
        'pinyin': obj.pinyin,
        'level': obj.level,
        'level_display': obj.get_level_display(),
        'parent_id': obj.parent_id,
        'parent_name': obj.parent.name if obj.parent_id else '',
        'sort': obj.sort,
        'status': obj.status,
        'note': obj.note,
        'create_time': fmt_time(obj.create_time),
        'update_time': fmt_time(obj.update_time),
    }


def _member_level_payload(obj):
    return {
        'id': obj.pk,
        'name': obj.name,
        'code': obj.code,
        'min_points': obj.min_points,
        'discount': float(obj.discount or 0),
        'icon': obj.icon,
        'sort': obj.sort,
        'status': obj.status,
        'description': obj.description,
        'create_time': fmt_time(obj.create_time),
        'update_time': fmt_time(obj.update_time),
    }


# ==================== 部门 ====================

@csrf_exempt
@api_login_required
@api_permission_required('dept:view')
@field_whitelisted('rbac.Department')
def department_list(request):
    """GET /api/rbac/departments/ - list departments."""
    queryset = Department.objects.select_related('parent')
    keyword = str(request.GET.get('keyword') or '').strip()
    if keyword:
        queryset = queryset.filter(
            Q(name__icontains=keyword) | Q(code__icontains=keyword)
            | Q(leader__icontains=keyword)
        )
    status = request.GET.get('status')
    if status not in (None, ''):
        queryset = queryset.filter(status=_as_bool(status))
    rows = [_department_payload(row) for row in queryset.order_by('sort', 'id')]
    return success_response({'list': rows, 'total': len(rows)})


@csrf_exempt
@api_login_required
@api_permission_required('dept:add')
def department_create(request):
    """POST /api/rbac/departments/create/."""
    if request.method != 'POST':
        return error_response('Method not allowed', 405)
    body = get_request_body(request)
    name = str(body.get('name') or '').strip()
    code = str(body.get('code') or '').strip()
    if not name or not code:
        return error_response('部门名称和编码不能为空', 400)
    try:
        department_type = _int_value(body.get('type'), 3, 1, 4)
        sort = _int_value(body.get('sort'), 0, 0, 999999)
        parent = _parent_for(Department, None, body.get('parent_id'))
        email = str(body.get('email') or '').strip()
        if email:
            validate_email(email)
        with transaction.atomic():
            obj = Department.objects.create(
                name=name[:150], code=code[:64], type=department_type,
                parent=parent, leader=str(body.get('leader') or '')[:50],
                phone=str(body.get('phone') or '')[:30], email=email,
                sort=sort, status=_as_bool(body.get('status'), True),
                note=str(body.get('note') or '')[:255],
            )
    except ValidationError:
        return error_response('邮箱格式不正确', 400)
    except ValueError as exc:
        return error_response(str(exc), 400)
    except IntegrityError:
        return error_response('部门编码已存在', 400)
    return success_response({'id': obj.pk}, msg='创建成功')


@csrf_exempt
@api_login_required
@api_permission_required('dept:view')
@field_whitelisted('rbac.Department')
def department_detail(request, pk):
    """GET/PUT/DELETE /api/rbac/departments/<id>/."""
    try:
        obj = Department.objects.select_related('parent').get(pk=pk)
    except Department.DoesNotExist:
        return error_response('部门不存在', 404)

    if request.method == 'GET':
        return success_response(_department_payload(obj))

    if request.method == 'PUT':
        if not has_permission(request.user, 'dept:edit', request):
            return error_response('无权限', 403)
        body = get_request_body(request)
        name = str(body.get('name') or obj.name).strip()
        code = str(body.get('code') or obj.code).strip()
        if not name or not code:
            return error_response('部门名称和编码不能为空', 400)
        try:
            parent = _parent_for(
                Department, obj, body.get('parent_id') if 'parent_id' in body else obj.parent_id
            )
            department_type = _int_value(
                body.get('type') if 'type' in body else obj.type, obj.type, 1, 4
            )
            sort = _int_value(
                body.get('sort') if 'sort' in body else obj.sort, obj.sort, 0, 999999
            )
            email = str(body.get('email') if 'email' in body else obj.email).strip()
            if email:
                validate_email(email)
            with transaction.atomic():
                obj.name = name[:150]
                obj.code = code[:64]
                obj.type = department_type
                obj.parent = parent
                obj.leader = str(body.get('leader') if 'leader' in body else obj.leader)[:50]
                obj.phone = str(body.get('phone') if 'phone' in body else obj.phone)[:30]
                obj.email = email
                obj.sort = sort
                obj.status = _as_bool(
                    body.get('status') if 'status' in body else obj.status, obj.status
                )
                obj.note = str(body.get('note') if 'note' in body else obj.note)[:255]
                obj.save()
        except ValidationError:
            return error_response('邮箱格式不正确', 400)
        except ValueError as exc:
            return error_response(str(exc), 400)
        except IntegrityError:
            return error_response('部门编码已存在', 400)
        return success_response(msg='更新成功')

    if request.method == 'DELETE':
        if not has_permission(request.user, 'dept:delete', request):
            return error_response('无权限', 403)
        if obj.children.exists():
            return error_response('请先删除下级部门', 400)
        obj.delete()
        return success_response(msg='删除成功')

    return error_response('Method not allowed', 405)


# ==================== 岗位 ====================

@csrf_exempt
@api_login_required
@api_permission_required('position:view')
@field_whitelisted('rbac.Position')
def position_list(request):
    """GET /api/rbac/positions/ - list positions."""
    queryset = Position.objects.all()
    keyword = str(request.GET.get('keyword') or '').strip()
    if keyword:
        queryset = queryset.filter(
            Q(name__icontains=keyword) | Q(code__icontains=keyword)
        )
    status = request.GET.get('status')
    if status not in (None, ''):
        queryset = queryset.filter(status=_as_bool(status))
    rows = [_position_payload(row) for row in queryset.order_by('sort', 'id')]
    return success_response({'list': rows, 'total': len(rows)})


@csrf_exempt
@api_login_required
@api_permission_required('position:add')
def position_create(request):
    """POST /api/rbac/positions/create/."""
    if request.method != 'POST':
        return error_response('Method not allowed', 405)
    body = get_request_body(request)
    name = str(body.get('name') or '').strip()
    code = str(body.get('code') or '').strip()
    if not name or not code:
        return error_response('岗位名称和编码不能为空', 400)
    try:
        sort = _int_value(body.get('sort'), 0, 0, 999999)
        with transaction.atomic():
            obj = Position.objects.create(
                name=name[:150], code=code[:64], sort=sort,
                status=_as_bool(body.get('status'), True),
                note=str(body.get('note') or '')[:255],
            )
    except ValueError as exc:
        return error_response(str(exc), 400)
    except IntegrityError:
        return error_response('岗位编码已存在', 400)
    return success_response({'id': obj.pk}, msg='创建成功')


@csrf_exempt
@api_login_required
@api_permission_required('position:view')
@field_whitelisted('rbac.Position')
def position_detail(request, pk):
    """GET/PUT/DELETE /api/rbac/positions/<id>/."""
    try:
        obj = Position.objects.get(pk=pk)
    except Position.DoesNotExist:
        return error_response('岗位不存在', 404)

    if request.method == 'GET':
        return success_response(_position_payload(obj))

    if request.method == 'PUT':
        if not has_permission(request.user, 'position:edit', request):
            return error_response('无权限', 403)
        body = get_request_body(request)
        name = str(body.get('name') or obj.name).strip()
        code = str(body.get('code') or obj.code).strip()
        if not name or not code:
            return error_response('岗位名称和编码不能为空', 400)
        try:
            obj.name = name[:150]
            obj.code = code[:64]
            obj.sort = _int_value(
                body.get('sort') if 'sort' in body else obj.sort, obj.sort, 0, 999999
            )
            obj.status = _as_bool(
                body.get('status') if 'status' in body else obj.status, obj.status
            )
            obj.note = str(body.get('note') if 'note' in body else obj.note)[:255]
            obj.save()
        except ValueError as exc:
            return error_response(str(exc), 400)
        except IntegrityError:
            return error_response('岗位编码已存在', 400)
        return success_response(msg='更新成功')

    if request.method == 'DELETE':
        if not has_permission(request.user, 'position:delete', request):
            return error_response('无权限', 403)
        obj.delete()
        return success_response(msg='删除成功')

    return error_response('Method not allowed', 405)


# ==================== 地区 ====================

@csrf_exempt
@api_login_required
@api_permission_required('region:view')
def region_list(request):
    """GET /api/rbac/regions/ - list regions.

    ``_region_payload`` is the explicit response whitelist for this large
    collection; applying the generic decorator would serialize 40k+ rows twice.
    ``page`` enables server-side paging; omitting it keeps the legacy full-list
    response for exports and existing integrations.
    """
    queryset = Region.objects.select_related('parent')
    keyword = str(request.GET.get('keyword') or '').strip()
    if keyword:
        queryset = queryset.filter(
            Q(name__icontains=keyword) | Q(code__icontains=keyword)
            | Q(pinyin__icontains=keyword)
        )
    status = request.GET.get('status')
    if status not in (None, ''):
        queryset = queryset.filter(status=_as_bool(status))
    max_level = request.GET.get('max_level')
    if max_level not in (None, ''):
        try:
            queryset = queryset.filter(level__lte=int(max_level))
        except (TypeError, ValueError):
            return error_response('max_level 必须是整数', 400)
    level = request.GET.get('level')
    if level not in (None, ''):
        try:
            queryset = queryset.filter(level=int(level))
        except (TypeError, ValueError):
            return error_response('level 必须是整数', 400)

    node_id = request.GET.get('node_id')
    if node_id not in (None, ''):
        try:
            node = Region.objects.get(pk=int(node_id))
        except (TypeError, ValueError, Region.DoesNotExist):
            return error_response('地区节点不存在', 400)
        prefix_len = {1: 2, 2: 4, 3: 6, 4: 9}.get(node.level, len(node.code))
        queryset = queryset.filter(code__startswith=node.code[:prefix_len])

    queryset = queryset.order_by('sort', 'id')
    page = request.GET.get('page')
    if page in (None, ''):
        rows = [_region_payload(row) for row in queryset]
        return success_response({'list': rows, 'total': len(rows)})

    try:
        page = max(1, int(page))
        page_size = min(200, max(10, int(request.GET.get('page_size') or 20)))
    except (TypeError, ValueError):
        return error_response('分页参数必须是整数', 400)
    total = queryset.count()
    start = (page - 1) * page_size
    rows = [_region_payload(row) for row in queryset[start:start + page_size]]
    return success_response({
        'list': rows, 'total': total, 'page': page, 'page_size': page_size,
    })


@csrf_exempt
@api_login_required
@api_permission_required('region:view')
def region_tree(request):
    """GET /api/rbac/regions/tree/ - province/city plus municipality districts."""
    provinces = list(Region.objects.filter(level=1).order_by('sort', 'id'))
    province_ids = [row.pk for row in provinces]
    cities = list(Region.objects.filter(
        level=2, parent_id__in=province_ids
    ).order_by('sort', 'id'))
    city_ids = [row.pk for row in cities]
    municipality_districts = list(Region.objects.filter(
        level=3, parent_id__in=province_ids
    ).order_by('sort', 'id'))
    district_parent_ids = {row.parent_id for row in municipality_districts}

    children = {province.pk: [] for province in provinces}
    for city in cities:
        children.setdefault(city.parent_id, []).append(city)
    for district in municipality_districts:
        children.setdefault(district.parent_id, []).append(district)

    def node(row):
        return {
            'id': row.pk, 'name': row.name, 'code': row.code,
            'level': row.level, 'status': row.status,
            'children': [node(child) for child in children.get(row.pk, [])],
        }

    roots = [
        node(province) for province in provinces
        if children.get(province.pk) or province.pk not in district_parent_ids
    ]
    return success_response({
        'list': roots,
        'total': len(provinces) + len(cities) + len(municipality_districts),
        'city_count': len(city_ids),
    })


@csrf_exempt
@api_login_required
@api_permission_required('region:add')
def region_create(request):
    """POST /api/rbac/regions/create/."""
    if request.method != 'POST':
        return error_response('Method not allowed', 405)
    body = get_request_body(request)
    name = str(body.get('name') or '').strip()
    code = str(body.get('code') or '').strip()
    if not name or not code:
        return error_response('地区名称和行政编码不能为空', 400)
    try:
        level = _int_value(body.get('level'), 1, 1, 5)
        sort = _int_value(body.get('sort'), 0, 0, 999999)
        parent = _parent_for(Region, None, body.get('parent_id'))
        with transaction.atomic():
            obj = Region.objects.create(
                name=name[:150], code=code[:20], area_code=str(body.get('area_code') or '')[:20],
                zip_code=str(body.get('zip_code') or '')[:20],
                pinyin=str(body.get('pinyin') or '')[:150], level=level, parent=parent,
                sort=sort, status=_as_bool(body.get('status'), True),
                note=str(body.get('note') or '')[:255],
            )
    except ValueError as exc:
        return error_response(str(exc), 400)
    except IntegrityError:
        return error_response('行政编码已存在', 400)
    return success_response({'id': obj.pk}, msg='创建成功')


@csrf_exempt
@api_login_required
@api_permission_required('region:view')
@field_whitelisted('rbac.Region')
def region_detail(request, pk):
    """GET/PUT/DELETE /api/rbac/regions/<id>/."""
    try:
        obj = Region.objects.select_related('parent').get(pk=pk)
    except Region.DoesNotExist:
        return error_response('地区不存在', 404)

    if request.method == 'GET':
        return success_response(_region_payload(obj))

    if request.method == 'PUT':
        if not has_permission(request.user, 'region:edit', request):
            return error_response('无权限', 403)
        body = get_request_body(request)
        name = str(body.get('name') or obj.name).strip()
        code = str(body.get('code') or obj.code).strip()
        if not name or not code:
            return error_response('地区名称和行政编码不能为空', 400)
        try:
            parent = _parent_for(
                Region, obj, body.get('parent_id') if 'parent_id' in body else obj.parent_id
            )
            obj.name = name[:150]
            obj.code = code[:20]
            obj.area_code = str(body.get('area_code') if 'area_code' in body else obj.area_code)[:20]
            obj.zip_code = str(body.get('zip_code') if 'zip_code' in body else obj.zip_code)[:20]
            obj.pinyin = str(body.get('pinyin') if 'pinyin' in body else obj.pinyin)[:150]
            obj.level = _int_value(
                body.get('level') if 'level' in body else obj.level, obj.level, 1, 5
            )
            obj.parent = parent
            obj.sort = _int_value(
                body.get('sort') if 'sort' in body else obj.sort, obj.sort, 0, 999999
            )
            obj.status = _as_bool(
                body.get('status') if 'status' in body else obj.status, obj.status
            )
            obj.note = str(body.get('note') if 'note' in body else obj.note)[:255]
            obj.save()
        except ValueError as exc:
            return error_response(str(exc), 400)
        except IntegrityError:
            return error_response('行政编码已存在', 400)
        return success_response(msg='更新成功')

    if request.method == 'DELETE':
        if not has_permission(request.user, 'region:delete', request):
            return error_response('无权限', 403)
        if obj.children.exists():
            return error_response('请先删除下级地区', 400)
        obj.delete()
        return success_response(msg='删除成功')

    return error_response('Method not allowed', 405)


# ==================== 会员等级 ====================

@csrf_exempt
@api_login_required
@api_permission_required('member_level:view')
@field_whitelisted('rbac.MemberLevel')
def member_level_list(request):
    """GET /api/rbac/member-levels/ - list member levels."""
    queryset = MemberLevel.objects.all()
    keyword = str(request.GET.get('keyword') or '').strip()
    if keyword:
        queryset = queryset.filter(
            Q(name__icontains=keyword) | Q(code__icontains=keyword)
        )
    status = request.GET.get('status')
    if status not in (None, ''):
        queryset = queryset.filter(status=_as_bool(status))
    rows = [_member_level_payload(row) for row in queryset.order_by('sort', 'id')]
    return success_response({'list': rows, 'total': len(rows)})


@csrf_exempt
@api_login_required
@api_permission_required('member_level:add')
def member_level_create(request):
    """POST /api/rbac/member-levels/create/."""
    if request.method != 'POST':
        return error_response('Method not allowed', 405)
    body = get_request_body(request)
    name = str(body.get('name') or '').strip()
    code = str(body.get('code') or '').strip()
    if not name or not code:
        return error_response('等级名称和编码不能为空', 400)
    try:
        min_points = _int_value(body.get('min_points'), 0, 0, 999999999)
        sort = _int_value(body.get('sort'), 0, 0, 999999)
        discount = Decimal(str(body.get('discount', 100) or 100))
        if discount < 0 or discount > 100:
            raise ValueError('折扣比例必须在 0 到 100 之间')
        with transaction.atomic():
            obj = MemberLevel.objects.create(
                name=name[:150], code=code[:64], min_points=min_points,
                discount=discount, icon=str(body.get('icon') or '')[:50],
                sort=sort, status=_as_bool(body.get('status'), True),
                description=str(body.get('description') or '')[:255],
            )
    except (ValueError, InvalidOperation) as exc:
        return error_response(str(exc), 400)
    except IntegrityError:
        return error_response('等级编码已存在', 400)
    return success_response({'id': obj.pk}, msg='创建成功')


@csrf_exempt
@api_login_required
@api_permission_required('member_level:view')
@field_whitelisted('rbac.MemberLevel')
def member_level_detail(request, pk):
    """GET/PUT/DELETE /api/rbac/member-levels/<id>/."""
    try:
        obj = MemberLevel.objects.get(pk=pk)
    except MemberLevel.DoesNotExist:
        return error_response('会员等级不存在', 404)

    if request.method == 'GET':
        return success_response(_member_level_payload(obj))

    if request.method == 'PUT':
        if not has_permission(request.user, 'member_level:edit', request):
            return error_response('无权限', 403)
        body = get_request_body(request)
        name = str(body.get('name') or obj.name).strip()
        code = str(body.get('code') or obj.code).strip()
        if not name or not code:
            return error_response('等级名称和编码不能为空', 400)
        try:
            discount = Decimal(str(
                body.get('discount') if 'discount' in body else obj.discount
            ))
            if discount < 0 or discount > 100:
                raise ValueError('折扣比例必须在 0 到 100 之间')
            obj.name = name[:150]
            obj.code = code[:64]
            obj.min_points = _int_value(
                body.get('min_points') if 'min_points' in body else obj.min_points,
                obj.min_points, 0, 999999999,
            )
            obj.discount = discount
            obj.icon = str(body.get('icon') if 'icon' in body else obj.icon)[:50]
            obj.sort = _int_value(
                body.get('sort') if 'sort' in body else obj.sort, obj.sort, 0, 999999
            )
            obj.status = _as_bool(
                body.get('status') if 'status' in body else obj.status, obj.status
            )
            obj.description = str(
                body.get('description') if 'description' in body else obj.description
            )[:255]
            obj.save()
        except (ValueError, InvalidOperation) as exc:
            return error_response(str(exc), 400)
        except IntegrityError:
            return error_response('等级编码已存在', 400)
        return success_response(msg='更新成功')

    if request.method == 'DELETE':
        if not has_permission(request.user, 'member_level:delete', request):
            return error_response('无权限', 403)
        obj.delete()
        return success_response(msg='删除成功')

    return error_response('Method not allowed', 405)


# ==================== 导入 / 导出 / 批量操作 ====================

DATA_RESOURCES = {
    'departments': {
        'model': Department,
        'label': 'departments',
        'add_permission': 'dept:add',
        'edit_permission': 'dept:edit',
        'delete_permission': 'dept:delete',
        'view_permission': 'dept:view',
        'fields': (
            'name', 'code', 'type', 'parent_code', 'leader', 'phone',
            'email', 'sort', 'status', 'note',
        ),
    },
    'positions': {
        'model': Position,
        'label': 'positions',
        'add_permission': 'position:add',
        'edit_permission': 'position:edit',
        'delete_permission': 'position:delete',
        'view_permission': 'position:view',
        'fields': ('name', 'code', 'sort', 'status', 'note'),
    },
    'regions': {
        'model': Region,
        'label': 'regions',
        'add_permission': 'region:add',
        'edit_permission': 'region:edit',
        'delete_permission': 'region:delete',
        'view_permission': 'region:view',
        'fields': (
            'name', 'code', 'level', 'parent_code', 'area_code',
            'zip_code', 'pinyin', 'sort', 'status', 'note',
        ),
    },
    'member_levels': {
        'model': MemberLevel,
        'label': 'member-levels',
        'add_permission': 'member_level:add',
        'edit_permission': 'member_level:edit',
        'delete_permission': 'member_level:delete',
        'view_permission': 'member_level:view',
        'fields': (
            'name', 'code', 'min_points', 'discount', 'icon',
            'sort', 'status', 'description',
        ),
    },
}


def _resource_config(resource):
    config = DATA_RESOURCES.get(str(resource or '').strip())
    if not config:
        raise ValueError('不支持的数据类型')
    return config


def _export_row(resource, obj):
    if resource in ('departments', 'regions'):
        parent_code = obj.parent.code if obj.parent_id else ''
    else:
        parent_code = None
    if resource == 'departments':
        return {
            'name': obj.name, 'code': obj.code, 'type': obj.type,
            'parent_code': parent_code, 'leader': obj.leader,
            'phone': obj.phone, 'email': obj.email, 'sort': obj.sort,
            'status': 1 if obj.status else 0, 'note': obj.note,
        }
    if resource == 'positions':
        return {
            'name': obj.name, 'code': obj.code, 'sort': obj.sort,
            'status': 1 if obj.status else 0, 'note': obj.note,
        }
    if resource == 'regions':
        return {
            'name': obj.name, 'code': obj.code, 'level': obj.level,
            'parent_code': parent_code, 'area_code': obj.area_code,
            'zip_code': obj.zip_code, 'pinyin': obj.pinyin, 'sort': obj.sort,
            'status': 1 if obj.status else 0, 'note': obj.note,
        }
    return {
        'name': obj.name, 'code': obj.code, 'min_points': obj.min_points,
        'discount': str(obj.discount), 'icon': obj.icon, 'sort': obj.sort,
        'status': 1 if obj.status else 0, 'description': obj.description,
    }


@csrf_exempt
@api_login_required
def data_export(request):
    """GET /api/rbac/data-export/?resource=departments&format=csv|xlsx."""
    import csv
    import io
    from datetime import date

    from django.http import HttpResponse

    try:
        resource = str(request.GET.get('resource') or '')
        config = _resource_config(resource)
    except ValueError as exc:
        return error_response(str(exc), 400)
    if not has_permission(request.user, config['view_permission'], request):
        return error_response('无权限', 403)
    export_format = str(request.GET.get('format') or 'csv').lower()
    if export_format not in ('csv', 'xlsx'):
        return error_response('导出格式必须是 csv 或 xlsx', 400)

    queryset = config['model'].objects.all()
    if resource in ('departments', 'regions'):
        queryset = queryset.select_related('parent')
    queryset = queryset.order_by('sort', 'id')
    filename = '%s-%s.%s' % (config['label'], date.today().isoformat(), export_format)
    if export_format == 'xlsx':
        try:
            from openpyxl import Workbook
        except ImportError:
            return error_response('服务器未安装 openpyxl，无法导出 Excel', 500)
        workbook = Workbook(write_only=True)
        sheet = workbook.create_sheet('data')
        sheet.append(config['fields'])
        for obj in queryset.iterator():
            row = _export_row(resource, obj)
            sheet.append([row.get(field, '') for field in config['fields']])
        output = io.BytesIO()
        workbook.save(output)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
    else:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=config['fields'], lineterminator='\n')
        writer.writeheader()
        for obj in queryset.iterator():
            writer.writerow(_export_row(resource, obj))
        response = HttpResponse(
            '\ufeff' + output.getvalue(),
            content_type='text/csv; charset=utf-8',
        )
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename
    return response


def _import_bool(value, default=True):
    if value in (None, ''):
        return default
    return str(value).strip().lower() in ('1', 'true', 'yes', 'on', '启用', '是')


def _cell_text(value):
    import datetime as dt

    if value is None:
        return ''
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()
    return str(value).strip()


def _uploaded_rows(uploaded):
    import csv
    import io

    raw = uploaded.read()
    if len(raw) > 5 * 1024 * 1024:
        raise ValueError('导入文件不能超过 5MB')
    filename = str(getattr(uploaded, 'name', '') or '').lower()
    content_type = str(getattr(uploaded, 'content_type', '') or '').lower()
    if filename.endswith('.xlsx') or content_type.endswith(
        'spreadsheetml.sheet'
    ):
        try:
            from openpyxl import load_workbook
        except ImportError:
            raise ValueError('服务器未安装 openpyxl，无法导入 Excel')
        try:
            workbook = load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
            sheet = workbook.active
            iterator = sheet.iter_rows(values_only=True)
            headers = [_cell_text(value) for value in next(iterator)]
            if not any(headers):
                raise ValueError('Excel 缺少表头')
            rows = []
            for values in iterator:
                if not any(value not in (None, '') for value in values):
                    continue
                rows.append({
                    headers[index]: _cell_text(values[index])
                    for index in range(min(len(headers), len(values)))
                    if headers[index]
                })
            return rows
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError('Excel 文件无法解析: %s' % exc)

    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        raise ValueError('CSV 文件必须是 UTF-8 编码')
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValueError('CSV 缺少表头')
    return list(reader)


def _parse_int(value, field, minimum=None, maximum=None, default=0):
    try:
        result = int(value if value not in (None, '') else default)
    except (TypeError, ValueError):
        raise ValueError('%s 必须是整数' % field)
    if minimum is not None and result < minimum:
        raise ValueError('%s 不能小于 %s' % (field, minimum))
    if maximum is not None and result > maximum:
        raise ValueError('%s 不能大于 %s' % (field, maximum))
    return result


def _parse_decimal(value, field, minimum=0, maximum=100, default='100'):
    value = str(value if value not in (None, '') else default)
    try:
        result = Decimal(value)
    except InvalidOperation:
        raise ValueError('%s 必须是数字' % field)
    if result < minimum or result > maximum:
        raise ValueError('%s 必须在 %s 到 %s 之间' % (field, minimum, maximum))
    return result


def _upsert_rows(resource, config, rows, mode, dry_run=False):
    from .models import Department, MemberLevel, Position, Region

    model = config['model']
    codes = [str(row.get('code') or '').strip() for row in rows]
    if any(not code for code in codes):
        raise ValueError('每行都必须填写 code')
    if len(codes) != len(set(codes)):
        raise ValueError('CSV 中存在重复 code')

    created = []
    updated = []
    skipped = []
    errors = []
    parent_rows = []
    with transaction.atomic():
        for index, row in enumerate(rows, start=2):
            code = str(row.get('code') or '').strip()
            name = str(row.get('name') or '').strip()
            if not name:
                errors.append({'row': index, 'message': 'name 不能为空'})
                continue
            existing = model.objects.filter(code=code).first()
            if existing and mode == 'insert':
                skipped.append(code)
                continue
            try:
                if resource == 'departments':
                    obj = existing or Department(code=code)
                    obj.name = name[:150]
                    obj.type = _parse_int(row.get('type'), 'type', 1, 4, 3)
                    obj.leader = str(row.get('leader') or '')[:50]
                    obj.phone = str(row.get('phone') or '')[:30]
                    obj.email = str(row.get('email') or '')[:254]
                    obj.sort = _parse_int(row.get('sort'), 'sort', 0, 999999, 0)
                    obj.status = _import_bool(row.get('status'), True)
                    obj.note = str(row.get('note') or '')[:255]
                    parent_rows.append((obj, str(row.get('parent_code') or '').strip()))
                elif resource == 'positions':
                    obj = existing or Position(code=code)
                    obj.name = name[:150]
                    obj.sort = _parse_int(row.get('sort'), 'sort', 0, 999999, 0)
                    obj.status = _import_bool(row.get('status'), True)
                    obj.note = str(row.get('note') or '')[:255]
                elif resource == 'regions':
                    obj = existing or Region(code=code)
                    obj.name = name[:150]
                    obj.level = _parse_int(row.get('level'), 'level', 1, 5, 1)
                    obj.area_code = str(row.get('area_code') or '')[:20]
                    obj.zip_code = str(row.get('zip_code') or '')[:20]
                    obj.pinyin = str(row.get('pinyin') or '')[:150]
                    obj.sort = _parse_int(row.get('sort'), 'sort', 0, 999999, 0)
                    obj.status = _import_bool(row.get('status'), True)
                    obj.note = str(row.get('note') or '')[:255]
                    parent_rows.append((obj, str(row.get('parent_code') or '').strip()))
                else:
                    obj = existing or MemberLevel(code=code)
                    obj.name = name[:150]
                    obj.min_points = _parse_int(row.get('min_points'), 'min_points', 0, 999999999, 0)
                    obj.discount = _parse_decimal(row.get('discount'), 'discount')
                    obj.icon = str(row.get('icon') or '')[:50]
                    obj.sort = _parse_int(row.get('sort'), 'sort', 0, 999999, 0)
                    obj.status = _import_bool(row.get('status'), True)
                    obj.description = str(row.get('description') or '')[:255]
                if not dry_run:
                    obj.save()
                (updated if existing else created).append(code)
            except (ValueError, IntegrityError) as exc:
                errors.append({'row': index, 'message': str(exc)})

        if parent_rows and not dry_run:
            by_code = {}
            for obj, parent_code in parent_rows:
                by_code[obj.code] = obj
                if parent_code:
                    parent = Department.objects.filter(code=parent_code).first() \
                        if resource == 'departments' else Region.objects.filter(code=parent_code).first()
                    if not parent:
                        errors.append({
                            'row': 'parent:' + obj.code,
                            'message': '上级编码不存在: %s' % parent_code,
                        })
                        continue
                    obj.parent = parent
                    obj.save(update_fields=['parent'])
                else:
                    obj.parent = None
                    obj.save(update_fields=['parent'])
    return {
        'created': len(created),
        'updated': len(updated),
        'skipped': len(skipped),
        'errors': errors[:50],
        'created_codes': created[:20],
        'updated_codes': updated[:20],
    }


@csrf_exempt
@api_login_required
def data_import(request):
    """POST /api/rbac/data-import/ - import CSV for a data resource."""
    if request.method != 'POST':
        return error_response('Method not allowed', 405)
    try:
        resource = str(request.POST.get('resource') or '')
        config = _resource_config(resource)
    except ValueError as exc:
        return error_response(str(exc), 400)
    mode = str(request.POST.get('mode') or 'upsert').lower()
    if mode not in ('insert', 'upsert'):
        return error_response('导入模式无效', 400)
    required = [config['add_permission']]
    if mode == 'upsert':
        required.append(config['edit_permission'])
    if any(not has_permission(request.user, code, request) for code in required):
        return error_response('无权限', 403)
    uploaded = request.FILES.get('file')
    if not uploaded:
        return error_response('请选择 CSV 或 Excel 文件', 400)
    try:
        rows = _uploaded_rows(uploaded)
        if len(rows) > 10000:
            raise ValueError('单次最多导入 10000 行')
        result = _upsert_rows(resource, config, rows, mode)
    except ValueError as exc:
        return error_response(str(exc), 400)
    return success_response(result, msg='导入完成')


@csrf_exempt
@api_login_required
def data_batch_delete(request):
    """POST /api/rbac/data-batch-delete/ - delete selected data rows."""
    if request.method != 'POST':
        return error_response('Method not allowed', 405)
    body = get_request_body(request)
    try:
        resource = str(body.get('resource') or '')
        config = _resource_config(resource)
    except ValueError as exc:
        return error_response(str(exc), 400)
    if not has_permission(request.user, config['delete_permission'], request):
        return error_response('无权限', 403)
    raw_ids = body.get('ids')
    if not isinstance(raw_ids, list) or not raw_ids:
        return error_response('请选择要删除的数据', 400)
    try:
        ids = {int(item) for item in raw_ids}
    except (TypeError, ValueError):
        return error_response('ID 必须是整数', 400)
    if len(ids) > 500:
        return error_response('单次最多操作 500 条', 400)

    model = config['model']
    objects = list(model.objects.filter(pk__in=ids))
    skipped = []
    deletable = []
    for obj in objects:
        children = getattr(obj, 'children', None)
        if children is not None and children.exclude(pk__in=ids).exists():
            skipped.append({'id': obj.pk, 'name': str(obj)})
        else:
            deletable.append(obj)
    deleted = []
    with transaction.atomic():
        for obj in deletable:
            deleted.append(obj.pk)
            obj.delete()
    return success_response({
        'deleted': len(deleted),
        'deleted_ids': deleted,
        'skipped': skipped,
    }, msg='批量删除完成')


@csrf_exempt
@api_login_required
def data_batch_status(request):
    """POST /api/rbac/data-batch-status/ - enable or disable selected rows."""
    if request.method != 'POST':
        return error_response('Method not allowed', 405)
    body = get_request_body(request)
    try:
        resource = str(body.get('resource') or '')
        config = _resource_config(resource)
    except ValueError as exc:
        return error_response(str(exc), 400)
    if not has_permission(request.user, config['edit_permission'], request):
        return error_response('无权限', 403)
    raw_ids = body.get('ids')
    if not isinstance(raw_ids, list) or not raw_ids:
        return error_response('请选择数据', 400)
    try:
        ids = {int(item) for item in raw_ids}
    except (TypeError, ValueError):
        return error_response('ID 必须是整数', 400)
    if len(ids) > 500:
        return error_response('单次最多操作 500 条', 400)
    target = _as_bool(body.get('status'), True)
    updated = config['model'].objects.filter(pk__in=ids).update(status=target)
    return success_response({'updated': updated, 'status': target}, msg='状态已更新')
