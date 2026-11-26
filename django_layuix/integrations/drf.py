# -*- coding: utf-8 -*-
"""Optional DRF adapter. Import is safe to skip when DRF is not installed."""
try:
    from rest_framework.authentication import BaseAuthentication
    from rest_framework.permissions import BasePermission
except ImportError as exc:  # pragma: no cover - depends on optional dependency
    raise ImportError(
        'django_layuix.integrations.drf requires djangorestframework'
    ) from exc

from django_layuix.integrations.auth import register_authenticator
from django_layuix.rbac.permissions import has_permission


def simplejwt_authenticator(request):
    """Bridge SimpleJWT tokens into the generic authentication registry."""
    try:
        from rest_framework_simplejwt.authentication import JWTAuthentication
    except ImportError:
        return None
    result = JWTAuthentication().authenticate(request)
    return result[0] if result else None


register_authenticator(simplejwt_authenticator, name='simplejwt', priority=50)


class SimpleJWTAuthentication(BaseAuthentication):
    """Drop-in DRF authentication class backed by SimpleJWT."""

    def authenticate(self, request):
        try:
            from rest_framework_simplejwt.authentication import JWTAuthentication
        except ImportError:
            return None
        return JWTAuthentication().authenticate(request)


class LayuiRBACPermission(BasePermission):
    """DRF permission class backed by django-layuix RBAC.

    Set ``layui_permission`` on a view, or ``layui_permission_map`` keyed by
    DRF action. Views without a declared code are left untouched.
    """

    def _permission_code(self, view):
        code = getattr(view, 'layui_permission', None) or getattr(view, 'permission_code', None)
        if code:
            return code
        mapping = getattr(view, 'layui_permission_map', None) or {}
        return mapping.get(getattr(view, 'action', None))

    def has_permission(self, request, view):
        if getattr(view, 'layui_permission_exempt', False):
            return True
        code = self._permission_code(view)
        if not code:
            return False
        return has_permission(getattr(request, 'user', None), code, request)

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)
