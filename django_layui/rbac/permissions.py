from functools import wraps
from django.http import JsonResponse


def api_permission_required(permission_code):
    """权限校验装饰器"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({'code': 401, 'msg': '未登录'})
            if request.user.username == 'admin' or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            from .models import Menu
            has_perm = Menu.objects.filter(
                roles__users=request.user,
                permission=permission_code,
                status=True
            ).exists()
            if not has_perm:
                return JsonResponse({'code': 403, 'msg': '无权限'})
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def api_login_required(view_func):
    """登录校验装饰器"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'code': 401, 'msg': '未登录'})
        return view_func(request, *args, **kwargs)
    return wrapper
