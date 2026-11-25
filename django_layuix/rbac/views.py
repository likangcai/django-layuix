# -*- coding: utf-8 -*-
"""
RBAC API Views - User info, menu data, system info, profile management
"""
import json
import os
import platform
import socket
from functools import wraps
from datetime import datetime
import time

import django_layuix
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.contrib.auth import update_session_auth_hash
from django.utils.timezone import localtime
from .permissions import (
    api_permission_by_method, api_permission_required, resolve_api_user,
)


def fmt_time(dt, format_str='%Y-%m-%d %H:%M:%S'):
    """将 timezone-aware datetime 转为当前时区后格式化"""
    if dt is None:
        return ''
    return localtime(dt).strftime(format_str)


def api_login_required(view_func):
    """API 登录校验：Session 与 Bearer Token 双通道。"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = resolve_api_user(request)
        if user is None or not getattr(user, 'is_authenticated', False):
            return JsonResponse({'code': 401, 'msg': '未登录'}, status=401)
        request.user = user
        return view_func(request, *args, **kwargs)
    return wrapper


def get_request_body(request):
    """Get parsed request body - supports JSON and form data for all HTTP methods"""
    try:
        if request.content_type == 'application/json':
            return json.loads(request.body)
        # For form data (application/x-www-form-urlencoded), try POST first, then parse body for PUT/PATCH
        if request.POST:
            return dict(request.POST)
        # Try to parse form data from body for PUT/PATCH requests
        if request.body:
            from urllib.parse import parse_qs
            data = parse_qs(request.body.decode('utf-8'))
            # parse_qs returns lists, convert single-item lists to values
            return {k: v[0] if len(v) == 1 else v for k, v in data.items()}
        return {}
    except (json.JSONDecodeError, ValueError, TypeError, UnicodeDecodeError):
        return {}


def success_response(data=None, msg='success'):
    return JsonResponse({'code': 200, 'msg': msg, 'data': data})


def error_response(msg='error', code=400):
    return JsonResponse({'code': code, 'msg': msg}, status=code)


def _get_user_model():
    """Get the user model"""
    from django.contrib.auth import get_user_model
    return get_user_model()


def _build_menu_tree(menus, parent_id=None):
    """Build menu tree from flat menu list"""
    tree = []
    for menu in menus:
        parent_val = menu.get('parent_id') or menu.get('parent')
        if parent_val == parent_id or (parent_val is None and parent_id is None):
            children = _build_menu_tree(menus, menu['id'])
            item = dict(menu)
            if children:
                item['children'] = children
            tree.append(item)
    return tree


@csrf_exempt
@api_login_required
def user_info(request):
    """Get current user info with menus"""
    User = _get_user_model()
    try:
        user = User.objects.get(pk=request.user.pk)
    except Exception:
        user = request.user

    # Build user data
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip

    user_data = {
        'id': user.id,
        'username': user.username,
        'nickname': getattr(user, 'nickname', '') or user.username,
        'phone': getattr(user, 'phone', ''),
        'avatar': getattr(user, 'avatar_url', ''),
        'email': getattr(user, 'email', ''),
        'is_superuser': user.is_superuser,
        'is_active': user.is_active,
        'theme': getattr(user, 'theme', '默认深色'),
        'language': getattr(user, 'language', 'zh-hans'),
        'ip': get_client_ip(request),
    }

    # Get roles
    roles = []
    if hasattr(user, 'roles'):
        roles = [{'id': r.id, 'name': r.name, 'code': r.code, 'description': r.description or ''} for r in user.roles.filter(status=True)]
    user_data['roles'] = roles

    # Get menus based on permissions
    menus = _get_user_menus(user)
    user_data['menus'] = menus

    # Get permissions count
    user_data['permissions'] = _get_user_permissions(user)

    return success_response(user_data)


def _get_user_menus(user):
    """Get menus available to the user (后台侧边栏使用,只返回 backend_visible=True 的菜单)"""
    from .engine import visible_menu_queryset

    # Get user's language preference
    user_lang = getattr(user, 'language', 'zh-hans') if hasattr(user, 'language') else 'zh-hans'

    menus = visible_menu_queryset(user, 'backend').order_by('sort', 'id')

    menu_list = []
    for m in menus:
        # Use localized menu name based on user's language
        menu_name = m.get_name_by_lang(user_lang)
        
        menu_list.append({
            'id': m.id,
            'parent_id': m.parent_id,
            'name': menu_name,
            'name_zh_hans': m.name_zh_hans,
            'name_en': m.name_en,
            'icon': m.icon,
            'path': m.path,
            'component': m.component,
            'menu_type': m.menu_type,
            'permission': m.permission,
            'sort': m.sort,
            'visible': m.visible,
            'backend_visible': m.backend_visible,
            'frontend_visible': m.frontend_visible,
        })

    return _build_menu_tree(menu_list)


def _get_frontend_menus(user):
    """Get menus available to the user (前台使用,只返回 frontend_visible=True 的菜单)"""
    from .engine import visible_menu_queryset

    # Get user's language preference
    user_lang = getattr(user, 'language', 'zh-hans') if hasattr(user, 'language') else 'zh-hans'

    menus = visible_menu_queryset(user, 'frontend').order_by('sort', 'id')

    menu_list = []
    for m in menus:
        # Use localized menu name based on user's language
        menu_name = m.get_name_by_lang(user_lang)
        
        menu_list.append({
            'id': m.id,
            'parent_id': m.parent_id,
            'name': menu_name,
            'name_zh_hans': m.name_zh_hans,
            'name_en': m.name_en,
            'icon': m.icon,
            'path': m.path,
            'component': m.component,
            'menu_type': m.menu_type,
            'permission': m.permission,
            'sort': m.sort,
            'visible': m.visible,
            'backend_visible': m.backend_visible,
            'frontend_visible': m.frontend_visible,
        })

    return _build_menu_tree(menu_list)


def _get_user_permissions(user):
    """Get user permission strings (inheritance and active roles included)."""
    from .engine import get_effective_permissions
    return list(get_effective_permissions(user))


@csrf_exempt
@api_login_required
@api_permission_required('config:view')
def system_info(request):
    """Get system information including CPU, memory, disk, network"""
    import psutil
    data = {
        'python_version': platform.python_version(),
        'django_version': _get_django_version(),
        'system': platform.system(),
        'system_release': platform.release(),
        'system_version': platform.version(),
        'architecture': platform.machine(),
        'processor': platform.processor() or 'N/A',
        'hostname': socket.gethostname(),
        'server_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }

    # CPU info
    try:
        data['cpu_count'] = psutil.cpu_count(logical=True)
        data['cpu_count_physical'] = psutil.cpu_count(logical=False)
        data['cpu_percent'] = psutil.cpu_percent(interval=0.5)
        data['cpu_percent_per_core'] = psutil.cpu_percent(interval=0.5, percpu=True)
    except Exception:
        data['cpu_count'] = 0
        data['cpu_percent'] = 0

    # Memory info
    try:
        mem = psutil.virtual_memory()
        data['memory'] = {
            'total': mem.total,
            'used': mem.used,
            'free': mem.free,
            'available': mem.available,
            'percent': mem.percent,
            'total_human': _bytes_to_human(mem.total),
            'used_human': _bytes_to_human(mem.used),
            'available_human': _bytes_to_human(mem.available),
        }
    except Exception:
        data['memory'] = {}

    # Disk info - aggregate all physical partitions
    try:
        total_disk = used_disk = free_disk = 0
        if platform.system() == 'Windows':
            # Windows: iterate all physical drives (C:, D:, etc.)
            for part in psutil.disk_partitions():
                if 'cdrom' in part.opts.lower() or part.fstype == '':
                    continue
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    total_disk += usage.total
                    used_disk += usage.used
                    free_disk += usage.free
                except (PermissionError, OSError):
                    continue
        else:
            # Linux/Mac: iterate all non-virtual partitions
            for part in psutil.disk_partitions():
                # Skip virtual/loop filesystems
                if part.fstype in ('tmpfs', 'devtmpfs', 'overlay', 'proc', 'sysfs',
                                   'cgroup', 'cgroup2', 'devpts', 'mqueue', 'hugetlbfs',
                                   'nfs', 'nfs4', 'squashfs', 'iso9660', 'fuseblk'):
                    continue
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    total_disk += usage.total
                    used_disk += usage.used
                    free_disk += usage.free
                except (PermissionError, OSError):
                    continue

        if total_disk > 0:
            data['disk'] = {
                'total': total_disk,
                'used': used_disk,
                'free': free_disk,
                'percent': round(used_disk / total_disk * 100, 2),
                'total_human': _bytes_to_human(total_disk),
                'used_human': _bytes_to_human(used_disk),
                'free_human': _bytes_to_human(free_disk),
            }
        else:
            # Fallback: directly check root partition (Docker/container environments)
            try:
                disk = psutil.disk_usage('/')
                data['disk'] = {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': round(disk.used / disk.total * 100, 2),
                    'total_human': _bytes_to_human(disk.total),
                    'used_human': _bytes_to_human(disk.used),
                    'free_human': _bytes_to_human(disk.free),
                }
            except Exception:
                data['disk'] = {}
    except Exception:
        data['disk'] = {}

    # Network info
    try:
        net = psutil.net_io_counters()
        data['network'] = {
            'bytes_sent': net.bytes_sent,
            'bytes_recv': net.bytes_recv,
            'packets_sent': net.packets_sent,
            'packets_recv': net.packets_recv,
            'bytes_sent_human': _bytes_to_human(net.bytes_sent),
            'bytes_recv_human': _bytes_to_human(net.bytes_recv),
        }
    except Exception:
        data['network'] = {}

    # Database info
    try:
        data['database'] = _get_db_info()
    except Exception:
        data['database'] = {}

    return success_response(data)


@csrf_exempt
def system_info_stream(request):
    """
    SSE (Server-Sent Events) 流式推送系统信息
    支持Token认证和Session认证
    
    推送频率：每3秒一次（平衡实时性和服务器性能）
    最大推送次数：300次（约15分钟，之后客户端会自动重连）
    
    注意: Django开发服务器使用WSGI，可能不支持真正的流式推送。
    在生产环境中建议使用 ASGI (Daphne/Uvicorn) 或 Nginx 代理。
    """
    import psutil
    from .token_auth import token_authenticate
    
    # Token认证或Session认证
    user = token_authenticate(request)
    if not user:
        user = request.user
    
    if not user or not user.is_authenticated:
        return error_response('未登录', 401)
    from .permissions import has_permission
    if not has_permission(user, 'config:view', request):
        return error_response('无权限', 403)

    def event_stream():
        """生成SSE事件流"""
        try:
            # 发送初始连接消息
            yield f": connected\n\n"
            
            count = 0
            max_iterations = 300  # 最多推送300次（约5分钟），避免长时间占用
            
            while count < max_iterations:
                # 获取系统信息
                data = {
                    'python_version': platform.python_version(),
                    'django_version': _get_django_version(),
                    'system': platform.system(),
                    'system_release': platform.release(),
                    'architecture': platform.machine(),
                    'hostname': socket.gethostname(),
                    'server_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                }
                
                # CPU
                try:
                    data['cpu_count'] = psutil.cpu_count(logical=True)
                    data['cpu_percent'] = psutil.cpu_percent(interval=0.3)
                except Exception:
                    data['cpu_percent'] = 0
                
                # 内存
                try:
                    mem = psutil.virtual_memory()
                    data['memory'] = {
                        'total': mem.total,
                        'used': mem.used,
                        'free': mem.free,
                        'available': mem.available,
                        'percent': mem.percent,
                        'total_human': _bytes_to_human(mem.total),
                        'used_human': _bytes_to_human(mem.used),
                        'available_human': _bytes_to_human(mem.available),
                    }
                except Exception:
                    data['memory'] = {}
                
                # 磁盘
                try:
                    total_disk = used_disk = free_disk = 0
                    if platform.system() == 'Windows':
                        for part in psutil.disk_partitions():
                            if 'cdrom' in part.opts.lower() or part.fstype == '':
                                continue
                            try:
                                usage = psutil.disk_usage(part.mountpoint)
                                total_disk += usage.total
                                used_disk += usage.used
                                free_disk += usage.free
                            except (PermissionError, OSError):
                                continue
                    else:
                        for part in psutil.disk_partitions():
                            if part.fstype in ('tmpfs', 'devtmpfs', 'overlay', 'proc', 'sysfs',
                                               'cgroup', 'cgroup2', 'devpts', 'mqueue', 'hugetlbfs',
                                               'nfs', 'nfs4', 'squashfs', 'iso9660', 'fuseblk'):
                                continue
                            try:
                                usage = psutil.disk_usage(part.mountpoint)
                                total_disk += usage.total
                                used_disk += usage.used
                                free_disk += usage.free
                            except (PermissionError, OSError):
                                continue
                    
                    if total_disk > 0:
                        data['disk'] = {
                            'total': total_disk,
                            'used': used_disk,
                            'free': free_disk,
                            'percent': round(used_disk / total_disk * 100, 2),
                            'total_human': _bytes_to_human(total_disk),
                            'used_human': _bytes_to_human(used_disk),
                            'free_human': _bytes_to_human(free_disk),
                        }
                    else:
                        try:
                            disk = psutil.disk_usage('/')
                            data['disk'] = {
                                'total': disk.total,
                                'used': disk.used,
                                'free': disk.free,
                                'percent': round(disk.used / disk.total * 100, 2),
                                'total_human': _bytes_to_human(disk.total),
                                'used_human': _bytes_to_human(disk.used),
                                'free_human': _bytes_to_human(disk.free),
                            }
                        except Exception:
                            data['disk'] = {}
                except Exception:
                    data['disk'] = {}
                
                # 网络
                try:
                    net = psutil.net_io_counters()
                    data['network'] = {
                        'bytes_sent': net.bytes_sent,
                        'bytes_recv': net.bytes_recv,
                        'packets_sent': net.packets_sent,
                        'packets_recv': net.packets_recv,
                        'bytes_sent_human': _bytes_to_human(net.bytes_sent),
                        'bytes_recv_human': _bytes_to_human(net.bytes_recv),
                    }
                except Exception:
                    data['network'] = {}
                
                # 发送SSE事件
                try:
                    yield f"data: {json.dumps({'code': 200, 'data': data})}\n\n"
                except Exception:
                    # 客户端断开连接
                    break
                
                count += 1
                # 每3秒推送一次数据（降低服务器压力）
                time.sleep(3)
                
        except GeneratorExit:
            # 客户端断开连接
            pass
        except Exception as e:
            # 发生错误时也发送错误信息
            try:
                yield f"data: {json.dumps({'code': 500, 'msg': str(e)})}\n\n"
            except Exception:
                pass
    
    # 返回SSE响应
    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream',
    )
    # 设置SSE相关的响应头
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'  # Nginx禁用缓冲
    
    return response


def _get_django_version():
    """Get Django version"""
    import django
    return django.get_version()


def _bytes_to_human(n):
    """Convert bytes to human readable format (1TB=1024GB)"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(n) < 1024.0:
            return f"{n:.2f} {unit}"
        n /= 1024.0
    return f"{n:.2f} PB"


