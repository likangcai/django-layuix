# -*- coding: utf-8 -*-
"""Optional Django Ninja adapter. Import is safe to skip when Ninja is absent."""
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
    """Ninja auth class backed by the generic django-layuix authenticator registry."""

    def authenticate(self, request, token):
        user = resolve_api_user(request)
        if user is not None and getattr(user, 'is_authenticated', False):
            return user
        return None


def ninja_permission_required(permission_code):
    """Enforce a layuix permission code on a Ninja operation."""
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
