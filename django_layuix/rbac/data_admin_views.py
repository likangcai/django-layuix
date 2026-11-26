# -*- coding: utf-8 -*-
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


# ==================== Department ====================

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


# ==================== Position ====================

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


# ==================== Region ====================

@csrf_exempt
@api_login_required
@api_permission_required('region:view')
@field_whitelisted('rbac.Region')
def region_list(request):
    """GET /api/rbac/regions/ - list regions."""
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
    rows = [_region_payload(row) for row in queryset.order_by('sort', 'id')]
    return success_response({'list': rows, 'total': len(rows)})


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
        level = _int_value(body.get('level'), 1, 1, 4)
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
                body.get('level') if 'level' in body else obj.level, obj.level, 1, 4
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


# ==================== Member level ====================

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