def _get_db_info():
    """Get database information"""
    from django.db import connections

    db_info = {}
    db_settings = getattr(settings, 'DATABASES', {}).get('default', {})
    engine = db_settings.get('ENGINE', '')

    if 'sqlite' in engine:
        db_info['engine'] = 'SQLite'
        db_name = db_settings.get('NAME', '')
        if db_name and os.path.exists(db_name):
            db_info['size'] = _bytes_to_human(os.path.getsize(db_name))
        # Get table count
        try:
            with connections['default'].cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                db_info['table_count'] = cursor.fetchone()[0]
        except Exception:
            pass
    elif 'postgresql' in engine:
        db_info['engine'] = 'PostgreSQL'
        try:
            with connections['default'].cursor() as cursor:
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                db_info['version'] = version.split(',')[0] if version else ''
                cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'")
                db_info['table_count'] = cursor.fetchone()[0]
        except Exception:
            pass
    elif 'mysql' in engine:
        db_info['engine'] = 'MySQL'
        try:
            with connections['default'].cursor() as cursor:
                cursor.execute("SELECT VERSION()")
                db_info['version'] = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE()")
                db_info['table_count'] = cursor.fetchone()[0]
        except Exception:
            pass
    else:
        db_info['engine'] = engine.split('.')[-1].replace('Backend', '')

    return db_info


@csrf_exempt
def public_config(request):
    """Get public system configuration (no auth required) - for login page etc."""
    from .models import SystemConfig

    db_configs = {}
    try:
        for sc in SystemConfig.objects.all():
            db_configs[sc.key] = sc.value
    except Exception:
        pass

    settings_config = getattr(settings, 'LAYUI_CONFIG', {})

    def get_config(key, default=''):
        if key in db_configs:
            return db_configs[key]
        return settings_config.get(key, default)

    return success_response({
        'system_name': get_config('system_name', 'Django Layuix Admin'),
        'system_version': get_config('system_version', django_layuix.__version__),
        'logo_icon': get_config('logo_icon', 'layui-icon-code-circle'),
        'logo_url': get_config('logo_url', ''),
        'favicon_url': get_config('favicon_url', ''),
        'copyright': get_config('copyright', ''),
        'login_bg_type': get_config('login_bg_type', 'gradient'),
        'login_bg_value': get_config('login_bg_value', 'linear-gradient(135deg, #2d3a4b 0%, #1a1a2e 100%)'),
        'login_bg_image': get_config('login_bg_image', ''),
    })


@csrf_exempt
@api_login_required
def system_config(request):
    """Get system configuration - database first, settings as fallback"""
    from .models import SystemConfig

    # 从 settings 获取默认值
    settings_config = getattr(settings, 'LAYUI_CONFIG', {})

    # 从数据库获取配置，合并到默认值上（数据库优先）
    db_configs = {}
    try:
        for sc in SystemConfig.objects.all():
            db_configs[sc.key] = sc.value
    except Exception:
        pass  # 数据库表可能还不存在

    def get_config(key, default=''):
        """优先取数据库值，其次取 settings 值，最后用默认值"""
        if key in db_configs:
            return db_configs[key]
        return settings_config.get(key, default)

    return success_response({
        'system_name': get_config('system_name', 'Django Layuix Admin'),
        'system_version': get_config('system_version', django_layuix.__version__),
        'system_description': get_config('system_description', ''),
        'logo_icon': get_config('logo_icon', 'layui-icon-code-circle'),
        'logo_url': get_config('logo_url', ''),
        'favicon_url': get_config('favicon_url', ''),
        'frontend_url': get_config('frontend_url', ''),
        'copyright': get_config('copyright', ''),
    })


