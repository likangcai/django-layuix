from django.urls import path
from . import views

urlpatterns = [
    # User info & menus
    path('userinfo/', views.user_info, name='rbac_user_info'),

    # System info
    path('system/info/', views.system_info, name='rbac_system_info'),
    path('system/info/stream/', views.system_info_stream, name='rbac_system_info_stream'),  # SSE流式推送
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

    # Role CRUD
    path('roles/', views.role_list, name='rbac_role_list'),
    path('roles/create/', views.role_create, name='rbac_role_create'),
    path('roles/<int:pk>/', views.role_detail, name='rbac_role_detail'),
    path('roles/<int:pk>/update/', views.role_detail, name='rbac_role_update'),
    path('roles/<int:pk>/delete/', views.role_detail, name='rbac_role_delete'),
    path('roles/<int:pk>/copy/', views.role_copy, name='rbac_role_copy'),

    # User CRUD
    path('users/', views.user_list, name='rbac_user_list'),
    path('users/create/', views.user_create, name='rbac_user_create'),
    path('users/<int:pk>/update/', views.user_update, name='rbac_user_update'),
    path('users/<int:pk>/delete/', views.user_delete, name='rbac_user_delete'),
    path('users/<int:pk>/reset-password/', views.user_reset_password, name='rbac_user_reset_password'),
    path('users/<int:pk>/status/', views.user_toggle_status, name='rbac_user_toggle_status'),

    # Operation Log
    path('logs/', views.log_list, name='rbac_log_list'),

    # System Config CRUD
    path('configs/', views.config_list, name='rbac_config_list'),
    path('configs/create/', views.config_create, name='rbac_config_create'),
    path('configs/<int:pk>/update/', views.config_update, name='rbac_config_update'),
    path('configs/<int:pk>/delete/', views.config_delete, name='rbac_config_delete'),
]
