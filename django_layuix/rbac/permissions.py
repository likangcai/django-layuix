# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-26 22:19
# @FileName  : permissions.py
# -----------------------------
from functools import wraps
from django.http import JsonResponse


def _has_explicit_token(request):
    if request.META.get('HTTP_AUTHORIZATION', '').lower().startswith('bearer '):
        return True
    if request.META.get('HTTP_X_TOKEN'):
        return True
    query_token = request.GET.get('token')
    if not query_token:
        return False
    from django.conf import settings
    return bool(
        getattr(settings, 'LAYUI_ALLOW_QUERY_TOKEN', False)
        or str(request.path).endswith('/system/info/stream/')
    )


def resolve_api_user(request):
    """统一解析 API 调用者；显式 Token 优先于 Session，避免身份混淆。"""
    from django_layuix.integrations.auth import authenticate_request

    if _has_explicit_token(request):
        from .token_auth import token_authenticate

        user = token_authenticate(request)
        if user is not None:
            request.user = user
        return user

    user = getattr(request, 'user', None)
    if user is not None and getattr(user, 'is_authenticated', False):
        return user
    return authenticate_request(request)


def has_permission(user, permission_code, request=None):
    """统一权限判定入口；未注册权限码默认拒绝。"""
    if user is None or not getattr(user, 'is_authenticated', False):
        return False
    from .permission_registry import is_registered_permission

    if not is_registered_permission(permission_code):
        return False
    checker = getattr(user, 'has_perm', None)
    if not callable(checker):
        return False
    return bool(checker(permission_code))


def api_permission_required(permission_code):
    """服务端强制权限校验：统一走 has_permission（含继承与约束）。"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = resolve_api_user(request)
            if user is None or not getattr(user, 'is_authenticated', False):
                return JsonResponse({'code': 401, 'msg': '未登录'}, status=401)
            request.user = user
            if not has_permission(user, permission_code, request):
                return JsonResponse({'code': 403, 'msg': '无权限'}, status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def api_permission_by_method(mapping, default=None):
    """按 HTTP 方法选择 required 权限码。映射示例：{'GET': 'x:view', 'POST': 'x:edit', '*': 'x:view'}。"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = resolve_api_user(request)
            if user is None or not getattr(user, 'is_authenticated', False):
                return JsonResponse({'code': 401, 'msg': '未登录'}, status=401)
            request.user = user
            method = 'GET' if request.method == 'HEAD' else request.method
            code = mapping.get(method) or default
            if not code or not has_permission(user, code, request):
                return JsonResponse({'code': 403, 'msg': '无权限'}, status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def api_login_required(view_func):
    """登录校验装饰器：委托给通用认证桥接层。"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = resolve_api_user(request)
        if user is None or not getattr(user, 'is_authenticated', False):
            return JsonResponse({'code': 401, 'msg': '未登录'}, status=401)
        request.user = user
        return view_func(request, *args, **kwargs)
    return wrapper