@csrf_exempt
@api_login_required
def profile_update(request):
    """Update user profile"""
    if request.method != 'PUT':
        return error_response('Method not allowed', 405)

    User = _get_user_model()
    body = get_request_body(request)

    user = request.user
    if hasattr(user, 'nickname'):
        if 'nickname' in body:
            user.nickname = body['nickname']
    if hasattr(user, 'phone'):
        if 'phone' in body:
            user.phone = body['phone']

    user.save()
    return success_response(msg='保存成功')


@csrf_exempt
@api_login_required
def profile_password(request):
    """Change user password"""
    if request.method != 'PUT':
        return error_response('Method not allowed', 405)

    body = get_request_body(request)
    old_password = body.get('old_password', '')
    new_password = body.get('new_password', '')
    confirm_password = body.get('confirm_password', '')

    if not old_password or not new_password or not confirm_password:
        return error_response('请填写完整密码信息', 400)
    if len(new_password) < 6:
        return error_response('新密码长度不能少于6位', 400)
    if new_password != confirm_password:
        return error_response('两次密码不一致', 400)

    user = request.user
    if not user.check_password(old_password):
        return error_response('原密码错误', 400)

    user.set_password(new_password)
    user.save()
    # 注意：不调用 update_session_auth_hash，让 session 失效，强制重新登录
    return success_response(msg='密码修改成功')


@csrf_exempt
@api_login_required
def profile_theme(request):
    """Update user theme preference - supports both new format ('dark'/'light') and legacy Chinese theme names"""
    if request.method != 'PUT':
        return error_response('Method not allowed', 405)

    body = get_request_body(request)
    raw_theme = body.get('theme', 'dark')

    from .themes import normalize_theme, get_all_themes
    theme = normalize_theme(raw_theme)

    user = request.user
    if hasattr(user, 'theme'):
        user.theme = theme
        user.save(update_fields=['theme'])

    return success_response(msg='主题已切换')


@csrf_exempt
@api_login_required
def available_themes(request):
    """GET /api/rbac/available-themes/ - Get available themes (dark/light only)"""
    from .themes import get_all_themes

    themes = get_all_themes()
    data = [{'name': t['name'], 'file': t['file']} for t in themes]

    return success_response(data)


@csrf_exempt
@api_login_required
def set_language(request):
    """Set user language preference"""
    if request.method != 'POST':
        return error_response('Method not allowed', 405)

    body = get_request_body(request)
    language = body.get('language', 'zh-hans')

    if language not in ('zh-hans', 'en'):
        return error_response('不支持的语言', 400)

    user = request.user
    if hasattr(user, 'language'):
        user.language = language
        user.save(update_fields=['language'])

    # Django <=5 使用 session 键；Django 6 起 LocaleMiddleware 只读取语言 Cookie
    request.session['_language'] = language
    response = success_response({'language': language}, msg='语言已切换')
    response.set_cookie(
        settings.LANGUAGE_COOKIE_NAME,
        language,
        max_age=settings.LANGUAGE_COOKIE_AGE,
        path=settings.LANGUAGE_COOKIE_PATH,
        domain=getattr(settings, 'LANGUAGE_COOKIE_DOMAIN', None),
        samesite=getattr(settings, 'LANGUAGE_COOKIE_SAMESITE', None),
        secure=getattr(settings, 'LANGUAGE_COOKIE_SECURE', False),
        httponly=getattr(settings, 'LANGUAGE_COOKIE_HTTPONLY', False),
    )
    return response


@csrf_exempt
def register(request):
    """POST /api/rbac/register/ - 用户注册（默认关闭）"""
    if request.method != 'POST':
        return error_response('Method not allowed', 405)
    if not getattr(settings, 'LAYUI_ALLOW_REGISTRATION', False):
        return error_response('注册功能未开放', 403)

    User = _get_user_model()
    body = get_request_body(request)

    username = body.get('username', '').strip()
    password = body.get('password', '')
    email = body.get('email', '').strip()

    if not username:
        return error_response('用户名不能为空', 400)
    if username.lower() in {'admin', 'root', 'superuser'}:
        return error_response('该用户名为系统保留名称', 400)
    if not password:
        return error_response('密码不能为空', 400)
    if len(password) < 6:
        return error_response('密码长度不能少于6位', 400)
    if User.objects.filter(username=username).exists():
        return error_response('用户名已存在', 400)

    user = User.objects.create_user(
        username=username,
        password=password,
        email=email,
        is_active=True,
        is_staff=False,
        is_superuser=False
    )

    # 自动绑定注册用户角色
    from .models import Role
    try:
        registered_role = Role.objects.get(code='registered')
        user.roles.add(registered_role)
    except Role.DoesNotExist:
        pass

    return success_response(msg='注册成功')


@csrf_exempt
def api_login(request):
    """API login - 支持Session和Token双认证"""
    from django.contrib.auth import authenticate, login as django_login
    from .token_auth import generate_token
    
    body = get_request_body(request)
    username = body.get('username', '').strip()
    password = body.get('password', '')
    next_url = body.get('next', '/admin/')

    if not username or not password:
        return error_response('请输入用户名和密码', 400)

    user = authenticate(request, username=username, password=password)
    if user is None:
        return error_response('用户名或密码错误', 401)

    if not user.is_active:
        return error_response('用户已被禁用', 403)

    # Django Session登录（保持兼容）
    django_login(request, user)
    
    # 生成Token（用于SSE等场景）
    token = generate_token(user)
    
    return success_response(
        msg='登录成功', 
        data={
            'next': next_url,
            'token': token,  # 新增token
            'user': {
                'id': user.id,
                'username': user.username,
                'nickname': user.nickname if hasattr(user, 'nickname') else '',
            }
        }
    )


@csrf_exempt
@api_login_required
def logout(request):
    """AJAX logout - clear session and return success"""
    from django.contrib.auth import logout as django_logout
    django_logout(request)
    return success_response(msg='已退出登录')


@csrf_exempt
@api_login_required
@api_permission_required('dashboard:view')
def stats_data(request):
    """Get statistics data for dashboard"""
    from .models import Menu, Role, OperationLog

    User = _get_user_model()

    data = {
        'user_count': User.objects.count(),
        'role_count': Role.objects.count(),
        'menu_count': Menu.objects.filter(menu_type__in=[1, 2]).count(),
        'log_count': OperationLog.objects.count(),
    }

    return success_response(data)


# ==================== Menu CRUD ====================

@csrf_exempt
@api_login_required
@api_permission_required('menu:view')
def menu_tree(request):
    """GET /api/rbac/menus/tree/ - 获取所有菜单树（管理用，包含所有菜单）"""
    from .models import Menu

    menus = Menu.objects.all().order_by('sort', 'id')
    menu_list = []
    for m in menus:
        menu_list.append({
            'id': m.id,
            'parent_id': m.parent_id,
            'name': m.name,
            'name_en': m.name_en,
            'name_zh_hans': m.name_zh_hans,
            'icon': m.icon,
            'path': m.path,
            'component': m.component,
            'menu_type': m.menu_type,
            'menu_type_display': m.get_menu_type_display(),
            'permission': m.permission,
            'sort': m.sort,
            'visible': m.visible,
            'status': m.status,
            'backend_visible': m.backend_visible,
            'frontend_visible': m.frontend_visible,
            'create_time': fmt_time(m.create_time),
            'update_time': fmt_time(m.update_time),
        })

    tree = _build_menu_tree(menu_list)
    return success_response(tree)


@csrf_exempt
@api_login_required
def frontend_menu_tree(request):
    """GET /api/rbac/menus/frontend/ - 获取前台菜单树（只返回 frontend_visible=True 的菜单）"""
    menus = _get_frontend_menus(request.user)
    return success_response(menus)


@csrf_exempt
@api_login_required
@api_permission_required('menu:view')
def menu_detail(request, pk):
    """GET/PUT/DELETE /api/rbac/menus/<id>/ - 菜单详情/更新/删除"""
    from .models import Menu

    try:
        menu = Menu.objects.get(pk=pk)
    except Menu.DoesNotExist:
        return error_response('菜单不存在', 404)

    if request.method == 'GET':
        data = {
            'id': menu.id,
            'parent_id': menu.parent_id,
            'name': menu.name,
            'name_en': menu.name_en,
            'name_zh_hans': menu.name_zh_hans,
            'icon': menu.icon,
            'path': menu.path,
            'component': menu.component,
            'menu_type': menu.menu_type,
            'menu_type_display': menu.get_menu_type_display(),
            'permission': menu.permission,
            'sort': menu.sort,
            'visible': menu.visible,
            'status': menu.status,
            'backend_visible': menu.backend_visible,
            'frontend_visible': menu.frontend_visible,
            'create_time': fmt_time(menu.create_time),
            'update_time': fmt_time(menu.update_time),
        }
        return success_response(data)

    elif request.method == 'PUT':
        if not request.user.has_perm('menu:edit'):
            return error_response('无权限', 403)
        body = get_request_body(request)
        if 'name' in body:
            menu.name = body['name']
        if 'name_en' in body:
            menu.name_en = body['name_en']
        if 'name_zh_hans' in body:
            menu.name_zh_hans = body['name_zh_hans']
        if 'parent_id' in body:
            menu.parent_id = body['parent_id'] if body['parent_id'] else None
        if 'icon' in body:
            menu.icon = body['icon']
        if 'path' in body:
            menu.path = body['path']
        if 'component' in body:
            menu.component = body['component']
        if 'menu_type' in body:
            menu.menu_type = int(body['menu_type'])
        if 'permission' in body:
            menu.permission = body['permission']
        if 'sort' in body:
            menu.sort = int(body['sort'])
        if 'visible' in body:
            menu.visible = bool(body['visible'])
        if 'status' in body:
            menu.status = bool(body['status'])
        if 'backend_visible' in body:
            menu.backend_visible = bool(body['backend_visible'])
        if 'frontend_visible' in body:
            menu.frontend_visible = bool(body['frontend_visible'])
        menu.save()
        return success_response(msg='更新成功')

    elif request.method == 'DELETE':
        if not request.user.has_perm('menu:delete'):
            return error_response('无权限', 403)
        # 检查是否有子菜单
        if Menu.objects.filter(parent_id=pk).exists():
            return error_response('该菜单下有子菜单，无法删除', 400)
        menu.delete()
        return success_response(msg='删除成功')

    return error_response('Method not allowed', 405)


