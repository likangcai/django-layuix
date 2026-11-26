# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-26 22:19
# @FileName  : ninja.py
# -----------------------------
"""可选的 Django Ninja 适配器。未安装 Ninja 时跳过导入是安全的。"""
import inspect
from functools import wraps

try:
    from ninja.errors import HttpError
    from ninja.security import HttpBearer
except ImportError as exc:  # pragma: no cover - depends on optional dependency
    raise ImportError(
        'django_layuix.integrations.ninja requires django-ninja'
    ) from exc

from django_layuix.rbac.permissions import has_permission, resolve_api_user


class LayuiNinjaAuth(HttpBearer):
    """基于通用 django-layuix 认证注册表的 Ninja 认证类。"""

    def authenticate(self, request, token):
        if token:
            from django_layuix.rbac.token_auth import verify_token

            result = verify_token(token)
            user = result.get('user') if result.get('valid') else None
            if user is not None and getattr(user, 'is_authenticated', False):
                request.user = user
                return user
            return None
        user = resolve_api_user(request)
        if user is not None and getattr(user, 'is_authenticated', False):
            return user
        return None


def ninja_permission_required(permission_code):
    """对 Ninja 操作强制校验 layuix 权限码。"""
    def decorator(func):
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(request, *args, **kwargs):
                user = resolve_api_user(request)
                if user is None or not getattr(user, 'is_authenticated', False):
                    raise HttpError(401, '未登录')
                if not has_permission(user, permission_code, request):
                    raise HttpError(403, '无权限')
                return await func(request, *args, **kwargs)
            return async_wrapper

        @wraps(func)
        def wrapper(request, *args, **kwargs):
            user = resolve_api_user(request)
            if user is None or not getattr(user, 'is_authenticated', False):
                raise HttpError(401, '未登录')
            if not has_permission(user, permission_code, request):
                raise HttpError(403, '无权限')
            return func(request, *args, **kwargs)
        return wrapper
    return decorator
