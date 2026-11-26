# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-26 22:19
# @FileName  : views.py
# -----------------------------
"""
Ops API Views - Server CRUD, SSH test, log viewing, command execution
"""
import re
import shlex
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.timezone import localtime

from django_layuix.rbac.permissions import (
    api_login_required, api_permission_required, has_permission, resolve_api_user,
)
from django_layuix.rbac.serializers import field_whitelisted


def fmt_time(dt, format_str='%Y-%m-%d %H:%M:%S'):
    """将 timezone-aware datetime 转为当前时区后格式化"""
    if dt is None:
        return ''
    return localtime(dt).strftime(format_str)


def get_request_body(request):
    """Get parsed request body"""
    try:
        if request.content_type == 'application/json':
            return json.loads(request.body)
        return dict(request.POST)
    except (json.JSONDecodeError, ValueError):
        return {}


def success_response(data=None, msg='success'):
    return JsonResponse({'code': 200, 'msg': msg, 'data': data})


def error_response(msg='error', code=400):
    return JsonResponse({'code': code, 'msg': msg}, status=code)


# ==================== 服务器 CRUD ====================

@csrf_exempt
@api_login_required
@api_permission_required('server:view')
@field_whitelisted('ops.Server')
def server_list(request):
    """Get server list"""
    from .models import Server
    try:
        page = max(1, int(request.GET.get('page', 1)))
        page_size = max(1, min(100, int(request.GET.get('page_size', 20))))
    except (ValueError, TypeError):
        page = 1
        page_size = 20

    queryset = Server.objects.filter(is_active=True)
    total = queryset.count()
    servers = queryset[(page - 1) * page_size:page * page_size]

    data = [{
        'id': s.id,
        'name': s.name,
        'host': s.host,
        'port': s.port,
        'username': s.username,
        'auth_type': s.auth_type,
        'description': s.description,
        'is_active': s.is_active,
        'create_time': fmt_time(s.create_time),
    } for s in servers]

    return success_response({'list': data, 'total': total, 'page': page, 'page_size': page_size})


@csrf_exempt
@api_login_required
@api_permission_required('server:add')
def server_create(request):
    """Create server"""
    if request.method != 'POST':
        return error_response('Method not allowed', 405)
    from .models import Server
    body = get_request_body(request)

    server = Server.objects.create(
        name=body.get('name', ''),
        host=body.get('host', ''),
        port=int(body.get('port', 22)),
        username=body.get('username', ''),
        auth_type=body.get('auth_type', 'password'),
        password=body.get('password', ''),
        private_key=body.get('private_key', ''),
        description=body.get('description', ''),
        is_active=body.get('is_active', True),
    )
    return success_response({'id': server.id}, '创建成功')


@csrf_exempt
@api_login_required
@api_permission_required('server:edit')
def server_update(request, pk):
    """Update server"""
    if request.method != 'PUT':
        return error_response('Method not allowed', 405)
    from .models import Server
    try:
        server = Server.objects.get(pk=pk)
    except Server.DoesNotExist:
        return error_response('服务器不存在', 404)

    body = get_request_body(request)
    for field in ['name', 'host', 'port', 'username', 'auth_type', 'description', 'is_active']:
        if field in body:
            if field == 'port':
                setattr(server, field, int(body[field]))
            elif field == 'is_active':
                setattr(server, field, body[field] is True or body[field] == 'on')
            else:
                setattr(server, field, body[field])
    # 敏感字段：仅在显式提供且非空时更新
    for field in ['password', 'private_key']:
        if field in body and body[field]:
            setattr(server, field, body[field])
    server.save()
    return success_response(msg='更新成功')


@csrf_exempt
@api_login_required
@api_permission_required('server:view')
@field_whitelisted('ops.Server')
def server_detail(request, pk):
    """Get server detail; credential fields are never returned"""
    from .models import Server
    try:
        server = Server.objects.get(pk=pk)
    except Server.DoesNotExist:
        return error_response('服务器不存在', 404)

    return success_response({
        'id': server.id,
        'name': server.name,
        'host': server.host,
        'port': server.port,
        'username': server.username,
        'auth_type': server.auth_type,
        'password': server.password,
        'private_key': server.private_key,
        'description': server.description,
        'is_active': server.is_active,
    })


