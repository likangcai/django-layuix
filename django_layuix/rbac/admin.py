from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    Menu, Role, RoleMutex, RolePrerequisite, PluginRegistry,
    UserProfile, OperationLog, SystemConfig,
)


class MenuAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'parent', 'menu_type', 'sort', 'visible', 'status']
    list_filter = ['menu_type', 'status', 'visible']
    search_fields = ['name', 'permission']
    list_editable = ['sort', 'visible', 'status']
    ordering = ['sort', 'id']


class RoleAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'code', 'is_system', 'status']
    list_filter = ['is_system', 'status']
    search_fields = ['name', 'code']
    filter_horizontal = ['menus', 'parent_roles']


# BUG-30 FIX: 继承 UserAdmin 以正确处理密码字段
class UserProfileAdmin(BaseUserAdmin):
    list_display = ['id', 'username', 'nickname', 'phone', 'is_active', 'is_tester', 'theme']
    list_filter = ['is_active', 'is_tester', 'theme']
    search_fields = ['username', 'nickname', 'phone']
    filter_horizontal = ['roles']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('扩展信息', {
            'fields': ('nickname', 'phone', 'avatar', 'theme', 'language', 'is_tester', 'roles')
        }),
    )


class OperationLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'module', 'action', 'ip', 'method', 'status', 'create_time']
    list_filter = ['module', 'status', 'method']
    search_fields = ['action', 'user__username']
    readonly_fields = ['user', 'module', 'action', 'ip', 'method', 'url', 'status', 'create_time']
    date_hierarchy = 'create_time'


class SystemConfigAdmin(admin.ModelAdmin):
    list_display = ['id', 'key', 'value', 'config_type', 'sort']
    search_fields = ['key', 'value']
    list_editable = ['sort']


admin.site.register(Menu, MenuAdmin)
admin.site.register(Role, RoleAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(OperationLog, OperationLogAdmin)
admin.site.register(SystemConfig, SystemConfigAdmin)


class RoleMutexAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'kind', 'is_active', 'create_time']
    list_filter = ['kind', 'is_active']
    search_fields = ['name']
    filter_horizontal = ['roles', 'permissions']


class RolePrerequisiteAdmin(admin.ModelAdmin):
    list_display = ['id', 'role', 'prerequisite', 'create_time']
    search_fields = ['role__name', 'prerequisite__name']


class PluginRegistryAdmin(admin.ModelAdmin):
    list_display = ['id', 'key', 'name', 'version', 'source', 'is_active', 'validation_error']
    list_filter = ['source', 'is_active']
    search_fields = ['key', 'name', 'app_label']
    readonly_fields = ['create_time', 'update_time', 'validation_error']

    def save_model(self, request, obj, form, change):
        from .plugins import set_plugin_active

        was_active = False
        if obj.pk:
            was_active = bool(
                PluginRegistry.objects.filter(pk=obj.pk).values_list('is_active', flat=True).first()
            )
        super().save_model(request, obj, form, change)
        if was_active != obj.is_active:
            set_plugin_active(obj.key, obj.is_active)


admin.site.register(RoleMutex, RoleMutexAdmin)
admin.site.register(RolePrerequisite, RolePrerequisiteAdmin)
admin.site.register(PluginRegistry, PluginRegistryAdmin)
