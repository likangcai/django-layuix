# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-26 22:19
# @FileName  : apps.py
# -----------------------------
import os
from django.apps import AppConfig

from .defaults import get_default_configs


_REGISTERED = False


class RbacConfig(AppConfig):
    name = 'django_layuix.rbac'
    label = 'django_layuix_rbac'
    verbose_name = 'Layui RBAC'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        global _REGISTERED
        if _REGISTERED:
            return
        _REGISTERED = True
        self._ensure_base_app_registered()
        self._register_template_dirs()
        self._register_api_urls()
        self._register_operation_log_middleware()
        self._register_rbac_session_middleware()
        self._register_api_origin_guard_middleware()
        from django.db.models.signals import post_migrate

        post_migrate.connect(
            self._on_post_migrate,
            sender=self,
            dispatch_uid='django_layuix.rbac.ensure_default_configs',
        )

    def _on_post_migrate(self, sender, **kwargs):
        self._ensure_default_configs()

    def _ensure_base_app_registered(self):
        """Ensure 'django_layuix' is in INSTALLED_APPS for templatetags and static files"""
        from django.conf import settings

        # 配置可能使用元组；修改前先归一化为可变列表。
        for attr in ('INSTALLED_APPS', 'MIDDLEWARE'):
            try:
                current = getattr(settings, attr)
                if not isinstance(current, list):
                    setattr(settings, attr, list(current or []))
            except Exception:
                pass

        if 'django_layuix' not in settings.INSTALLED_APPS:
            settings.INSTALLED_APPS.insert(0, 'django_layuix')

        # Only provide a Chinese default when Django's built-in default is still in place.
        # 已显式配置的语言（包括英文）保持不变。
        if getattr(settings, 'LANGUAGE_CODE', 'en-us') == 'en-us':
            settings.LANGUAGE_CODE = 'zh-hans'
        settings.USE_I18N = True

        # 修复 iframe/嵌入环境下的 CSRF Cookie
        # Keep Django's default cookie behavior for normal HTTP deployments.
        # 跨域 API 客户端应使用 Bearer Token，而不是会话 Cookie。
        if getattr(settings, 'CSRF_COOKIE_SAMESITE', 'Lax') != 'None':
            settings.CSRF_COOKIE_SAMESITE = None
        if getattr(settings, 'SESSION_COOKIE_SAMESITE', 'Lax') != 'None':
            settings.SESSION_COOKIE_SAMESITE = None

        # 确保已加载 LocaleMiddleware 以支持国际化
        locale_middleware = 'django.middleware.locale.LocaleMiddleware'
        if locale_middleware not in settings.MIDDLEWARE:
            # 插入到 SessionMiddleware 之后、CommonMiddleware 之前
            session_idx = None
            for i, m in enumerate(settings.MIDDLEWARE):
                if 'SessionMiddleware' in m:
                    session_idx = i
                    break
            if session_idx is not None:
                settings.MIDDLEWARE.insert(session_idx + 1, locale_middleware)
            else:
                settings.MIDDLEWARE.insert(0, locale_middleware)

        # 确保 CsrfViewMiddleware 位于 LocaleMiddleware 之后
        csrf_middleware = 'django.middleware.csrf.CsrfViewMiddleware'
        if csrf_middleware in settings.MIDDLEWARE:
            settings.MIDDLEWARE.remove(csrf_middleware)
            # 插入到 LocaleMiddleware 之后
            locale_idx = settings.MIDDLEWARE.index(locale_middleware) if locale_middleware in settings.MIDDLEWARE else 0
            settings.MIDDLEWARE.insert(locale_idx + 1, csrf_middleware)

        # 手动注册模板标签（已错过自动发现时机）
        self._register_templatetag_library('django_layuix.templatetags.layui_tags', 'layui_tags')

        # 手动注册静态文件查找器（已错过自动发现时机）
        self._register_static_files()

    def _register_templatetag_library(self, module_path, tag_name):
        """Manually register a templatetag library"""
        try:
            from django.template.backends.django import DjangoTemplates
            from django.template.library import import_library
            from django.template import engines as _engines
            for engine in _engines.all():
                if isinstance(engine, DjangoTemplates):
                    engine.engine.libraries[tag_name] = module_path
                    # 同时注册到 template_libraries（Django 初始化时会预加载）
                    if hasattr(engine.engine, 'template_libraries'):
                        engine.engine.template_libraries[tag_name] = import_library(module_path)
        except Exception:
            pass

    def _register_static_files(self):
        """Manually register django_layuix's static files directory"""
        try:
            import django_layuix
            base_dir = os.path.dirname(django_layuix.__file__)
            static_dir = os.path.join(base_dir, 'static')
            if not os.path.isdir(static_dir):
                return

            # 方式一：添加到 STATICFILES_DIRS
            from django.conf import settings
            staticfiles_dirs = list(getattr(settings, 'STATICFILES_DIRS', []))
            already_in_dirs = any(static_dir in d for d in staticfiles_dirs if isinstance(d, str))
            if not already_in_dirs:
                staticfiles_dirs.insert(0, static_dir)
                settings.STATICFILES_DIRS = staticfiles_dirs

            # 方式二：修补 AppDirectoriesFinder 实例
            from django.contrib.staticfiles.finders import get_finder
            finder = get_finder('django.contrib.staticfiles.finders.AppDirectoriesFinder')
            if hasattr(finder, 'storages') and 'django_layuix' not in finder.storages:
                from django.core.files.storage import FileSystemStorage
                finder.storages['django_layuix'] = FileSystemStorage(location=static_dir)
                finder.apps.append('django_layuix')
        except Exception:
            pass

    def _register_template_dirs(self):
        """Ensure django_layuix templates override Django admin templates"""
        from django.conf import settings

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        templates_dir = os.path.join(base_dir, 'templates')

        if not os.path.isdir(templates_dir):
            return

        # 添加到 TEMPLATES 的 DIRS 配置
        if settings.TEMPLATES:
            dirs = list(settings.TEMPLATES[0].get('DIRS', []))
            if templates_dir not in dirs:
                settings.TEMPLATES[0]['DIRS'] = dirs + [templates_dir]

        # 修补 engine.dirs，确保文件系统加载器使用本项目的模板目录
        try:
            from django.template import engines
            for engine in engines.all():
                if hasattr(engine, 'engine') and hasattr(engine.engine, 'dirs'):
                    engine_dirs = list(engine.engine.dirs)
                    if templates_dir not in engine_dirs:
                        engine.engine.dirs = [templates_dir] + engine_dirs
        except Exception:
            pass

    def _register_api_urls(self):
        """Register RBAC and Ops API URLs under Django admin"""
        from django.contrib.admin import site
        from django.urls import path, include
        from . import urls as rbac_urls

        original_get_urls = site.get_urls

        def patched_get_urls():
            urls = original_get_urls()
            custom_urls = [
                path('api/rbac/', include((rbac_urls.urlpatterns, 'rbac'))),
            ]
            try:
                from django_layuix.ops import urls as ops_urls
                custom_urls.append(
                    path('api/ops/', include((ops_urls.urlpatterns, 'ops')))
                )
            except (ImportError, ModuleNotFoundError):
                pass
            return custom_urls + urls

        site.get_urls = patched_get_urls

    def _register_operation_log_middleware(self):
        """Register OperationLogMiddleware into Django MIDDLEWARE list"""
        from django.conf import settings

        middleware_path = 'django_layuix.rbac.middleware.OperationLogMiddleware'
        if middleware_path not in settings.MIDDLEWARE:
            # 插入到最后一个中间件之后（列表末尾）
            settings.MIDDLEWARE.append(middleware_path)

    def _register_rbac_session_middleware(self):
        """Register RBAC session middleware after Django authentication."""
        from django.conf import settings

        middleware_path = 'django_layuix.rbac.middleware.RbacSessionMiddleware'
        if middleware_path not in settings.MIDDLEWARE:
            settings.MIDDLEWARE.append(middleware_path)

    def _register_api_origin_guard_middleware(self):
        from django.conf import settings

        middleware_path = 'django_layuix.rbac.middleware.ApiOriginGuardMiddleware'
        if middleware_path not in settings.MIDDLEWARE:
            settings.MIDDLEWARE.insert(0, middleware_path)

    def _ensure_default_configs(self):
        """Ensure default system configs exist in database"""
        try:
            from .models import SystemConfig
            # 首次迁移时先检查表是否存在，避免报错
            from django.db import connection
            table_exists = 'sys_config' in connection.introspection.table_names()
            if not table_exists:
                return
            
            default_configs = get_default_configs()
            existing_keys = set(SystemConfig.objects.values_list('key', flat=True))
            for cfg in default_configs:
                if cfg['key'] not in existing_keys:
                    SystemConfig.objects.create(**cfg)
        except Exception:
            pass


