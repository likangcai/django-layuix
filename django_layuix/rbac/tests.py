# -*- coding: utf-8 -*-
"""RBAC3 regression tests: inheritance, constraints and server-side enforcement."""
import hashlib
import importlib.util
import re
import time
from pathlib import Path
from unittest import mock, skipUnless

from django.contrib.auth import get_user_model
from django.test import Client, RequestFactory, SimpleTestCase, TestCase, override_settings

from django_layuix.integrations.auth import (
    authenticate_request, register_authenticator,
    registered_authenticators, unregister_authenticator,
)
from django_layuix.plugins import PluginConfig

from .engine import (
    RbacConstraintError,
    validate_active_roles,
    validate_assignment,
    validate_prerequisite,
    validate_role_parents,
)
from .models import Menu, PluginRegistry, Role, RoleMutex, RolePrerequisite, SystemConfig
from .permissions import api_permission_required, has_permission
from .plugins import (
    discover_entry_point_plugins, list_plugins, register_plugin,
    register_plugin_class, set_plugin_active, unregister_plugin,
)

# Browser writes always send Origin/Referer. Test clients simulate that by default;
# tests that exercise the guard can override or remove this header explicitly.
_original_client_init = Client.__init__


def _client_init_with_origin(self, *args, **kwargs):
    _original_client_init(self, *args, **kwargs)
    self.defaults.setdefault('HTTP_ORIGIN', 'http://testserver')


Client.__init__ = _client_init_with_origin


class Rbac3Tests(TestCase):

    def setUp(self):
        User = get_user_model()
        self.employee = Role.objects.create(name='员工', code='employee')
        self.manager = Role.objects.create(name='经理', code='manager')
        self.cashier = Role.objects.create(name='出纳', code='cashier')
        self.accountant = Role.objects.create(name='会计', code='accountant')
        self.limited = Role.objects.create(name='限额角色', code='limited', max_users=1)

        self.menu_employee = Menu.objects.create(
            name='员工菜单', menu_type=2, permission='test:employee'
        )
        self.menu_cashier = Menu.objects.create(
            name='出纳菜单', menu_type=2, permission='test:cashier'
        )
        self.menu_accountant = Menu.objects.create(
            name='会计菜单', menu_type=2, permission='test:accountant'
        )
        self.employee.menus.add(self.menu_employee)
        self.cashier.menus.add(self.menu_cashier)
        self.accountant.menus.add(self.menu_accountant)
        self.limited.menus.add(self.menu_employee)

        self.user = User.objects.create_user(username='tester', password='pass12345')

    # ---------- RBAC1 ----------
    def test_direct_role_permission(self):
        self.user.roles.add(self.employee)
        self.assertTrue(self.user.has_perm('test:employee'))

    def test_inherited_role_permission(self):
        self.manager.parent_roles.add(self.employee)
        self.user.roles.add(self.manager)
        self.assertTrue(self.user.has_perm('test:employee'))

    def test_inheritance_cycle_rejected(self):
        self.manager.parent_roles.add(self.employee)
        with self.assertRaises(RbacConstraintError):
            validate_role_parents(self.employee.id, [self.manager.id])

    def test_self_inheritance_rejected(self):
        with self.assertRaises(RbacConstraintError):
            validate_role_parents(self.manager.id, [self.manager.id])

    # ---------- RBAC2: SSD ----------
    def test_ssd_blocks_direct_assignment(self):
        group = RoleMutex.objects.create(name='财务互斥', kind='ssd')
        group.roles.add(self.cashier, self.accountant)
        with self.assertRaises(RbacConstraintError):
            validate_assignment(self.user, [self.cashier.id, self.accountant.id])

    def test_ssd_blocks_inherited_conflict(self):
        self.accountant.parent_roles.add(self.cashier)
        group = RoleMutex.objects.create(name='财务互斥', kind='ssd')
        group.roles.add(self.cashier, self.accountant)
        with self.assertRaises(RbacConstraintError):
            validate_assignment(self.user, [self.accountant.id, self.cashier.id])

    # ---------- RBAC2: prerequisites ----------
    def test_prerequisite_auto_granted(self):
        RolePrerequisite.objects.create(role=self.manager, prerequisite=self.employee)
        final_ids = validate_assignment(self.user, [self.manager.id])
        self.assertEqual(final_ids, {self.manager.id, self.employee.id})

    def test_prerequisite_cycle_rejected(self):
        RolePrerequisite.objects.create(role=self.employee, prerequisite=self.manager)
        with self.assertRaises(RbacConstraintError):
            validate_prerequisite(self.manager.id, self.employee.id)

    # ---------- RBAC2: cardinality ----------
    def test_role_max_users(self):
        User = get_user_model()
        other = User.objects.create_user(username='other', password='pass12345')
        other.roles.add(self.limited)
        with self.assertRaises(RbacConstraintError):
            validate_assignment(self.user, [self.limited.id])

    def test_existing_user_excluded_from_quota(self):
        self.user.roles.add(self.limited)
        final_ids = validate_assignment(
            self.user, [self.limited.id], exclude_user_pk=self.user.pk
        )
        self.assertEqual(final_ids, {self.limited.id})

    # ---------- RBAC2: DSD ----------
    def test_dsd_blocks_joint_activation(self):
        self.user.roles.add(self.cashier, self.accountant)
        group = RoleMutex.objects.create(name='财务动态互斥', kind='dsd')
        group.roles.add(self.cashier, self.accountant)
        with self.assertRaises(RbacConstraintError):
            validate_active_roles(self.user, [self.cashier.id, self.accountant.id])
        self.assertEqual(
            validate_active_roles(self.user, [self.cashier.id]), {self.cashier.id}
        )

    def test_active_roles_limit_permissions(self):
        self.user.roles.add(self.cashier, self.accountant)
        self.user._layui_active_role_ids = [self.cashier.id]
        self.assertTrue(self.user.has_perm('test:cashier'))
        self.assertFalse(self.user.has_perm('test:accountant'))

    # ---------- Backend enforcement ----------
    def test_api_permission_decorator(self):
        @api_permission_required('test:cashier')
        def protected(request):
            return 'ok'

        request = RequestFactory().get('/')
        request.user = self.user
        self.assertEqual(protected(request).status_code, 403)

        self.user.roles.add(self.cashier)
        request.user = self.user
        self.assertEqual(protected(request), 'ok')


