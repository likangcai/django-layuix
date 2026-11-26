# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-26 22:19
# @FileName  : admin.py
# -----------------------------
from django.contrib import admin
from .models import Server, AIModelConfig


class ServerAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'host', 'port', 'username', 'auth_type', 'is_active']
    list_filter = ['auth_type', 'is_active']
    search_fields = ['name', 'host', 'username']
    list_editable = ['is_active']
    exclude = ['password', 'private_key']  # Don't show sensitive fields in list

    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'host', 'port', 'username', 'description')
        }),
        ('认证信息', {
            'fields': ('auth_type', 'password', 'private_key'),
            'classes': ('wide',)
        }),
        ('状态', {
            'fields': ('is_active',)
        }),
    )


class AIModelConfigAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'provider', 'model', 'is_default', 'is_active', 'created_at']
    list_filter = ['provider', 'is_default', 'is_active']
    search_fields = ['name', 'model', 'base_url']
    list_editable = ['is_default', 'is_active']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'provider', 'model', 'description')
        }),
        ('API 配置', {
            'fields': ('api_key', 'base_url'),
            'classes': ('wide',)
        }),
        ('状态', {
            'fields': ('is_default', 'is_active')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


admin.site.register(Server, ServerAdmin)
admin.site.register(AIModelConfig, AIModelConfigAdmin)
