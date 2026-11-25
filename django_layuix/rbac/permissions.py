from functools import wraps
from django.http import JsonResponse


def resolve_api_user(request):
    """统一解析 API 调用者，委托给通用认证桥接层。"""
    from django_layuix.integrations.auth import authenticate_request

    user = getattr(request, 'user', None)
    if user is not None and getattr(user, 'is_authenticated', False):
        return user
    return authenticate_request(request)


def has_permission(user, permission_code, request=None):
    """统一权限判定入口，供 Django 视图与第三方框架适配器复用。"""
    if user is None or not getattr(user, 'is_authenticated', False):
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
            if not has_permission(user, permission_code, request):
                return JsonResponse({'code': 403, 'msg': '无权限'}, status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def api_permission_by_method(mapping, default=None):
    """Require a permission code selected by HTTP method.

    mapping: {'GET': 'x:view', 'POST': 'x:edit', '*': 'x:view'}
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = resolve_api_user(request)
            if user is None or not getattr(user, 'is_authenticated', False):
                return JsonResponse({'code': 401, 'msg': '未登录'}, status=401)
            request.user = user
            code = mapping.get(request.method) or mapping.get('*') or default
            if code and not has_permission(user, code, request):
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