class Rbac3ApiTests(TestCase):

    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(
            username='api_admin', email='admin@example.com', password='pass12345'
        )
        self.client.force_login(self.admin)
        self.employee = Role.objects.create(name='员工', code='api_employee')
        self.manager = Role.objects.create(name='经理', code='api_manager')
        self.cashier = Role.objects.create(name='出纳', code='api_cashier')
        self.accountant = Role.objects.create(name='会计', code='api_accountant')

    def test_role_create_with_inheritance(self):
        response = self.client.post('/admin/api/rbac/roles/create/', {
            'name': '高级经理', 'code': 'api_senior',
            'parent_ids': [self.employee.id], 'menu_ids': [],
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        created = Role.objects.get(code='api_senior')
        self.assertEqual(list(created.parent_roles.values_list('id', flat=True)), [self.employee.id])

    def test_user_create_rejects_ssd(self):
        group = RoleMutex.objects.create(name='API 财务互斥', kind='ssd')
        group.roles.add(self.cashier, self.accountant)
        response = self.client.post('/admin/api/rbac/users/create/', {
            'username': 'cashier_user', 'password': 'pass12345',
            'role_ids': [self.cashier.id, self.accountant.id],
        }, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('互斥', response.json()['msg'])
        self.assertFalse(get_user_model().objects.filter(username='cashier_user').exists())

    def test_language_switch_writes_cookie_and_session(self):
        response = self.client.post(
            '/admin/api/rbac/set-language/',
            {'language': 'en'}, content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['language'], 'en')
        self.assertEqual(response.cookies.get('django_language').value, 'en')
        self.assertEqual(self.client.session.get('_language'), 'en')
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.language, 'en')

    def test_constraint_and_active_role_apis(self):
        response = self.client.get('/admin/api/rbac/constraints/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('mutex', response.json()['data'])

        self.admin.roles.add(self.cashier)
        response = self.client.post('/admin/api/rbac/active-roles/', {
            'role_ids': [self.cashier.id],
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['active_ids'], [self.cashier.id])


class Rbac4ExtensionTests(TestCase):

    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        User = get_user_model()
        self.user = User.objects.create_user(username='rbac4_user', password='pass12345')
        self.admin = User.objects.create_superuser(
            username='rbac4_admin', email='rbac4@example.com', password='pass12345'
        )
        self.employee = Role.objects.create(name='员工4', code='rbac4_employee')
        self.manager = Role.objects.create(name='经理4', code='rbac4_manager')
        self.cashier = Role.objects.create(name='出纳4', code='rbac4_cashier')
        self.accountant = Role.objects.create(name='会计4', code='rbac4_accountant')

        # Plugin state is persisted; make tests independent of the development DB.
        register_plugin(key='ops', name='运维管理')
        PluginRegistry.objects.filter(key='ops').update(validation_error='')
        set_plugin_active('ops', True)

    def test_menu_name_localization(self):
        menu = Menu.objects.create(
            name='菜单管理', name_en='Menu Management',
            name_zh_hans='菜单管理', menu_type=2,
        )
        self.assertEqual(menu.get_name_by_lang('en'), 'Menu Management')
        self.assertEqual(menu.get_name_by_lang('zh-hans'), '菜单管理')
        self.assertEqual(menu.get_name_by_lang('fr'), '菜单管理')

        self.admin.language = 'en'
        self.admin.save(update_fields=['language'])
        self.client.force_login(self.admin)
        response = self.client.get('/admin/api/rbac/userinfo/')
        self.assertEqual(response.status_code, 200)
        names = [item['name'] for item in response.json()['data']['menus']]
        self.assertIn('Menu Management', names)

    def test_bearer_token_works_without_session(self):
        from .token_auth import generate_token
        token = generate_token(self.user)
        anonymous = self.client_class()
        response = anonymous.get(
            '/admin/api/rbac/userinfo/', HTTP_AUTHORIZATION='Bearer ' + token
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['username'], 'rbac4_user')

        denied = anonymous.get('/admin/api/rbac/userinfo/')
        self.assertEqual(denied.status_code, 401)

    def test_bearer_token_respects_permissions(self):
        from .token_auth import generate_token
        token = generate_token(self.user)
        anonymous = self.client_class()
        response = anonymous.post(
            '/admin/api/rbac/roles/create/',
            {'name': 'x', 'code': 'rbac4_x'},
            content_type='application/json',
            HTTP_AUTHORIZATION='Bearer ' + token,
        )
        self.assertEqual(response.status_code, 403)

    def test_prerequisite_reject_strategy(self):
        SystemConfig.objects.create(
            key='rbac_prerequisite_strategy', value='reject', config_type='string'
        )
        RolePrerequisite.objects.create(role=self.manager, prerequisite=self.employee)
        with self.assertRaises(RbacConstraintError):
            validate_assignment(self.user, [self.manager.id])

    def test_dsd_explicit_strategy_never_auto_activates_conflict(self):
        SystemConfig.objects.create(
            key='rbac_dsd_strategy', value='explicit', config_type='string'
        )
        self.user.roles.add(self.cashier, self.accountant)
        group = RoleMutex.objects.create(name='财务动态互斥4', kind='dsd')
        group.roles.add(self.cashier, self.accountant)
        from .engine import get_active_role_ids
        active = get_active_role_ids(self.user)
        self.assertEqual(len(active), 1)

    def test_permission_level_mutex(self):
        pay = Menu.objects.create(name='支付', menu_type=3, permission='rbac4:pay')
        audit = Menu.objects.create(name='审计', menu_type=3, permission='rbac4:audit')
        self.cashier.menus.add(pay)
        self.accountant.menus.add(audit)
        group = RoleMutex.objects.create(name='权限互斥4', kind='ssd')
        group.permissions.add(pay, audit)
        with self.assertRaises(RbacConstraintError):
            validate_assignment(self.user, [self.cashier.id, self.accountant.id])

    def test_plugin_registry_api(self):
        self.client.force_login(self.admin)
        response = self.client.get('/admin/api/rbac/plugins/')
        self.assertEqual(response.status_code, 200)
        names = [p['key'] for p in response.json()['data']]
        self.assertIn('ops', names)

    def test_plugin_registry_persists(self):
        self.addCleanup(unregister_plugin, 'demo_plugin')
        register_plugin(key='demo_plugin', name='演示插件', version='2.0.0')
        self.assertTrue(PluginRegistry.objects.filter(key='demo_plugin').exists())

        # Simulate a fresh process losing the in-process registry.
        from django_layuix.rbac import plugins as plugin_module
        backup = dict(plugin_module._PLUGINS)
        plugin_module._PLUGINS.clear()
        try:
            names = [p['key'] for p in list_plugins()]
        finally:
            plugin_module._PLUGINS.update(backup)
        self.assertIn('demo_plugin', names)

    def test_plugin_deactivation_survives_reregistration(self):
        self.addCleanup(unregister_plugin, 'persist_test')
        register_plugin(key='persist_test', name='持久测试插件')
        set_plugin_active('persist_test', False)
        register_plugin(key='persist_test', name='持久测试插件')

        self.assertFalse(PluginRegistry.objects.get(key='persist_test').is_active)
        self.assertNotIn('persist_test', [item['key'] for item in list_plugins()])

    def test_plugin_config_validation_and_hooks(self):
        class DemoPlugin(PluginConfig):
            name = 'demo_plugin_app'
            label = 'demo_plugin_app'
            plugin_key = 'demo_hooks'
            plugin_name = 'Hook 插件'
            plugin_dependencies = ('definitely-missing-package>=1.0',)
            enabled = []
            disabled = []

            def on_enable(self):
                self.__class__.enabled.append(True)

            def on_disable(self):
                self.__class__.disabled.append(True)

        import django_layuix.ops as ops_module
        plugin = DemoPlugin(DemoPlugin.name, ops_module)
        metadata = plugin.get_plugin_metadata()
        self.assertEqual(metadata['key'], 'demo_hooks')
        errors = plugin.validate_plugin()
        self.assertTrue(any('definitely-missing-package' in item for item in errors))

        self.addCleanup(unregister_plugin, 'demo_hooks')
        register_plugin_class('demo_hooks', DemoPlugin)
        register_plugin(
            key='demo_hooks', name='Hook 插件',
            dependencies=('definitely-missing-package>=1.0',),
            validation_errors=errors,
        )
        self.assertFalse(PluginRegistry.objects.get(key='demo_hooks').is_active)
        self.assertFalse(set_plugin_active('demo_hooks', True))
        PluginRegistry.objects.filter(key='demo_hooks').update(validation_error='')
        self.assertTrue(set_plugin_active('demo_hooks', True))
        self.assertEqual(DemoPlugin.enabled, [True])
        set_plugin_active('demo_hooks', False)
        self.assertEqual(DemoPlugin.disabled, [True])

    def test_entry_point_discovery(self):
        class EntryPlugin(PluginConfig):
            name = 'entry_plugin_app'
            label = 'entry_plugin_app'
            plugin_key = 'entry_demo'
            plugin_name = 'Entry 插件'
            plugin_menus = [
                ('Entry 插件', 'layui-icon-app', '/entry/home', 2, 1, None),
            ]

        class FakeEntry:
            name = 'entry_demo'

            def load(self):
                return EntryPlugin

        class FakeEntries:
            def select(self, group):
                return [FakeEntry()]

        self.addCleanup(unregister_plugin, 'entry_demo')
        with mock.patch('importlib.metadata.entry_points', return_value=FakeEntries()):
            discovered = discover_entry_point_plugins()

        self.assertIn('entry_demo', [item['key'] for item in discovered])
        self.assertTrue(PluginRegistry.objects.get(key='entry_demo').is_active)
        self.assertTrue(Menu.objects.filter(plugin_key='entry_demo').exists())

    def test_plugin_manifest_api(self):
        Menu.objects.create(
            name='插件首页', path='/mycrm/home', menu_type=2,
            permission='mycrm:view', plugin_key='ops',
        )
        self.client.force_login(self.admin)
        response = self.client.get('/admin/api/rbac/plugins/manifest/')
        self.assertEqual(response.status_code, 200)
        ops = next(item for item in response.json()['data'] if item['key'] == 'ops')
        self.assertIn('mycrm:view', ops['permissions'])
        self.assertTrue(ops['menus'])

    def test_custom_authenticator_bridge(self):
        def custom_authenticator(request):
            if request.META.get('HTTP_X_CUSTOM_AUTH') == 'yes':
                return self.user
            return None

        register_authenticator(custom_authenticator, name='test_custom', priority=1)
        self.addCleanup(unregister_authenticator, 'test_custom')

        request = RequestFactory().get('/', HTTP_X_CUSTOM_AUTH='yes')
        self.assertEqual(authenticate_request(request), self.user)
        self.assertIn('test_custom', registered_authenticators())

        anonymous = self.client_class()
        response = anonymous.get(
            '/admin/api/rbac/userinfo/', HTTP_X_CUSTOM_AUTH='yes'
        )
        self.assertEqual(response.status_code, 200)

    def test_has_permission_entry_point(self):
        self.assertFalse(has_permission(self.admin, 'any:code'))
        self.assertFalse(has_permission(None, 'any:code'))

    @skipUnless(importlib.util.find_spec('rest_framework'), 'DRF not installed')
    def test_drf_permission_adapter(self):
        from django_layuix.integrations.drf import LayuiRBACPermission

        class DummyView:
            layui_permission = 'test:drf'

        Menu.objects.create(name='审计 DRF 权限', permission='test:drf', status=True)
        request = mock.Mock(user=self.admin)
        self.assertTrue(LayuiRBACPermission().has_permission(request, DummyView()))
        request.user = self.user
        self.assertFalse(LayuiRBACPermission().has_permission(request, DummyView()))

    @skipUnless(importlib.util.find_spec('ninja'), 'django-ninja not installed')
    def test_ninja_adapter(self):
        from ninja.errors import HttpError

        from django_layuix.integrations.ninja import (
            LayuiNinjaAuth, ninja_permission_required,
        )
        from .token_auth import generate_token

        token = generate_token(self.user)
        request = RequestFactory().get('/', HTTP_AUTHORIZATION='Bearer ' + token)
        self.assertEqual(LayuiNinjaAuth().authenticate(request, token), self.user)

        @ninja_permission_required('any:code')
        def protected(request):
            return 'ok'

        admin_request = RequestFactory().get('/')
        admin_request.user = self.admin
        self.assertEqual(protected(admin_request), 'ok')

        user_request = RequestFactory().get('/')
        user_request.user = self.user
        with self.assertRaises(HttpError):
            protected(user_request)


class Rbac141CompatibilityTests(TestCase):

    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(
            username='rbac141_admin', email='rbac141@example.com', password='pass12345'
        )
        self.user = User.objects.create_user(username='rbac141_user', password='pass12345')
        self.cashier = Role.objects.create(name='范围角色', code='rbac141_scope')
        self.client.force_login(self.admin)

    def _create_role(self, name, code, **extra):
        payload = {'name': name, 'code': code, 'menu_ids': []}
        payload.update(extra)
        response = self.client.post('/admin/api/rbac/roles/create/', payload, content_type='application/json')
        self.assertEqual(response.status_code, 200, response.content)
        return Role.objects.get(code=code)

    def test_parent_id_and_effective_permissions(self):
        menu = Menu.objects.create(name='支付查看', menu_type=3, permission='rbac141:pay:view')
        parent = self._create_role('财务经理', 'rbac141_manager', menu_ids=[menu.id])
        child = self._create_role('财务专员', 'rbac141_staff', parent_id=parent.id)

        roles = self.client.get('/admin/api/rbac/roles/').json()['data']
        child_payload = next(item for item in roles if item['id'] == child.id)
        parent_payload = next(item for item in roles if item['id'] == parent.id)
        self.assertEqual(child_payload['parent_id'], parent.id)
        self.assertIn(child.id, parent_payload['children_ids'])

        response = self.client.get('/admin/api/rbac/roles/%s/effective_permissions/' % child.id)
        self.assertEqual(response.status_code, 200)
        data = response.json()['data']
        self.assertIn('rbac141:pay:view', data['all_permissions'])
        self.assertTrue(any(item['source_role_id'] == parent.id for item in data['inherited']))

    def test_parent_cycle_rejected(self):
        role_a = self._create_role('角色A', 'rbac141_a')
        role_b = self._create_role('角色B', 'rbac141_b', parent_id=role_a.id)
        response = self.client.put(
            '/admin/api/rbac/roles/%s/update/' % role_a.id,
            {'parent_id': role_b.id}, content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        role_a.refresh_from_db()
        self.assertIsNone(role_a.parent_id)

    def test_sod_constraint_api_and_check(self):
        from .models import SoDConstraint

        role_a = self._create_role('制单员', 'rbac141_maker')
        role_b = self._create_role('审核员', 'rbac141_checker')
        response = self.client.post('/admin/api/rbac/sod-constraints/', {
            'name': '制单审核互斥', 'role_ids': [role_a.id, role_b.id],
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(SoDConstraint.objects.filter(name='制单审核互斥', kind='ssd').exists())

        check = self.client.post('/admin/api/rbac/sod-constraints/check/', {
            'user_id': self.user.id, 'role_ids': [role_a.id, role_b.id],
        }, content_type='application/json')
        self.assertEqual(check.status_code, 200)
        self.assertFalse(check.json()['data']['allowed'])
        self.assertTrue(check.json()['data']['conflicts'])

        response = self.client.post('/admin/api/rbac/users/create/', {
            'username': 'rbac141_conflict', 'password': 'pass12345',
            'role_ids': [role_a.id, role_b.id],
        }, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    @override_settings(
        LAYUIX_SCOPE_HIERARCHY=['global', 'region', 'team'],
        LAYUIX_SCOPE_TREE={'east_region': ['east_team_a']},
    )
    def test_scope_node_expansion(self):
        from .scopes import get_user_scope_nodes, visible_scope_nodes

        self.assertEqual({'east_region', 'east_team_a'}, visible_scope_nodes('east_region', 1))
        self.user.roles.add(self.cashier)
        self.cashier.scope_node = 'east_region'
        self.cashier.scope_depth = 1
        self.cashier.save(update_fields=['scope_node', 'scope_depth'])
        self.assertEqual({'east_region', 'east_team_a'}, get_user_scope_nodes(self.user))

    @override_settings(
        LAYUIX_SCOPE_HIERARCHY=['global', 'region', 'team'],
        LAYUIX_SCOPE_TREE={},
    )
    def test_scope_hierarchy_expands_multiple_levels(self):
        from .scopes import visible_scope_nodes

        self.assertEqual({'global', 'region', 'team'}, visible_scope_nodes('global', 2))

    def test_sod_check_without_user_id_is_not_exempt_for_admin_editor(self):
        role_a = self._create_role('制单', 'rbac141_maker2')
        role_b = self._create_role('审核', 'rbac141_checker2')
        self.client.post('/admin/api/rbac/sod-constraints/', {
            'name': '制单审核互斥2', 'role_ids': [role_a.id, role_b.id],
        }, content_type='application/json')
        response = self.client.post('/admin/api/rbac/sod-constraints/check/', {
            'role_ids': [role_a.id, role_b.id],
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['data']['allowed'])
        self.assertFalse(response.json()['data']['exempt'])

    def test_parent_ids_sync_compatible_parent_field(self):
        role_a = self._create_role('父同步A', 'rbac141_sync_a')
        role_b = self._create_role('父同步B', 'rbac141_sync_b')
        response = self.client.put(
            '/admin/api/rbac/roles/%s/update/' % role_a.id,
            {'parent_ids': [role_b.id]}, content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        role_a.refresh_from_db()
        self.assertEqual(role_a.parent_id, role_b.id)

    def test_role_copy_keeps_scope_and_parent(self):
        parent = self._create_role('复制父', 'rbac141_copy_parent')
        source = self._create_role(
            '复制源', 'rbac141_copy_source',
            parent_id=parent.id, scope_node='east_region', scope_depth=2,
        )
        response = self.client.post('/admin/api/rbac/roles/%s/copy/' % source.id, {}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        copied = Role.objects.get(code='rbac141_copy_source_copy')
        self.assertEqual(copied.parent_id, parent.id)
        self.assertEqual(copied.scope_node, 'east_region')
        self.assertEqual(copied.scope_depth, 2)


class Rbac142EnhancementTests(TestCase):

    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(
            username='rbac142_admin', email='rbac142@example.com', password='pass12345'
        )
        self.user = User.objects.create_user(username='rbac142_user', password='pass12345')
        self.sales = Role.objects.create(name='销售', code='sales')
        self.user.roles.add(self.sales)
        self.client.force_login(self.admin)

    def test_abac_expression_and_policies(self):
        from .abac import AbacError, evaluate_expression, evaluate_policies, filter_fields
        from .models import AbacPolicy

        self.assertTrue(evaluate_expression("'sales' in user.roles and resource.amount <= 10000", {
            'user': {'roles': ['sales']}, 'resource': {'amount': 5000}
        }))
        with self.assertRaises(AbacError):
            evaluate_expression("__import__('os').system('echo bad')", {})

        AbacPolicy.objects.create(
            name='大额订单拒绝', resource='store.Order', action='view', effect='deny',
            expression='resource.amount > 10000', priority=10,
        )
        self.assertFalse(evaluate_policies(
            self.user, 'view', 'store.Order',
            extra_context={'resource': {'amount': 20000}}
        ).allowed)
        self.assertTrue(evaluate_policies(
            self.user, 'view', 'store.Order',
            extra_context={'resource': {'amount': 5000}}
        ).allowed)

        AbacPolicy.objects.create(
            name='成本字段白名单', resource='store.Order', action='view', field='cost',
            effect='allow', expression="user.username == 'nobody'", priority=10,
        )
        self.assertEqual(
            filter_fields(self.user, 'view', 'store.Order', ['id', 'cost']), []
        )

    def test_abac_api_rejects_invalid_expression(self):
        response = self.client.post('/admin/api/rbac/abac-policies/', {
            'name': '非法表达式', 'resource': 'store.Order',
            'expression': "__import__('os').system('bad')",
        }, content_type='application/json')
        self.assertEqual(response.status_code, 400)

        response = self.client.post('/admin/api/rbac/abac-policies/', {
            'name': '小额可见', 'resource': 'store.Order', 'action': 'view',
            'effect': 'allow', 'expression': 'resource.amount <= 10000',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        check = self.client.post('/admin/api/rbac/abac-check/', {
            'user_id': self.user.id, 'action': 'view', 'resource': 'store.Order',
            'context': {'resource': {'amount': 5000}},
        }, content_type='application/json')
        self.assertEqual(check.status_code, 200)
        self.assertTrue(check.json()['data']['allowed'])

    def test_scope_node_tree_and_cycle_rejection(self):
        root = self.client.post('/admin/api/rbac/scope-nodes/', {
            'code': 'global', 'name': '全局',
        }, content_type='application/json')
        self.assertEqual(root.status_code, 200)
        root_id = root.json()['data']['id']

        child = self.client.post('/admin/api/rbac/scope-nodes/', {
            'code': 'east_region', 'name': '华东', 'parent_id': root_id,
        }, content_type='application/json')
        self.assertEqual(child.status_code, 200)
        child_id = child.json()['data']['id']

        tree = self.client.get('/admin/api/rbac/scope-nodes/').json()['data']
        self.assertEqual(tree[0]['code'], 'global')
        self.assertEqual(tree[0]['children'][0]['code'], 'east_region')

        cycle = self.client.put('/admin/api/rbac/scope-nodes/%s/' % root_id, {
            'parent_id': child_id,
        }, content_type='application/json')
        self.assertEqual(cycle.status_code, 400)

    def test_frontend_permissions_endpoint(self):
        response = self.client.get('/admin/api/rbac/frontend/permissions/')
        self.assertEqual(response.status_code, 200)
        data = response.json()['data']
        for key in ('user', 'permissions', 'roles', 'menus', 'plugins', 'scope_nodes', 'abac_policies'):
            self.assertIn(key, data)

    def test_system_config_defaults_are_complete(self):
        from django.core.management import call_command

        from .defaults import get_default_configs
        from .models import SystemConfig

        rows = get_default_configs()
        keys = [row['key'] for row in rows]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(len(keys), 17)
        for row in rows:
            self.assertTrue(all(field in row for field in ('value', 'description', 'config_type', 'sort')))
        for required in (
            'webssh_url', 'home_stats_cards', 'home_quick_links',
            'rbac_max_roles_per_user', 'rbac_prerequisite_strategy', 'rbac_dsd_strategy',
        ):
            self.assertIn(required, keys)

        call_command('init_menu', verbosity=0)
        stored = set(SystemConfig.objects.values_list('key', flat=True))
        self.assertTrue(set(keys).issubset(stored))

    def test_admin_context_does_not_mutate_settings(self):
        from django.conf import settings
        from django.test import override_settings

        from django_layuix.admin import LayuiAdminSite

        from .models import SystemConfig

        SystemConfig.objects.create(
            key='site_marker', value='db', description='test', config_type='string', sort=99
        )
        with override_settings(LAYUI_CONFIG={'site_marker': 'settings'}):
            request = RequestFactory().get('/admin/')
            request.user = self.admin
            context = LayuiAdminSite().each_context(request)
            self.assertEqual(context['layui_config']['site_marker'], 'db')
            self.assertEqual(settings.LAYUI_CONFIG['site_marker'], 'settings')

    def test_init_permission_demo_command_is_idempotent(self):
        from django.core.management import call_command

        from .models import AbacPolicy, Role, ScopeNode, SoDConstraint

        call_command('init_permission_demo', verbosity=0)
        counts = (
            Role.objects.filter(code__startswith='demo_').count(),
            SoDConstraint.objects.filter(name='demo_maker_checker_sod').count(),
            ScopeNode.objects.filter(code__startswith='demo_').count(),
            AbacPolicy.objects.filter(name__startswith='demo_').count(),
        )
        self.assertEqual(counts, (6, 1, 3, 2))

        call_command('init_permission_demo', verbosity=0)
        self.assertEqual(counts, (
            Role.objects.filter(code__startswith='demo_').count(),
            SoDConstraint.objects.filter(name='demo_maker_checker_sod').count(),
            ScopeNode.objects.filter(code__startswith='demo_').count(),
            AbacPolicy.objects.filter(name__startswith='demo_').count(),
        ))

    def test_permission_demo_api_applies_scope_and_abac(self):
        from django.contrib.auth import get_user_model
        from django.core.management import call_command
        from django.test import Client

        call_command('init_permission_demo', verbosity=0)
        User = get_user_model()

        expectations = {
            self.admin.username: (3, True),
            'demo_scope_user': (1, False),
            'demo_finance_user': (3, True),
        }
        for username, (count, sees_cost) in expectations.items():
            client = Client()
            client.force_login(User.objects.get(username=username))
            response = client.get('/admin/api/permission-demo/orders/')
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data['count'], count)
            self.assertEqual('cost' in data['fields'], sees_cost)

    def test_permission_demo_api_paginates_orders(self):
        from django.contrib.auth import get_user_model
        from django.core.management import call_command
        from django.test import Client

        call_command('init_permission_demo', verbosity=0)
        client = Client()
        client.force_login(get_user_model().objects.get(username=self.admin.username))

        first = client.get('/admin/api/permission-demo/orders/?page=1&page_size=1').json()
        second = client.get('/admin/api/permission-demo/orders/?page=2&page_size=1').json()

        self.assertEqual(len(first['data']), 1)
        self.assertEqual(first['count'], 3)
        self.assertEqual(first['page'], 1)
        self.assertEqual(first['page_size'], 1)
        self.assertEqual(first['total_pages'], 3)
        self.assertEqual(len(second['data']), 1)
        self.assertNotEqual(first['data'][0]['id'], second['data'][0]['id'])


class RbacFinalAuditTests(TestCase):

    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(
            username='audit_admin', email='audit@example.com', password='pass12345'
        )
        self.user = User.objects.create_user(username='audit_user', password='pass12345')
        self.client.force_login(self.admin)

    def test_init_permission_demo_syncs_configured_password(self):
        import os

        from django.core.management import call_command

        with mock.patch.dict(os.environ, {'DEMO_PASSWORD': 'Audit@2026'}):
            call_command('init_permission_demo', verbosity=0)
        user = get_user_model().objects.get(username='demo_scope_user')
        self.assertTrue(user.check_password('Audit@2026'))

    def test_api_origin_guard_blocks_cross_site_writes(self):
        cross = self.client.post(
            '/admin/api/rbac/scope-nodes/',
            {'code': 'evil', 'name': 'Evil'},
            content_type='application/json',
            HTTP_ORIGIN='https://evil.example',
        )
        self.assertEqual(cross.status_code, 403)

        same = self.client.post(
            '/admin/api/rbac/scope-nodes/',
            {'code': 'same', 'name': 'Same'},
            content_type='application/json',
            HTTP_ORIGIN='http://testserver',
        )
        self.assertEqual(same.status_code, 200)

    def test_abac_runtime_error_denies(self):
        from .abac import evaluate_policies
        from .models import AbacPolicy

        AbacPolicy.objects.create(
            name='bad expression', resource='audit.Resource', action='view',
            effect='deny', expression='resource.missing > 10', priority=1,
        )
        decision = evaluate_policies(self.user, 'view', 'audit.Resource')
        self.assertFalse(decision.allowed)
        self.assertTrue(decision.errors)

    def test_field_whitelist_ignores_row_level_allow(self):
        from .abac import filter_fields
        from .models import AbacPolicy

        AbacPolicy.objects.create(
            name='row allow', resource='audit.Resource', action='view',
            effect='allow', expression='true', priority=1,
        )
        AbacPolicy.objects.create(
            name='field allow', resource='audit.Resource', action='view', field='secret',
            effect='allow', expression='false', priority=2,
        )
        self.assertEqual(
            filter_fields(self.user, 'view', 'audit.Resource', ['id', 'secret']), []
        )

    def test_abac_boolean_operators_short_circuit(self):
        from .abac import evaluate_expression

        self.assertTrue(evaluate_expression('true or resource.missing > 1', {}))
        self.assertFalse(evaluate_expression('false and resource.missing > 1', {}))

    def test_resource_context_filters_sensitive_fields(self):
        from .abac import resource_context

        context = resource_context(self.user)
        self.assertNotIn('password', context)
        self.assertNotIn('api_key', context)

    def test_frontend_permissions_hides_abac_metadata_from_regular_users(self):
        from django.test import Client

        from .models import AbacPolicy

        AbacPolicy.objects.create(
            name='public meta', resource='audit.Resource', action='view',
            effect='deny', expression='true', priority=1,
        )
        regular = Client()
        regular.force_login(self.user)
        data = regular.get('/admin/api/rbac/frontend/permissions/').json()['data']
        self.assertEqual(data['abac_policies'], [])

        admin_data = self.client.get('/admin/api/rbac/frontend/permissions/').json()['data']
        self.assertEqual(len(admin_data['abac_policies']), 1)
        self.assertNotIn('expression', admin_data['abac_policies'][0])

    @override_settings(LAYUIX_API_PREFIXES=['/custom-api/'])
    def test_api_prefix_guard_is_configurable(self):
        from .middleware import ApiOriginGuardMiddleware

        middleware = ApiOriginGuardMiddleware(lambda request: None)
        self.assertTrue(middleware._is_api_path('/custom-api/rbac/test/'))
        self.assertFalse(middleware._is_api_path('/admin/api/rbac/test/'))

    def test_abac_check_rejects_unknown_target_user(self):
        response = self.client.post('/admin/api/rbac/abac-check/', {
            'user_id': 999999, 'action': 'view', 'resource': 'audit.Resource',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_fake_bearer_header_does_not_bypass_origin_guard(self):
        response = self.client.post(
            '/admin/api/rbac/scope-nodes/',
            {'code': 'fake', 'name': 'Fake'},
            content_type='application/json',
            HTTP_AUTHORIZATION='Bearer invalid.token',
            HTTP_ORIGIN='https://evil.example',
        )
        self.assertEqual(response.status_code, 403)

    @override_settings(LAYUIX_API_ALLOWED_ORIGINS=['admin.example.com'])
    def test_api_allowed_origins_supports_reverse_proxy(self):
        allowed = self.client.post(
            '/admin/api/rbac/scope-nodes/',
            {'code': 'proxy', 'name': 'Proxy'},
            content_type='application/json',
            HTTP_ORIGIN='https://admin.example.com',
        )
        self.assertEqual(allowed.status_code, 200)
        blocked = self.client.post(
            '/admin/api/rbac/scope-nodes/',
            {'code': 'proxy2', 'name': 'Proxy2'},
            content_type='application/json',
            HTTP_ORIGIN='https://evil.example',
        )
        self.assertEqual(blocked.status_code, 403)

    def test_frontend_permissions_includes_superuser_flag(self):
        data = self.client.get('/admin/api/rbac/frontend/permissions/').json()['data']
        self.assertTrue(data['user']['is_superuser'])

    def test_abac_check_rejects_superuser_impersonation(self):
        from django.contrib.auth import get_user_model
        from django.test import Client

        from .models import AbacPolicy

        AbacPolicy.objects.create(
            name='audit policy', resource='audit.Resource', action='view',
            effect='deny', expression='true', priority=1,
        )
        editor = get_user_model().objects.create_user(username='audit_editor', password='pass12345')
        editor.roles.add(Role.objects.create(name='编辑', code='audit_editor'))
        client = Client()
        client.force_login(editor)
        response = client.post('/admin/api/rbac/abac-check/', {
            'user_id': self.admin.id, 'action': 'view', 'resource': 'audit.Resource',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_abac_admin_form_validates_expression(self):
        from .admin import AbacPolicyForm
        from .abac import AbacError

        form = AbacPolicyForm(data={
            'name': 'Bad', 'resource': 'audit.Resource', 'action': 'view',
            'field': '', 'effect': 'deny', 'expression': "__import__('os')",
            'priority': 1, 'is_active': True,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('expression', form.errors)
        with self.assertRaises(AbacError):
            from .abac import validate_expression
            validate_expression("__import__('os')")

    def test_standard_jwt_is_issued_and_tracked(self):
        import base64
        import json

        from .models import AuthToken
        from .token_auth import generate_token, verify_token

        token = generate_token(self.user, request=None)
        header_b64, payload_b64, signature = token.split('.')
        header = json.loads(base64.urlsafe_b64decode(header_b64 + '=='))
        payload = json.loads(base64.urlsafe_b64decode(payload_b64 + '=='))

        self.assertEqual(header['alg'], 'HS256')
        self.assertEqual(header['typ'], 'JWT')
        self.assertEqual(payload['sub'], str(self.user.id))
        self.assertTrue(payload['jti'])
        self.assertTrue(signature)
        self.assertTrue(AuthToken.objects.filter(jti=payload['jti'], status=1).exists())
        result = verify_token(token)
        self.assertTrue(result['valid'])
        self.assertEqual(result['user'].id, self.user.id)

    def test_revoked_jwt_is_rejected(self):
        from .token_auth import generate_token, revoke_token, verify_token

        token = generate_token(self.user)
        self.assertTrue(verify_token(token)['valid'])
        self.assertEqual(revoke_token(token, reason='test'), 1)
        self.assertFalse(verify_token(token)['valid'])

    def test_revoke_user_tokens_invalidates_all_tokens(self):
        from .token_auth import generate_token, revoke_user_tokens, verify_token

        first = generate_token(self.user)
        second = generate_token(self.user)
        self.assertTrue(verify_token(first)['valid'])
        self.assertTrue(verify_token(second)['valid'])
        self.assertEqual(revoke_user_tokens(self.user, reason='test_bulk'), 2)
        self.assertFalse(verify_token(first)['valid'])
        self.assertFalse(verify_token(second)['valid'])

    def test_legacy_token_can_be_disabled(self):
        from .token_auth import generate_token, verify_token

        token = generate_token(self.user)
        with override_settings(LAYUIX_ALLOW_LEGACY_TOKEN=False):
            self.assertTrue(verify_token(token)['valid'])

    def test_session_write_without_origin_is_rejected(self):
        client = Client()
        client.force_login(self.user)
        client.defaults.pop('HTTP_ORIGIN', None)
        response = client.post('/admin/api/rbac/roles/create/', {
            'name': '无来源', 'code': 'no_origin',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_public_login_without_origin_is_allowed(self):
        client = Client()
        client.defaults.pop('HTTP_ORIGIN', None)
        response = client.post('/admin/api/rbac/login/', {
            'username': self.user.username, 'password': 'pass12345',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_x_token_without_origin_is_allowed(self):
        from .token_auth import generate_token

        client = Client()
        client.defaults.pop('HTTP_ORIGIN', None)
        response = client.post(
            '/admin/api/rbac/roles/create/',
            {'name': 'X Token 角色', 'code': 'x_token_role'},
            content_type='application/json',
            HTTP_X_TOKEN=generate_token(self.admin),
        )
        self.assertEqual(response.status_code, 200, response.content.decode())

    def test_legacy_token_can_be_revoked(self):
        import base64
        import json
        import time
        from django.conf import settings

        from .token_auth import revoke_token, verify_token

        exp = int(time.time()) + 3600
        payload = {
            'user_id': self.user.id,
            'username': self.user.username,
            'exp': exp,
        }
        payload_str = json.dumps(payload, sort_keys=True)
        payload_b64 = base64.urlsafe_b64encode(payload_str.encode()).decode().rstrip('=')
        signature = hashlib.sha256((
            '%s.%s.%s' % (payload_str, self.user.password, settings.SECRET_KEY)
        ).encode()).hexdigest()
        token = payload_b64 + '.' + signature

        self.assertTrue(verify_token(token)['valid'])
        self.assertEqual(revoke_token(token, reason='test_legacy'), 1)
        self.assertFalse(verify_token(token)['valid'])

    def test_explicit_english_language_is_preserved(self):
        from django.conf import settings
        from django.test import override_settings

        import importlib

        from .apps import RbacConfig

        app = RbacConfig('django_layuix.rbac', importlib.import_module('django_layuix.rbac'))
        with override_settings(LANGUAGE_CODE='en', USE_I18N=True):
            app._ensure_base_app_registered()
            self.assertEqual(settings.LANGUAGE_CODE, 'en')
            self.assertIn(settings.CSRF_COOKIE_SAMESITE, (None, 'None'))
            self.assertIn(settings.SESSION_COOKIE_SAMESITE, (None, 'None'))

    def test_scope_node_database_expansion(self):
        from .models import ScopeNode
        from .scopes import visible_scope_nodes

        root = ScopeNode.objects.create(code='audit_global', name='Global')
        child = ScopeNode.objects.create(code='audit_child', name='Child', parent=root)
        ScopeNode.objects.create(code='audit_grandchild', name='Grandchild', parent=child)
        self.assertEqual(
            visible_scope_nodes('audit_global', 1),
            {'audit_global', 'audit_child'},
        )

    def test_low_privilege_user_cannot_use_management_write_apis(self):
        from django.test import Client

        low = get_user_model().objects.create_user(username='audit_low', password='pass12345')
        client = Client()
        client.force_login(low)
        cases = [
            ('delete', '/admin/api/rbac/users/%s/delete/' % self.admin.pk),
            ('put', '/admin/api/rbac/users/%s/reset-password/' % self.admin.pk),
            ('put', '/admin/api/rbac/users/%s/status/' % self.admin.pk),
            ('post', '/admin/api/rbac/configs/create/'),
        ]
        for method, url in cases:
            with self.subTest(method=method, url=url):
                response = getattr(client, method)(url, {}, content_type='application/json')
                self.assertEqual(response.status_code, 403)

    def test_low_privilege_user_cannot_read_management_apis(self):
        from django.test import Client

        low = get_user_model().objects.create_user(username='audit_reader', password='pass12345')
        client = Client()
        client.force_login(low)
        urls = [
            '/admin/api/rbac/users/',
            '/admin/api/rbac/roles/',
            '/admin/api/rbac/logs/',
            '/admin/api/rbac/configs/',
            '/admin/api/rbac/stats/',
            '/admin/api/rbac/system/info/',
            '/admin/api/rbac/plugins/',
            '/admin/api/rbac/menus/tree/',
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(client.get(url).status_code, 403)

    def test_registration_is_disabled_and_reserves_admin_name(self):
        response = self.client.post('/admin/api/rbac/register/', {
            'username': 'new_user', 'password': 'pass12345',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 403)

        with override_settings(LAYUI_ALLOW_REGISTRATION=True):
            reserved = self.client.post('/admin/api/rbac/register/', {
                'username': 'admin', 'password': 'pass12345',
            }, content_type='application/json')
            self.assertEqual(reserved.status_code, 400)
            created = self.client.post('/admin/api/rbac/register/', {
                'username': 'allowed_user', 'password': 'pass12345',
            }, content_type='application/json')
            self.assertEqual(created.status_code, 200)

    def test_admin_username_alone_is_not_full_access(self):
        from .engine import is_full_access

        fake = get_user_model().objects.create_user(username='admin', password='pass12345')
        self.assertFalse(is_full_access(fake))

    def test_plugin_validation_failure_recovers_when_dependencies_fixed(self):
        self.addCleanup(unregister_plugin, 'audit_recover')
        register_plugin(
            key='audit_recover', name='Recover',
            validation_errors=['missing dependency'],
        )
        record = PluginRegistry.objects.get(key='audit_recover')
        self.assertFalse(record.is_active)
        self.assertTrue(record.desired_active)

        register_plugin(key='audit_recover', name='Recover', validation_errors=[])
        record.refresh_from_db()
        self.assertTrue(record.is_active)

    def test_plugin_state_failure_does_not_call_hooks(self):
        self.addCleanup(unregister_plugin, 'audit_db_fail')
        register_plugin(key='audit_db_fail', name='DB Fail')
        original = bool(PluginRegistry.objects.get(key='audit_db_fail').is_active)
        with mock.patch('django_layuix.rbac.plugins._db', side_effect=RuntimeError('db down')):
            result = set_plugin_active('audit_db_fail', not original)
        self.assertFalse(result)
        self.assertEqual(
            bool(PluginRegistry.objects.get(key='audit_db_fail').is_active), original
        )

    def test_unregister_plugin_removes_its_menus(self):
        from .menu_registry import register_menus

        self.addCleanup(unregister_plugin, 'audit_cleanup')
        register_plugin(key='audit_cleanup', name='Cleanup')
        Menu.objects.filter(plugin_key='audit_cleanup').delete()
        register_menus(
            menus_data=[('审计插件菜单', 'layui-icon-app', '/audit', 2, 1, None)],
            skip_existing=True,
            plugin_key='audit_cleanup',
        )
        self.assertTrue(Menu.objects.filter(plugin_key='audit_cleanup').exists())
        unregister_plugin('audit_cleanup')
        self.assertFalse(Menu.objects.filter(plugin_key='audit_cleanup').exists())

    def test_register_menus_skip_existing(self):
        from .menu_registry import register_menus

        self.addCleanup(Menu.objects.filter(name='审计跳过菜单').delete)
        spec = [('审计跳过菜单', 'layui-icon-app', '/audit/skip', 2, 1, None)]
        register_menus(menus_data=spec, skip_existing=True)
        Menu.objects.filter(name='审计跳过菜单').update(icon='changed')
        register_menus(
            menus_data=[('审计跳过菜单', 'layui-icon-user', '/audit/new', 2, 2, None)],
            skip_existing=True,
        )
        menu = Menu.objects.get(name='审计跳过菜单')
        self.assertEqual(menu.icon, 'changed')
        self.assertEqual(menu.path, '/audit/skip')
        register_menus(
            menus_data=[('审计跳过菜单', 'layui-icon-user', '/audit/new', 2, 2, None)],
            skip_existing=False,
        )
        menu.refresh_from_db()
        self.assertEqual(menu.icon, 'layui-icon-user')
        self.assertEqual(menu.path, '/audit/new')

    def test_ops_apis_require_rbac_permissions(self):
        from django.test import Client

        low = get_user_model().objects.create_user(username='audit_ops_low', password='pass12345')
        client = Client()
        client.force_login(low)
        cases = [
            ('get', '/admin/api/ops/servers/'),
            ('get', '/admin/api/ops/ai/config/list/'),
            ('post', '/admin/api/ops/servers/1/exec/'),
        ]
        for method, url in cases:
            with self.subTest(url=url):
                response = getattr(client, method)(url, {}, content_type='application/json')
                self.assertEqual(response.status_code, 403)

    def test_token_round_trip_with_extra_data(self):
        from .token_auth import generate_token, verify_token

        token = generate_token(self.admin, {'tenant': 'audit', 'user_id': 999999})
        result = verify_token(token)
        self.assertTrue(result['valid'])
        self.assertEqual(result['payload']['tenant'], 'audit')
        self.assertEqual(result['payload']['user_id'], self.admin.pk)

    def test_active_roles_are_session_scoped(self):
        from django.test import Client

        from .engine import ACTIVE_ROLES_SESSION_KEY
        from .models import RoleMutex

        first = Role.objects.create(name='会话角色A', code='audit_session_a')
        second = Role.objects.create(name='会话角色B', code='audit_session_b')
        group = RoleMutex.objects.create(name='会话互斥', kind='dsd')
        group.roles.add(first, second)
        self.user.roles.add(first, second)

        client_a = Client()
        client_a.force_login(self.user)
        selected = client_a.post('/admin/api/rbac/active-roles/', {
            'role_ids': [second.id],
        }, content_type='application/json')
        self.assertEqual(selected.status_code, 200)
        self.assertEqual(client_a.session[ACTIVE_ROLES_SESSION_KEY], [second.id])

        client_b = Client()
        client_b.force_login(self.user)
        response = client_b.get('/admin/api/rbac/active-roles/')
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.json()['data']['active_ids'], [second.id])

    def test_register_plugin_db_failure_does_not_mutate_memory_or_hooks(self):
        class FailingPlugin(PluginConfig):
            name = 'audit_failing_plugin'
            label = 'audit_failing_plugin'
            plugin_key = 'audit_failing'
            enabled = []
            disabled = []

            def on_enable(self):
                self.__class__.enabled.append(True)

        register_plugin_class('audit_failing', FailingPlugin)
        with mock.patch('django_layuix.rbac.plugins._db', side_effect=RuntimeError('db down')):
            result = register_plugin(key='audit_failing', name='Failing')
        self.assertNotIn('audit_failing', PluginRegistry.objects.values_list('key', flat=True))
        self.assertEqual(FailingPlugin.enabled, [])

    def test_unregister_plugin_deletes_record_when_menu_cleanup_fails(self):
        self.addCleanup(unregister_plugin, 'audit_cleanup_fail')
        register_plugin(key='audit_cleanup_fail', name='Cleanup Fail')
        with mock.patch(
            'django_layuix.rbac.menu_registry.unregister_plugin_menus',
            side_effect=RuntimeError('menu down'),
        ):
            unregister_plugin('audit_cleanup_fail')
        self.assertFalse(PluginRegistry.objects.filter(key='audit_cleanup_fail').exists())

    def test_plugin_owned_menus_update_with_skip_existing(self):
        from .menu_registry import register_menus

        self.addCleanup(Menu.objects.filter(name='审计插件升级菜单').delete)
        register_menus(
            menus_data=[('审计插件升级菜单', 'layui-icon-app', '/old', 2, 1, None)],
            skip_existing=True,
            plugin_key='audit_upgrade',
        )
        register_menus(
            menus_data=[('审计插件升级菜单', 'layui-icon-app', '/new', 2, 2, None)],
            skip_existing=True,
            plugin_key='audit_upgrade',
        )
        self.assertEqual(Menu.objects.get(name='审计插件升级菜单').path, '/new')

    def test_menu_view_permission_codes_are_enforced_in_views(self):
        root = Path(__file__).resolve().parents[2]
        sources = [
            (root / 'django_layuix/rbac/views.py').read_text(encoding='utf-8'),
            (root / 'django_layuix/rbac/dictionary_views.py').read_text(encoding='utf-8'),
            (root / 'django_layuix/ops/views.py').read_text(encoding='utf-8'),
        ]
        from .menu_permissions import MENU_VIEW_PERMISSIONS

        for code in MENU_VIEW_PERMISSIONS.values():
            with self.subTest(code=code):
                self.assertTrue(
                    any("'%s'" % code in source for source in sources),
                    'permission code %s is not enforced' % code,
                )

    def test_token_active_roles_are_enforced(self):
        from django.test import Client

        from .token_auth import generate_token

        view_menu = Menu.objects.create(name='审计用户查看', menu_type=3, permission='user:view')
        high = Role.objects.create(name='高权限', code='audit_high')
        low = Role.objects.create(name='低权限', code='audit_low')
        high.menus.add(view_menu)
        caller = get_user_model().objects.create_user(username='audit_token_roles', password='pass12345')
        caller.roles.add(high, low)
        token = generate_token(caller, active_roles=[low.id])

        client = Client()
        response = client.get(
            '/admin/api/rbac/users/', HTTP_AUTHORIZATION='Bearer ' + token
        )
        self.assertEqual(response.status_code, 403)

    def test_query_token_is_rejected_on_regular_api(self):
        from django.test import Client

        from .token_auth import generate_token

        token = generate_token(self.user)
        anonymous = Client()
        response = anonymous.get('/admin/api/rbac/userinfo/?token=' + token)
        self.assertEqual(response.status_code, 401)

    def test_menu_parent_cycle_is_rejected(self):
        first = Menu.objects.create(name='审计菜单A', menu_type=1)
        second = Menu.objects.create(name='审计菜单B', menu_type=1, parent=first)
        response = self.client.put(
            '/admin/api/rbac/menus/%s/' % first.pk,
            {'parent_id': second.pk},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        first.refresh_from_db()
        self.assertIsNone(first.parent_id)

    def test_build_menu_tree_skips_cycles(self):
        from .views import _build_menu_tree

        menus = [
            {'id': 1, 'parent_id': 2},
            {'id': 2, 'parent_id': 1},
        ]
        self.assertEqual(_build_menu_tree(menus), [])

    def test_upload_rejects_svg_content(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        uploaded = SimpleUploadedFile(
            'logo.svg', b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',
            content_type='image/png',
        )
        response = self.client.post(
            '/admin/api/rbac/upload/image/', {'image': uploaded}, format='multipart'
        )
        self.assertEqual(response.status_code, 400)

    def test_filter_queryset_uses_sanitized_resource_context(self):
        from .abac import filter_queryset
        from .models import AbacPolicy

        AbacPolicy.objects.create(
            name='secret field probe', resource='audit.User', action='view',
            effect='allow', expression="resource.password != ''", priority=1,
        )
        result = filter_queryset(
            get_user_model().objects.filter(pk=self.user.pk),
            self.user, 'view', 'audit.User',
        )
        self.assertFalse(result.exists())

    def test_plugin_does_not_take_foreign_menu(self):
        from .menu_registry import register_menus

        menu = Menu.objects.create(name='审计插件归属', plugin_key='other_plugin')
        self.addCleanup(menu.delete)
        register_menus(
            menus_data=[('审计插件归属', 'layui-icon-app', '/new', 2, 1, None)],
            skip_existing=True,
            plugin_key='new_plugin',
        )
        menu.refresh_from_db()
        self.assertEqual(menu.plugin_key, 'other_plugin')
        self.assertEqual(menu.path, '')

    def test_scope_node_delete_reparents_children(self):
        from .models import ScopeNode

        parent = ScopeNode.objects.create(code='audit_parent', name='审计父节点')
        child = ScopeNode.objects.create(code='audit_child', name='审计子节点', parent=parent)
        response = self.client.delete('/admin/api/rbac/scope-nodes/%s/' % parent.pk)
        self.assertEqual(response.status_code, 200)
        child.refresh_from_db()
        self.assertIsNone(child.parent_id)
        self.assertFalse(ScopeNode.objects.filter(pk=parent.pk).exists())

    def test_scope_node_delete_rejects_referenced_node(self):
        from .models import ScopeNode

        node = ScopeNode.objects.create(code='audit_scope_ref', name='审计引用节点')
        Role.objects.create(name='审计数据范围角色', code='audit_scope_role', scope_node=node.code)
        response = self.client.delete('/admin/api/rbac/scope-nodes/%s/' % node.pk)
        self.assertEqual(response.status_code, 409)
        self.assertTrue(ScopeNode.objects.filter(pk=node.pk).exists())

    def test_explicit_token_is_preferred_over_session(self):
        from django.test import Client

        from .token_auth import generate_token

        low = get_user_model().objects.create_user(username='audit_session_low', password='pass12345')
        client = Client()
        client.force_login(low)
        response = client.get(
            '/admin/api/rbac/userinfo/',
            HTTP_AUTHORIZATION='Bearer ' + generate_token(self.admin),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['username'], self.admin.username)

    def test_revoke_token_requires_matching_user(self):
        from .token_auth import generate_token, revoke_token, verify_token

        token = generate_token(self.user)
        self.assertEqual(revoke_token(token, reason='attack', user=self.admin), 0)
        self.assertTrue(verify_token(token)['valid'])
        self.assertEqual(revoke_token(token, reason='logout', user=self.user), 1)
        self.assertFalse(verify_token(token)['valid'])

    def test_stream_ticket_authenticates_sse_without_jwt_in_url(self):
        from django.test import RequestFactory

        from .token_auth import generate_stream_ticket, token_authenticate

        ticket = generate_stream_ticket(self.admin)
        request = RequestFactory().get(
            '/admin/api/rbac/system/info/stream/', {'stream_ticket': ticket}
        )
        self.assertEqual(token_authenticate(request).pk, self.admin.pk)

    def test_disabled_plugin_menus_are_hidden(self):
        from .engine import visible_menu_queryset
        from .models import PluginRegistry

        menu = Menu.objects.create(
            name='审计禁用插件菜单', menu_type=2, path='/audit-disabled',
            plugin_key='audit_disabled_plugin',
        )
        PluginRegistry.objects.create(
            key='audit_disabled_plugin', name='Disabled Plugin', is_active=False
        )
        visible = visible_menu_queryset(self.admin, 'backend')
        self.assertFalse(visible.filter(pk=menu.pk).exists())

    def test_disabled_business_node_blocks_builtin_permission(self):
        from .permission_registry import register_page_permissions

        register_page_permissions()
        catalog = Menu.objects.get(
            permission='user:view', plugin_key='permission_catalog', status=True
        )
        business = Menu.objects.create(
            name='审计用户业务按钮', menu_type=3, permission='user:view',
            status=True, visible=True,
        )
        role = Role.objects.create(name='审计按钮角色', code='audit_button_role')
        role.menus.add(business)
        self.user.roles.add(role)
        self.assertTrue(has_permission(self.user, 'user:view'))

        business.status = False
        business.save()
        self.assertFalse(has_permission(self.user, 'user:view'))
        self.assertTrue(catalog.status)

    def test_department_tree_crud_and_cycle_protection(self):
        response = self.client.post(
            '/admin/api/rbac/departments/create/',
            {'name': '技术中心', 'code': 'tech', 'type': 3},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        parent_id = response.json()['data']['id']
        response = self.client.post(
            '/admin/api/rbac/departments/create/',
            {'name': '平台组', 'code': 'platform', 'type': 4, 'parent_id': parent_id},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        child_id = response.json()['data']['id']

        listed = self.client.get('/admin/api/rbac/departments/').json()['data']['list']
        self.assertEqual(len(listed), 2)
        self.assertEqual(listed[1]['parent_id'], parent_id)

        response = self.client.put(
            '/admin/api/rbac/departments/%s/' % parent_id,
            {'parent_id': child_id},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

        response = self.client.delete('/admin/api/rbac/departments/%s/' % parent_id)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.delete('/admin/api/rbac/departments/%s/' % child_id).status_code, 200)
        self.assertEqual(self.client.delete('/admin/api/rbac/departments/%s/' % parent_id).status_code, 200)

    def test_position_and_member_level_crud(self):
        response = self.client.post(
            '/admin/api/rbac/positions/create/',
            {'name': '运营专员', 'code': 'operator', 'sort': 2},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        position_id = response.json()['data']['id']
        self.assertEqual(
            len(self.client.get('/admin/api/rbac/positions/').json()['data']['list']), 1
        )
        self.assertEqual(
            self.client.delete('/admin/api/rbac/positions/%s/' % position_id).status_code,
            200,
        )

        response = self.client.post(
            '/admin/api/rbac/member-levels/create/',
            {'name': '金卡', 'code': 'gold', 'min_points': 1000, 'discount': 95},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        level_id = response.json()['data']['id']
        response = self.client.put(
            '/admin/api/rbac/member-levels/%s/' % level_id,
            {'discount': 120},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        response = self.client.put(
            '/admin/api/rbac/member-levels/%s/' % level_id,
            {'discount': 98.5, 'min_points': 1200},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.client.delete('/admin/api/rbac/member-levels/%s/' % level_id).status_code,
            200,
        )

    def test_region_tree_crud_and_page_permissions_are_registered(self):
        response = self.client.post(
            '/admin/api/rbac/regions/create/',
            {'name': '浙江省', 'code': '330000', 'level': 1},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        province_id = response.json()['data']['id']
        response = self.client.post(
            '/admin/api/rbac/regions/create/',
            {'name': '杭州市', 'code': '330100', 'level': 2, 'parent_id': province_id},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        city_id = response.json()['data']['id']
        self.assertEqual(
            self.client.delete('/admin/api/rbac/regions/%s/' % province_id).status_code,
            400,
        )
        self.assertEqual(self.client.delete('/admin/api/rbac/regions/%s/' % city_id).status_code, 200)
        self.assertEqual(self.client.delete('/admin/api/rbac/regions/%s/' % province_id).status_code, 200)

        from .permission_registry import PAGE_PERMISSIONS
        for path in (
            '/static/layui/pages/dept.html', '/static/layui/pages/position.html',
            '/static/layui/pages/region.html', '/static/layui/pages/member-level.html',
        ):
            self.assertIn(path, PAGE_PERMISSIONS)

    def test_role_code_conflict_is_rejected_atomically(self):
        from .permission_registry import register_page_permissions

        register_page_permissions()
        catalog = Menu.objects.get(permission='user:view', plugin_key='permission_catalog')
        role = Role.objects.create(name='审计原子角色', code='audit_atomic_role')
        role.menus.add(catalog)
        Role.objects.create(name='冲突管理员', code='admin')

        response = self.client.put(
            '/admin/api/rbac/roles/%s/update/' % role.pk,
            {'name': '冲突角色', 'code': 'admin', 'menu_ids': [catalog.id]},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        role.refresh_from_db()
        self.assertEqual(role.name, '审计原子角色')
        self.assertEqual(role.code, 'audit_atomic_role')
        self.assertEqual(list(role.menus.values_list('id', flat=True)), [catalog.id])

    def test_unknown_resource_serializer_fails_closed(self):
        from .serializers import serialize_instance

        request = RequestFactory().get('/admin/api/example/')
        request.user = self.admin
        self.assertEqual(
            serialize_instance(
                {'id': 1, 'password': 'should-not-leak', 'secret': 'x'},
                request, 'rbac.Unknown',
            ),
            {},
        )

    def test_standard_table_defaults_to_html_escape(self):
        from pathlib import Path

        root = Path(__file__).resolve().parents[2]
        source = (root / 'django_layuix/static/layui/js/common.js').read_text(encoding='utf-8')
        self.assertIn('settings.escape = settings.escape !== false;', source)

    def test_dictionary_crud_and_options_api(self):
        create = self.client.post(
            '/admin/api/rbac/dictionaries/create/',
            {'code': 'audit_order_status', 'name': '订单状态', 'status': True, 'sort': 1},
            content_type='application/json',
        )
        self.assertEqual(create.status_code, 200)
        dict_id = create.json()['data']['id']

        item = self.client.post(
            '/admin/api/rbac/dictionaries/%s/items/create/' % dict_id,
            {'label': '待支付', 'value': 'pending', 'sort': 1, 'status': True, 'is_default': True},
            content_type='application/json',
        )
        self.assertEqual(item.status_code, 200)
        item_id = item.json()['data']['id']

        listed = self.client.get('/admin/api/rbac/dictionaries/?keyword=audit_order_status')
        self.assertEqual(listed.status_code, 200)
        row = listed.json()['data']['list'][0]
        self.assertEqual(row['code'], 'audit_order_status')
        self.assertEqual(row['item_count'], 1)

        options = self.client.get('/admin/api/rbac/dictionaries/options/audit_order_status/')
        self.assertEqual(options.status_code, 200)
        self.assertEqual(options.json()['data'][0]['value'], 'pending')
        self.assertTrue(options.json()['data'][0]['is_default'])

        disabled = self.client.put(
            '/admin/api/rbac/dictionary-items/%s/' % item_id,
            {'label': '待支付', 'value': 'pending', 'status': False},
            content_type='application/json',
        )
        self.assertEqual(disabled.status_code, 200)
        self.assertEqual(
            self.client.get('/admin/api/rbac/dictionaries/options/audit_order_status/').json()['data'],
            [],
        )

    def test_system_dictionary_cannot_be_deleted(self):
        from .models import Dictionary

        obj = Dictionary.objects.create(
            code='audit_system_dict', name='系统字典', is_system=True,
        )
        response = self.client.delete('/admin/api/rbac/dictionaries/%s/' % obj.pk)
        self.assertEqual(response.status_code, 400)
        self.assertTrue(Dictionary.objects.filter(pk=obj.pk).exists())

    def test_role_page_has_reference_style_permission_grant_dialog(self):
        root = Path(__file__).resolve().parents[2]
        source = (root / 'django_layuix/static/layui/pages/role.html').read_text(encoding='utf-8')
        self.assertIn('permissionDialogTpl', source)
        self.assertIn("lay-event=\"grant\"", source)
        self.assertIn('permissionSearch', source)
        self.assertIn('permissionExpandAll', source)

    def test_user_page_has_reference_style_list_interactions(self):
        root = Path(__file__).resolve().parents[2]
        source = (root / 'django_layuix/static/layui/pages/user.html').read_text(encoding='utf-8')
        self.assertIn('ref-toolbar', source)
        self.assertIn('batchDeleteBtn', source)
        self.assertIn("lay-filter=\"userStatus\"", source)
        self.assertIn("type: 'checkbox'", source)
        self.assertIn('action-chip', source)

    def test_new_user_default_theme_is_light(self):
        user = get_user_model().objects.create_user(username='audit_light_theme', password='pass12345')
        self.assertEqual(user.theme, '默认浅色')

    def test_builtin_button_permissions_are_pre_registered(self):
        from .permission_registry import permission_catalog, register_page_permissions

        created = register_page_permissions()
        self.assertGreater(len(created), 0)
        for code in permission_catalog():
            self.assertTrue(
                Menu.objects.filter(permission=code, status=True, visible=True).exists(),
                'permission %s is not registered' % code,
            )

    def test_business_api_field_whitelist_removes_unregistered_fields(self):
        from .serializers import serialize_instance

        request = RequestFactory().get('/admin/api/rbac/users/')
        request.user = self.admin
        row = {
            'id': 1,
            'username': 'whitelist',
            'password_hash': 'should-not-leak',
            'internal_marker': 'should-not-leak',
            'roles': [{
                'id': 2, 'name': '审计角色', 'code': 'audit_role',
                'description': 'should-not-leak', 'max_users': 10,
            }],
        }
        data = serialize_instance(row, request, 'rbac.User')
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['username'], 'whitelist')
        self.assertNotIn('password_hash', data)
        self.assertNotIn('internal_marker', data)
        self.assertEqual(
            data['roles'],
            [{'id': 2, 'name': '审计角色', 'code': 'audit_role'}],
        )

    def test_abac_field_policy_can_hide_registered_field(self):
        from .models import AbacPolicy
        from .serializers import serialize_instance

        AbacPolicy.objects.create(
            name='hide phone', resource='rbac.User', action='view',
            field='phone', effect='allow', expression="user.username == 'nobody'",
            priority=1,
        )
        request = RequestFactory().get('/admin/api/rbac/users/')
        request.user = self.user
        data = serialize_instance(
            {'id': 1, 'username': 'audit_user', 'phone': '13800000000'},
            request, 'rbac.User',
        )
        self.assertIn('username', data)
        self.assertNotIn('phone', data)

    def test_angular_standalone_bootstrap_example_exists(self):
        root = Path(__file__).resolve().parents[2]
        source = (root / 'django_layuix/static/sdk/angular/standalone.ts').read_text(encoding='utf-8')
        self.assertIn('provideLayuiPermission', source)
        self.assertIn('layuiPermissionGuard', source)
        self.assertIn('bootstrapLayuiStandalone', source)

    def test_virtual_table_supports_column_configuration(self):
        root = Path(__file__).resolve().parents[2]
        source = (root / 'django_layuix/static/layui/js/common.js').read_text(encoding='utf-8')
        self.assertIn('columnsConfigurable', source)
        self.assertIn('setColumnConfig', source)
        self.assertIn('openColumnSettings', source)

    def test_user_batch_delete_protects_current_and_admins(self):
        User = get_user_model()
        target = User.objects.create_user(username='audit_batch_target', password='pass12345')
        superuser = User.objects.create_user(username='audit_batch_admin', password='pass12345')
        superuser.is_superuser = True
        superuser.save()

        response = self.client.post(
            '/admin/api/rbac/users/batch-delete/',
            {'ids': [target.id, superuser.id, self.admin.id]},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()['data']
        self.assertEqual(data['deleted'], 1)
        self.assertEqual(data['deleted_ids'], [target.id])
        self.assertEqual(len(data['skipped']), 2)
        self.assertFalse(User.objects.filter(pk=target.pk).exists())
        self.assertTrue(User.objects.filter(pk=superuser.pk).exists())
        self.assertTrue(User.objects.filter(pk=self.admin.pk).exists())

        invalid = self.client.post(
            '/admin/api/rbac/users/batch-delete/',
            {'ids': []},
            content_type='application/json',
        )
        self.assertEqual(invalid.status_code, 400)

    def test_server_detail_never_returns_credentials(self):
        from django.test import Client

        from django_layuix.ops.models import Server

        server = Server.objects.create(
            name='audit-secret-server', host='127.0.0.1', port=22,
            username='root', auth_type='password', password='secret-password',
            private_key='secret-key',
        )
        client = Client()
        client.force_login(self.admin)
        response = client.get('/admin/api/ops/servers/%s/detail/' % server.pk)
        self.assertEqual(response.status_code, 200)
        data = response.json()['data']
        self.assertIn('host', data)
        self.assertNotIn('password', data)
        self.assertNotIn('private_key', data)

    def test_role_permission_tree_echoes_exact_parent_ids(self):
        root = Path(__file__).resolve().parents[2]
        source = (root / 'django_layuix/static/layui/pages/role.html').read_text(encoding='utf-8')
        self.assertIn('syncTreeParentStates', source)
        self.assertIn('applyExactTreeChecks', source)
        self.assertIn('Object.keys(checkedSet)', source)
        self.assertIn('idSet[String(checkedIds[i])]', source)

    def test_unregistered_permission_is_denied(self):
        from .permission_registry import is_registered_permission

        self.assertFalse(is_registered_permission('audit:unregistered'))
        self.assertFalse(has_permission(self.admin, 'audit:unregistered'))
        self.assertFalse(self.admin.has_perm('audit:unregistered'))

    def test_registered_builtin_permission_is_available(self):
        from .permission_registry import is_registered_permission

        self.assertTrue(is_registered_permission('menu:view'))
        self.assertTrue(has_permission(self.admin, 'menu:view'))

    def test_frontend_permissions_expose_catalog(self):
        response = self.client.get('/admin/api/rbac/frontend/permissions/')
        self.assertEqual(response.status_code, 200)
        data = response.json()['data']
        self.assertIn('/static/layui/pages/menu.html', data['page_permissions'])
        self.assertIn('/static/layui/pages/dict.html', data['page_permissions'])
        self.assertIn('menu:view', data['permission_catalog'])
        self.assertIn('dict:view', data['permission_catalog'])
        self.assertTrue(any(item['value'] == 'add' for item in data['button_actions']))

    def test_generate_menu_buttons_is_idempotent_and_replaces(self):
        from .button_generator import generate_menu_buttons
        from .models import Menu

        menu = Menu.objects.create(name='审计权限菜单', permission='audit:view', menu_type=2)
        first = generate_menu_buttons(menu, ['view', 'add'], replace=True)
        second = generate_menu_buttons(menu, ['view', 'add'], replace=True)
        self.assertEqual(first['created'], ['audit:view', 'audit:add'])
        self.assertEqual(second['created'], [])
        self.assertTrue(Menu.objects.filter(parent=menu, permission='audit:add').exists())
        generated = generate_menu_buttons(menu, ['delete'], replace=True)
        self.assertEqual(generated['removed'], ['audit:view', 'audit:add'])
        self.assertFalse(Menu.objects.filter(parent=menu, permission='audit:add').exists())

    def test_generate_permissions_api_requires_menu_edit(self):
        from .models import Menu

        menu = Menu.objects.create(name='审计生成权限', permission='auditgen:view', menu_type=2)
        limited = get_user_model().objects.create_user(username='audit_gen_limited', password='pass12345')
        client = Client()
        client.force_login(limited)
        response = client.post(
            '/admin/api/rbac/menus/%s/generate-permissions/' % menu.pk,
            {'actions': ['add']}, content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)
        response = self.client.post(
            '/admin/api/rbac/menus/%s/generate-permissions/' % menu.pk,
            {'actions': ['add']}, content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Menu.objects.filter(parent=menu, permission='auditgen:add').exists())

    def test_virtual_table_supports_server_paging_and_persisted_widths(self):
        root = Path(__file__).resolve().parents[2]
        source = (root / 'django_layuix/static/layui/js/common.js').read_text(encoding='utf-8')
        for token in ('pageMode', 'loadPage', 'localStorage', 'layuix-virtual-resizer'):
            self.assertIn(token, source)

    def test_svelte_ssr_prefetch_helper_exists(self):
        root = Path(__file__).resolve().parents[2]
        core = (root / 'django_layuix/static/sdk/core/permission-client.js').read_text(encoding='utf-8')
        server = (root / 'django_layuix/static/sdk/svelte/server.js').read_text(encoding='utf-8')
        self.assertIn('prefetchPermissions', core)
        self.assertIn('prefetchServerPermissions', server)
        self.assertIn('event.fetch', server)


class I18nCoverageTests(SimpleTestCase):

    def test_layui_switch_text_is_translated(self):
        root = Path(__file__).resolve().parents[2]
        source = (root / 'django_layuix/static/layui/js/common.js').read_text(encoding='utf-8')
        self.assertIn("'lay-text': true", source)

    def test_template_keys_exist_in_both_languages(self):
        root = Path(__file__).resolve().parents[2]
        i18n_path = root / 'django_layuix/static/layui/js/i18n.js'
        source = i18n_path.read_text(encoding='utf-8')

        dictionaries = {'zh': set(), 'en': set()}
        current = None
        key_pattern = re.compile(r"^\s*['\"]([^'\"]+)['\"]\s*:")
        for line in source.splitlines():
            if line.strip().startswith("'zh-hans': {"):
                current = 'zh'
            elif line.strip().startswith("'en': {"):
                current = 'en'
                continue
            if line.strip().startswith("'zh-hans': {"):
                continue
            match = key_pattern.match(line)
            if current and match:
                dictionaries[current].add(match.group(1))

        used_keys = set()
        html_roots = [
            root / 'django_layuix/static/layui/pages',
            root / 'django_layuix/templates/admin',
            root / 'example/permission_demo/static',
            root / 'example/store/static',
        ]
        for html_root in html_roots:
            if not html_root.exists():
                continue
            for path in html_root.rglob('*.html'):
                html = path.read_text(encoding='utf-8')
                used_keys.update(re.findall(r"\bt\(\s*['\"]([^'\"]+)['\"]", html))
                used_keys.update(re.findall(r'data-i18n=["\']([^"\']+)["\']', html))

        js_files = [
            root / 'django_layuix/static/layui/js/common.js',
            root / 'django_layuix/static/layui/js/i18n.js',
        ]
        js_files.extend((root / 'django_layuix/static/sdk').rglob('*.js'))
        for js_path in js_files:
            if not js_path.exists():
                continue
            js = js_path.read_text(encoding='utf-8')
            js = '\n'.join(
                line for line in js.splitlines()
                if not line.lstrip().startswith(('*', '//'))
            )
            used_keys.update(re.findall(r"\bt\(\s*['\"]([^'\"]+)['\"]", js))

        missing = sorted(
            key for key in used_keys
            if key not in dictionaries['zh'] or key not in dictionaries['en']
        )
        self.assertEqual(missing, [])
        self.assertEqual(dictionaries['zh'], dictionaries['en'])
