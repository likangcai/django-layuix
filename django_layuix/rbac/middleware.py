# -*- coding: utf-8 -*-
"""
OperationLogMiddleware - 自动记录 API 操作日志
支持通过 Django settings 配置需要记录的路径前缀
"""
import json
import logging
import re
from urllib.parse import urlsplit

from django.conf import settings
from django.http import JsonResponse

logger = logging.getLogger(__name__)

# 默认需要忽略的路径关键字（非业务接口）
DEFAULT_IGNORE_KEYWORDS = [
    'login',
    'logout',
    'register',
    'upload',
    'system/info',
    'system/config',
    'stats',
]

# 默认需要记录的路径前缀
DEFAULT_LOG_PREFIXES = [
    '/admin/api/rbac/',
    '/admin/api/ops/',
]

# 模块名称映射（路径前缀 -> 模块名）
MODULE_PREFIX_MAP = {
    '/admin/api/rbac/': 'rbac',
    '/admin/api/ops/': 'ops',
}

# 模块路径名 -> 中文显示名映射
MODULE_NAME_MAP = {
    'users': '用户',
    'roles': '角色',
    'menus': '菜单',
    'configs': '系统配置',
    'config': '系统配置',
    'servers': '服务器',
    'ai-configs': 'AI配置',
    'ai_config': 'AI配置',
    'ai': 'AI配置',
    'logs': '操作日志',
    'profile': '个人中心',
    'set-language': '语言切换',
    'set-default': '默认设置',
}


class ForceUtf8Middleware:
    """强制所有响应使用 UTF-8 编码
    解决静态 HTML 文件在中文 Windows 浏览器中因默认 GBK 编码显示乱码的问题
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        content_type = response.get('Content-Type', '')
        # 只处理 text/* 类型的响应，添加 charset=utf-8
        if content_type.startswith('text/') and 'charset' not in content_type:
            response['Content-Type'] = content_type + '; charset=utf-8'
        return response


class OperationLogMiddleware:
    """自动记录操作日志的中间件

    通过 settings.OPERATION_LOG 配置：
    - PREFIXES: 需要记录的路径前缀列表（默认包含 rbac 和 ops）
    - IGNORE_KEYWORDS: 需要忽略的路径关键字列表
    - EXCLUDE_PREFIXES: 需要排除的路径前缀列表（优先级高于 PREFIXES）

    示例 settings.py:
        OPERATION_LOG = {
            'PREFIXES': ['/admin/api/rbac/', '/admin/api/ops/', '/api/'],
            'IGNORE_KEYWORDS': ['login', 'logout', 'upload'],
            'EXCLUDE_PREFIXES': ['/api/public/'],
        }
    """

    def __init__(self, get_response):
        self.get_response = get_response
        config = getattr(settings, 'OPERATION_LOG', {})
        self.prefixes = config.get('PREFIXES', DEFAULT_LOG_PREFIXES)
        self.ignore_keywords = config.get('IGNORE_KEYWORDS', DEFAULT_IGNORE_KEYWORDS)
        self.exclude_prefixes = config.get('EXCLUDE_PREFIXES', [])

    def __call__(self, request):
        response = self.get_response(request)
        self._record_log(request, response)
        return response

    def _should_record(self, request):
        """判断是否需要记录日志"""
        path = request.path

        # 只记录 POST/PUT/DELETE 请求
        if request.method not in ('POST', 'PUT', 'DELETE'):
            return False

        # 排除指定前缀
        for prefix in self.exclude_prefixes:
            if path.startswith(prefix):
                return False

        # 检查是否匹配需要记录的前缀
        matched = False
        for prefix in self.prefixes:
            if path.startswith(prefix):
                matched = True
                break
        if not matched:
            return False

        # 忽略非业务接口
        for keyword in self.ignore_keywords:
            if keyword in path:
                return False

        return True

    def _get_client_ip(self, request):
        """获取客户端 IP"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip

    def _get_api_prefix(self, path):
        """获取匹配的 API 前缀"""
        for prefix in self.prefixes:
            if path.startswith(prefix):
                return prefix
        return ''

    def _get_module(self, path):
        """从请求路径中提取操作模块（中文友好名）"""
        prefix = self._get_api_prefix(path)
        if not prefix:
            return ''

        # 去掉前缀后取第一段作为模块名
        relative = path.replace(prefix, '').strip('/')
        parts = relative.split('/')
        if parts:
            raw_module = parts[0]
            # 优先使用中文映射，fallback 到原始路径名
            return MODULE_NAME_MAP.get(raw_module, raw_module)
        return ''

    def _get_action(self, request, path, response):
        """生成操作描述"""
        module = self._get_module(path)
        method = request.method

        action_map = {
            'POST': '新增',
            'PUT': '编辑',
            'DELETE': '删除',
        }
        action_prefix = action_map.get(method, method)

        # 尝试从路径中提取操作对象
        prefix = self._get_api_prefix(path)
        relative = path.replace(prefix, '').strip('/').split('/')
        if len(relative) >= 2:
            if relative[-1] in ('create',):
                return f'{action_prefix}{module}'
            elif relative[-1] in ('update',):
                return f'{action_prefix}{module} (ID:{relative[-2]})'
            elif relative[-1] in ('delete',):
                return f'{action_prefix}{module} (ID:{relative[-2]})'
            elif relative[-1] == 'copy':
                return f'复制{module} (ID:{relative[-2]})'
            elif relative[-1] == 'reset-password':
                return f'重置{module}密码 (ID:{relative[-2]})'
            elif relative[-1] == 'status':
                return f'切换{module}状态 (ID:{relative[-2]})'
            elif relative[-1] == 'test':
                return f'测试{module} (ID:{relative[-2]})'
            elif relative[-1] == 'save':
                return f'保存{module}配置'
            elif relative[-1] == 'log':
                return f'查看{module}日志 (ID:{relative[-2]})'

        return f'{action_prefix}{module}'

    def _get_request_params(self, request):
        """获取请求参数（脱敏处理）"""
        try:
            if request.content_type == 'application/json' and request.body:
                body = json.loads(request.body)
                # 脱敏：移除密码字段
                sensitive_fields = ('password', 'new_password', 'old_password', 'confirm_password',
                                    'secret_key', 'private_key', 'token')
                for field in sensitive_fields:
                    if field in body:
                        body[field] = '******'
                return json.dumps(body, ensure_ascii=False)[:2000]
        except (json.JSONDecodeError, ValueError):
            pass
        return ''

    def _record_log(self, request, response):
        """记录操作日志"""
        if not self._should_record(request):
            return

        try:
            from .models import OperationLog

            path = request.path
            status_code = getattr(response, 'status_code', 0)

            # 状态码 2xx 视为成功
            log_status = 1 if 200 <= status_code < 300 else 0

            OperationLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                module=self._get_module(path),
                action=self._get_action(request, path, response),
                ip=self._get_client_ip(request),
                method=request.method,
                url=path,
                status=log_status,
            )
        except Exception as e:
            logger.warning(f'Failed to record operation log: {e}')


