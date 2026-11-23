import os
from django.apps import AppConfig


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
        self._ensure_default_configs()

    def _ensure_base_app_registered(self):
        """Ensure 'django_layuix' is in INSTALLED_APPS for templatetags and static files"""
        from django.conf import settings

        if 'django_layuix' not in settings.INSTALLED_APPS:
            settings.INSTALLED_APPS.insert(0, 'django_layuix')

        # Set default language to Chinese if not configured
        if not getattr(settings, 'LANGUAGE_CODE', '').startswith('zh'):
            settings.LANGUAGE_CODE = 'zh-hans'
            settings.USE_I18N = True

        # Fix CSRF cookie for iframe/embedded environments
        if getattr(settings, 'CSRF_COOKIE_SAMESITE', 'Lax') != 'None':
            settings.CSRF_COOKIE_SAMESITE = None
        if getattr(settings, 'SESSION_COOKIE_SAMESITE', 'Lax') != 'None':
            settings.SESSION_COOKIE_SAMESITE = None

        # Ensure LocaleMiddleware is present for i18n support
        locale_middleware = 'django.middleware.locale.LocaleMiddleware'
        if locale_middleware not in settings.MIDDLEWARE:
            # Insert after SessionMiddleware, before CommonMiddleware
            session_idx = None
            for i, m in enumerate(settings.MIDDLEWARE):
                if 'SessionMiddleware' in m:
                    session_idx = i
                    break
            if session_idx is not None:
                settings.MIDDLEWARE.insert(session_idx + 1, locale_middleware)
            else:
                settings.MIDDLEWARE.insert(0, locale_middleware)

        # Ensure CsrfViewMiddleware is after LocaleMiddleware
        csrf_middleware = 'django.middleware.csrf.CsrfViewMiddleware'
        if csrf_middleware in settings.MIDDLEWARE:
            settings.MIDDLEWARE.remove(csrf_middleware)
            # Insert after LocaleMiddleware
            locale_idx = settings.MIDDLEWARE.index(locale_middleware) if locale_middleware in settings.MIDDLEWARE else 0
            settings.MIDDLEWARE.insert(locale_idx + 1, csrf_middleware)

        # Manually register templatetags (too late for auto-discovery)
        self._register_templatetag_library('django_layuix.templatetags.layui_tags', 'layui_tags')

        # Manually register static files finder (too late for auto-discovery)
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
                    # Also register in template_libraries (Django pre-loads these at init)
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

            # Method 1: Add to STATICFILES_DIRS
            from django.conf import settings
            staticfiles_dirs = list(getattr(settings, 'STATICFILES_DIRS', []))
            already_in_dirs = any(static_dir in d for d in staticfiles_dirs if isinstance(d, str))
            if not already_in_dirs:
                staticfiles_dirs.insert(0, static_dir)
                settings.STATICFILES_DIRS = staticfiles_dirs

            # Method 2: Patch AppDirectoriesFinder instances
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

        # Add to TEMPLATES DIRS setting
        if settings.TEMPLATES:
            dirs = list(settings.TEMPLATES[0].get('DIRS', []))
            if templates_dir not in dirs:
                settings.TEMPLATES[0]['DIRS'] = dirs + [templates_dir]

        # Patch engine.dirs to ensure filesystem loader uses our templates dir
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
            # Insert after the last middleware (at the end of the list)
            settings.MIDDLEWARE.append(middleware_path)

    def _register_rbac_session_middleware(self):
        """Register RBAC session middleware after Django authentication."""
        from django.conf import settings

        middleware_path = 'django_layuix.rbac.middleware.RbacSessionMiddleware'
        if middleware_path not in settings.MIDDLEWARE:
            settings.MIDDLEWARE.append(middleware_path)

    def _ensure_default_configs(self):
        """Ensure default system configs exist in database"""
        try:
            from .models import SystemConfig
            # Check if table exists first to avoid errors during initial migrations
            from django.db import connection
            table_exists = 'sys_config' in connection.introspection.table_names()
            if not table_exists:
                return
            
            default_configs = [
                {'key': 'system_name', 'value': 'Django Layuix Admin', 'description': '系统名称', 'config_type': 'string', 'sort': 1},
                {'key': 'system_version', 'value': '1.0.0', 'description': '系统版本号', 'config_type': 'string', 'sort': 2},
                {'key': 'system_description', 'value': '', 'description': '系统描述（显示在管理后台底部）', 'config_type': 'text', 'sort': 3},
                {'key': 'logo_icon', 'value': 'layui-icon-code-circle', 'description': 'Logo图标（layui-icon类名）', 'config_type': 'string', 'sort': 4},
                {'key': 'logo_url', 'value': '', 'description': 'Logo图片URL（优先于图标）', 'config_type': 'image', 'sort': 5},
                {'key': 'favicon_url', 'value': '', 'description': '网站图标URL', 'config_type': 'image', 'sort': 6},
                {'key': 'copyright', 'value': 'Yingzi © 2026 Django Layuix Admin', 'description': '版权信息', 'config_type': 'string', 'sort': 7},
                {'key': 'frontend_url', 'value': '', 'description': '前端项目地址', 'config_type': 'string', 'sort': 8},
                {'key': 'login_bg_type', 'value': 'gradient', 'description': '登录页背景类型：gradient(渐变)/color(纯色)/image(图片)', 'config_type': 'string', 'sort': 9},
                {'key': 'login_bg_value', 'value': 'linear-gradient(135deg, #2d3a4b 0%, #1a1a2e 100%)', 'description': '登录页背景渐变/颜色值', 'config_type': 'color', 'sort': 10},
                {'key': 'login_bg_image', 'value': '', 'description': '登录页背景图片URL（当login_bg_type为image时生效）', 'config_type': 'image', 'sort': 11},
                {'key': 'rbac_max_roles_per_user', 'value': '0', 'description': 'RBAC2：每个用户最多可分配角色数，0表示不限', 'config_type': 'integer', 'sort': 12},
                {'key': 'rbac_prerequisite_strategy', 'value': 'auto_grant', 'description': 'RBAC4：前置角色策略 auto_grant/reject', 'config_type': 'string', 'sort': 13},
                {'key': 'rbac_dsd_strategy', 'value': 'greedy', 'description': 'RBAC4：DSD 激活策略 greedy/explicit', 'config_type': 'string', 'sort': 14},
            ]
            existing_keys = set(SystemConfig.objects.values_list('key', flat=True))
            for cfg in default_configs:
                if cfg['key'] not in existing_keys:
                    SystemConfig.objects.create(**cfg)
        except Exception:
            pass


