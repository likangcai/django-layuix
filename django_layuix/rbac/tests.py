# -*- coding: utf-8 -*-
"""RBAC3 regression tests: inheritance, constraints and server-side enforcement."""
import importlib.util
from unittest import mock, skipUnless

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase, override_settings

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
        self.assertTrue(has_permission(self.admin, 'any:code'))
        self.assertFalse(has_permission(None, 'any:code'))

    @skipUnless(importlib.util.find_spec('rest_framework'), 'DRF not installed')
    def test_drf_permission_adapter(self):
        from django_layuix.integrations.drf import LayuiRBACPermission

        class DummyView:
            layui_permission = 'test:drf'

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
            filter_fields(self.user, 'view', 'store.Order', ['id', 'cost']), ['id']
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
