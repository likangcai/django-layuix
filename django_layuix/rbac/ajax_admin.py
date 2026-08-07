# -*- coding: utf-8 -*-
"""
Django-Layuix AJAX Admin Mixin

提供以下功能:
1. AJAX批量操作
2. 自定义Action异步调用
3. Layer弹窗配置
4. 搜索和过滤条件处理
"""

import json
import logging
import traceback
from django.contrib import admin
from django.db.models import Q
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import path

logger = logging.getLogger(__name__)


class LayuiAjaxAdmin(admin.ModelAdmin):
    """
    Django-Layuix AJAX Admin Mixin
    
    为你的ModelAdmin添加AJAX功能
    
    使用示例:
        from django_layuix.rbac.ajax_admin import LayuiAjaxAdmin
        
        @admin.register(Product)
        class ProductAdmin(LayuiAjaxAdmin):
            # 定义自定义action
            def batch_publish(self, request, queryset):
                '''批量发布'''
                count = queryset.update(status='published')
                return {
                    'status': 'success',
                    'msg': f'成功发布 {count} 个商品'
                }
            
            # 配置Layer弹窗
            @layer
            def custom_action(self, request):
                return {
                    'type': 2,
                    'title': '自定义操作',
                    'content': '/custom/url/',
                    'area': ['600px', '400px']
                }
    """
    
    def _get_queryset_with_filters(self, request):
        """
        获取应用了过滤条件的QuerySet
        
        支持:
        - 选中的数据过滤
        - 搜索条件过滤
        - 自定义过滤参数
        """
        post = request.POST
        action = post.get("_action")
        selected = post.get("_selected")
        select_across = post.get("select_across", "0")
        
        if not hasattr(self, action):
            raise Exception(f"Action '{action}' not found")
        
        # 获取基础QuerySet
        queryset = self.get_changelist_instance(request).get_queryset(request)
        
        # 如果没有选择全部,只包含选中的数据
        if select_across == "0" and selected:
            selected_ids = selected.split(",")
            queryset = queryset.filter(pk__in=selected_ids)
        else:
            # 选择全部时,应用搜索和过滤条件
            
            # 应用搜索条件
            search_value = post.get("_search")
            if search_value:
                search_fields = self.get_search_fields(request)
                if search_fields:
                    q = Q()
                    for field in search_fields:
                        q |= Q(**{f"{field}__icontains": search_value})
                    queryset = queryset.filter(q)
            
            # 应用过滤条件
            filter_data = post.get("_filter")
            if filter_data:
                try:
                    filters = json.loads(filter_data)
                    cleaned_filters = self._clean_filters(filters)
                    queryset = queryset.filter(**cleaned_filters)
                except Exception as e:
                    logger.error(f"Filter parsing error: {e}")
                    traceback.print_exc()
        
        return queryset
    
    def _clean_filters(self, filters):
        """
        清理和标准化过滤参数
        
        处理特殊情况:
        - __exact 转 __in (用于多选)
        - 空值过滤
        """
        cleaned = {}
        for key, value in filters.items():
            # 处理多选情况
            if "__exact" in key and isinstance(value, list):
                new_key = key.replace('__exact', '__in')
                cleaned[new_key] = value[0] if value else None
            else:
                cleaned[key] = value
        
        # 移除None值
        return {k: v for k, v in cleaned.items() if v is not None}
    
    def ajax_callback(self, request):
        """
        AJAX回调处理入口
        
        处理流程:
        1. 获取action名称
        2. 获取过滤后的QuerySet
        3. 调用对应的action方法
        4. 返回统一格式的响应
        """
        post = request.POST
        action = post.get("_action")
        
        try:
            # 检查action是否存在
            if not hasattr(self, action):
                return JsonResponse({
                    'status': 'error',
                    'msg': f'Action "{action}" not found'
                }, status=404)
            
            # 获取action函数
            func, action_name, description = self.get_action(action)
            
            # 获取过滤后的QuerySet
            queryset = self._get_queryset_with_filters(request)
            
            # 调用action
            result = func(self, request, queryset)
            
            # 处理不同类型的返回值
            if result is None:
                # 无返回值,默认成功
                return JsonResponse({
                    'status': 'success',
                    'msg': '操作成功'
                })
            elif isinstance(result, HttpResponseRedirect):
                # 重定向
                return JsonResponse({
                    'status': 'redirect',
                    'url': result.url
                })
            elif isinstance(result, JsonResponse):
                # 直接返回JsonResponse
                return result
            elif isinstance(result, dict):
                # 字典格式,自动包装为成功响应
                return JsonResponse({
                    'status': 'success',
                    **result
                })
            else:
                # 其他类型,记录警告
                logger.warning(f"Action {action} returned unexpected type: {type(result)}")
                return JsonResponse({
                    'status': 'error',
                    'msg': str(result)
                })
        
        except Exception as e:
            logger.error(f"AJAX action error: {e}")
            traceback.print_exc()
            return JsonResponse({
                'status': 'error',
                'msg': f'操作失败: {str(e)}'
            }, status=500)
    
    def get_layer_config(self, request):
        """
        获取Layer弹窗配置
        
        用于动态配置弹窗的参数、标题、内容等
        
        使用方式:
            @layer
            def my_action(self, request):
                return {
                    'type': 2,  # iframe类型
                    'title': '我的弹窗',
                    'content': '/some/url/',
                    'area': ['800px', '600px']
                }
        """
        action = request.POST.get("_action")
        
        try:
            if not hasattr(self, action):
                raise Exception(f'Action "{action}" not found')
            
            func, action_name, description = self.get_action(action)
            
            # 检查是否有layer装饰器
            if hasattr(func, 'layer'):
                layer_func = func.layer
                
                # 根据参数数量调用不同的版本
                arg_count = layer_func.__code__.co_argcount
                
                if arg_count == 2:
                    # 新版本: layer(self, request)
                    result = layer_func(self, request)
                elif arg_count == 3:
                    # 兼容旧版本: layer(self, request, queryset)
                    queryset = self._get_queryset_with_filters(request)
                    result = layer_func(self, request, queryset)
                else:
                    raise Exception(f"Invalid layer function signature: {arg_count} args")
                
                return JsonResponse(result, safe=False)
            else:
                raise Exception(f'Action "{action}" has no @layer decorator')
        
        except Exception as e:
            logger.error(f"Get layer config error: {e}")
            return JsonResponse({
                'status': 'error',
                'msg': str(e)
            }, status=500)
    
    def get_urls(self):
        """
        注册AJAX相关URL
        
        添加两个端点:
        - ajax: AJAX操作回调
        - layer: Layer弹窗配置
        """
        info = self.model._meta.app_label, self.model._meta.model_name
        
        custom_urls = [
            path('ajax/', self.ajax_callback, name=f'{info[0]}_{info[1]}_ajax'),
            path('layer/', self.get_layer_config, name=f'{info[0]}_{info[1]}_layer'),
        ]
        
        return custom_urls + super().get_urls()


def layer(func):
    """
    Layer弹窗配置装饰器
    
    使用示例:
        class MyAdmin(LayuiAjaxAdmin):
            @layer
            def custom_action(self, request):
                return {
                    'type': 2,
                    'title': '自定义弹窗',
                    'content': '/custom/url/',
                    'area': ['600px', '400px'],
                    'btn': ['确定', '取消']
                }
    """
    func.layer = func
    return func
