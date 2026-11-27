# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-26 22:19
# @FileName  : drf.py
# -----------------------------
"""可选的 DRF 适配器。未安装 DRF 时跳过导入是安全的。"""
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
    """将 SimpleJWT 令牌接入通用认证注册表。"""
    try:
        from rest_framework_simplejwt.authentication import JWTAuthentication
    except ImportError:
        return None
    result = JWTAuthentication().authenticate(request)
    return result[0] if result else None


register_authenticator(simplejwt_authenticator, name='simplejwt', priority=50)


class SimpleJWTAuthentication(BaseAuthentication):
    """基于 SimpleJWT 的可直接替换 DRF 认证类。"""

    def authenticate(self, request):
        try:
            from rest_framework_simplejwt.authentication import JWTAuthentication
        except ImportError:
            return None
        return JWTAuthentication().authenticate(request)


class LayuiRBACPermission(BasePermission):
    """基于 django-layuix RBAC 的 DRF 权限类。在视图上设置 ``layui_permission``，或按 DRF action 设置 ``layui_permission_map``；未声明权限码的视图保持不变。"""

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