@csrf_exempt
@api_login_required
@api_permission_required('menu:add')
def menu_create(request):
    """POST /api/rbac/menus/ - 创建菜单"""
    if request.method != 'POST':
        return error_response('Method not allowed', 405)

    from .models import Menu

    body = get_request_body(request)
    name = body.get('name', '').strip()
    if not name:
        return error_response('菜单名称不能为空', 400)

    parent_id = body.get('parent_id')
    menu = Menu(
        name=name,
        name_en=body.get('name_en', ''),
        name_zh_hans=body.get('name_zh_hans', ''),
        parent_id=parent_id if parent_id else None,
        icon=body.get('icon', 'layui-icon-app'),
        path=body.get('path', ''),
        component=body.get('component', ''),
        menu_type=int(body.get('menu_type', 2)),
        permission=body.get('permission', ''),
        sort=int(body.get('sort', 0)),
        visible=bool(body.get('visible', True)),
        status=bool(body.get('status', True)),
        backend_visible=bool(body.get('backend_visible', True)),
        frontend_visible=bool(body.get('frontend_visible', True)),
    )
    menu.save()
    return success_response({'id': menu.id}, msg='创建成功')


# ==================== Role CRUD ====================

def _role_payload(role):
    parent_ids = list(role.parent_roles.values_list('id', flat=True))
    children_ids = sorted(set(
        list(role.children.values_list('id', flat=True)) +
        list(role.child_roles.values_list('id', flat=True))
    ))
    return {
        'id': role.id,
        'name': role.name,
        'code': role.code,
        'description': role.description,
        'is_system': role.is_system,
        'status': role.status,
        'menu_ids': list(role.menus.values_list('id', flat=True)),
        'parent_ids': parent_ids,
        'parent_id': role.parent_id or (parent_ids[0] if parent_ids else None),
        'children_ids': children_ids,
        'max_users': role.max_users,
        'scope_node': role.scope_node,
        'scope_depth': role.scope_depth,
        'create_time': fmt_time(role.create_time),
        'update_time': fmt_time(role.update_time),
    }


@csrf_exempt
@api_login_required
@api_permission_required('role:view')
def role_list(request):
    """GET /api/rbac/roles/ - 角色列表"""
    from .models import Role

    roles = Role.objects.all().order_by('id')
    return success_response([_role_payload(role) for role in roles])


@csrf_exempt
@api_login_required
@api_permission_required('role:view')
def role_effective_permissions(request, pk):
    """GET /api/rbac/roles/<id>/effective_permissions/ - 自有与继承权限来源"""
    from .engine import effective_permissions_for_role
    data = effective_permissions_for_role(pk)
    if data is None:
        return error_response('角色不存在', 404)
    return success_response(data)


@csrf_exempt
@api_login_required
@api_permission_required('role:view')
def role_detail(request, pk):
    """GET/PUT/DELETE /api/rbac/roles/<id>/ - 角色详情/更新/删除"""
    from .models import Role

    try:
        role = Role.objects.get(pk=pk)
    except Role.DoesNotExist:
        return error_response('角色不存在', 404)

    if request.method == 'GET':
        return success_response(_role_payload(role))

    elif request.method == 'PUT':
        if not request.user.has_perm('role:edit'):
            return error_response('无权限', 403)
        from .engine import RbacConstraintError, validate_role_parents
        body = get_request_body(request)
        if 'name' in body:
            role.name = body['name']
        if 'code' in body:
            role.code = body['code']
        if 'description' in body:
            role.description = body['description']
        if 'status' in body:
            role.status = bool(body['status'])
        if 'max_users' in body:
            try:
                role.max_users = int(body['max_users']) or None
            except (TypeError, ValueError):
                return error_response('人数上限必须是整数', 400)
        if 'scope_node' in body:
            role.scope_node = str(body['scope_node'] or '')[:100]
        if 'scope_depth' in body:
            try:
                role.scope_depth = max(0, int(body['scope_depth'] or 0))
            except (TypeError, ValueError):
                return error_response('作用域层数必须是非负整数', 400)

        parent_ids_payload = body.get('parent_ids')
        if 'parent_id' in body:
            raw_parent = body['parent_id']
            try:
                parent_id = int(raw_parent) if raw_parent else None
            except (TypeError, ValueError):
                return error_response('上级角色必须是整数', 400)
            if parent_id == role.pk:
                return error_response('上级角色不能是自身', 400)
            try:
                parent_ids_payload = validate_role_parents(
                    role.id, [parent_id] if parent_id else []
                )
            except RbacConstraintError as e:
                return error_response(e.message, 400)
            role.parent_id = parent_id

        role.save()
        if 'menu_ids' in body:
            role.menus.set(body['menu_ids'])
        if parent_ids_payload is not None:
            try:
                parents = validate_role_parents(role.id, parent_ids_payload)
            except RbacConstraintError as e:
                return error_response(e.message, 400)
            role.parent_roles.set(parents)
            if 'parent_id' not in body:
                role.parent = Role.objects.filter(id__in=parents).order_by('id').first()
                role.save(update_fields=['parent'])
        return success_response(msg='更新成功')

    elif request.method == 'DELETE':
        if not request.user.has_perm('role:delete'):
            return error_response('无权限', 403)
        if role.is_system:
            return error_response('系统内置角色无法删除', 400)
        role.delete()
        return success_response(msg='删除成功')

    return error_response('Method not allowed', 405)


@csrf_exempt
@api_login_required
@api_permission_required('role:add')
def role_create(request):
    """POST /api/rbac/roles/create/ - 创建角色"""
    if request.method != 'POST':
        return error_response('Method not allowed', 405)

    from .models import Role, Menu

    body = get_request_body(request)
    name = body.get('name', '').strip()
    code = body.get('code', '').strip()
    if not name:
        return error_response('角色名称不能为空', 400)
    if not code:
        return error_response('角色编码不能为空', 400)
    if Role.objects.filter(code=code).exists():
        return error_response('角色编码已存在', 400)

    from .engine import RbacConstraintError, validate_role_parents
    try:
        max_users = int(body.get('max_users') or 0) or None
        scope_depth = max(0, int(body.get('scope_depth') or 0))
    except (TypeError, ValueError):
        return error_response('人数上限/作用域层数必须是整数', 400)

    parent_ids_payload = body.get('parent_ids')
    parent_id = None
    if 'parent_id' in body:
        raw_parent = body['parent_id']
        try:
            parent_id = int(raw_parent) if raw_parent else None
        except (TypeError, ValueError):
            return error_response('上级角色必须是整数', 400)
        parent_ids_payload = [parent_id] if parent_id else []

    role = Role(
        name=name,
        code=code,
        description=body.get('description', ''),
        status=bool(body.get('status', True)),
        max_users=max_users,
        scope_node=str(body.get('scope_node') or '')[:100],
        scope_depth=scope_depth,
        parent_id=parent_id,
    )
    role.save()

    if parent_ids_payload is not None:
        try:
            parents = validate_role_parents(role.id, parent_ids_payload)
            role.parent_roles.set(parents)
        except RbacConstraintError as e:
            role.delete()
            return error_response(e.message, 400)
        if 'parent_id' not in body:
            role.parent = Role.objects.filter(id__in=parents).order_by('id').first()
            role.save(update_fields=['parent'])

    if 'menu_ids' in body and body['menu_ids']:
        role.menus.set(body['menu_ids'])
    else:
        from .models import Menu
        default_menus = Menu.objects.filter(
            permission__in=['profile:view', 'profile:edit']
        ) | Menu.objects.filter(
            path__icontains='/profile'
        )
        if default_menus.exists():
            role.menus.set(default_menus)
        else:
            profile_menu = Menu.objects.filter(
                menu_type=2,
                path__icontains='profile'
            ).first()
            if profile_menu:
                role.menus.set([profile_menu.id])

    return success_response({'id': role.id}, msg='创建成功')


