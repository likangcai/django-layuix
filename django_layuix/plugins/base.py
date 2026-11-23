# -*- coding: utf-8 -*-
"""Base class for third-party django-layuix plugins."""
from django.apps import AppConfig


class PluginConfig(AppConfig):
    """Django AppConfig with plugin metadata, validation and lifecycle hooks."""

    plugin_key = None
    plugin_name = None
    plugin_version = '1.0.0'
    plugin_description = ''
    plugin_api_prefix = ''
    plugin_menu_path = ''
    plugin_dependencies = ()
    plugin_menus = ()
    plugin_buttons = ()
    min_layuix_version = None
    source = 'app'

    def get_plugin_metadata(self):
        return {
            'key': self.plugin_key or self.label,
            'name': self.plugin_name or self.verbose_name or self.label,
            'version': self.plugin_version,
            'description': self.plugin_description,
            'api_prefix': self.plugin_api_prefix,
            'menu_path': self.plugin_menu_path,
            'app_label': self.label,
            'dependencies': tuple(self.plugin_dependencies or ()),
            'min_layuix_version': self.min_layuix_version,
        }

    def validate_plugin(self):
        from django_layuix.rbac.plugins import validate_plugin_metadata
        return validate_plugin_metadata(self.get_plugin_metadata())

    def ready(self):
        super().ready()
        from django_layuix.rbac.plugins import register_plugin, register_plugin_class

        metadata = self.get_plugin_metadata()
        key = metadata.pop('key')
        metadata.pop('min_layuix_version', None)
        register_plugin_class(key, self.__class__)
        metadata['validation_errors'] = self.validate_plugin()
        registered = register_plugin(key=key, source=self.source, **metadata)

        if registered.get('is_active') and (self.plugin_menus or self.plugin_buttons):
            from django_layuix.rbac.menu_registry import register_menus
            register_menus(
                menus_data=list(self.plugin_menus),
                buttons_data=list(self.plugin_buttons),
                skip_existing=True,
                plugin_key=key,
            )

    def on_enable(self):
        """Called when the plugin becomes active. Override in subclasses."""

    def on_disable(self):
        """Called when the plugin is deactivated. Override in subclasses."""
