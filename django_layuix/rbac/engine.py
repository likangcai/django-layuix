# -*- coding: utf-8 -*-
"""
RBAC3 permission engine.

Single source of truth for:
  - RBAC1 role inheritance expansion
  - RBAC2 constraints (SSD / DSD / prerequisites / cardinality)
  - session-scoped active roles
"""
import logging
from collections import deque

from django.conf import settings


ACTIVE_ROLES_SESSION_KEY = 'layui_active_roles'
MAX_ROLES_CONFIG_KEY = 'rbac_max_roles_per_user'
PREREQ_STRATEGY_KEY = 'rbac_prerequisite_strategy'
DSD_STRATEGY_KEY = 'rbac_dsd_strategy'

logger = logging.getLogger(__name__)


class RbacConstraintError(Exception):
    """Raised when a role assignment or activation violates RBAC2 constraints."""

    def __init__(self, message, code='constraint_violation'):
        super().__init__(message)
        self.message = message
        self.code = code


def _models():
    from .models import Role, Menu, SystemConfig, RoleMutex, RolePrerequisite
    return Role, Menu, SystemConfig, RoleMutex, RolePrerequisite


def _as_int_set(values):
    result = set()
    for value in values or []:
        try:
            result.add(int(value))
        except (TypeError, ValueError):
            continue
    return result


def get_assigned_role_ids(user):
    """IDs of active roles directly assigned to the user."""
    if not getattr(user, 'is_authenticated', False):
        return set()
    try:
        return set(user.roles.filter(status=True).values_list('id', flat=True))
    except (AttributeError, ValueError):
        # Unsaved user instance or custom user model without roles
        return set()


def expand_role_ids(role_ids):
    """RBAC1: expand role IDs to include all inherited (parent) roles."""
    Role, *_ = _models()
    result = _as_int_set(role_ids)
    queue = deque(result)
    while queue:
        role_id = queue.popleft()
        role = Role.objects.filter(pk=role_id).prefetch_related('parent_roles').first()
        if not role:
            continue
        parent_ids = {item.id for item in role.parent_roles.all() if item.status}
        if role.parent_id:
            parent_ids.add(role.parent_id)
        for parent_id in parent_ids:
            if parent_id and parent_id not in result:
                result.add(parent_id)
                queue.append(parent_id)
    return result


def expand_child_ids(role_ids):
    """Reverse traversal used for inheritance-cycle detection."""
    Role, *_ = _models()
    result = _as_int_set(role_ids)
    queue = deque(result)
    while queue:
        role_id = queue.popleft()
        child_ids = set(Role.objects.filter(pk=role_id).values_list('child_roles__id', flat=True))
        child_ids.update(Role.objects.filter(parent_id=role_id).values_list('id', flat=True))
        for child_id in child_ids:
            if child_id and child_id not in result:
                result.add(child_id)
                queue.append(child_id)
    return result


def _get_config(key, default, settings_name=None):
    """Read a strategy value: database config first, settings second, default last."""
    _, _, SystemConfig, _, _ = _models()
    obj = SystemConfig.objects.filter(key=key).first()
    raw = obj.value if obj else getattr(settings, settings_name or key.upper(), default)
    return raw if raw not in (None, '') else default


def _active_mutex_groups(kind):
    _, _, _, RoleMutex, _ = _models()
    return list(RoleMutex.objects.filter(
        is_active=True, kind=kind
    ).prefetch_related('roles', 'permissions'))


def get_active_role_ids(user):
    """Roles effective in the current session (DSD-safe by default)."""
    assigned = get_assigned_role_ids(user)
    if not assigned:
        return set()

    raw = getattr(user, '_layui_active_role_ids', None)
    if raw is not None:
        selected = _as_int_set(raw) & assigned
        if selected:
            return selected

    strategy = str(_get_config(
        DSD_STRATEGY_KEY, 'greedy', 'LAYUI_RBAC_DSD_STRATEGY'
    )).lower()
    if strategy == 'explicit':
        # Explicit mode never auto-activates a conflicting set; user must choose.
        return {min(assigned)}

    # Greedy mode: keep roles in stable order, skip DSD conflicts.
    groups = _active_mutex_groups('dsd')
    selected = set()
    for role_id in sorted(assigned):
        effective = expand_role_ids(selected | {role_id})
        if any(len(effective & {r.id for r in g.roles.all()}) > 1 for g in groups):
            continue
        selected.add(role_id)
    return selected or {min(assigned)}


