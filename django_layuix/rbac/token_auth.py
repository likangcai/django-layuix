"""
Token认证工具
支持JWT-like token生成和验证，用于SSE等需要长连接的场景
"""
import hashlib
import hmac
import time
import json
import base64
from django.conf import settings
from django.contrib.auth import get_user_model


RESERVED_TOKEN_FIELDS = {'user_id', 'username', 'exp', 'iat', 'active_roles'}


def _token_expire_seconds():
    return getattr(settings, 'TOKEN_EXPIRE_SECONDS', 24 * 60 * 60)


def generate_token(user, extra_data=None, active_roles=None):
    """
    生成认证token。

    active_roles 会被签入 payload，使 Bearer Token 路径遵守 DSD 选择；
    未传时读取 user._layui_active_role_ids（由会话或主动切换写入）。
    """
    timestamp = int(time.time())
    payload = {
        'user_id': user.id,
        'username': user.username,
        'exp': timestamp + _token_expire_seconds(),
        'iat': timestamp,
    }

    roles = active_roles
    if roles is None:
        roles = getattr(user, '_layui_active_role_ids', None)
    if roles is not None:
        payload['active_roles'] = sorted({
            int(value) for value in roles
            if str(value).isdigit()
        })

    if extra_data:
        payload.update({
            key: value for key, value in extra_data.items()
            if key not in RESERVED_TOKEN_FIELDS
        })

    # 使用用户的密码哈希作为secret key的一部分，确保密码修改后token失效
    user_secret = getattr(user, 'password', '')
    secret_key = getattr(settings, 'SECRET_KEY', '')
    
    # 创建payload字符串
    payload_str = json.dumps(payload, sort_keys=True)
    payload_b64 = base64.urlsafe_b64encode(payload_str.encode()).decode().rstrip('=')
    
    # 创建签名
    signature_str = f"{payload_str}.{user_secret}.{secret_key}"
    signature = hashlib.sha256(signature_str.encode()).hexdigest()
    
    # 组合token
    token = f"{payload_b64}.{signature}"
    
    return token


def verify_token(token):
    """
    验证token
    
    Args:
        token: token字符串
    
    Returns:
        dict: {'valid': bool, 'user': User, 'payload': dict} 或 {'valid': False, 'error': str}
    """
    if not token:
        return {'valid': False, 'error': 'Token is required'}
    
    try:
        parts = token.split('.')
        if len(parts) != 2:
            return {'valid': False, 'error': 'Invalid token format'}
        
        payload_b64, signature = parts
        
        # 解码payload
        payload_str = base64.urlsafe_b64decode(payload_b64 + '==').decode()
        payload = json.loads(payload_str)
        
        # 验证过期时间
        if 'exp' not in payload or payload['exp'] < time.time():
            return {'valid': False, 'error': 'Token expired'}
        
        # 获取用户
        User = get_user_model()
        try:
            user = User.objects.get(id=payload.get('user_id'))
        except User.DoesNotExist:
            return {'valid': False, 'error': 'User not found'}
        if not getattr(user, 'is_active', True):
            return {'valid': False, 'error': 'User inactive'}

        # 验证签名
        user_secret = getattr(user, 'password', '')
        secret_key = getattr(settings, 'SECRET_KEY', '')

        expected_signature_str = f"{payload_str}.{user_secret}.{secret_key}"
        expected_signature = hashlib.sha256(expected_signature_str.encode()).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
            return {'valid': False, 'error': 'Invalid signature'}
        
        # 验证用户名是否匹配
        if payload.get('username') != user.username:
            return {'valid': False, 'error': 'Username mismatch'}

        if 'active_roles' in payload:
            user._layui_active_role_ids = list(payload['active_roles'])

        return {
            'valid': True,
            'user': user,
            'payload': payload
        }
        
    except Exception as e:
        return {'valid': False, 'error': f'Token verification failed: {str(e)}'}


def token_authenticate(request):
    """
    从request中获取token并认证用户
    
    支持多种方式获取token：
    1. Header: Authorization: Bearer <token>
    2. Query参数: ?token=<token>
    3. POST body: {"token": "<token>"}
    
    Args:
        request: Django request对象
    
    Returns:
        User or None: 认证的用户对象，失败返回None
    """
    token = None
    
    # 1. 从Authorization header获取
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header.lower().startswith('bearer '):
        token = auth_header[7:].strip()
    
    # 2. 从X-Token header获取（备选）
    if not token:
        token = request.META.get('HTTP_X_TOKEN')
    
    # 3. query token 仅用于 SSE 等明确允许的场景，避免泄漏到日志/历史记录
    if not token:
        query_allowed = (
            getattr(settings, 'LAYUI_ALLOW_QUERY_TOKEN', False)
            or str(request.path).endswith('/system/info/stream/')
        )
        if query_allowed:
            token = request.GET.get('token')
    
    # 4. 从POST body获取
    if not token and request.method == 'POST':
        try:
            import json
            body = json.loads(request.body)
            token = body.get('token')
        except (json.JSONDecodeError, TypeError, AttributeError, ValueError):
            pass
    
    if not token:
        return None
    
    # 验证token
    result = verify_token(token)
    if result['valid']:
        return result['user']
    
    return None
