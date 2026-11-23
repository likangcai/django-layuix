# -*- coding: utf-8 -*-
"""Third-party plugin registry: discovery, validation, persistence and hooks."""
import importlib
import logging
import os
import re

from django.conf import settings

logger = logging.getLogger(__name__)

ENTRY_POINT_GROUP = 'django_layuix.plugins'
_PLUGINS = {}
_PLUGIN_CLASSES = {}

_FIELDS = (
    'key', 'name', 'version', 'description',
    'api_prefix', 'menu_path', 'app_label',
    'dependencies', 'source', 'validation_error', 'is_active',
)

_SPEC_RE = re.compile(r'^([A-Za-z0-9_.-]+)\s*(>=|==|<=|>|<)?\s*([0-9][0-9A-Za-z.\-]*)?$')


def _db():
    from .models import PluginRegistry
    return PluginRegistry.objects


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
    """Return a list of human-readable validation errors."""
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


def register_plugin(key, name, version='1.0.0', description='',
                    api_prefix='', menu_path='', app_label='',
                    dependencies=(), is_active=True, source='app',
                    validation_error='', validation_errors=None):
    """Register or update plugin metadata. Safe to call from AppConfig.ready()."""
    errors = list(validation_errors or [])
    if validation_error:
        errors.append(validation_error)
    error_text = '\n'.join(errors)

    existing = None
    try:
        existing = _db().filter(key=key).first()
    except Exception:
        pass
    previous_active = bool(getattr(existing, 'is_active', False))

    # A persisted deactivation must survive restarts; validation failures always disable.
    desired_active = (previous_active if existing else bool(is_active)) and not errors

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
        'is_active': desired_active,
    }
    _PLUGINS[key] = data

    try:
        obj, _ = _db().update_or_create(
            key=key,
            defaults={field: data[field] for field in _FIELDS if field != 'key'},
        )
        data['id'] = obj.id
    except Exception:
        logger.exception('Failed to persist plugin metadata for %s', key)

    if desired_active and not previous_active:
        _call_hook(key, 'on_enable')
    elif previous_active and not desired_active:
        _call_hook(key, 'on_disable')
    return data


def unregister_plugin(key):
    data = _PLUGINS.pop(key, None)
    if data and data.get('is_active', True):
        _call_hook(key, 'on_disable')
    try:
        _db().filter(key=key).delete()
    except Exception:
        pass


def set_plugin_active(key, active):
    """Enable/disable a plugin and invoke its lifecycle hook on transition."""
    previous = _was_active(key)
    if previous == bool(active):
        return False
    try:
        record = _db().filter(key=key).first()
        if active and record and record.validation_error:
            return False
        _db().filter(key=key).update(is_active=bool(active))
    except Exception:
        logger.exception('Failed to update active state for plugin %s', key)
    if key in _PLUGINS:
        _PLUGINS[key]['is_active'] = bool(active)
    _call_hook(key, 'on_enable' if active else 'on_disable')
    return True


def register_plugin_menus(key, plugin_instance):
    """Register menus and buttons declared by a PluginConfig."""
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
    """Discover plugins published by installed third-party packages."""
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
    """Merge persisted records with the in-process registry."""
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