def store_active_roles(request, role_ids):
    ids = sorted(_as_int_set(role_ids))
    request.session[ACTIVE_ROLES_SESSION_KEY] = ids
    user = getattr(request, 'user', None)
    if user is not None:
        user._layui_active_role_ids = ids


def clear_active_roles(request):
    request.session.pop(ACTIVE_ROLES_SESSION_KEY, None)
    user = getattr(request, 'user', None)
    if user is not None and hasattr(user, '_layui_active_role_ids'):
        delattr(user, '_layui_active_role_ids')


def get_effective_role_ids(user):
    return expand_role_ids(get_active_role_ids(user))


def is_full_access(user):
    """Superuser, built-in admin account, or holder of the admin role."""
    Role, *_ = _models()
    if not getattr(user, 'is_authenticated', False):
        return False
    if getattr(user, 'is_superuser', False):
        return True
    return Role.objects.filter(
        id__in=get_effective_role_ids(user), code='admin', status=True
    ).exists()


def _disabled_plugin_keys():
    """Plugin keys whose effective state is disabled."""
    from .models import PluginRegistry

    try:
        return set(PluginRegistry.objects.filter(
            is_active=False
        ).exclude(key='permission_catalog').values_list('key', flat=True))
    except Exception:
        logger.exception('Failed to read disabled plugin keys')
        return set()


def get_effective_permissions(user):
    """Permission strings granted by effective roles (inheritance included)."""
    _, Menu, *_ = _models()
    disabled = _disabled_plugin_keys()
    if is_full_access(user):
        return set(Menu.objects.filter(
            status=True, permission__gt=''
        ).exclude(plugin_key__in=disabled).values_list('permission', flat=True))
    return set(Menu.objects.filter(
        status=True, permission__gt='', roles__id__in=get_effective_role_ids(user)
    ).exclude(plugin_key__in=disabled).values_list('permission', flat=True).distinct())


def visible_menu_queryset(user, scope='backend'):
    """Menu queryset for sidebar / frontend menus, respecting roles and plugin state."""
    _, Menu, *_ = _models()
    visibility_field = 'frontend_visible' if scope == 'frontend' else 'backend_visible'
    filters = {'status': True, 'visible': True, visibility_field: True}
    disabled = _disabled_plugin_keys()
    if is_full_access(user):
        return Menu.objects.filter(**filters).exclude(plugin_key__in=disabled)
    return Menu.objects.filter(
        **filters, roles__id__in=get_effective_role_ids(user)
    ).exclude(plugin_key__in=disabled).distinct()


def get_max_roles_per_user():
    """Global role-count limit; 0 means unlimited."""
    _, _, SystemConfig, _, _ = _models()
    config = SystemConfig.objects.filter(key=MAX_ROLES_CONFIG_KEY).first()
    raw = config.value if config else getattr(settings, 'LAYUI_RBAC_MAX_ROLES_PER_USER', 0)
    try:
        return max(0, int(raw))
    except (TypeError, ValueError):
        return 0


def require_roles(role_ids):
    Role, *_ = _models()
    ids = _as_int_set(role_ids)
    roles = list(Role.objects.filter(id__in=ids, status=True))
    if len(roles) != len(ids):
        raise RbacConstraintError('角色不存在或已停用', 'invalid_role')
    return roles


def _prerequisite_closure(role_id, limit=20):
    """All roles transitively required by role_id."""
    _, _, _, _, RolePrerequisite = _models()
    result = set()
    frontier = {int(role_id)}
    for _ in range(limit):
        next_ids = set(RolePrerequisite.objects.filter(
            role_id__in=frontier
        ).values_list('prerequisite_id', flat=True)) - result
        if not next_ids:
            return result
        result |= next_ids
        frontier = next_ids
    raise RbacConstraintError('前置角色关系存在环', 'prerequisite_cycle')


