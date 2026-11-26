# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-26 22:19
# @FileName  : plugins.py
# -----------------------------
"""第三方插件注册表：发现、校验、持久化和钩子。"""
import importlib
import logging
import os
import re

from django.conf import settings
from django.db import IntegrityError, transaction

logger = logging.getLogger(__name__)

ENTRY_POINT_GROUP = 'django_layuix.plugins'
_PLUGINS = {}
_PLUGIN_CLASSES = {}

_FIELDS = (
    'key', 'name', 'version', 'description',
    'api_prefix', 'menu_path', 'app_label',
    'dependencies', 'source', 'validation_error', 'desired_active', 'is_active',
)

_SPEC_RE = re.compile(r'^([A-Za-z0-9_.-]+)\s*(>=|==|<=|>|<)?\s*([0-9][0-9A-Za-z.\-]*)?$')


def _db():
    from .models import PluginRegistry
    return PluginRegistry.objects


def _supports_desired_active():
    """避免迁移执行前查询不存在的字段。"""
    from .models import PluginRegistry
    return any(field.name == 'desired_active' for field in PluginRegistry._meta.get_fields())


def _version_tuple(value):
    if not value:
        return ()
    parts = re.split(r'[^\d]+', str(value))
    return tuple(int(part) if part.isdigit() else part for part in parts if part != '')


def _installed_version(package):
    normalized = package.lower().replace('_', '-')
    if normalized == 'django-layuix':
        import django_layuix
        return getattr(django_layuix, '__version__', '0.0.0')

    from importlib.metadata import PackageNotFoundError, version
    try:
        return version(package)
    except PackageNotFoundError:
        try:
            return version(normalized)
        except PackageNotFoundError:
            return None


def _satisfies(spec):
    match = _SPEC_RE.match(str(spec).strip())
    if not match:
        return True  # Unknown spec format: do not block startup.
    package, operator, expected = match.groups()
    current = _installed_version(package)
    if current is None:
        return False
    if not operator or not expected:
        return True
    current_tuple = _version_tuple(current)
    expected_tuple = _version_tuple(expected)
    if operator == '>=':
        return current_tuple >= expected_tuple
    if operator == '>':
        return current_tuple > expected_tuple
    if operator == '<=':
        return current_tuple <= expected_tuple
    if operator == '<':
        return current_tuple < expected_tuple
    return current_tuple == expected_tuple


def _as_lines(value):
    if isinstance(value, (list, tuple, set)):
        return '\n'.join(str(item) for item in value)
    return str(value or '')


def validate_plugin_metadata(metadata):
    """返回可读性良好的校验错误列表。"""
    errors = []
    minimum = metadata.get('min_layuix_version')
    if minimum and not _satisfies('django-layuix>=%s' % minimum):
        errors.append('django-layuix 版本低于插件要求的 %s' % minimum)

    for spec in metadata.get('dependencies') or ():
        if not _satisfies(spec):
            errors.append('缺少依赖：%s' % spec)
    return errors


def register_plugin_class(key, plugin_class):
    _PLUGIN_CLASSES[key] = plugin_class


def _plugin_instance(key):
    cls = _PLUGIN_CLASSES.get(key)
    if cls is None:
        return None
    app_name = getattr(cls, 'name', key)
    try:
        module = importlib.import_module(app_name.split('.')[0])
    except Exception:
        class _DummyModule:
            __name__ = app_name
            __path__ = [os.path.dirname(__file__)]
        module = _DummyModule()
    try:
        return cls(app_name, module)
    except Exception:
        return None


def _call_hook(key, hook_name):
    instance = _plugin_instance(key)
    if instance is None:
        return
    hook = getattr(instance, hook_name, None)
    if callable(hook):
        try:
            hook()
        except Exception:
            logger.exception('Plugin %s hook %s failed', key, hook_name)


def _was_active(key):
    try:
        return bool(_db().filter(key=key).values_list('is_active', flat=True).first())
    except Exception:
        return False


RESERVED_PLUGIN_KEYS = {'permission_catalog'}


def register_plugin(key, name, version='1.0.0', description='',
                    api_prefix='', menu_path='', app_label='',
                    dependencies=(), is_active=True, source='app',
                    validation_error='', validation_errors=None):
    """注册或更新插件元数据。可从 AppConfig.ready() 安全调用。"""
    errors = list(validation_errors or [])
    if key in RESERVED_PLUGIN_KEYS:
        errors.append('插件键 %s 为系统保留键' % key)
        return {
            'key': key, 'name': name, 'version': version,
            'description': description, 'api_prefix': api_prefix,
            'menu_path': menu_path, 'app_label': app_label,
            'dependencies': _as_lines(dependencies), 'source': source,
            'validation_error': '\n'.join(errors), 'desired_active': False,
            'is_active': False,
        }
    if validation_error:
        errors.append(validation_error)
    error_text = '\n'.join(errors)

    existing = None
    db_error = False
    try:
        existing = _db().filter(key=key).first()
    except Exception:
        logger.exception('Failed to read plugin metadata for %s', key)
        db_error = True
    previous_active = bool(getattr(existing, 'is_active', False))
    desired_active = (
        bool(getattr(existing, 'desired_active', True)) if existing else bool(is_active)
    )
    # 没有持久化状态时默认拒绝：不得仅凭声明将插件报告为启用，也不得
    # 仅凭声明触发生命周期钩子。
    effective_active = desired_active and not errors and not db_error

    data = {
        'key': key,
        'name': name,
        'version': version,
        'description': description,
        'api_prefix': api_prefix,
        'menu_path': menu_path,
        'app_label': app_label,
        'dependencies': _as_lines(dependencies),
        'source': source,
        'validation_error': error_text,
        'desired_active': desired_active,
        'is_active': effective_active,
    }
    if db_error:
        return data

    persisted_fields = [f for f in _FIELDS if f != 'key']
    if not _supports_desired_active():
        persisted_fields = [f for f in persisted_fields if f != 'desired_active']
    try:
        obj = None
        for attempt in range(2):
            try:
                with transaction.atomic():
                    obj, _ = _db().update_or_create(
                        key=key,
                        defaults={field: data[field] for field in persisted_fields},
                    )
                break
            except IntegrityError:
                if attempt == 1:
                    raise
        data['id'] = obj.id
    except Exception:
        logger.exception('Failed to persist plugin metadata for %s', key)
        return data

    _PLUGINS[key] = data
    if effective_active and not previous_active:
        _call_hook(key, 'on_enable')
    elif previous_active and not effective_active:
        _call_hook(key, 'on_disable')
    return data