@csrf_exempt
@api_login_required
@api_permission_required('role:copy')
def role_copy(request, pk):
    """POST /api/rbac/roles/<id>/copy/ - 复制角色"""
    if request.method != 'POST':
        return error_response('Method not allowed', 405)

    from .models import Role

    try:
        role = Role.objects.get(pk=pk)
    except Role.DoesNotExist:
        return error_response('角色不存在', 404)

    body = get_request_body(request)
    new_name = body.get('name', f'{role.name}_copy').strip()
    new_code = body.get('code', f'{role.code}_copy').strip()

    if Role.objects.filter(code=new_code).exists():
        return error_response('角色编码已存在', 400)

    new_role = Role(
        name=new_name,
        code=new_code,
        description=role.description,
        status=role.status,
        max_users=role.max_users,
        parent=role.parent,
        scope_node=role.scope_node,
        scope_depth=role.scope_depth,
    )
    new_role.save()
    new_role.menus.set(role.menus.all())
    new_role.parent_roles.set(role.parent_roles.all())
    return success_response({'id': new_role.id}, msg='复制成功')


# ==================== User CRUD ====================

@csrf_exempt
@api_login_required
@api_permission_required('user:view')
def user_list(request):
    """GET /api/rbac/users/ - 用户列表"""
    from django.db.models import Q

    User = _get_user_model()

    users = User.objects.all().order_by('-id')

    # keyword 过滤（username/nickname/email/phone 模糊搜索）
    keyword = request.GET.get('keyword', '').strip()
    if keyword:
        q = Q(username__icontains=keyword)
        if hasattr(User, 'nickname'):
            q |= Q(nickname__icontains=keyword)
        if hasattr(User, 'phone'):
            q |= Q(phone__icontains=keyword)
        q |= Q(email__icontains=keyword)
        users = users.filter(q)

    # is_active 过滤
    is_active = request.GET.get('is_active', '').strip()
    if is_active.lower() in ('true', 'false'):
        users = users.filter(is_active=(is_active.lower() == 'true'))

    total = users.count()

    # 分页支持
    try:
        page = int(request.GET.get('page', 1))
    except (ValueError, TypeError):
        page = 1
    try:
        page_size = int(request.GET.get('page_size', 10))
    except (ValueError, TypeError):
        page_size = 10

    page_size = max(1, min(page_size, 100))
    offset = (page - 1) * page_size
    users = users[offset:offset + page_size]

    data = []
    for u in users:
        roles = []
        if hasattr(u, 'roles'):
            roles = [{'id': r.id, 'name': r.name, 'code': r.code} for r in u.roles.all()]
        data.append({
            'id': u.id,
            'username': u.username,
            'nickname': getattr(u, 'nickname', '') or '',
            'phone': getattr(u, 'phone', ''),
            'email': getattr(u, 'email', ''),
            'avatar': getattr(u, 'avatar_url', ''),
            'is_active': u.is_active,
            'is_superuser': u.is_superuser,
            'is_staff': u.is_staff,
            'is_tester': getattr(u, 'is_tester', False),
            'roles': roles,
            'last_login': fmt_time(u.last_login),
            'date_joined': fmt_time(u.date_joined),
        })
    return success_response({'list': data, 'total': total})


@csrf_exempt
@api_login_required
@api_permission_required('user:add')
def user_create(request):
    """POST /api/rbac/users/create/ - 创建用户"""
    if request.method != 'POST':
        return error_response('Method not allowed', 405)

    User = _get_user_model()
    body = get_request_body(request)

    username = body.get('username', '').strip()
    password = body.get('password', '')
    if not username:
        return error_response('用户名不能为空', 400)
    if not password:
        return error_response('密码不能为空', 400)
    if len(password) < 6:
        return error_response('密码长度不能少于6位', 400)
    if User.objects.filter(username=username).exists():
        return error_response('用户名已存在', 400)

    from .engine import RbacConstraintError, is_full_access, validate_assignment
    if body.get('is_superuser') and not is_full_access(request.user):
        return error_response('无权限设置超级管理员', 403)

    user = User(
        username=username,
        email=body.get('email', ''),
        is_active=bool(body.get('is_active', True)),
        is_staff=bool(body.get('is_staff', False)),
        is_superuser=bool(body.get('is_superuser', False)),
    )
    if hasattr(user, 'nickname'):
        user.nickname = body.get('nickname', '')
    if hasattr(user, 'phone'):
        user.phone = body.get('phone', '')
    if hasattr(user, 'is_tester'):
        user.is_tester = bool(body.get('is_tester', False))

    final_role_ids = None
    if 'role_ids' in body and hasattr(User, 'roles'):
        try:
            final_role_ids = validate_assignment(user, body['role_ids'])
        except RbacConstraintError as e:
            return error_response(e.message, 400)

    user.set_password(password)
    user.save()

    if final_role_ids is not None:
        from .models import Role
        user.roles.set(Role.objects.filter(id__in=final_role_ids))

    return success_response({'id': user.id}, msg='创建成功')


@csrf_exempt
@api_login_required
@api_permission_required('user:edit')
def user_update(request, pk):
    """PUT /api/rbac/users/<id>/update/ - 更新用户"""
    if request.method != 'PUT':
        return error_response('Method not allowed', 405)

    User = _get_user_model()

    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return error_response('用户不存在', 404)

    body = get_request_body(request)
    from .engine import RbacConstraintError, is_full_access, validate_assignment
    if 'is_superuser' in body and body['is_superuser'] and not is_full_access(request.user):
        return error_response('无权限设置超级管理员', 403)
    if 'email' in body:
        user.email = body['email']
    if 'is_active' in body:
        user.is_active = bool(body['is_active'])
    if 'is_staff' in body:
        user.is_staff = bool(body['is_staff'])
    if 'is_superuser' in body:
        user.is_superuser = bool(body['is_superuser'])
    if hasattr(user, 'nickname') and 'nickname' in body:
        user.nickname = body['nickname']
    if hasattr(user, 'phone') and 'phone' in body:
        user.phone = body['phone']
    if hasattr(user, 'is_tester') and 'is_tester' in body:
        user.is_tester = bool(body['is_tester'])

    final_role_ids = None
    if 'role_ids' in body and hasattr(user, 'roles'):
        try:
            final_role_ids = validate_assignment(user, body['role_ids'], exclude_user_pk=user.pk)
        except RbacConstraintError as e:
            return error_response(e.message, 400)

    user.save()

    if final_role_ids is not None:
        from .models import Role
        user.roles.set(Role.objects.filter(id__in=final_role_ids))
        from .engine import clear_active_roles
        clear_active_roles(request)

    return success_response(msg='更新成功')


@csrf_exempt
@api_login_required
@api_permission_required('user:delete')
def user_delete(request, pk):
    """DELETE /api/rbac/users/<id>/delete/ - 删除用户"""
    if request.method != 'DELETE':
        return error_response('Method not allowed', 405)

    User = _get_user_model()

    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return error_response('用户不存在', 404)

    if user.pk == request.user.pk:
        return error_response('不能删除当前登录用户', 400)
    from .engine import is_full_access
    if is_full_access(user):
        return error_response('不能删除超级管理员或内置管理员', 403)

    user.delete()
    return success_response(msg='删除成功')


@csrf_exempt
@api_login_required
@api_permission_required('user:reset_password')
def user_reset_password(request, pk):
    """PUT /api/rbac/users/<id>/reset-password/ - 重置用户密码"""
    if request.method != 'PUT':
        return error_response('Method not allowed', 405)

    User = _get_user_model()

    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return error_response('用户不存在', 404)

    from .engine import is_full_access
    if is_full_access(user):
        return error_response('不能重置超级管理员或内置管理员密码', 403)

    body = get_request_body(request)
    new_password = body.get('new_password', '')
    if not new_password:
        return error_response('新密码不能为空', 400)
    if len(new_password) < 6:
        return error_response('密码长度不能少于6位', 400)

    user.set_password(new_password)
    user.save()
    return success_response(msg='密码重置成功')


@csrf_exempt
@api_login_required
@api_permission_required('user:toggle_status')
def user_toggle_status(request, pk):
    """PUT /api/rbac/users/<id>/status/ - 切换用户状态"""
    if request.method != 'PUT':
        return error_response('Method not allowed', 405)

    User = _get_user_model()

    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return error_response('用户不存在', 404)

    if user.pk == request.user.pk:
        return error_response('不能禁用当前登录用户', 400)
    from .engine import is_full_access
    if is_full_access(user):
        return error_response('不能禁用超级管理员或内置管理员', 403)

    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    return success_response({'is_active': user.is_active}, msg='状态已更新')


# ==================== Operation Log ====================

@csrf_exempt
@api_login_required
@api_permission_required('log:view')
def log_list(request):
    """GET /api/rbac/logs/ - 操作日志列表（支持搜索和分页）"""
    from .models import OperationLog

    logs = OperationLog.objects.select_related('user').all()

    # 搜索参数
    username = request.GET.get('username', '').strip()
    if username:
        logs = logs.filter(user__username__icontains=username)

    module = request.GET.get('module', '').strip()
    if module:
        logs = logs.filter(module__icontains=module)

    status = request.GET.get('status', '').strip()
    if status in ('0', '1'):
        logs = logs.filter(status=int(status))

    start_time = request.GET.get('start_time', '').strip()
    if start_time:
        logs = logs.filter(create_time__gte=start_time)

    end_time = request.GET.get('end_time', '').strip()
    if end_time:
        logs = logs.filter(create_time__lte=end_time)

    # 排序
    ordering = request.GET.get('ordering', '-create_time')
    logs = logs.order_by(ordering)

    # 分页
    total = logs.count()
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 10))
    page_size = min(page_size, 100)
    start = (page - 1) * page_size
    end = start + page_size
    logs = logs[start:end]

    data = []
    for log in logs:
        data.append({
            'id': log.id,
            'user': log.user.username if log.user else '',
            'user_id': log.user_id,
            'module': log.module,
            'action': log.action,
            'ip': log.ip or '',
            'method': log.method,
            'url': log.url,
            'status': log.status,
            'status_display': '成功' if log.status == 1 else '失败',
            'create_time': fmt_time(log.create_time),
        })
    return success_response({'list': data, 'total': total})


