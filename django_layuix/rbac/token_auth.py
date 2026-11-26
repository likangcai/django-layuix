"""
JWT authentication helpers.

Issues standards-compatible HS256 JWTs (header.payload.signature) with a jti,
persists token state in ``sys_auth_token`` and the Django cache backend
(Redis when configured), and keeps a verifier for pre-1.4.4 two-part tokens.
"""
import base64
import hashlib
import hmac
import json
import secrets
import time
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone

from .models import AuthToken


RESERVED_TOKEN_FIELDS = {
    'user_id', 'username', 'exp', 'iat', 'active_roles',
    'jti', 'sub', 'iss',
}
DEFAULT_ISSUER = 'django-layuix'


def _token_expire_seconds():
    return int(getattr(settings, 'TOKEN_EXPIRE_SECONDS', 24 * 60 * 60))


def _jwt_issuer():
    return getattr(settings, 'LAYUI_JWT_ISSUER', DEFAULT_ISSUER)


def _allow_legacy_token():
    return getattr(settings, 'LAYUIX_ALLOW_LEGACY_TOKEN', True)


def _cache_prefix():
    return getattr(settings, 'LAYUIX_TOKEN_CACHE_PREFIX', 'layuix:auth:')


def _token_cache_key(jti):
    return '%stoken:%s' % (_cache_prefix(), jti)


def _user_index_key(user_id):
    return '%suser:%s:tokens' % (_cache_prefix(), user_id)


def _safe_cache_get(key):
    try:
        return cache.get(key)
    except Exception:
        return None


def _safe_cache_set(key, value, timeout):
    try:
        cache.set(key, value, timeout=max(1, int(timeout)))
    except Exception:
        pass


def _safe_cache_delete(key):
    try:
        cache.delete(key)
    except Exception:
        pass


def _legacy_fingerprint(payload_str):
    return hashlib.sha256(payload_str.encode()).hexdigest()


def _b64url_encode(value):
    if isinstance(value, str):
        value = value.encode()
    return base64.urlsafe_b64encode(value).decode().rstrip('=')