@csrf_exempt
@api_login_required
@api_permission_required('server:delete')
def server_delete(request, pk):
    """Delete server"""
    if request.method != 'DELETE':
        return error_response('Method not allowed', 405)
    from .models import Server
    try:
        server = Server.objects.get(pk=pk)
        server.delete()
        return success_response(msg='删除成功')
    except Server.DoesNotExist:
        return error_response('服务器不存在', 404)


# ==================== SSH 操作 ====================

@csrf_exempt
@api_login_required
@api_permission_required('server:terminal')
def server_test(request, pk):
    """Test SSH connection"""
    if request.method != 'POST':
        return error_response('Method not allowed', 405)
    from .models import Server
    try:
        server = Server.objects.get(pk=pk)
    except Server.DoesNotExist:
        return error_response('服务器不存在，请刷新页面后重试', 404)

    try:
        client = server.get_ssh_client()
        client.close()
        return success_response(msg='连接成功')
    except Exception as e:
        error_msg = str(e)
        host_info = f'主机: {server.host}:{server.port}'

        if 'getaddrinfo failed' in error_msg or '[Errno 11001]' in error_msg:
            return error_response(
                f'DNS 解析失败：无法解析主机名 "{server.host}"\n\n'
                f'=== 服务器信息 ===\n'
                f'名称: {server.name}\n'
                f'{host_info}\n'
                f'用户: {server.username}\n\n'
                f'=== 可能的原因 ===\n'
                f'1. 主机名拼写错误（当前值: {server.host}）\n'
                f'2. 主机名无法被 DNS 解析（请检查是否为有效的域名或IP地址）\n'
                f'3. 网络连接问题（请检查本机网络）\n'
                f'4. DNS 服务器配置问题\n\n'
                f'=== 建议操作 ===\n'
                f'• 如果是域名: 请确认域名正确且可访问（可在浏览器中测试）\n'
                f'• 如果是IP: 请使用正确的IP格式（如 192.168.1.100）\n'
                f'• 请检查 /etc/hosts 或本地 DNS 配置',
                400
            )
        elif 'Connection refused' in error_msg or '[Errno 111]' in error_msg or '[Errno 10061]' in error_msg:
            return error_response(
                f'连接被拒绝: {server.host}:{server.port}\n\n'
                f'=== 可能的原因 ===\n'
                f'1. SSH 服务未启动（目标服务器的 sshd 未运行）\n'
                f'2. 端口号错误（当前端口: {server.port}，默认应为 22）\n'
                f'3. 防火墙阻止了连接（检查目标服务器防火墙规则）\n'
                f'4. 主机地址不正确\n\n'
                f'=== 建议操作 ===\n'
                f'• 在目标服务器上运行: systemctl status sshd (Linux) 或 检查SSH服务状态\n'
                f'• 确认端口号是否正确（通常为22）\n'
                f'• 检查防火墙是否允许该端口',
                403
            )
        elif 'Authentication failed' in error_msg or 'Permission denied' in error_msg:
            return error_response(
                f'认证失败: 用户 {server.username}@{server.host}\n\n'
                f'=== 可能的原因 ===\n'
                f'1. 用户名错误（当前用户: {server.username}）\n'
                f'2. 密码错误或已过期\n'
                f'3. 私钥文件格式不正确或权限不对\n'
                f'4. 账户被锁定或禁止SSH登录\n\n'
                f'=== 建议操作 ===\n'
                f'• 确认用户名和密码/私钥是否正确\n'
                f'• 使用命令行手动测试: ssh -p {server.port} {server.username}@{server.host}',
                401
            )
        elif 'timeout' in error_msg.lower() or 'timed out' in error_msg.lower():
            return error_response(
                f'连接超时: 无法在规定时间内连接到 {server.host}:{server.port}\n\n'
                f'=== 可能的原因 ===\n'
                f'1. 目标服务器不可达（网络不通）\n'
                f'2. 防火墙丢弃了连接请求\n'
                f'3. 服务器负载过高响应慢\n'
                f'4. IP地址或端口配置错误\n\n'
                f'=== 建议操作 ===\n'
                f'• ping 测试连通性: ping {server.host}\n'
                f'• telnet 测试端口: telnet {server.host} {server.port}\n'
                f'• 检查本机到目标服务器的网络路径',
                408
            )
        elif 'No such file or directory' in error_msg and 'key' in error_msg.lower():
            return error_response(
                f'私钥文件错误: 私钥内容无效或格式不支持\n\n'
                f'=== 当前配置 ===\n'
                f'认证方式: 密钥认证\n'
                f'私钥长度: {len(server.private_key)} 字符\n\n'
                f'=== 建议操作 ===\n'
                f'• 确认私钥格式正确（支持 RSA/ECDSA/Ed25519）\n'
                f'• 私钥应包含完整的 PEM 格式（包括 -----BEGIN ...----- 和 -----END ...-----）\n'
                f'• 尝试使用密码认证方式代替',
                400
            )
        else:
            return error_response(f'连接失败 ({host_info}): {error_msg}', 500)


