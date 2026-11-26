from django.urls import path
from . import data_admin_views, dictionary_views, permission_catalog_views, views

urlpatterns = [
    # User info & menus
    path('userinfo/', views.user_info, name='rbac_user_info'),

    # System info
    path('system/info/', views.system_info, name='rbac_system_info'),
    path('system/info/stream/', views.system_info_stream, name='rbac_system_info_stream'),  # SSE流式推送
    path('system/info/stream-ticket/', views.system_info_stream_ticket, name='rbac_system_info_stream_ticket'),
    path('system/public-config/', views.public_config, name='rbac_public_config'),         # 公开配置(无需登录)
    path('system/config/', views.system_config, name='rbac_system_config'),                # 需要登录

    # Profile
    path('profile/', views.profile_update, name='rbac_profile_update'),
    path('profile/password/', views.profile_password, name='rbac_profile_password'),
    path('profile/theme/', views.profile_theme, name='rbac_profile_theme'),
    path('profile/avatar/', views.profile_avatar, name='rbac_profile_avatar'),
    path('available-themes/', views.available_themes, name='rbac_available_themes'),

    # Upload
    path('upload/image/', views.upload_image, name='rbac_upload_image'),

    # Language
    path('set-language/', views.set_language, name='rbac_set_language'),

    # Register
    path('register/', views.register, name='rbac_register'),

    # Login (CSRF exempt fallback)
    path('login/', views.api_login, name='rbac_api_login'),

    # Logout
    path('logout/', views.logout, name='rbac_logout'),

    # Stats
    path('stats/', views.stats_data, name='rbac_stats_data'),

    # Menu CRUD
    path('menus/tree/', views.menu_tree, name='rbac_menu_tree'),
    path('menus/frontend/', views.frontend_menu_tree, name='rbac_frontend_menu_tree'),
    path('menus/create/', views.menu_create, name='rbac_menu_create'),
    path('menus/<int:pk>/', views.menu_detail, name='rbac_menu_detail'),
    path('menus/<int:pk>/generate-permissions/', views.menu_generate_permissions, name='rbac_menu_generate_permissions'),

    # Role CRUD
    path('roles/', views.role_list, name='rbac_role_list'),
    path('roles/create/', views.role_create, name='rbac_role_create'),
    path('roles/<int:pk>/effective_permissions/', views.role_effective_permissions, name='rbac_role_effective_permissions'),
    path('roles/<int:pk>/', views.role_detail, name='rbac_role_detail'),
    path('roles/<int:pk>/update/', views.role_detail, name='rbac_role_update'),
    path('roles/<int:pk>/delete/', views.role_detail, name='rbac_role_delete'),
    path('roles/<int:pk>/copy/', views.role_copy, name='rbac_role_copy'),

    # User CRUD
    path('users/', views.user_list, name='rbac_user_list'),
    path('users/org-options/', views.user_org_options, name='rbac_user_org_options'),
    path('users/batch-delete/', views.user_batch_delete, name='rbac_user_batch_delete'),
    path('users/create/', views.user_create, name='rbac_user_create'),
    path('users/<int:pk>/update/', views.user_update, name='rbac_user_update'),
    path('users/<int:pk>/delete/', views.user_delete, name='rbac_user_delete'),
    path('users/<int:pk>/reset-password/', views.user_reset_password, name='rbac_user_reset_password'),
    path('users/<int:pk>/status/', views.user_toggle_status, name='rbac_user_toggle_status'),
    path('users/<int:pk>/position-assignments/', views.user_position_assignments, name='rbac_user_position_assignments'),
    path('position-assignments/<int:pk>/end/', views.end_position_assignment, name='rbac_end_position_assignment'),

    # Plugin registry
    path('plugins/manifest/', views.plugin_manifest, name='rbac_plugin_manifest'),
    path('plugins/', views.plugin_list, name='rbac_plugin_list'),

    # 1.4.2 ABAC and scope nodes
    path('scope-nodes/', views.scope_node_list, name='rbac_scope_node_list'),
    path('scope-nodes/<int:pk>/', views.scope_node_detail, name='rbac_scope_node_detail'),
    path('abac-policies/', views.abac_policy_list, name='rbac_abac_policy_list'),
    path('abac-policies/<int:pk>/', views.abac_policy_detail, name='rbac_abac_policy_detail'),
    path('abac-check/', views.abac_check, name='rbac_abac_check'),
    path('frontend/permissions/', views.frontend_permissions, name='rbac_frontend_permissions'),

    # 1.4.1 SoD compatibility endpoints
    path('sod-constraints/check/', views.sod_constraint_check, name='rbac_sod_constraint_check'),
    path('sod-constraints/', views.sod_constraint_list, name='rbac_sod_constraint_list'),
    path('sod-constraints/<int:pk>/', views.sod_constraint_detail, name='rbac_sod_constraint_detail'),

    # RBAC3 / RBAC4 constraints & active roles
    path('constraints/', views.constraint_list, name='rbac_constraint_list'),
    path('constraints/mutex/', views.mutex_create, name='rbac_mutex_create'),
    path('constraints/mutex/<int:pk>/', views.mutex_delete, name='rbac_mutex_delete'),
    path('constraints/prerequisite/', views.prerequisite_create, name='rbac_prerequisite_create'),
    path('constraints/prerequisite/<int:pk>/', views.prerequisite_delete, name='rbac_prerequisite_delete'),
    path('active-roles/', views.active_roles, name='rbac_active_roles'),

    # Data dictionary
    path('dictionaries/', dictionary_views.dictionary_list, name='rbac_dictionary_list'),
    path('dictionaries/create/', dictionary_views.dictionary_create, name='rbac_dictionary_create'),
    path('dictionaries/options/<str:code>/', dictionary_views.dictionary_options, name='rbac_dictionary_options'),
    path('dictionaries/<int:pk>/items/', dictionary_views.dictionary_items, name='rbac_dictionary_items'),
    path('dictionaries/<int:pk>/items/create/', dictionary_views.dictionary_item_create, name='rbac_dictionary_item_create'),
    path('dictionaries/<int:pk>/', dictionary_views.dictionary_detail, name='rbac_dictionary_detail'),
    path('dictionary-items/<int:pk>/', dictionary_views.dictionary_item_detail, name='rbac_dictionary_item_detail'),

    # Department / position / region / member level
    path('departments/', data_admin_views.department_list, name='rbac_department_list'),
    path('departments/create/', data_admin_views.department_create, name='rbac_department_create'),
    path('departments/<int:pk>/', data_admin_views.department_detail, name='rbac_department_detail'),
    path('positions/', data_admin_views.position_list, name='rbac_position_list'),
    path('positions/create/', data_admin_views.position_create, name='rbac_position_create'),
    path('positions/<int:pk>/', data_admin_views.position_detail, name='rbac_position_detail'),
    path('permission-catalog/', permission_catalog_views.permission_catalog_list, name='rbac_permission_catalog_list'),
    path('permission-catalog/<int:pk>/status/', permission_catalog_views.permission_catalog_set_status, name='rbac_permission_catalog_status'),
    path('regions/', data_admin_views.region_list, name='rbac_region_list'),
    path('regions/tree/', data_admin_views.region_tree, name='rbac_region_tree'),
    path('regions/create/', data_admin_views.region_create, name='rbac_region_create'),
    path('regions/<int:pk>/', data_admin_views.region_detail, name='rbac_region_detail'),
    path('member-levels/', data_admin_views.member_level_list, name='rbac_member_level_list'),
    path('member-levels/create/', data_admin_views.member_level_create, name='rbac_member_level_create'),
    path('member-levels/<int:pk>/', data_admin_views.member_level_detail, name='rbac_member_level_detail'),

    # Generic data import/export and batch operations
    path('data-export/', data_admin_views.data_export, name='rbac_data_export'),
    path('data-import/', data_admin_views.data_import, name='rbac_data_import'),
    path('data-batch-delete/', data_admin_views.data_batch_delete, name='rbac_data_batch_delete'),
    path('data-batch-status/', data_admin_views.data_batch_status, name='rbac_data_batch_status'),

    # Operation Log
    path('logs/', views.log_list, name='rbac_log_list'),

    # System Config CRUD
    path('configs/', views.config_list, name='rbac_config_list'),
    path('configs/create/', views.config_create, name='rbac_config_create'),
    path('configs/<int:pk>/update/', views.config_update, name='rbac_config_update'),
    path('configs/<int:pk>/delete/', views.config_delete, name='rbac_config_delete'),
]