def _b64url_decode(value):
    padding = '=' * ((4 - len(value) % 4) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _signing_secret(user):
    return ('%s.%s' % (
        getattr(settings, 'SECRET_KEY', ''),
        getattr(user, 'password', ''),
    )).encode()


def _client_info(request):
    if not request:
        return '', ''
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    ip = forwarded.split(',')[0].strip() if forwarded else request.META.get('REMOTE_ADDR', '')
    return ip[:64], request.META.get('HTTP_USER_AGENT', '')[:255]


def _active_roles_payload(user, active_roles):
    roles = active_roles
    if roles is None:
        roles = getattr(user, '_layui_active_role_ids', None)
    if roles is None:
        return None
    return sorted({int(value) for value in roles if str(value).isdigit()})


def generate_token(user, extra_data=None, active_roles=None, request=None):
    """Issue a signed HS256 JWT and persist its state."""
    issued = int(time.time())
    ttl = _token_expire_seconds()
    expires = issued + ttl
    jti = secrets.token_hex(32)
    payload = {
        'sub': str(user.id),
        'user_id': user.id,
        'username': user.username,
        'iat': issued,
        'exp': expires,
        'jti': jti,
        'iss': _jwt_issuer(),
    }
    roles = _active_roles_payload(user, active_roles)
    if roles is not None:
        payload['active_roles'] = roles
    if extra_data:
        payload.update({
            key: value for key, value in extra_data.items()
            if key not in RESERVED_TOKEN_FIELDS
        })

    header = {'alg': 'HS256', 'typ': 'JWT'}
    header_b64 = _b64url_encode(json.dumps(header, sort_keys=True, separators=(',', ':')))
    payload_b64 = _b64url_encode(json.dumps(payload, sort_keys=True, separators=(',', ':')))
    signing_input = ('%s.%s' % (header_b64, payload_b64)).encode()
    signature = hmac.new(_signing_secret(user), signing_input, hashlib.sha256).digest()
    token = '%s.%s.%s' % (header_b64, payload_b64, _b64url_encode(signature))

    ip, user_agent = _client_info(request)
    AuthToken.objects.create(
        user=user,
        jti=jti,
        issued_at=timezone.now(),
        expires_at=timezone.now() + timedelta(seconds=ttl),
        client_ip=ip,
        user_agent=user_agent,
    )
    state = {'status': 1, 'user_id': user.id, 'exp': expires}
    _safe_cache_set(_token_cache_key(jti), state, ttl)
    index_key = _user_index_key(user.id)
    index = _safe_cache_get(index_key) or []
    if jti not in index:
        index.append(jti)
    _safe_cache_set(index_key, index, ttl * 2)
    return token


def _check_token_state(payload, user):
    jti = payload.get('jti')
    if not jti:
        return False
    cached = _safe_cache_get(_token_cache_key(jti))
    if cached and cached.get('status') == 0:
        return False
    record = AuthToken.objects.filter(jti=jti).first()
    if not record or record.status != 1 or record.user_id != user.id:
        return False
    if record.expires_at and record.expires_at < timezone.now():
        return False
    remaining = max(1, int(payload.get('exp', 0) - time.time()))
    _safe_cache_set(_token_cache_key(jti), {
        'status': 1, 'user_id': user.id, 'exp': payload.get('exp', 0),
    }, remaining)
    return True


def _verify_standard_token(token):
    parts = token.split('.')
    if len(parts) != 3:
        return None
    header_b64, payload_b64, signature_b64 = parts
    try:
        header = json.loads(_b64url_decode(header_b64).decode())
        payload = json.loads(_b64url_decode(payload_b64).decode())
    except Exception:
        return {'valid': False, 'error': 'Invalid JWT encoding'}
    if header.get('alg') != 'HS256' or header.get('typ') != 'JWT':
        return {'valid': False, 'error': 'Unsupported JWT algorithm'}
    if payload.get('iss') != _jwt_issuer():
        return {'valid': False, 'error': 'Invalid JWT issuer'}
    if 'exp' not in payload or payload['exp'] < time.time():
        return {'valid': False, 'error': 'Token expired'}

    User = get_user_model()
    try:
        user = User.objects.get(id=int(payload.get('sub') or payload.get('user_id')))
    except (User.DoesNotExist, TypeError, ValueError):
        return {'valid': False, 'error': 'User not found'}
    if not getattr(user, 'is_active', True):
        return {'valid': False, 'error': 'User inactive'}

    signing_input = ('%s.%s' % (header_b64, payload_b64)).encode()
    expected = hmac.new(_signing_secret(user), signing_input, hashlib.sha256).digest()
    try:
        signature = _b64url_decode(signature_b64)
    except Exception:
        return {'valid': False, 'error': 'Invalid JWT signature'}
    if not hmac.compare_digest(signature, expected):
        return {'valid': False, 'error': 'Invalid signature'}
    if payload.get('username') != user.username:
        return {'valid': False, 'error': 'Username mismatch'}
    if not _check_token_state(payload, user):
        return {'valid': False, 'error': 'Token revoked or unknown'}

    if 'active_roles' in payload:
        user._layui_active_role_ids = list(payload['active_roles'])
    return {'valid': True, 'user': user, 'payload': payload}


def _verify_legacy_token(token):
    """Verify pre-1.4.4 two-part tokens during the transition window."""
    if not _allow_legacy_token():
        return {'valid': False, 'error': 'Legacy tokens are disabled'}
    parts = token.split('.')
    if len(parts) != 2:
        return {'valid': False, 'error': 'Invalid token format'}
    payload_b64, signature = parts
    try:
        payload_str = _b64url_decode(payload_b64).decode()
        payload = json.loads(payload_str)
    except Exception:
        return {'valid': False, 'error': 'Invalid token encoding'}
    legacy_jti = _legacy_fingerprint(payload_str)
    legacy_state = _safe_cache_get(_token_cache_key(legacy_jti))
    if legacy_state and legacy_state.get('status') == 0:
        return {'valid': False, 'error': 'Token revoked'}
    if AuthToken.objects.filter(jti=legacy_jti, status=0).exists():
        return {'valid': False, 'error': 'Token revoked'}
    if 'exp' not in payload or payload['exp'] < time.time():
        return {'valid': False, 'error': 'Token expired'}
    User = get_user_model()
    try:
        user = User.objects.get(id=payload.get('user_id'))
    except User.DoesNotExist:
        return {'valid': False, 'error': 'User not found'}
    if not getattr(user, 'is_active', True):
        return {'valid': False, 'error': 'User inactive'}
    expected = hashlib.sha256((
        '%s.%s.%s' % (payload_str, getattr(user, 'password', ''), settings.SECRET_KEY)
    ).encode()).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return {'valid': False, 'error': 'Invalid signature'}
    if payload.get('username') != user.username:
        return {'valid': False, 'error': 'Username mismatch'}
    if 'active_roles' in payload:
        user._layui_active_role_ids = list(payload['active_roles'])
    return {'valid': True, 'user': user, 'payload': payload}


def verify_token(token):
    if not token:
        return {'valid': False, 'error': 'Token is required'}
    try:
        if len(token.split('.')) == 3:
            return _verify_standard_token(token)
        return _verify_legacy_token(token)
    except Exception as exc:
        return {'valid': False, 'error': 'Token verification failed: %s' % exc}


def revoke_token(token, reason='logout', user=None):
    """Revoke a token after verifying it belongs to ``user`` when supplied."""
    result = verify_token(token)
    if not result.get('valid'):
        return 0
    token_user = result['user']
    if user is not None and getattr(user, 'pk', None) != token_user.pk:
        return 0

    payload = result['payload']
    parts = token.split('.')
    jti = payload.get('jti') or (
        _legacy_fingerprint(_b64url_decode(parts[0]).decode())
        if len(parts) == 2 else None
    )
    if not jti:
        return 0
    remaining = max(1, int(payload.get('exp', 0) - time.time()))
    revoked_at = timezone.now()
    expires_at = revoked_at + timedelta(seconds=remaining)
    record, created = AuthToken.objects.get_or_create(
        jti=jti,
        defaults={
            'user': token_user,
            'token_type': 'legacy' if len(parts) == 2 else 'access',
            'status': 0,
            'issued_at': revoked_at,
            'expires_at': expires_at,
            'revoked_at': revoked_at,
            'revoke_reason': reason,
        },
    )
    if not created:
        updated = AuthToken.objects.filter(jti=jti).update(
            status=0, revoked_at=revoked_at, revoke_reason=reason,
        )
    else:
        updated = 1
    _safe_cache_set(_token_cache_key(jti), {
        'status': 0, 'user_id': token_user.id, 'exp': payload.get('exp', 0),
    }, remaining)
    return updated


def revoke_user_tokens(user, reason='password_change'):
    """Revoke all active tokens for a user."""
    records = list(AuthToken.objects.filter(user=user, status=1))
    revoked_at = timezone.now()
    for record in records:
        record.status = 0
        record.revoked_at = revoked_at
        record.revoke_reason = reason
        record.save(update_fields=['status', 'revoked_at', 'revoke_reason', 'update_time'])
        remaining = max(1, int((record.expires_at - timezone.now()).total_seconds()))
        _safe_cache_set(_token_cache_key(record.jti), {
            'status': 0, 'user_id': user.id, 'exp': int(record.expires_at.timestamp()),
        }, remaining)
    _safe_cache_delete(_user_index_key(user.id))
    return len(records)


def cleanup_expired_tokens():
    expired = AuthToken.objects.filter(expires_at__lt=timezone.now())
    jtis = list(expired.values_list('jti', flat=True))
    deleted = expired.delete()[0]
    for jti in jtis:
        _safe_cache_delete(_token_cache_key(jti))
    return deleted


def generate_stream_ticket(user, ttl=60):
    """Issue a short-lived ticket for EventSource URLs instead of a JWT."""
    ticket = secrets.token_hex(32)
    expires = int(time.time()) + max(1, int(ttl))
    _safe_cache_set('%sstream:%s' % (_cache_prefix(), ticket), {
        'user_id': user.id, 'exp': expires,
    }, expires - int(time.time()))
    return ticket


def verify_stream_ticket(ticket):
    if not ticket:
        return None
    data = _safe_cache_get('%sstream:%s' % (_cache_prefix(), ticket))
    if not data or data.get('exp', 0) < time.time():
        return None
    User = get_user_model()
    user = User.objects.filter(id=data.get('user_id'), is_active=True).first()
    return user


def token_authenticate(request):
    """Resolve a user from Authorization Bearer, X-Token, query or POST body."""
    token = None
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header.lower().startswith('bearer '):
        token = auth_header[7:].strip()
    if not token:
        token = request.META.get('HTTP_X_TOKEN')
    if not token and str(request.path).endswith('/system/info/stream/'):
        user = verify_stream_ticket(request.GET.get('stream_ticket'))
        if user is not None:
            return user
    if not token and getattr(settings, 'LAYUI_ALLOW_QUERY_TOKEN', False):
        token = request.GET.get('token')
    if not token:
        return None
    result = verify_token(token)
    return result.get('user') if result.get('valid') else None
