# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-26 22:19
# @FileName  : auth.py
# -----------------------------
"""面向 Django 原生接口与第三方 API 的通用认证桥接层。"""
import importlib
import logging

from django.conf import settings

logger = logging.getLogger(__name__)
_AUTHENTICATORS = []


def register_authenticator(func, name=None, priority=100):
    """注册一个可调用对象 ``func(request) -> user|None``。"""
    key = name or getattr(func, '__name__', repr(func))
    _AUTHENTICATORS[:] = [
        item for item in _AUTHENTICATORS if item['name'] != key
    ]
    _AUTHENTICATORS.append({'name': key, 'func': func, 'priority': priority})
    _AUTHENTICATORS.sort(key=lambda item: item['priority'])
    return func


def unregister_authenticator(name_or_func):
    if callable(name_or_func):
        name = getattr(name_or_func, '__name__', repr(name_or_func))
    else:
        name = name_or_func
    _AUTHENTICATORS[:] = [
        item for item in _AUTHENTICATORS if item['name'] != name
    ]


def _resolve_callable(path):
    module_path, _, attr = path.rpartition('.')
    if not module_path:
        raise ValueError('Invalid authenticator path: %s' % path)
    module = importlib.import_module(module_path)
    target = module
    for part in attr.split('.'):
        target = getattr(target, part)
    return target


def load_configured_authenticators():
    """加载 ``LAYUI_RBAC_AUTHENTICATORS`` 中声明的认证器。"""
    paths = getattr(settings, 'LAYUI_RBAC_AUTHENTICATORS', []) or []
    for index, path in enumerate(paths):
        try:
            register_authenticator(
                _resolve_callable(path),
                name='settings:%s' % path,
                priority=50 + index,
            )
        except Exception:
            logger.exception('Failed to load authenticator %s', path)
            continue


def session_authenticator(request):
    user = getattr(request, 'user', None)
    if user is not None and getattr(user, 'is_authenticated', False):
        return user
    return None


def builtin_token_authenticator(request):
    from django_layuix.rbac.token_auth import token_authenticate
    return token_authenticate(request)


register_authenticator(session_authenticator, name='session', priority=0)
register_authenticator(builtin_token_authenticator, name='layuix_token', priority=100)


def authenticate_request(request):
    """使用所有已注册认证器解析 API 调用方用户。"""
    for item in list(_AUTHENTICATORS):
        try:
            user = item['func'](request)
        except Exception:
            logger.exception('Authenticator %s failed', item['name'])
            continue
        if user is not None and getattr(user, 'is_authenticated', False):
            request.user = user
            return user
    return None


def registered_authenticators():
    return [item['name'] for item in _AUTHENTICATORS]