# ==================== System Config CRUD ====================

@csrf_exempt
@api_login_required
@api_permission_required('config:view')
def config_list(request):
    """GET /api/rbac/configs/ - 系统配置列表"""
    from .models import SystemConfig

    configs = SystemConfig.objects.all().order_by('sort', 'id')
    data = []
    for c in configs:
        data.append({
            'id': c.id,
            'key': c.key,
            'value': c.value,
            'description': c.description,
            'config_type': c.config_type,
            'sort': c.sort,
            'create_time': fmt_time(c.create_time),
            'update_time': fmt_time(c.update_time),
        })
    return success_response(data)


@csrf_exempt
@api_login_required
@api_permission_required('config:add')
def config_create(request):
    """POST /api/rbac/configs/create/ - 创建系统配置"""
    if request.method != 'POST':
        return error_response('Method not allowed', 405)

    from .models import SystemConfig

    body = get_request_body(request)
    key = body.get('key', '').strip()
    if not key:
        return error_response('配置键不能为空', 400)
    if SystemConfig.objects.filter(key=key).exists():
        return error_response('配置键已存在', 400)

    # 验证 config_type
    config_type = body.get('config_type', 'string')
    valid_types = [choice[0] for choice in SystemConfig.CONFIG_TYPE_CHOICES]
    if config_type not in valid_types:
        return error_response(f'无效的配置类型: {config_type}，支持的类型: {", ".join(valid_types)}', 400)

    # 如果是 json 类型，验证 JSON 格式
    if config_type == 'json':
        value = body.get('value', '')
        try:
            json.loads(value)
        except (json.JSONDecodeError, TypeError) as e:
            return error_response(f'JSON 格式错误: {str(e)}', 400)

    config = SystemConfig(
        key=key,
        value=body.get('value', ''),
        description=body.get('description', ''),
        config_type=config_type,
        sort=int(body.get('sort', 0)),
    )
    config.save()
    return success_response({'id': config.id}, msg='创建成功')


@csrf_exempt
@api_login_required
@api_permission_required('config:edit')
def config_update(request, pk):
    """PUT /api/rbac/configs/<id>/update/ - 更新系统配置"""
    if request.method != 'PUT':
        return error_response('Method not allowed', 405)

    from .models import SystemConfig

    try:
        config = SystemConfig.objects.get(pk=pk)
    except SystemConfig.DoesNotExist:
        return error_response('配置不存在', 404)

    body = get_request_body(request)
    
    # 验证 config_type
    if 'config_type' in body:
        config_type = body['config_type']
        valid_types = [choice[0] for choice in SystemConfig.CONFIG_TYPE_CHOICES]
        if config_type not in valid_types:
            return error_response(f'无效的配置类型: {config_type}，支持的类型: {", ".join(valid_types)}', 400)
        
        # 如果是 json 类型，验证 JSON 格式
        if config_type == 'json':
            value = body.get('value', config.value)
            try:
                json.loads(value)
            except (json.JSONDecodeError, TypeError) as e:
                return error_response(f'JSON 格式错误: {str(e)}', 400)
        
        config.config_type = config_type
    
    if 'value' in body:
        # 如果 config_type 是 json，验证 JSON 格式
        if config.config_type == 'json':
            try:
                json.loads(body['value'])
            except (json.JSONDecodeError, TypeError) as e:
                return error_response(f'JSON 格式错误: {str(e)}', 400)
        config.value = body['value']
    if 'description' in body:
        config.description = body['description']
    if 'sort' in body:
        config.sort = int(body['sort'])
    config.save()
    return success_response(msg='更新成功')


@csrf_exempt
@api_login_required
@api_permission_required('config:delete')
def config_delete(request, pk):
    """DELETE /api/rbac/configs/<id>/delete/ - 删除系统配置"""
    if request.method != 'DELETE':
        return error_response('Method not allowed', 405)

    from .defaults import get_default_configs
    from .models import SystemConfig

    try:
        config = SystemConfig.objects.get(pk=pk)
    except SystemConfig.DoesNotExist:
        return error_response('配置不存在', 404)

    protected = {row['key'] for row in get_default_configs()}
    if config.key in protected:
        return error_response('内置系统配置不能删除', 403)

    config.delete()
    return success_response(msg='删除成功')


# ==================== Profile Avatar ====================

@csrf_exempt
@api_login_required
def profile_avatar(request):
    """POST /api/rbac/profile/avatar/ - 上传头像"""
    if request.method != 'POST':
        return error_response('Method not allowed', 405)

    user = request.user
    if not hasattr(user, 'avatar'):
        return error_response('当前用户模型不支持头像', 400)

    avatar_file = request.FILES.get('avatar')
    if not avatar_file:
        return error_response('请选择头像文件', 400)

    # 验证文件类型
    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    if avatar_file.content_type not in allowed_types:
        return error_response('仅支持 JPG、PNG、GIF、WebP 格式', 400)

    # 验证文件大小（最大 2MB）
    if avatar_file.size > 2 * 1024 * 1024:
        return error_response('头像文件不能超过 2MB', 400)

    # 删除旧头像
    if user.avatar:
        user.avatar.delete(save=False)

    user.avatar = avatar_file
    user.save(update_fields=['avatar'])

    return success_response({'avatar': user.avatar_url}, msg='头像上传成功')


# ==================== Generic Image Upload ====================

@csrf_exempt
@api_login_required
@api_permission_required('config:edit')
def upload_image(request):
    """POST /api/rbac/upload/image/ - 通用图片上传（用于 Logo、Favicon 等配置）"""
    if request.method != 'POST':
        return error_response('Method not allowed', 405)

    image_file = request.FILES.get('image')
    if not image_file:
        return error_response('请选择图片文件', 400)

    # 验证文件类型
    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/x-icon', 'image/svg+xml']
    if image_file.content_type not in allowed_types:
        return error_response('仅支持 JPG、PNG、GIF、WebP、ICO、SVG 格式', 400)

    # 验证文件大小（最大 2MB）
    if image_file.size > 2 * 1024 * 1024:
        return error_response('图片文件不能超过 2MB', 400)

    # 保存到 MEDIA_ROOT/uploads/config/ 目录
    import os
    from django.core.files.storage import default_storage
    from django.utils import timezone

    ext = os.path.splitext(image_file.name)[1].lower() or '.png'
    filename = f'config/{timezone.now().strftime("%Y%m%d%H%M%S")}{ext}'
    saved_path = default_storage.save(filename, image_file)

    url = default_storage.url(saved_path)
    return success_response({'url': url, 'filename': filename}, msg='上传成功')


# ==================== Plugin Registry ====================

@csrf_exempt
@api_login_required
@api_permission_required('config:view')
def plugin_list(request):
    """GET /api/rbac/plugins/ - 已安装插件列表"""
    from .plugins import list_plugins
    return success_response(list_plugins())


@csrf_exempt
@api_login_required
@api_permission_required('config:view')
def plugin_manifest(request):
    """GET /api/rbac/plugins/manifest/ - 分离前端插件清单"""
    from .models import Menu
    from .plugins import list_plugins

    result = []
    for plugin in list_plugins():
        key = plugin['key']
        rows = Menu.objects.filter(
            plugin_key=key, status=True, visible=True
        ).order_by('sort', 'id')
        items = [{
            'id': menu.id,
            'parent_id': menu.parent_id,
            'name': menu.name,
            'icon': menu.icon,
            'path': menu.path,
            'component': menu.component,
            'menu_type': menu.menu_type,
            'permission': menu.permission,
            'sort': menu.sort,
        } for menu in rows]
        result.append({
            **plugin,
            'menus': _build_menu_tree(items),
            'permissions': sorted({
                item['permission'] for item in items if item['permission']
            }),
        })
    return success_response(result)


# ==================== RBAC3 Constraints & Active Roles ====================

@csrf_exempt
@api_login_required
@api_permission_by_method({'GET': 'constraint:view', '*': 'role:edit'})
def constraint_list(request):
    """GET /api/rbac/constraints/ - 互斥组、前置角色与全局上限"""
    from .engine import _get_config, DSD_STRATEGY_KEY, PREREQ_STRATEGY_KEY, get_max_roles_per_user
    from .models import RoleMutex, RolePrerequisite

    mutex = []
    for group in RoleMutex.objects.all().prefetch_related('roles', 'permissions'):
        mutex.append({
            'id': group.id,
            'name': group.name,
            'kind': group.kind,
            'role_ids': list(group.roles.values_list('id', flat=True)),
            'permission_ids': list(group.permissions.values_list('id', flat=True)),
            'permission_names': list(group.permissions.values_list('permission', flat=True)),
            'description': group.description,
            'is_active': group.is_active,
        })

    prerequisites = []
    for item in RolePrerequisite.objects.select_related('role', 'prerequisite'):
        prerequisites.append({
            'id': item.id,
            'role_id': item.role_id,
            'role_name': item.role.name,
            'prerequisite_id': item.prerequisite_id,
            'prerequisite_name': item.prerequisite.name,
        })

    return success_response({
        'mutex': mutex,
        'prerequisites': prerequisites,
        'limits': {
            'max_roles_per_user': get_max_roles_per_user(),
            'prerequisite_strategy': _get_config(PREREQ_STRATEGY_KEY, 'auto_grant'),
            'dsd_strategy': _get_config(DSD_STRATEGY_KEY, 'greedy'),
        },
    })


