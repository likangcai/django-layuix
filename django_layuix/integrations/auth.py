# -*- coding: utf-8 -*-
"""Generic authentication bridge for Django-native and third-party APIs."""
import importlib
import logging

from django.conf import settings

logger = logging.getLogger(__name__)
_AUTHENTICATORS = []


def register_authenticator(func, name=None, priority=100):
    """Register a callable ``func(request) -> user|None``."""
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
    """Load authenticators declared in ``LAYUI_RBAC_AUTHENTICATORS``."""
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
    """Resolve the API caller using all registered authenticators."""
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
