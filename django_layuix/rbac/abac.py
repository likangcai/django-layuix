# -*- coding: utf-8 -*-
"""1.4.2 dependency-free ABAC expression engine.

Supported syntax:
    and / or / not
    == != > >= < <= in / not in / contains
    parentheses, dotted paths, strings, numbers, true/false/null

Expressions can only read keys from the supplied context. There is no eval(),
attribute call, import or arbitrary Python execution.
"""
import re
from dataclasses import dataclass
from datetime import datetime

from django.utils import timezone


class AbacError(ValueError):
    pass


_TOKEN_RE = re.compile(
    r"""
    \s*(?:
        (?P<string>"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')
      | (?P<number>-?\d+(?:\.\d+)?)
      | (?P<op>==|!=|>=|<=|>|<|\bnot\s+in\b|\bin\b|\bcontains\b|\band\b|\bor\b|\bnot\b)
      | (?P<ident>[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)
      | (?P<punct>[(),])
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

_COMPARISONS = {'==', '!=', '>', '>=', '<', '<=', 'in', 'not in', 'contains'}


def _tokenize(expression):
    tokens = []
    pos = 0
    while pos < len(expression):
        match = _TOKEN_RE.match(expression, pos)
        if not match:
            if expression[pos].isspace():
                pos += 1
                continue
            raise AbacError('无法解析表达式字符：%s' % expression[pos])
        pos = match.end()
        kind = match.lastgroup
        value = match.group(kind)
        if kind == 'op':
            value = re.sub(r'\s+', ' ', value).lower()
        tokens.append((kind, value))
    tokens.append(('eof', ''))
    return tokens


class _Parser:
    def __init__(self, tokens, context, validate=False):
        self.tokens = tokens
        self.context = context
        self.validate = validate
        self.index = 0

    def peek(self):
        return self.tokens[self.index]

    def consume(self):
        token = self.tokens[self.index]
        self.index += 1
        return token

    def parse(self):
        value = self.parse_or()
        if self.peek()[0] != 'eof':
            raise AbacError('表达式存在多余内容：%s' % self.peek()[1])
        return value

    def parse_or(self):
        value = self.parse_and()
        while self.peek() == ('op', 'or'):
            self.consume()
            right = self.parse_and()
            value = value or right
        return value

    def parse_and(self):
        value = self.parse_not()
        while self.peek() == ('op', 'and'):
            self.consume()
            right = self.parse_not()
            value = value and right
        return value

    def parse_not(self):
        if self.peek() == ('op', 'not'):
            self.consume()
            return not self.parse_not()
        return self.parse_comparison()

    def parse_comparison(self):
        left = self.parse_primary()
        kind, value = self.peek()
        if kind == 'op' and value in _COMPARISONS:
            self.consume()
            right = self.parse_primary()
            return _compare(left, value, right, self.context, self.validate)
        return bool(left)

    def parse_primary(self):
        kind, value = self.consume()
        if kind == 'punct' and value == '(':
            result = self.parse_or()
            if self.consume() != ('punct', ')'):
                raise AbacError('表达式缺少右括号')
            return result
        if kind == 'string':
            quote = value[0]
            return value[1:-1].replace(quote + '\\', quote).replace('\\\\', '\\')
        if kind == 'number':
            return float(value) if '.' in value else int(value)
        if kind == 'ident':
            lowered = value.lower()
            if lowered == 'true':
                return True
            if lowered == 'false':
                return False
            if lowered == 'null':
                return None
            return ('path', value)
        raise AbacError('表达式语法错误：%s' % value)


def _resolve(node, context, validate=False):
    if not (isinstance(node, tuple) and len(node) == 2 and node[0] == 'path'):
        return node
    parts = node[1].split('.')
    if parts[0] not in context:
        if validate:
            return None
        raise AbacError('上下文缺少字段：%s' % parts[0])
    value = context[parts[0]]
    for part in parts[1:]:
        if isinstance(value, dict):
            if part not in value:
                if validate:
                    return None
                raise AbacError('上下文缺少字段：%s' % node[1])
            value = value[part]
        else:
            value = getattr(value, part, None)
    return value


def _compare(left, operator, right, context, validate=False):
    left = _resolve(left, context, validate)
    right = _resolve(right, context, validate)
    if validate:
        return True
    try:
        if operator == '==':
            return left == right
        if operator == '!=':
            return left != right
        if operator == '>':
            return left > right
        if operator == '>=':
            return left >= right
        if operator == '<':
            return left < right
        if operator == '<=':
            return left <= right
        if operator == 'in':
            if isinstance(right, str):
                return str(left) in right
            return left in right
        if operator == 'not in':
            if isinstance(right, str):
                return str(left) not in right
            return left not in right
        if operator == 'contains':
            if hasattr(right, '__contains__'):
                return left in right
            return str(left) in str(right)
    except TypeError as exc:
        raise AbacError('表达式类型不兼容：%s' % exc)
    return False


def validate_expression(expression):
    """Validate syntax only, without requiring a runtime context."""
    _Parser(_tokenize(str(expression or '')), {}, validate=True).parse()
    return True


def evaluate_expression(expression, context):
    """Evaluate a safe boolean expression against a plain context dict."""
    if not expression or not str(expression).strip():
        return False
    return bool(_Parser(_tokenize(str(expression)), context or {}).parse())


def user_context(user):
    if not user or not getattr(user, 'is_authenticated', False):
        return {}
    roles = getattr(user, 'roles', None)
    role_rows = list(roles.all()) if roles is not None else []
    context = {
        'id': getattr(user, 'pk', None),
        'username': getattr(user, 'username', ''),
        'is_superuser': bool(getattr(user, 'is_superuser', False)),
        'roles': [role.code for role in role_rows],
        'role_names': [role.name for role in role_rows],
        'scope_nodes': [role.scope_node for role in role_rows if getattr(role, 'scope_node', '')],
        'department': getattr(user, 'department', ''),
    }
    if hasattr(user, 'permissions'):
        from .engine import get_effective_permissions
        context['permissions'] = list(get_effective_permissions(user))
    else:
        context['permissions'] = []
    return context


def resource_context(resource):
    if resource is None:
        return {}
    if isinstance(resource, dict):
        return dict(resource)
    model_meta = getattr(resource, '_meta', None)
    if model_meta is None:
        return {'value': resource}
    result = {}
    for field in model_meta.concrete_fields:
        if 'password' in field.name:
            continue
        result[field.name] = getattr(resource, field.attname)
    return result


def resource_codes(resource):
    if isinstance(resource, str):
        return [resource]
    model_meta = getattr(resource, '_meta', None)
    if model_meta is None:
        return [type(resource).__name__]
    return [
        '%s.%s' % (model_meta.app_label, model_meta.model_name),
        model_meta.model_name,
    ]


def build_context(user, action, resource, field=None, extra_context=None):
    context = dict(extra_context or {})
    context.setdefault('user', user_context(user))
    context.setdefault('resource', resource_context(resource))
    context.setdefault('action', action)
    context.setdefault('field', field or '')
    now = timezone.now()
    context.setdefault('time', {
        'hour': now.hour,
        'weekday': now.weekday(),
        'date': now.date().isoformat(),
    })
    return context


@dataclass
class AbacDecision:
    allowed: bool
    matched: list
    errors: list


def _policies_for(resource, action, field):
    from .models import AbacPolicy

    codes = resource_codes(resource)
    queryset = AbacPolicy.objects.filter(is_active=True, resource__in=codes)
    queryset = queryset.filter(action__in=[action, '*'])
    if field:
        queryset = queryset.filter(field=field)
    else:
        queryset = queryset.filter(field='')
    return list(queryset.order_by('priority', 'id'))


def evaluate_policies(user, action, resource, field=None, extra_context=None):
    """Return an ABAC decision. No policy means allow (backward compatible)."""
    if getattr(user, 'is_superuser', False):
        return AbacDecision(True, [], [])
    policies = _policies_for(resource, action, field)
    if not policies:
        return AbacDecision(True, [], [])

    resource_for_context = (extra_context or {}).get('resource', resource)
    context = build_context(user, action, resource_for_context, field, extra_context)
    matched = []
    errors = []
    for policy in policies:
        try:
            hit = evaluate_expression(policy.expression, context)
        except AbacError as exc:
            errors.append({'policy_id': policy.id, 'error': str(exc)})
            continue
        if hit:
            matched.append(policy)
            if policy.effect == 'deny':
                return AbacDecision(False, [policy.id], errors)
    if errors:
        return AbacDecision(False, [policy.id for policy in matched], errors)
    return AbacDecision(True, [policy.id for policy in matched], errors)


def filter_queryset(queryset, user, action, resource, extra_context=None):
    """Python-level row filter; returns a QuerySet restricted by primary keys."""
    allowed_pks = []
    for obj in queryset:
        context = dict(extra_context or {})
        context.setdefault('resource', obj)
        if evaluate_policies(user, action, resource or obj, extra_context=context).allowed:
            allowed_pks.append(obj.pk)
    return queryset.filter(pk__in=allowed_pks)


def filter_fields(user, action, resource, fields, extra_context=None):
    """Return fields visible to the user for the given resource and action."""
    if getattr(user, 'is_superuser', False):
        return list(fields or [])

    visible = []
    for field in fields or []:
        field_policies = [
            policy for policy in _policies_for(resource, action, field)
            if policy.field == field
        ]
        has_allow_whitelist = any(policy.effect == 'allow' for policy in field_policies)
        decision = evaluate_policies(user, action, resource, field, extra_context)
        if decision.allowed and (not has_allow_whitelist or decision.matched):
            visible.append(field)
    return visible
