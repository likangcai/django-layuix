# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-26 22:19
# @FileName  : permission_catalog_views.py
# -----------------------------
"""权限目录管理 API。"""
from django.db.models import Count, Q
from django.views.decorators.csrf import csrf_exempt

from .button_generator import derive_permission_prefix, generate_menu_buttons
from .permission_registry import BUTTON_ACTIONS, build_permission_code, permission_catalog
from .models import Menu
from .views import (
    api_login_required, api_permission_required, error_response,
    get_request_body, parse_bool_value, success_response,
)

PROTECTED_CODES = {'permission:view', 'permission:edit'}


def _catalog_row(menu):
    kind = 'page' if menu.path else 'button'
    builtin = menu.plugin_key == 'permission_catalog'
    return {
        'id': menu.pk,
        'name': menu.name,
        'code': menu.permission,
        'path': menu.path,
        'kind': kind,
        'kind_label': '页面' if kind == 'page' else '按钮',
        'status': menu.status,
        'role_count': getattr(menu, 'role_count', 0),
        'parent_id': menu.parent_id,
        'parent_name': getattr(menu.parent, 'name', ''),
        'source': 'builtin' if builtin else 'business',
        'source_label': '内置' if builtin else '业务',
        'deletable': not builtin,
        'protected': menu.permission in PROTECTED_CODES,
        'update_time': menu.update_time.strftime('%Y-%m-%d %H:%M:%S') if menu.update_time else '',
    }


@csrf_exempt
@api_login_required
@api_permission_required('permission:view')
def permission_catalog_list(request):
    """GET /api/rbac/permission-catalog/ - 获取已注册权限码列表。"""
    if request.method != 'GET':
        return error_response('Method not allowed', 405)
    queryset = Menu.objects.filter(menu_type=3).filter(
        Q(plugin_key='permission_catalog') | Q(plugin_key='')
    ).select_related('parent').annotate(role_count=Count('roles')).order_by(
        'permission', 'id'
    )
    keyword = str(request.GET.get('keyword') or '').strip()
    if keyword:
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
    """POST /api/rbac/permission-catalog/<id>/status/ - 启用或停用权限码。"""
    if request.method != 'POST':
        return error_response('Method not allowed', 405)
    try:
        menu = Menu.objects.get(pk=pk, menu_type=3)
        if menu.plugin_key not in ('permission_catalog', ''):
            raise Menu.DoesNotExist
    except Menu.DoesNotExist:
        return error_response('权限不存在', 404)
    body = get_request_body(request)
    if 'status' not in body:
        return error_response('缺少目标状态', 400)
    desired = parse_bool_value(body.get('status'))
    if desired is None:
        return error_response('状态值无效', 400)
    if menu.permission in PROTECTED_CODES and not desired:
        return error_response('核心权限不能停用', 400)
    menu.status = desired
    menu.save(update_fields=['status'])
    return success_response(
        {'id': menu.pk, 'status': menu.status},
        msg='权限已启用' if menu.status else '权限已停用',
    )


@csrf_exempt
@api_login_required
@api_permission_required('permission:edit')
def permission_catalog_buttons_create(request):
    """POST /api/rbac/permission-catalog/buttons/create/ - 为菜单创建按钮权限。"""
    if request.method != 'POST':
        return error_response('Method not allowed', 405)
    body = get_request_body(request)
    try:
        parent_id = int(body.get('parent_id') or 0)
    except (TypeError, ValueError):
        return error_response('请选择有效的上级菜单', 400)
    parent = Menu.objects.filter(pk=parent_id, menu_type__in=(1, 2)).exclude(
        plugin_key='permission_catalog'
    ).first()
    if parent is None:
        return error_response('上级菜单不存在或不可授权', 404)
    actions = body.get('actions') or []
    if isinstance(actions, str):
        actions = [item for item in actions.split(',') if item]
    if not isinstance(actions, list) or not actions:
        return error_response('请至少选择一个按钮动作', 400)
    prefix = derive_permission_prefix(parent)
    builtin_codes = set(permission_catalog())
    conflicts = []
    for action in actions:
        key = action.get('value') if isinstance(action, dict) else action
        key = str(key or '').strip()
        if key not in BUTTON_ACTIONS:
            continue
        code = build_permission_code(prefix, key)
        if code and code in builtin_codes:
            conflicts.append(code)
    if conflicts:
        return error_response('以下权限码已由内置目录管理，不能重复创建：%s' % '、'.join(sorted(set(conflicts))), 400)
    replace = parse_bool_value(body.get('replace'), False)
    result = generate_menu_buttons(parent, actions, replace=replace, actor=request.user)
    codes = result['created'] + result['updated']
    rows = Menu.objects.filter(
        parent=parent, permission__in=codes, menu_type=3, plugin_key=''
    ).values('id', 'permission', 'name')
    return success_response({
        'parent_id': parent.pk,
        'prefix': result['prefix'],
        'actions': result['actions'],
        'rows': list(rows),
        'created': result['created'],
        'updated': result['updated'],
    }, msg='按钮权限已创建')


@csrf_exempt
@api_login_required
@api_permission_required('permission:edit')
def permission_catalog_buttons_delete(request, pk):
    """POST /api/rbac/permission-catalog/buttons/<pk>/delete/ - 删除业务按钮权限。"""
    if request.method != 'POST':
        return error_response('Method not allowed', 405)
    menu = Menu.objects.filter(pk=pk, menu_type=3, plugin_key='').first()
    if menu is None:
        return error_response('业务按钮权限不存在或不可删除', 404)
    if menu.permission in PROTECTED_CODES:
        return error_response('核心权限不能删除', 400)
    payload = {'id': menu.pk, 'code': menu.permission, 'parent_id': menu.parent_id}
    menu.delete()
    return success_response(payload, msg='按钮权限已删除')