def unregister_plugin(key):
    if key in RESERVED_PLUGIN_KEYS:
        logger.warning('Refused to unregister reserved plugin key %s', key)
        return False
    data = _PLUGINS.get(key)
    was_active = bool(data and data.get('is_active')) or _was_active(key)
    try:
        deleted, _ = _db().filter(key=key).delete()
    except Exception:
        logger.exception('Failed to delete plugin record for %s', key)
        return False
    if not deleted:
        return False

    try:
        from .menu_registry import unregister_plugin_menus
        unregister_plugin_menus(key)
    except Exception:
        logger.exception('Failed to clean plugin menus for %s', key)

    _PLUGINS.pop(key, None)
    if was_active:
        _call_hook(key, 'on_disable')
    return True


def set_plugin_active(key, active):
    """先持久化用户意图，仅在状态切换成功后调用生命周期钩子。"""
    active = bool(active)
    supports_desired = _supports_desired_active()
    try:
        with transaction.atomic():
            record = _db().select_for_update().filter(key=key).first()
            if record is None:
                return False
            desired = bool(getattr(record, 'desired_active', True)) if supports_desired else True
            if active and record.validation_error:
                if supports_desired:
                    _db().filter(key=key).update(desired_active=True)
                if key in _PLUGINS:
                    _PLUGINS[key]['desired_active'] = True
                return False
            previous = bool(record.is_active)
            if previous == active and desired == active:
                return False
            values = {'is_active': active}
            if supports_desired:
                values['desired_active'] = active
            updated = _db().filter(key=key).update(**values)
            if not updated:
                return False
    except Exception:
        logger.exception('Failed to update active state for plugin %s', key)
        return False

    if key in _PLUGINS:
        _PLUGINS[key]['is_active'] = active
        _PLUGINS[key]['desired_active'] = active
    _call_hook(key, 'on_enable' if active else 'on_disable')
    return True


def register_plugin_menus(key, plugin_instance):
    """注册 PluginConfig 声明的菜单和按钮。"""
    if key in RESERVED_PLUGIN_KEYS:
        logger.warning('Refused to register menus for reserved plugin key %s', key)
        return
    menus = list(getattr(plugin_instance, 'plugin_menus', ()) or ())
    buttons = list(getattr(plugin_instance, 'plugin_buttons', ()) or ())
    if not menus and not buttons:
        return
    from .menu_registry import register_menus
    register_menus(
        menus_data=menus, buttons_data=buttons,
        skip_existing=True, plugin_key=key,
    )


def discover_entry_point_plugins():
    """发现已安装第三方包发布的插件。"""
    from importlib.metadata import entry_points

    try:
        eps = entry_points()
        candidates = (
            eps.select(group=ENTRY_POINT_GROUP)
            if hasattr(eps, 'select') else eps.get(ENTRY_POINT_GROUP, [])
        )
    except Exception:
        return []

    discovered = []
    for entry in candidates:
        try:
            cls = entry.load()
            if not isinstance(cls, type) or not hasattr(cls, 'get_plugin_metadata'):
                raise TypeError('entry point must point to a PluginConfig subclass')
            key = entry.name or cls.plugin_key or cls.label
            register_plugin_class(key, cls)
            instance = _plugin_instance(key)
            if instance is None:
                raise TypeError('cannot instantiate plugin config')
            metadata = instance.get_plugin_metadata()
            metadata['key'] = key
            metadata.pop('min_layuix_version', None)
            metadata['validation_errors'] = instance.validate_plugin()
            registered = register_plugin(source='entry_point', **metadata)
            if registered.get('is_active'):
                register_plugin_menus(key, instance)
            discovered.append(registered)
        except Exception:
            logger.exception('Failed to load plugin entry point %s', entry.name)
    return discovered


def list_plugins():
    """将持久化记录与进程内注册表合并。"""
    merged = {}
    persisted_keys = set()
    try:
        for row in _db().order_by('key').values(*_FIELDS):
            persisted_keys.add(row['key'])
            if row['is_active']:
                merged[row['key']] = dict(row)
    except Exception:
        pass

    for key, value in _PLUGINS.items():
        if key not in persisted_keys and value.get('is_active', True):
            merged[key] = dict(value)

    return [merged[key] for key in sorted(merged)]
