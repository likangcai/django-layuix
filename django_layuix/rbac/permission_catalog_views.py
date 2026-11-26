# -*- coding: utf-8 -*-
"""Permission catalog management APIs."""
from django.db.models import Count
from django.views.decorators.csrf import csrf_exempt

from .models import Menu
from .views import (
    api_login_required, api_permission_required, error_response,
    get_request_body, success_response,
)

PROTECTED_CODES = {'permission:view', 'permission:edit'}


def _catalog_row(menu):
    kind = 'page' if menu.path else 'button'
    return {
        'id': menu.pk,
        'name': menu.name,
        'code': menu.permission,
        'path': menu.path,
        'kind': kind,
        'kind_label': '页面' if kind == 'page' else '按钮',
        'status': menu.status,
        'role_count': getattr(menu, 'role_count', 0),
        'parent_name': getattr(menu.parent, 'name', ''),
        'update_time': menu.update_time.strftime('%Y-%m-%d %H:%M:%S') if menu.update_time else '',
    }


@csrf_exempt
@api_login_required
@api_permission_required('permission:view')
def permission_catalog_list(request):
    """GET /api/rbac/permission-catalog/ - list registered permission codes."""
    if request.method != 'GET':
        return error_response('Method not allowed', 405)
    queryset = Menu.objects.filter(
        plugin_key='permission_catalog', menu_type=3,
    ).select_related('parent').annotate(role_count=Count('roles')).order_by(
        'permission', 'id'
    )
    keyword = str(request.GET.get('keyword') or '').strip()
    if keyword:
        from django.db.models import Q
        queryset = queryset.filter(
            Q(name__icontains=keyword) | Q(permission__icontains=keyword)
            | Q(path__icontains=keyword)
        )
    kind = str(request.GET.get('kind') or '').strip()
    if kind == 'page':
        queryset = queryset.exclude(path='')
    elif kind == 'button':
        queryset = queryset.filter(path='')
    status = request.GET.get('status')
    if status not in (None, ''):
        queryset = queryset.filter(status=str(status).lower() in ('1', 'true', 'on'))
    rows = [_catalog_row(row) for row in queryset]
    return success_response({
        'list': rows,
        'total': len(rows),
        'page_count': sum(1 for row in rows if row['kind'] == 'page'),
        'button_count': sum(1 for row in rows if row['kind'] == 'button'),
    })


@csrf_exempt
@api_login_required
@api_permission_required('permission:edit')
def permission_catalog_set_status(request, pk):
    """POST /api/rbac/permission-catalog/<id>/status/ - enable or disable a code."""
    if request.method != 'POST':
        return error_response('Method not allowed', 405)
    try:
        menu = Menu.objects.get(pk=pk, plugin_key='permission_catalog', menu_type=3)
    except Menu.DoesNotExist:
        return error_response('权限不存在', 404)
    body = get_request_body(request)
    if 'status' not in body:
        return error_response('缺少目标状态', 400)
    desired = bool(body.get('status'))
    if menu.permission in PROTECTED_CODES and not desired:
        return error_response('核心权限不能停用', 400)
    menu.status = desired
    menu.save(update_fields=['status'])
    return success_response(
        {'id': menu.pk, 'status': menu.status},
        msg='权限已启用' if menu.status else '权限已停用',
    )
