# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-26 22:19
# @FileName  : button_generator.py
# -----------------------------
"""Idempotent auto-generation of button permissions under a menu."""
from django.db import transaction

from .permission_registry import BUTTON_ACTIONS, build_permission_code
from .permissions import has_permission


def derive_permission_prefix(menu):
    """Derive a stable permission prefix from a menu's existing code/path/name."""
    code = str(getattr(menu, 'permission', '') or '').strip()
    if ':' in code:
        return code.split(':', 1)[0]
    path = str(getattr(menu, 'path', '') or '').strip('/')
    if path:
        segment = path.split('/')[-1].replace('.html', '').replace('-', '_')
        if segment:
            return segment.lower()
    return 'menu'


def existing_actions(menu):
    """Return action keys already generated under this menu."""
    prefix = derive_permission_prefix(menu)
    records = menu.children.filter(menu_type=3, plugin_key='').values_list('permission', flat=True)
    actions = set()
    for code in records:
        if code and code.startswith(prefix + ':'):
            actions.add(code.split(':', 1)[1])
    return actions


def generate_menu_buttons(menu, actions, replace=False, actor=None):
    """Create button permission nodes for ``actions``; return changed nodes."""
    from .models import Menu, Role

    prefix = derive_permission_prefix(menu)
    requested = []
    for action in actions or []:
        key = action.get('value') if isinstance(action, dict) else action
        key = str(key or '').strip()
        if key in BUTTON_ACTIONS and key not in requested:
            requested.append(key)

    desired_codes = {build_permission_code(prefix, action) for action in requested}
    desired_codes.discard('')
    created = []
    updated = []
    removed = []
    with transaction.atomic():
        children = list(Menu.objects.filter(
            parent=menu, menu_type=3, permission__startswith=prefix + ':', plugin_key=''
        ))
        current = {child.permission: child for child in children if child.permission}
        if replace:
            for code, child in current.items():
                if code not in desired_codes:
                    removed.append(code)
                    child.delete()
        for sort, action in enumerate(requested, 1):
            code = build_permission_code(prefix, action)
            if not code:
                continue
            labels = BUTTON_ACTIONS[action]
            name = '%s%s' % (labels[0], menu.name)
            child = current.get(code)
            if child:
                changed = False
                for field, value in (
                    ('name', name), ('name_en', '%s %s' % (labels[1], menu.name)),
                    ('name_zh_hans', name), ('permission', code), ('sort', sort),
                    ('status', True), ('visible', True),
                ):
                    if getattr(child, field) != value:
                        setattr(child, field, value)
                        changed = True
                if changed:
                    child.save()
                    updated.append(code)
            else:
                child = Menu.objects.create(
                    parent=menu, name=name, name_en='%s %s' % (labels[1], menu.name),
                    name_zh_hans=name, menu_type=3, permission=code, sort=sort,
                    status=True, visible=True,
                )
                created.append(code)
                current[code] = child
            roles = set(Role.objects.filter(menus=menu))
            admin_role = Role.objects.filter(code='admin', status=True).first()
            if admin_role:
                roles.add(admin_role)
            child.roles.add(*roles)

    return {
        'prefix': prefix,
        'created': created,
        'updated': updated,
        'removed': removed,
        'actions': requested,
    }


def can_generate(actor):
    """Whether ``actor`` may manage generated button permissions."""
    return has_permission(actor, 'menu:edit')