def _sod_payload(group):
    return {
        'id': group.id,
        'name': group.name,
        'mutually_exclusive_roles': [
            {'id': role.id, 'name': role.name}
            for role in group.roles.all().order_by('id')
        ],
        'role_ids': list(group.roles.values_list('id', flat=True)),
        'description': group.description,
        'is_active': group.is_active,
    }


@csrf_exempt
@api_login_required
@api_permission_by_method({'GET': 'constraint:view', '*': 'role:edit'})
def sod_constraint_list(request):
    """GET/POST /api/rbac/sod-constraints/ - 1.4.2 SSD 兼容端点"""
    from .engine import RbacConstraintError, require_roles
    from .models import SoDConstraint

    if request.method == 'GET':
        groups = SoDConstraint.objects.filter(kind='ssd').order_by('id').prefetch_related('roles')
        return success_response([_sod_payload(group) for group in groups])

    if request.method == 'POST':
        body = get_request_body(request)
        name = str(body.get('name', '')).strip()
        if not name:
            return error_response('约束名称不能为空', 400)
        if SoDConstraint.objects.filter(name=name).exists():
            return error_response('约束名称已存在', 400)
        try:
            role_ids = require_roles(body.get('mutually_exclusive_role_ids') or body.get('role_ids') or [])
        except RbacConstraintError as e:
            return error_response(e.message, 400)
        if len(role_ids) < 2:
            return error_response('互斥约束至少包含两个角色', 400)
        group = SoDConstraint.objects.create(
            name=name, kind='ssd',
            description=body.get('description', ''),
            is_active=bool(body.get('is_active', True)),
        )
        group.roles.set(role_ids)
        return success_response({'id': group.id}, msg='创建成功')

    return error_response('Method not allowed', 405)


@csrf_exempt
@api_login_required
@api_permission_by_method({'GET': 'constraint:view', '*': 'role:edit'})
def sod_constraint_detail(request, pk):
    """GET/PUT/DELETE /api/rbac/sod-constraints/<id>/ - 1.4.2 SSD 兼容端点"""
    from .engine import RbacConstraintError, require_roles
    from .models import SoDConstraint

    group = SoDConstraint.objects.filter(pk=pk, kind='ssd').first()
    if not group:
        return error_response('约束不存在', 404)

    if request.method == 'GET':
        return success_response(_sod_payload(group))

    if request.method == 'PUT':
        body = get_request_body(request)
        if 'name' in body:
            name = str(body['name']).strip()
            if not name:
                return error_response('约束名称不能为空', 400)
            if SoDConstraint.objects.filter(name=name).exclude(pk=pk).exists():
                return error_response('约束名称已存在', 400)
            group.name = name
        if 'description' in body:
            group.description = body['description']
        if 'is_active' in body:
            group.is_active = bool(body['is_active'])
        group.save()
        role_key = 'mutually_exclusive_role_ids' if 'mutually_exclusive_role_ids' in body else 'role_ids'
        if role_key in body:
            try:
                role_ids = require_roles(body[role_key] or [])
            except RbacConstraintError as e:
                return error_response(e.message, 400)
            if len(role_ids) < 2:
                return error_response('互斥约束至少包含两个角色', 400)
            group.roles.set(role_ids)
        return success_response(msg='更新成功')

    if request.method == 'DELETE':
        group.delete()
        return success_response(msg='删除成功')

    return error_response('Method not allowed', 405)


@csrf_exempt
@api_login_required
@api_permission_required('constraint:view')
def sod_constraint_check(request):
    """POST /api/rbac/sod-constraints/check/ - 实时 SSD 预校验"""
    from .engine import check_sod_conflict
    if request.method != 'POST':
        return error_response('Method not allowed', 405)
    body = get_request_body(request)
    target_user = None
    user_id = body.get('user_id')
    if user_id:
        from django.contrib.auth import get_user_model
        target_user = get_user_model().objects.filter(pk=user_id).first()
    result = check_sod_conflict(target_user, body.get('role_ids') or [], audit=False)
    if result['exempt']:
        result['message'] = '已豁免，操作将记录审计'
    return success_response(result)


@csrf_exempt
@api_login_required
@api_permission_required('role:edit')
def mutex_create(request):
    """POST /api/rbac/constraints/mutex/ - 创建互斥组"""
    if request.method != 'POST':
        return error_response('Method not allowed', 405)
    from .engine import RbacConstraintError, require_roles
    from .models import Menu, RoleMutex

    body = get_request_body(request)
    name = str(body.get('name', '')).strip()
    kind = body.get('kind', 'ssd')
    if not name:
        return error_response('互斥组名称不能为空', 400)
    if kind not in ('ssd', 'dsd'):
        return error_response('互斥类型必须是 ssd 或 dsd', 400)
    if RoleMutex.objects.filter(name=name).exists():
        return error_response('互斥组名称已存在', 400)
    try:
        role_ids = require_roles(body.get('role_ids', []))
    except RbacConstraintError as e:
        return error_response(e.message, 400)

    permission_ids = []
    for value in body.get('permission_ids', []) or []:
        try:
            permission_ids.append(int(value))
        except (TypeError, ValueError):
            continue
    found_permission_ids = set(Menu.objects.filter(
        id__in=permission_ids, permission__gt=''
    ).values_list('id', flat=True))
    if found_permission_ids != set(permission_ids):
        return error_response('互斥权限不存在或未配置权限标识', 400)

    if len(role_ids) + len(found_permission_ids) < 2:
        return error_response('互斥组至少需要两个角色或权限', 400)

    group = RoleMutex.objects.create(
        name=name,
        kind=kind,
        description=body.get('description', ''),
        is_active=bool(body.get('is_active', True)),
    )
    group.roles.set(role_ids)
    group.permissions.set(found_permission_ids)
    return success_response({'id': group.id}, msg='创建成功')


@csrf_exempt
@api_login_required
@api_permission_required('role:edit')
def mutex_delete(request, pk):
    """DELETE /api/rbac/constraints/mutex/<id>/ - 删除互斥组"""
    if request.method != 'DELETE':
        return error_response('Method not allowed', 405)
    from .models import RoleMutex
    deleted, _ = RoleMutex.objects.filter(pk=pk).delete()
    if not deleted:
        return error_response('互斥组不存在', 404)
    return success_response(msg='删除成功')


@csrf_exempt
@api_login_required
@api_permission_required('role:edit')
def prerequisite_create(request):
    """POST /api/rbac/constraints/prerequisite/ - 创建前置角色"""
    if request.method != 'POST':
        return error_response('Method not allowed', 405)
    from .engine import RbacConstraintError, validate_prerequisite
    from .models import RolePrerequisite

    body = get_request_body(request)
    try:
        role_id, prerequisite_id = validate_prerequisite(
            body.get('role_id'), body.get('prerequisite_id')
        )
    except (RbacConstraintError, TypeError, ValueError) as e:
        return error_response(getattr(e, 'message', str(e)), 400)

    item, created = RolePrerequisite.objects.get_or_create(
        role_id=role_id, prerequisite_id=prerequisite_id
    )
    return success_response({'id': item.id}, msg='创建成功' if created else '已存在')


@csrf_exempt
@api_login_required
@api_permission_required('role:edit')
def prerequisite_delete(request, pk):
    """DELETE /api/rbac/constraints/prerequisite/<id>/ - 删除前置角色"""
    if request.method != 'DELETE':
        return error_response('Method not allowed', 405)
    from .models import RolePrerequisite
    deleted, _ = RolePrerequisite.objects.filter(pk=pk).delete()
    if not deleted:
        return error_response('前置角色不存在', 404)
    return success_response(msg='删除成功')


@csrf_exempt
@api_login_required
def active_roles(request):
    """GET/POST /api/rbac/active-roles/ - 查询或切换当前会话激活角色"""
    from .engine import (
        RbacConstraintError, clear_active_roles, get_active_role_ids,
        get_assigned_role_ids, store_active_roles, validate_active_roles,
    )
    from .models import Role

    assigned_ids = get_assigned_role_ids(request.user)
    assigned = list(Role.objects.filter(id__in=assigned_ids).values('id', 'name', 'code'))

    if request.method == 'GET':
        active_ids = get_active_role_ids(request.user)
        return success_response({
            'assigned': assigned,
            'active_ids': sorted(active_ids),
        })

    if request.method == 'POST':
        body = get_request_body(request)
        if 'role_ids' in body and body['role_ids'] is not None:
            try:
                selected = validate_active_roles(request.user, body['role_ids'])
            except RbacConstraintError as e:
                return error_response(e.message, 400)
            store_active_roles(request, selected)
        else:
            clear_active_roles(request)
        return success_response({
            'assigned': assigned,
            'active_ids': sorted(get_active_role_ids(request.user)),
        }, msg='切换成功')

    return error_response('Method not allowed', 405)


# ==================== 1.4.2 Scope Nodes ====================