def apply_prerequisites(role_ids):
    """Apply prerequisite strategy: auto_grant (default) or reject."""
    Role, _, _, _, RolePrerequisite = _models()
    result = _as_int_set(role_ids)
    strategy = str(_get_config(
        PREREQ_STRATEGY_KEY, 'auto_grant', 'LAYUI_RBAC_PREREQ_STRATEGY'
    )).lower()

    if strategy == 'reject':
        missing = set(RolePrerequisite.objects.filter(
            role_id__in=result
        ).values_list('prerequisite_id', flat=True)) - result
        if missing:
            names = list(Role.objects.filter(id__in=missing).values_list('name', flat=True))
            raise RbacConstraintError(
                '缺少前置角色：%s' % '、'.join(names), 'missing_prerequisite'
            )
        return result

    for _ in range(20):
        additions = set(RolePrerequisite.objects.filter(
            role_id__in=result
        ).values_list('prerequisite_id', flat=True)) - result
        if not additions:
            return result
        result |= additions
    raise RbacConstraintError('前置角色关系存在环', 'prerequisite_cycle')


def check_conflicts(effective_role_ids, kind):
    """Reject when two roles of one active mutex group are effective."""
    Role, *_ = _models()
    for group in _active_mutex_groups(kind):
        overlap = effective_role_ids & {r.id for r in group.roles.all()}
        if len(overlap) > 1:
            names = list(Role.objects.filter(id__in=overlap).values_list('name', flat=True))
            raise RbacConstraintError(
                '互斥角色不能同时%s：%s' % (
                    '生效' if kind == 'ssd' else '激活', '、'.join(names)
                ),
                '%s_conflict' % kind,
            )


def validate_assignable_menus(menu_ids):
    """Only active, visible, non-disabled-plugin menus may be assigned to roles."""
    from .models import Menu

    ids = _as_int_set(menu_ids)
    if not ids:
        return []
    disabled = _disabled_plugin_keys()
    menus = list(Menu.objects.filter(id__in=ids, status=True, visible=True).exclude(
        plugin_key__in=disabled
    ))
    if len(menus) != len(ids):
        raise RbacConstraintError('包含未注册、已停用或不可见的菜单', 'invalid_menu')
    return menus


def effective_permission_codes_for_roles(role_ids):
    """Permission codes granted by a role set after inheritance expansion."""
    _, Menu, *_ = _models()
    return set(Menu.objects.filter(
        status=True, permission__gt='',
        roles__id__in=expand_role_ids(role_ids),
    ).values_list('permission', flat=True).distinct())


def check_permission_conflicts(permission_codes, kind):
    """RBAC4: reject when two permissions in one mutex group are effective."""
    for group in _active_mutex_groups(kind):
        codes = set(group.permissions.filter(
            status=True, permission__gt=''
        ).values_list('permission', flat=True))
        if len(codes) < 2:
            continue
        overlap = set(permission_codes) & codes
        if len(overlap) > 1:
            raise RbacConstraintError(
                '互斥权限不能同时%s：%s' % (
                    '生效' if kind == 'ssd' else '激活', '、'.join(sorted(overlap))
                ),
                '%s_permission_conflict' % kind,
            )


def effective_permissions_for_role(role_id):
    """Return own and inherited permissions of a role with source roles."""
    Role, Menu, *_ = _models()
    role = Role.objects.filter(pk=role_id).first()
    if not role:
        return None

    own = list(Menu.objects.filter(
        status=True, permission__gt='', roles=role
    ).values('id', 'name', 'permission').distinct())

    ancestor_ids = expand_role_ids([role_id]) - {int(role_id)}
    inherited = []
    if ancestor_ids:
        ancestors = Role.objects.filter(id__in=ancestor_ids).order_by('id').prefetch_related('menus')
        for ancestor in ancestors:
            for menu in ancestor.menus.filter(status=True, permission__gt=''):
                inherited.append({
                    'id': menu.id,
                    'name': menu.name,
                    'permission': menu.permission,
                    'source_role_id': ancestor.id,
                    'source_role_name': ancestor.name,
                })

    return {
        'role_id': role.id,
        'role_name': role.name,
        'own': own,
        'inherited': inherited,
        'all_permissions': sorted({
            item['permission'] for item in own + inherited if item.get('permission')
        }),
    }