class ApiOriginGuardMiddleware:
    """Reject cross-origin browser writes to admin APIs using session cookies.

    Many API views are ``csrf_exempt`` for Bearer-token clients. This
    middleware compensates by checking Origin/Referer for unsafe
    session-authenticated API calls. Token-authenticated calls are unaffected.
    """

    SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS', 'TRACE')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.method in self.SAFE_METHODS
            or not self._is_api_path(request.path)
            or getattr(settings, 'LAYUIX_DISABLE_API_ORIGIN_GUARD', False)
        ):
            return self.get_response(request)

        if self._is_valid_token_request(request):
            return self.get_response(request)

        source = request.META.get('HTTP_ORIGIN') or request.META.get('HTTP_REFERER')
        if not source:
            if self._is_public_api_path(request.path):
                return self.get_response(request)
            return JsonResponse({'code': 403, 'msg': 'Origin or Referer is required'}, status=403)

        try:
            source_host = (urlsplit(source).netloc or '').lower()
        except ValueError:
            source_host = ''
        if not source_host or not self._host_allowed(source_host, request):
            return JsonResponse({'code': 403, 'msg': 'Cross-origin request blocked'}, status=403)
        return self.get_response(request)

    def _is_api_path(self, path):
        prefixes = getattr(settings, 'LAYUIX_API_PREFIXES', ['/admin/api/'])
        return any(str(prefix) and path.startswith(str(prefix)) for prefix in prefixes or [])

    def _is_public_api_path(self, path):
        public_paths = getattr(settings, 'LAYUIX_PUBLIC_API_PATHS', None)
        if public_paths is None:
            prefixes = getattr(settings, 'LAYUIX_API_PREFIXES', ['/admin/api/'])
            public_paths = [
                str(prefix).rstrip('/') + '/rbac/login/'
                for prefix in prefixes
            ] + [
                str(prefix).rstrip('/') + '/rbac/register/'
                for prefix in prefixes
            ]
        return any(str(item) and path == str(item) for item in public_paths or [])

    def _is_valid_token_request(self, request):
        try:
            from .token_auth import token_authenticate

            user = token_authenticate(request)
            return bool(user and getattr(user, 'is_authenticated', False))
        except Exception:
            return False

    def _normalize_host(self, value):
        host = str(value or '').strip().lower()
        if '://' in host:
            host = urlsplit(host).netloc
        return host.split('/')[0]

    def _host_allowed(self, source_host, request):
        hosts = {self._normalize_host(request.get_host())}
        configured = getattr(settings, 'LAYUIX_API_ALLOWED_ORIGINS', None)
        if configured is None:
            configured = [
                host for host in getattr(settings, 'ALLOWED_HOSTS', [])
                if host and host != '*'
            ]
        for host in configured or []:
            normalized = self._normalize_host(host)
            if normalized:
                hosts.add(normalized)
        for host in hosts:
            if source_host == host:
                return True
            if host.startswith('*.') and source_host.endswith(host[1:]):
                return True
        return False


class RbacSessionMiddleware:
    """把会话中的激活角色挂到 user 上，供权限引擎读取（RBAC2 DSD）。"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if user is not None and getattr(user, 'is_authenticated', False):
            from .engine import ACTIVE_ROLES_SESSION_KEY
            active_ids = request.session.get(ACTIVE_ROLES_SESSION_KEY)
            if active_ids is not None:
                user._layui_active_role_ids = active_ids
        return self.get_response(request)
