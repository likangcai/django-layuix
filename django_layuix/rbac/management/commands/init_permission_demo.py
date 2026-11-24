# -*- coding: utf-8 -*-
"""一键初始化 1.4.1/1.4.2 权限功能示例数据。

用法:
    python manage.py migrate
    python manage.py init_permission_demo

重复执行不会创建重复数据；已存在对象只补齐关联关系。
"""
import os

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from django_layuix.rbac.models import AbacPolicy, Menu, Role, ScopeNode, SoDConstraint


ROLE_SPECS = [
    ('demo_base', '示例基础角色', ['menu:view', 'role:view', 'user:view']),
    ('demo_manager', '示例区域经理', ['demo:order:view']),
    ('demo_maker', '示例制单员', ['demo:order:view']),
    ('demo_checker', '示例审核员', ['demo:order:view']),
    ('demo_finance', '示例财务', ['demo:order:view', 'demo:order:cost:view']),
    ('demo_sales', '示例销售', ['demo:order:view']),
]

MENU_SPECS = [
    ('示例订单', 'layui-icon-form', '/static/permission_demo/pages/order.html', 2, 6, '演示应用'),
]

BUTTON_SPECS = [
    ('查看示例订单', '示例订单', 'demo:order:view', 1),
    ('查看成本字段', '示例订单', 'demo:order:cost:view', 2),
]


class Command(BaseCommand):
    help = '一键初始化角色继承、SSD、Scope、组织节点与 ABAC 示例数据'

    def handle(self, *args, **options):
        User = get_user_model()
        with transaction.atomic():
            if not User.objects.filter(is_superuser=True).exists():
                self.stdout.write('未发现超级管理员，先执行 init_data 创建 admin 用户')
                call_command('init_data', verbosity=0)
            if not Menu.objects.filter(name='权限管理').exists():
                call_command('init_menu', verbosity=0)

            self._register_demo_menus()
            roles = self._create_roles()
            self._create_sod(roles)
            self._create_scope_nodes(roles)
            self._create_abac_policies()
            self._create_users(roles)
            self._seed_app_data(roles)

        self.stdout.write(self.style.SUCCESS('权限示例数据初始化完成'))

    def _register_demo_menus(self):
        from django_layuix.rbac.menu_registry import register_menus

        Menu.objects.get_or_create(
            name='演示应用',
            defaults={
                'name_en': 'Demo App', 'name_zh_hans': '演示应用',
                'icon': 'layui-icon-app', 'path': '', 'menu_type': 1, 'sort': 4,
                'status': True, 'visible': True, 'backend_visible': True,
                'frontend_visible': False,
            },
        )
        register_menus(menus_data=MENU_SPECS, buttons_data=BUTTON_SPECS)
        Menu.objects.filter(name='示例订单').update(
            name_en='Demo Orders', name_zh_hans='示例订单'
        )
        Menu.objects.filter(permission__in=['demo:order:view', 'demo:order:cost:view']).update(
            name_en='Demo Order Permissions', name_zh_hans='示例订单权限'
        )

    def _create_roles(self):
        roles = {}
        for code, name, permissions in ROLE_SPECS:
            role, _ = Role.objects.get_or_create(
                code=code,
                defaults={'name': name, 'description': 'permission demo role', 'is_system': False},
            )
            if permissions:
                menus = Menu.objects.filter(permission__in=permissions)
                role.menus.add(*menus)
            roles[code] = role

        manager = roles['demo_manager']
        base = roles['demo_base']
        manager.parent_roles.add(base)
        manager.parent = base
        manager.save(update_fields=['parent'])

        admin_role = Role.objects.filter(code='admin').first()
        if admin_role:
            admin_role.menus.add(*Menu.objects.filter(permission__in=[
                'demo:order:view', 'demo:order:cost:view'
            ]))
        return roles

    def _create_sod(self, roles):
        group, _ = SoDConstraint.objects.get_or_create(
            name='demo_maker_checker_sod',
            defaults={
                'kind': 'ssd',
                'description': '示例：制单与审核不能由同一用户承担',
                'is_active': True,
            },
        )
        group.roles.set([roles['demo_maker'], roles['demo_checker']])

    def _create_scope_nodes(self, roles):
        root, _ = ScopeNode.objects.get_or_create(
            code='demo_global', defaults={'name': '示例全局', 'sort': 20}
        )
        region, _ = ScopeNode.objects.get_or_create(
            code='demo_region', defaults={'name': '示例华东区域', 'parent': root, 'sort': 21}
        )
        team, _ = ScopeNode.objects.get_or_create(
            code='demo_team', defaults={'name': '示例华东一组', 'parent': region, 'sort': 22}
        )
        ScopeNode.objects.filter(pk=team.pk).update(parent=region)

        sales = roles['demo_sales']
        sales.scope_node = region.code
        sales.scope_depth = 1
        sales.save(update_fields=['scope_node', 'scope_depth'])

    def _create_abac_policies(self):
        AbacPolicy.objects.update_or_create(
            name='demo_large_order_deny',
            defaults={
                'resource': 'permission_demo.DemoOrder',
                'action': 'view',
                'field': '',
                'effect': 'deny',
                'expression': "resource.amount > 15000 and 'demo_finance' not in user.roles",
                'priority': 10,
                'is_active': True,
            },
        )
        AbacPolicy.objects.update_or_create(
            name='demo_cost_field_view',
            defaults={
                'resource': 'permission_demo.DemoOrder',
                'action': 'view',
                'field': 'cost',
                'effect': 'allow',
                'expression': "'demo_finance' in user.roles",
                'priority': 10,
                'is_active': True,
            },
        )

    def _create_users(self, roles):
        User = get_user_model()
        password = os.getenv('DEMO_PASSWORD', 'Demo@2026')
        specs = [
            ('demo_manager_user', ['demo_manager']),
            ('demo_finance_user', ['demo_finance']),
            ('demo_scope_user', ['demo_sales']),
        ]
        for username, role_codes in specs:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'email': '%s@example.com' % username, 'is_staff': True},
            )
            user.set_password(password)
            user.save(update_fields=['password'])
            if hasattr(user, 'roles'):
                user.roles.add(*[roles[code] for code in role_codes])
        self.stdout.write('示例用户密码: %s（可用 DEMO_PASSWORD 覆盖）' % password)

    def _seed_app_data(self, roles):
        if apps.is_installed('store'):
            try:
                call_command('init_demo_data', verbosity=0)
            except Exception as exc:
                raise CommandError('store 示例数据初始化失败: %s' % exc) from exc

        if apps.is_installed('permission_demo'):
            try:
                call_command('init_permission_demo_data', verbosity=0)
            except Exception as exc:
                raise CommandError('permission_demo 示例数据初始化失败: %s' % exc) from exc