def _scope_node_payload(node):
    return {
        'id': node.id,
        'code': node.code,
        'name': node.name,
        'parent_id': node.parent_id,
        'sort': node.sort,
        'is_active': node.is_active,
    }


def _build_scope_tree(nodes, parent_id=None):
    tree = []
    for node in nodes:
        if node['parent_id'] == parent_id:
            item = dict(node)
            children = _build_scope_tree(nodes, node['id'])
            if children:
                item['children'] = children
            tree.append(item)
    return tree


def _scope_descendant_ids(node_id):
    from .models import ScopeNode

    result = set()
    queue = [node_id]
    while queue:
        current = queue.pop()
        for child in ScopeNode.objects.filter(parent_id=current).values_list('id', flat=True):
            if child not in result:
                result.add(child)
                queue.append(child)
    return result


@csrf_exempt
@api_login_required
@api_permission_by_method({'GET': 'scope:view', '*': 'role:edit'})
def scope_node_list(request):
    """GET/POST /api/rbac/scope-nodes/ - 组织节点树与创建入口"""
    from .models import ScopeNode

    if request.method == 'GET':
        rows = ScopeNode.objects.filter(is_active=True).order_by('sort', 'id')
        return success_response(_build_scope_tree([_scope_node_payload(row) for row in rows]))

    if request.method == 'POST':
        body = get_request_body(request)
        code = str(body.get('code', '')).strip()
        name = str(body.get('name', '')).strip()
        if not code or not name:
            return error_response('节点编码和名称不能为空', 400)
        if ScopeNode.objects.filter(code=code).exists():
            return error_response('节点编码已存在', 400)
        parent_id = body.get('parent_id') or None
        node = ScopeNode.objects.create(
            code=code, name=name, parent_id=parent_id,
            sort=int(body.get('sort') or 0),
            is_active=bool(body.get('is_active', True)),
        )
        return success_response({'id': node.id}, msg='创建成功')

    return error_response('Method not allowed', 405)


@csrf_exempt
@api_login_required
@api_permission_by_method({'GET': 'scope:view', '*': 'role:edit'})
def scope_node_detail(request, pk):
    """GET/PUT/DELETE /api/rbac/scope-nodes/<id>/"""
    from .models import ScopeNode

    node = ScopeNode.objects.filter(pk=pk).first()
    if not node:
        return error_response('节点不存在', 404)

    if request.method == 'GET':
        return success_response(_scope_node_payload(node))

    if request.method == 'PUT':
        body = get_request_body(request)
        if 'code' in body:
            code = str(body['code']).strip()
            if ScopeNode.objects.filter(code=code).exclude(pk=pk).exists():
                return error_response('节点编码已存在', 400)
            node.code = code
        if 'name' in body:
            node.name = str(body['name']).strip()
        if 'parent_id' in body:
            parent_id = int(body['parent_id']) if body['parent_id'] else None
            if parent_id == pk or parent_id in _scope_descendant_ids(pk):
                return error_response('上级节点不能是自身或后代', 400)
            node.parent_id = parent_id
        if 'sort' in body:
            node.sort = int(body['sort'] or 0)
        if 'is_active' in body:
            node.is_active = bool(body['is_active'])
        node.save()
        return success_response(msg='更新成功')

    if request.method == 'DELETE':
        ScopeNode.objects.filter(parent_id=pk).update(parent=None)
        node.delete()
        return success_response(msg='删除成功')

    return error_response('Method not allowed', 405)


# ==================== 1.4.2 ABAC policies ====================

def _abac_payload(policy, include_expression=True):
    data = {
        'id': policy.id,
        'name': policy.name,
        'resource': policy.resource,
        'action': policy.action,
        'field': policy.field,
        'effect': policy.effect,
        'priority': policy.priority,
        'is_active': policy.is_active,
    }
    if include_expression:
        data['expression'] = policy.expression
    return data


@csrf_exempt
@api_login_required
@api_permission_by_method({'GET': 'abac:view', '*': 'role:edit'})
def abac_policy_list(request):
    """GET/POST /api/rbac/abac-policies/"""
    from .abac import AbacError, validate_expression
    from .models import AbacPolicy

    if request.method == 'GET':
        rows = AbacPolicy.objects.all().order_by('priority', 'id')
        return success_response([_abac_payload(row) for row in rows])

    if request.method == 'POST':
        body = get_request_body(request)
        expression = str(body.get('expression', '')).strip()
        try:
            validate_expression(expression)
        except AbacError as exc:
            return error_response('表达式无效：%s' % exc, 400)
        if not str(body.get('name', '')).strip() or not str(body.get('resource', '')).strip():
            return error_response('策略名称和资源不能为空', 400)
        policy = AbacPolicy.objects.create(
            name=str(body['name']).strip(),
            resource=str(body['resource']).strip(),
            action=str(body.get('action') or 'view').strip(),
            field=str(body.get('field') or '').strip(),
            effect=str(body.get('effect') or 'allow'),
            expression=expression,
            priority=int(body.get('priority') or 100),
            is_active=bool(body.get('is_active', True)),
        )
        return success_response({'id': policy.id}, msg='创建成功')

    return error_response('Method not allowed', 405)


@csrf_exempt
@api_login_required
@api_permission_by_method({'GET': 'abac:view', '*': 'role:edit'})
def abac_policy_detail(request, pk):
    """GET/PUT/DELETE /api/rbac/abac-policies/<id>/"""
    from .abac import AbacError, validate_expression
    from .models import AbacPolicy

    policy = AbacPolicy.objects.filter(pk=pk).first()
    if not policy:
        return error_response('策略不存在', 404)

    if request.method == 'GET':
        return success_response(_abac_payload(policy))

    if request.method == 'PUT':
        body = get_request_body(request)
        simple_fields = ('name', 'resource', 'action', 'field', 'effect')
        for key in simple_fields:
            if key in body:
                setattr(policy, key, str(body[key] or '').strip())
        if 'priority' in body:
            policy.priority = int(body['priority'] or 100)
        if 'is_active' in body:
            policy.is_active = bool(body['is_active'])
        if 'expression' in body:
            expression = str(body['expression'] or '').strip()
            try:
                validate_expression(expression)
            except AbacError as exc:
                return error_response('表达式无效：%s' % exc, 400)
            policy.expression = expression
        policy.save()
        return success_response(msg='更新成功')

    if request.method == 'DELETE':
        policy.delete()
        return success_response(msg='删除成功')

    return error_response('Method not allowed', 405)


@csrf_exempt
@api_login_required
@api_permission_required('abac:view')
def abac_check(request):
    """POST /api/rbac/abac-check/ - 策略调试与前端字段/行级控制"""
    from .abac import evaluate_policies

    if request.method != 'POST':
        return error_response('Method not allowed', 405)
    body = get_request_body(request)
    target_user = request.user
    user_id = body.get('user_id')
    if user_id:
        target_user = _get_user_model().objects.filter(pk=user_id).first()
        if target_user is None:
            return error_response('目标用户不存在', 404)
    if (
        target_user != request.user
        and getattr(target_user, 'is_superuser', False)
        and not getattr(request.user, 'is_superuser', False)
    ):
        return error_response('无权以超级管理员上下文调试策略', 403)
    decision = evaluate_policies(
        target_user,
        str(body.get('action') or 'view'),
        body.get('resource') or '',
        field=str(body.get('field') or ''),
        extra_context=body.get('context') if isinstance(body.get('context'), dict) else None,
    )
    return success_response({
        'allowed': decision.allowed,
        'matched': decision.matched,
        'errors': decision.errors,
    })


@csrf_exempt
@api_login_required
def frontend_permissions(request):
    """GET /api/rbac/frontend/permissions/ - Vue/React SDK 的统一权限数据入口"""
    from .engine import visible_menu_queryset
    from .models import AbacPolicy, ScopeNode
    from .permissions import has_permission
    from .plugins import list_plugins

    if request.method != 'GET':
        return error_response('Method not allowed', 405)

    menus = visible_menu_queryset(request.user, 'frontend').order_by('sort', 'id')
    language = getattr(request.user, 'language', 'zh-hans')
    menu_rows = [{
        'id': menu.id, 'parent_id': menu.parent_id, 'name': menu.get_name_by_lang(language),
        'path': menu.path, 'component': menu.component, 'menu_type': menu.menu_type,
        'permission': menu.permission, 'icon': menu.icon, 'sort': menu.sort,
    } for menu in menus]
    scope_nodes = list(ScopeNode.objects.filter(is_active=True).order_by('sort', 'id').values(
        'id', 'code', 'name', 'parent_id', 'sort'
    ))
    can_view_policies = (
        bool(getattr(request.user, 'is_superuser', False))
        or has_permission(request.user, 'abac:view', request)
    )
    policies = [
        _abac_payload(row, include_expression=False)
        for row in AbacPolicy.objects.filter(is_active=True)
    ] if can_view_policies else []
    return success_response({
        'user': {
            'id': request.user.pk,
            'username': getattr(request.user, 'username', ''),
            'language': language,
            'is_superuser': bool(getattr(request.user, 'is_superuser', False)),
        },
        'permissions': _get_user_permissions(request.user),
        'roles': list(request.user.roles.values('id', 'code', 'name')) if hasattr(request.user, 'roles') else [],
        'menus': _build_menu_tree(menu_rows),
        'plugins': list_plugins(),
        'scope_nodes': _build_scope_tree(scope_nodes),
        'abac_policies': policies,
    })