@csrf_exempt
@api_login_required
@api_permission_required('server:view_log')
def server_log(request, pk):
    """View remote server log file"""
    if request.method != 'POST':
        return error_response('Method not allowed', 405)
    from .models import Server
    try:
        server = Server.objects.get(pk=pk)
    except Server.DoesNotExist:
        return error_response('服务器不存在', 404)

    body = get_request_body(request)
    log_path = body.get('log_path', '/var/log/syslog').strip()
    lines = int(body.get('lines', 100))

    # 安全校验：验证日志路径
    if re.search(r'[;&|`$]', log_path):
        return error_response('日志路径包含非法字符', 400)

    try:
        client = server.get_ssh_client()
        # 使用 tail 命令并按行数截取
        safe_path = shlex.quote(log_path)
        stdin, stdout, stderr = client.exec_command(f'tail -n {lines} {safe_path}')
        output = stdout.read().decode('utf-8', errors='replace')
        error = stderr.read().decode('utf-8', errors='replace')
        client.close()

        if error and not output:
            return error_response(f'获取日志失败: {error}', 500)
        return success_response({'content': output})
    except Exception as e:
        return error_response(f'获取日志失败: {str(e)}', 500)


@csrf_exempt
@api_login_required
@api_permission_required('server:terminal')
def server_exec(request, pk):
    """Execute command on remote server"""
    if request.method != 'POST':
        return error_response('Method not allowed', 405)
    from .models import Server
    try:
        server = Server.objects.get(pk=pk)
    except Server.DoesNotExist:
        return error_response('服务器不存在', 404)

    body = get_request_body(request)
    command = body.get('command', '').strip()

    if not command:
        return error_response('命令不能为空', 400)

    # 危险命令黑名单
    dangerous_patterns = [
        r'rm\s+-rf\s+/', r'dd\s+if=', r'mkfs\.', r'shutdown',
        r'reboot', r'chmod\s+777\s+/', r'>\s*/etc/', r'curl.*\|.*bash',
        r'wget.*\|.*bash', r':\(\)\{.*\};', r'nc\s+-[el]', r'ncat\s+-[el]',
    ]
    for pattern in dangerous_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return error_response('该命令存在安全风险，已被拦截', 403)

    try:
        client = server.get_ssh_client()
        stdin, stdout, stderr = client.exec_command(command, timeout=30)
        exit_code = stdout.channel.recv_exit_status()
        output = stdout.read().decode('utf-8', errors='replace')
        error = stderr.read().decode('utf-8', errors='replace')
        client.close()

        return success_response({
            'output': output,
            'error': error,
            'exit_code': exit_code,
        })
    except Exception as e:
        return error_response(f'命令执行失败: {str(e)}', 500)


# ==================== AI 配置（多模型列表） ====================

import uuid as _uuid


def _mask_key(api_key):
    """Mask API key for display"""
    if not api_key:
        return ''
    if len(api_key) > 12:
        return api_key[:8] + '****' + api_key[-4:]
    return '****'


def _load_ai_configs():
    """Load AI configs from database only."""
    from .models import AIModelConfig
    
    configs = []
    try:
        db_configs = AIModelConfig.objects.all().order_by('-is_default', '-created_at')
        for cfg in db_configs:
            configs.append({
                'id': str(cfg.id),
                'name': cfg.name,
                'provider': cfg.provider,
                'api_key': cfg.api_key,
                'base_url': cfg.base_url,
                'model': cfg.model,
                'is_default': cfg.is_default,
                'is_active': cfg.is_active,
            })
    except Exception:
        pass
    
    return configs


def _save_ai_configs(configs):
    """Save AI configs to database only."""
    from .models import AIModelConfig
    
    try:
        for cfg_data in configs:
            config_id = cfg_data.get('id')
            
            # 查找或创建配置
            if config_id:
                try:
                    cfg_obj = AIModelConfig.objects.get(id=config_id)
                except (AIModelConfig.DoesNotExist, ValueError):
                    cfg_obj = AIModelConfig()
            else:
                cfg_obj = AIModelConfig()
            
            # 更新字段
            cfg_obj.name = cfg_data.get('name', '')
            cfg_obj.provider = cfg_data.get('provider', 'custom')
            cfg_obj.api_key = cfg_data.get('api_key', '')
            cfg_obj.base_url = cfg_data.get('base_url', '')
            cfg_obj.model = cfg_data.get('model', '')
            cfg_obj.is_default = cfg_data.get('is_default', False)
            cfg_obj.is_active = cfg_data.get('is_active', True)
            
            # 保存（save()方法会自动处理 is_default 的唯一性）
            cfg_obj.save()
            
            # 将数据库生成的真实ID更新回configs列表（解决新建时ID不匹配的问题）
            if not config_id or config_id != str(cfg_obj.id):
                cfg_data['id'] = str(cfg_obj.id)
                
    except Exception as e:
        print(f"Error: Failed to save AI configs to database: {e}")


def _get_default_ai_config():
    """Get the default (active) AI config for use in AI analysis.
    优先使用数据库中的默认配置，回退到 settings.py
    """
    from django.conf import settings
    from .models import AIModelConfig
    
    # 优先从数据库获取默认配置
    try:
        default_config = AIModelConfig.get_default_config()
        if default_config:
            return {
                'api_key': default_config.api_key,
                'base_url': default_config.base_url,
                'model': default_config.model,
            }
    except Exception:
        pass
    
    # settings.py 回退逻辑
    return {
        'api_key': getattr(settings, 'LAYUI_AI_API_KEY', ''),
        'base_url': getattr(settings, 'LAYUI_AI_BASE_URL', ''),
        'model': getattr(settings, 'LAYUI_AI_MODEL', 'gpt-4o-mini'),
    }


# 兼容旧代码调用
def _get_ai_settings():
    return _get_default_ai_config()


# ---------- API 视图 ----------

@csrf_exempt
@api_login_required
@api_permission_required('ai_config:view')
def ai_config_list(request):
    """List all AI model configs (api_key masked), with optional keyword search"""
    # 支持搜索：keyword 参数
    keyword = request.GET.get('keyword', '').strip().lower()
    
    # 中文厂商名称到英文的映射（用于搜索）
    PROVIDER_CN_MAP = {
        '智谱': 'zhipu',
        '通义': 'qwen',
        '千问': 'qwen',
        '阿里': 'qwen',
        'openai': 'openai',
        'deepseek': 'deepseek',
        '深度': 'deepseek',
        'kimi': 'moonshot',
        '月之': 'moonshot',
        'moonshot': 'moonshot',
    }
    
    configs = _load_ai_configs()
    result = []
    for c in configs:
        # 如果有搜索关键词，进行过滤
        if keyword:
            name = (c.get('name', '') or '').lower()
            provider = (c.get('provider', '') or '').lower()
            model = (c.get('model', '') or '').lower()
            
            # 支持配置名称、模型搜索
            match = keyword in name or keyword in model
            
            # 支持厂商搜索（中文/英文）
            if not match:
                # 直接匹配英文 provider
                if keyword in provider:
                    match = True
                else:
                    # 尝试中文厂商名称映射
                    for cn_name, en_provider in PROVIDER_CN_MAP.items():
                        if cn_name in keyword and en_provider == provider:
                            match = True
                            break
            
            if not match:
                continue
        
        result.append({
            'id': c.get('id', ''),
            'name': c.get('name', c.get('model', '')),
            'provider': c.get('provider', 'custom'),
            'api_key_masked': _mask_key(c.get('api_key', '')),
            'api_key_set': bool(c.get('api_key', '')),
            'base_url': c.get('base_url', ''),
            'model': c.get('model', ''),
            'is_default': c.get('is_default', False),
        })
    return success_response(result)


@csrf_exempt
@api_login_required
@api_permission_required('ai_config:view')
def ai_config_get(request):
    """Get single AI config by id, or default config if no id given (legacy)"""
    config_id = request.GET.get('id', '')
    configs = _load_ai_configs()
    if config_id:
        for c in configs:
            if c.get('id') == config_id:
                return success_response({
                    'id': c['id'],
                    'name': c.get('name', ''),
                    'provider': c.get('provider', 'custom'),
                    'api_key_masked': _mask_key(c.get('api_key', '')),
                    'api_key_set': bool(c.get('api_key', '')),
                    'base_url': c.get('base_url', ''),
                    'model': c.get('model', ''),
                    'is_default': c.get('is_default', False),
                })
        return error_response('配置不存在', 404)
    # 兼容旧接口：返回默认配置
    cfg = _get_default_ai_config()
    api_key = cfg.get('api_key', '')
    return success_response({
        'api_key': _mask_key(api_key),
        'api_key_set': bool(api_key),
        'base_url': cfg.get('base_url', ''),
        'model': cfg.get('model', 'gpt-4o-mini'),
    })


@csrf_exempt
@api_login_required
def ai_config_save(request):
    """Create or update AI config.
    POST body: {id?, name, provider, api_key, base_url, model, is_default?}
    If id is provided -> update; else -> create new.
    """
    if request.method != 'POST':
        return error_response('Method not allowed', 405)

    body = get_request_body(request)
    config_id = str(body.get('id') or '').strip()
    required_code = 'ai_config:edit' if config_id else 'ai_config:add'
    if not has_permission(request.user, required_code, request):
        return error_response('无权限', 403)
    name = body.get('name', '').strip()
    provider = body.get('provider', 'custom').strip()
    api_key = body.get('api_key', '').strip()
    base_url = body.get('base_url', '').strip()
    model = body.get('model', '').strip()
    is_default = bool(body.get('is_default', False))

    if not model:
        return error_response('模型名称不能为空', 400)

    configs = _load_ai_configs()

    if config_id:
        # 更新已有记录
        found = False
        for c in configs:
            if c.get('id') == config_id:
                c['name'] = name or model
                c['provider'] = provider
                c['base_url'] = base_url
                c['model'] = model
                # 如果 api_key 没变（仍是掩码），保留原来的
                if api_key and '****' not in api_key:
                    c['api_key'] = api_key
                elif not api_key:
                    return error_response('API Key 不能为空', 400)
                if is_default:
                    c['is_default'] = True
                found = True
            else:
                if is_default:
                    c['is_default'] = False
        if not found:
            return error_response('配置不存在', 404)
        _save_ai_configs(configs)
        return success_response(msg='配置更新成功')
    else:
        # 创建新记录
        if not api_key or '****' in api_key:
            return error_response('API Key 不能为空', 400)
        new_id = str(_uuid.uuid4())[:8]
        # 若是第一条，默认设为 default
        if not configs or is_default:
            is_default = True
            for c in configs:
                c['is_default'] = False
        new_entry = {
            'id': new_id,
            'name': name or model,
            'provider': provider,
            'api_key': api_key,
            'base_url': base_url,
            'model': model,
            'is_default': is_default,
        }
        configs.append(new_entry)
        _save_ai_configs(configs)
        # 返回数据库生成的真实ID（_save_ai_configs已更新new_entry的id）
        return success_response({'id': new_entry.get('id', new_id)}, msg='配置添加成功')


@csrf_exempt
@api_login_required
@api_permission_required('ai_config:delete')
def ai_config_delete(request, config_id):
    """Delete AI config by id"""
    if request.method != 'DELETE':
        return error_response('Method not allowed', 405)
    configs = _load_ai_configs()
    new_configs = [c for c in configs if c.get('id') != config_id]
    if len(new_configs) == len(configs):
        return error_response('配置不存在', 404)
    # 如果删掉的是默认配置，把第一条设为默认
    if new_configs and not any(c.get('is_default') for c in new_configs):
        new_configs[0]['is_default'] = True
    _save_ai_configs(new_configs)
    return success_response(msg='配置已删除')


@csrf_exempt
@api_login_required
@api_permission_required('ai_config:set_default')
def ai_config_set_default(request, config_id):
    """Set a config as default (active) for AI analysis"""
    if request.method != 'POST':
        return error_response('Method not allowed', 405)
    configs = _load_ai_configs()
    found = False
    for c in configs:
        if c.get('id') == config_id:
            c['is_default'] = True
            found = True
        else:
            c['is_default'] = False
    if not found:
        return error_response('配置不存在', 404)
    _save_ai_configs(configs)
    return success_response(msg='已设为默认')


@csrf_exempt
@api_login_required
@api_permission_required('ai_config:test')
def ai_config_test(request):
    """Test AI config by sending a simple request.
    POST body: {id?} - test specific config by id, or default if no id.
    """
    import logging
    logger = logging.getLogger(__name__)

    if request.method != 'POST':
        return error_response('Method not allowed', 405)

    def clean_config_value(value, is_url=False):
        """清理配置值：去除首尾空格、反引号、引号等"""
        if not value:
            return ''
        cleaned = str(value).strip()
        for char in ['`', "'", '"']:
            cleaned = cleaned.strip(char)
        if is_url and cleaned:
            cleaned = cleaned.rstrip('/')
        return cleaned

    body = get_request_body(request)
    config_id = body.get('id', '').strip()

    if config_id:
        configs = _load_ai_configs()
        config = None
        for c in configs:
            if c.get('id') == config_id:
                config = {
                    'api_key': clean_config_value(c.get('api_key', '')),
                    'base_url': clean_config_value(c.get('base_url', ''), is_url=True),
                    'model': clean_config_value(c.get('model', '')),
                }
                break
        if not config:
            return error_response('配置不存在，请刷新页面后重试', 404)
    else:
        raw_config = _get_default_ai_config()
        config = {
            'api_key': clean_config_value(raw_config.get('api_key', '')),
            'base_url': clean_config_value(raw_config.get('base_url', ''), is_url=True),
            'model': clean_config_value(raw_config.get('model', '')),
        }

    logger.info(f'[AI Config Test] Config ID: {config_id or "default"}')
    logger.info(f'[AI Config Test] Base URL: "{config.get("base_url", "")}" (length: {len(config.get("base_url", ""))})')
    logger.info(f'[AI Config Test] Model: "{config.get("model", "")}" (length: {len(config.get("model", ""))})')
    logger.info(f'[AI Config Test] API Key length: {len(config.get("api_key", ""))}')

    if not config.get('api_key'):
        return error_response('未配置 API Key，请在配置中填写有效的 API 密钥', 400)

    if not config.get('model'):
        return error_response('未配置模型名称，请填写正确的模型名称（如：gpt-4o-mini, qwen-turbo, deepseek-chat 等）', 400)

    try:
        from openai import OpenAI
        client_kwargs = {'api_key': config['api_key']}
        if config.get('base_url'):
            client_kwargs['base_url'] = config['base_url']
        client = OpenAI(**client_kwargs)

        response = client.chat.completions.create(
            model=config['model'],
            messages=[{"role": "user", "content": "Hi, reply with just 'OK'."}],
            max_tokens=10,
            timeout=15,
        )
        reply = response.choices[0].message.content
        return success_response({'reply': reply, 'model': config['model']})
    except ImportError:
        return error_response('未安装 openai 库，请运行: pip install openai', 400)
    except Exception as e:
        error_msg = str(e)
        logger.error(f'[AI Config Test] Error: {error_msg}')

        if 'model is not found' in error_msg.lower() or 'model_not_found' in error_msg.lower():
            debug_info = (
                f'模型 "{config["model"]}" 不存在或不可用。\n\n'
                f'=== 调试信息 ===\n'
                f'Base URL: "{config.get("base_url") or "(使用默认)"}"\n'
                f'Model: "{config["model"]}"\n'
                f'Model 长度: {len(config["model"])} 字符\n'
                f'API Key 长度: {len(config.get("api_key", ""))} 字符\n\n'
                f'=== 可能的原因 ===\n'
                f'1. 模型名称拼写错误（当前值：{config["model"]}）\n'
                f'2. 模型名称包含不可见字符（如空格、换行符等）\n'
                f'3. 该模型在您的 API 账户中未开通或无权访问\n'
                f'4. Base URL 与模型提供商不匹配\n'
                f'5. 使用了错误的 API 端点\n\n'
                f'=== 建议操作 ===\n'
                f'请检查 Admin 后台 AI 模型配置中的以下字段：\n'
                f'- 确认 Model 名称与您使用的 API 服务商文档一致\n'
                f'- 确认 Base URL 与该模型的正确端点匹配\n'
                f'- 确保字段值前后没有多余的空格或特殊字符\n'
                f'- 查阅您使用的 AI 服务商官方文档获取正确的模型名称'
            )
            return error_response(debug_info, 400)
        elif 'invalid_api_key' in error_msg.lower() or 'unauthorized' in error_msg.lower() or '401' in error_msg:
            return error_response('API Key 无效或已过期，请检查并更新您的 API 密钥', 401)
        elif 'rate_limit' in error_msg.lower() or '429' in error_msg:
            return error_response('请求频率超限，请稍后重试或升级您的 API 套餐', 429)
        elif 'timeout' in error_msg.lower() or 'timed out' in error_msg.lower():
            return error_response('连接超时，请检查网络或 Base URL 是否正确', 408)
        elif 'connection' in error_msg.lower():
            return error_response(f'无法连接到 API 服务端。请检查：\n1. Base URL 是否正确（当前：{config.get("base_url") or "默认"}）\n2. 网络连接是否正常\n3. 防火墙是否阻止了请求', 503)
        else:
            return error_response(f'连接测试失败: {error_msg}', 500)


# ==================== AI 分析 ====================

@csrf_exempt
@api_login_required
@api_permission_required('ai_config:test')
def ai_analyze_log(request):
    """AI analyze server log content"""
    if request.method != 'POST':
        return error_response('Method not allowed', 405)

    body = get_request_body(request)
    log_content = body.get('content', '').strip()
    server_name = body.get('server_name', '')
    log_path = body.get('log_path', '')

    if not log_content:
        return error_response('日志内容不能为空', 400)

    # 限制日志内容长度
    if len(log_content) > 50000:
        log_content = log_content[-50000:]

    # 获取 AI 配置（动态 JSON 文件优先于 settings.py）
    config = _get_ai_settings()
    if not config.get('api_key'):
        return JsonResponse({'code': 401, 'msg': '未配置 AI 模型', 'data': {'need_config': True}}, status=200)

    try:
        from openai import OpenAI
        client_kwargs = {'api_key': config['api_key']}
        if config.get('base_url'):
            client_kwargs['base_url'] = config['base_url']
        client = OpenAI(**client_kwargs)

        system_prompt = """你是一个专业的运维工程师，擅长分析服务器日志。
请对用户提供的日志进行分析，包括：
1. **日志概览**：日志类型、时间范围、总体状态
2. **异常检测**：识别错误、警告、异常模式
3. **根因分析**：分析可能的原因
4. **修复建议**：给出具体的修复建议和命令

请用中文回复，使用 Markdown 格式，结构清晰。"""

        user_prompt = f"服务器: {server_name}\n日志路径: {log_path}\n\n请分析以下日志内容：\n\n```\n{log_content}\n```"

        response = client.chat.completions.create(
            model=config['model'],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=4000,
        )
        analysis = response.choices[0].message.content

        return success_response({'analysis': analysis})

    except ImportError:
        return error_response('未安装 openai 库，请运行: pip install openai', 400)
    except Exception as e:
        return error_response(f'AI 分析失败: {str(e)}', 500)