def check_sod_conflict(user, new_role_ids, audit=True):
    """1.4.1 compatible SSD check with structured conflict details."""
    Role, *_ = _models()
    candidate_ids = get_assigned_role_ids(user) | _as_int_set(new_role_ids)
    conflicts = []

    effective_ids = expand_role_ids(candidate_ids)
    for group in _active_mutex_groups('ssd'):
        overlap = effective_ids & {r.id for r in group.roles.all()}
        if len(overlap) > 1:
            conflicts.append({
                'type': 'role',
                'constraint_id': group.id,
                'constraint_name': group.name,
                'roles': [
                    {'id': r.id, 'name': r.name}
                    for r in Role.objects.filter(id__in=overlap).order_by('id')
                ],
            })

    permission_codes = effective_permission_codes_for_roles(candidate_ids)
    for group in _active_mutex_groups('ssd'):
        codes = set(group.permissions.filter(
            status=True, permission__gt=''
        ).values_list('permission', flat=True))
        overlap = permission_codes & codes
        if len(overlap) > 1:
            conflicts.append({
                'type': 'permission',
                'constraint_id': group.id,
                'constraint_name': group.name,
                'permissions': sorted(overlap),
            })

    result = {
        'allowed': not bool(conflicts),
        'exempt': False,
        'conflicts': conflicts,
    }
    if conflicts and is_full_access(user):
        result['allowed'] = True
        result['exempt'] = True
        if not audit:
            return result
        try:
            from .models import OperationLog
            OperationLog.objects.create(
                user=user if getattr(user, 'pk', None) else None,
                module='RBAC',
                action='SoD 约束豁免：%s' % '；'.join(
                    item['constraint_name'] for item in conflicts
                ),
                status=1,
            )
        except Exception:
            logger.warning('Failed to record SoD exemption audit for user %s', getattr(user, 'pk', None))
    return result


def validate_assignment(user, role_ids, exclude_user_pk=None):
    """Validate a new role set and return the final IDs (with prerequisites)."""
    Role, *_ = _models()
    final_ids = apply_prerequisites(role_ids)
    roles = require_roles(final_ids)
    check_conflicts(expand_role_ids(final_ids), 'ssd')
    check_permission_conflicts(
        effective_permission_codes_for_roles(final_ids), 'ssd'
    )

    for role in roles:
        if not role.max_users or role.max_users <= 0:
            continue
        holders = Role.objects.get(pk=role.pk).users.filter(is_active=True)
        if exclude_user_pk:
            holders = holders.exclude(pk=exclude_user_pk)
        if holders.count() >= role.max_users:
            raise RbacConstraintError(
                '角色「%s」最多允许 %s 人' % (role.name, role.max_users),
                'role_quota',
            )

    limit = get_max_roles_per_user()
    if limit and len(final_ids) > limit:
        raise RbacConstraintError(
            '每个用户最多分配 %s 个角色' % limit, 'user_quota'
        )
    return final_ids


def validate_active_roles(user, role_ids):
    """Validate roles selected for the current session (DSD)."""
    selected = _as_int_set(role_ids)
    assigned = get_assigned_role_ids(user)
    if not selected or not selected <= assigned:
        raise RbacConstraintError('只能激活已分配的角色', 'invalid_role')
    check_conflicts(expand_role_ids(selected), 'dsd')
    check_permission_conflicts(
        effective_permission_codes_for_roles(selected), 'dsd'
    )
    return selected


def validate_role_parents(role_id, parent_ids):
    """RBAC1: reject self-inheritance and inheritance cycles."""
    parents = _as_int_set(parent_ids)
    require_roles(parents)
    if role_id and int(role_id) in parents:
        raise RbacConstraintError('角色不能继承自身', 'inheritance_cycle')
    if role_id and parents & expand_child_ids([role_id]):
        raise RbacConstraintError('角色继承关系不能成环', 'inheritance_cycle')
    return parents


def validate_prerequisite(role_id, prerequisite_id):
    """RBAC2: reject self-reference and prerequisite cycles."""
    role_id = int(role_id)
    prerequisite_id = int(prerequisite_id)
    require_roles([role_id, prerequisite_id])
    if role_id == prerequisite_id:
        raise RbacConstraintError('角色不能依赖自身', 'prerequisite_cycle')
    if role_id in _prerequisite_closure(prerequisite_id):
        raise RbacConstraintError('前置角色关系不能成环', 'prerequisite_cycle')
    return role_id, prerequisite_id
