from django.urls import path

from . import views

urlpatterns = [
    # Server CRUD
    path('servers/', views.server_list, name='ops_server_list'),
    path('servers/create/', views.server_create, name='ops_server_create'),
    path('servers/<int:pk>/detail/', views.server_detail, name='ops_server_detail'),
    path('servers/<int:pk>/update/', views.server_update, name='ops_server_update'),
    path('servers/<int:pk>/delete/', views.server_delete, name='ops_server_delete'),

    # SSH Operations
    path('servers/<int:pk>/test/', views.server_test, name='ops_server_test'),
    path('servers/<int:pk>/log/', views.server_log, name='ops_server_log'),
    path('servers/<int:pk>/exec/', views.server_exec, name='ops_server_exec'),

    # AI Analysis
    path('ai/analyze-log/', views.ai_analyze_log, name='ops_ai_analyze_log'),

    # AI Config (multi-model)
    path('ai/config/', views.ai_config_get, name='ops_ai_config_get'),           # GET legacy / GET?id=xxx
    path('ai/config/list/', views.ai_config_list, name='ops_ai_config_list'),    # GET all
    path('ai/config/save/', views.ai_config_save, name='ops_ai_config_save'),    # POST create/update
    path('ai/config/test/', views.ai_config_test, name='ops_ai_config_test'),    # POST test
    path('ai/config/<str:config_id>/delete/', views.ai_config_delete, name='ops_ai_config_delete'),
    path('ai/config/<str:config_id>/set-default/', views.ai_config_set_default, name='ops_ai_config_set_default'),
]
