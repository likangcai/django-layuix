from functools import wraps
from django.http import JsonResponse


def resolve_api_user(request):
    """统一解析 API 调用者：Session 优先，未登录时尝试 Bearer Token。"""
    user = getattr(request, 'user', None)
    if user is not None and getattr(user, 'is_authenticated', False):
        return user

    from .token_auth import token_authenticate
    token_user = token_authenticate(request)
    if token_user is not None:
        request.user = token_user
    return getattr(request, 'user', None)


def api_permission_required(permission_code):
    """服务端强制权限校验：统一走 UserProfile.has_perm（含继承与约束）。"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = resolve_api_user(request)
            if user is None or not getattr(user, 'is_authenticated', False):
                return JsonResponse({'code': 401, 'msg': '未登录'}, status=401)
            if not user.has_perm(permission_code):
                return JsonResponse({'code': 403, 'msg': '无权限'}, status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def api_login_required(view_func):
    """登录校验装饰器：同时支持 Session 与 Bearer Token。"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = resolve_api_user(request)
        if user is None or not getattr(user, 'is_authenticated', False):
            return JsonResponse({'code': 401, 'msg': '未登录'}, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper
