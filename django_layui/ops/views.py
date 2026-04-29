# -*- coding: utf-8 -*-
"""
Ops API Views - Server CRUD, SSH test, log viewing, command execution
"""
import re
import shlex
import json
from functools import wraps
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


def api_login_required(view_func):
    """Login required decorator for API views"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'code': 401, 'msg': '未登录'}, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper


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


# ==================== Server CRUD ====================

@csrf_exempt
@api_login_required
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
        'create_time': s.create_time.strftime('%Y-%m-%d %H:%M:%S') if s.create_time else '',
    } for s in servers]

    return success_response({'list': data, 'total': total, 'page': page, 'page_size': page_size})


@csrf_exempt
@api_login_required
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
    # Sensitive fields: only update if explicitly provided and non-empty
    for field in ['password', 'private_key']:
        if field in body and body[field]:
            setattr(server, field, body[field])
    server.save()
    return success_response(msg='更新成功')


@csrf_exempt
@api_login_required
def server_detail(request, pk):
    """Get server detail (with password/private_key for edit form)"""
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


# ==================== SSH Operations ====================

@csrf_exempt
@api_login_required
def server_test(request, pk):
    """Test SSH connection"""
    if request.method != 'POST':
        return error_response('Method not allowed', 405)
    from .models import Server
    try:
        server = Server.objects.get(pk=pk)
    except Server.DoesNotExist:
        return error_response('服务器不存在', 404)

    try:
        client = server.get_ssh_client()
        client.close()
        return success_response(msg='连接成功')
    except Exception as e:
        return error_response(f'连接失败: {str(e)}', 500)


@csrf_exempt
@api_login_required
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

    # Security: validate log path
    if re.search(r'[;&|`$]', log_path):
        return error_response('日志路径包含非法字符', 400)

    try:
        client = server.get_ssh_client()
        # Use tail command with line count
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

    # Dangerous command blacklist
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


# ==================== AI Config (Multi-model list) ====================

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
                except AIModelConfig.DoesNotExist:
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
    
    # settings.py fallback
    return {
        'api_key': getattr(settings, 'LAYUI_AI_API_KEY', ''),
        'base_url': getattr(settings, 'LAYUI_AI_BASE_URL', ''),
        'model': getattr(settings, 'LAYUI_AI_MODEL', 'gpt-4o-mini'),
    }


# 兼容旧代码调用
def _get_ai_settings():
    return _get_default_ai_config()


# ---------- API Views ----------

@csrf_exempt
@api_login_required
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
    config_id = body.get('id', '').strip()
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
        # Update existing
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
        # Create new
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
        return success_response({'id': new_id}, msg='配置添加成功')


@csrf_exempt
@api_login_required
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
def ai_config_test(request):
    """Test AI config by sending a simple request.
    POST body: {id?} - test specific config by id, or default if no id.
    """
    if request.method != 'POST':
        return error_response('Method not allowed', 405)

    body = get_request_body(request)
    config_id = body.get('id', '').strip()

    if config_id:
        configs = _load_ai_configs()
        config = None
        for c in configs:
            if c.get('id') == config_id:
                config = {'api_key': c.get('api_key', ''), 'base_url': c.get('base_url', ''), 'model': c.get('model', '')}
                break
        if not config:
            return error_response('配置不存在', 404)
    else:
        config = _get_default_ai_config()

    if not config.get('api_key'):
        return error_response('未配置 API Key', 400)

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
        return error_response(f'连接测试失败: {str(e)}', 500)


# ==================== AI Analysis ====================

@csrf_exempt
@api_login_required
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

    # Limit log content length
    if len(log_content) > 50000:
        log_content = log_content[-50000:]

    # Get AI config (dynamic JSON file > settings.py)
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
