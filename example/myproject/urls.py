# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-26 22:19
# @FileName  : urls.py
# -----------------------------
"""
URL 配置 - django-layuix example project

django_layuix.rbac 的 AppConfig.ready() 会自动将 RBAC API 路由注册到
/admin/api/rbac/ 和 /admin/api/ops/ 下，无需在此手动配置。

store 的 API 路由通过 store/urls.py 注册到 /admin/api/store/ 下。

只需保留 admin.site.urls 即可使用全部功能。

WebSSH 集成（可选）：
- 需要安装 webssh 包：pip install webssh
- WebSSH 作为独立服务运行，也可集成到 Django 中
"""
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django_layuix.admin import layui_admin_site

def webssh_proxy(request):
    """WebSSH 代理 - 重定向到独立的 WebSSH 服务"""
    # 优先从数据库读取系统配置
    webssh_url = None
    try:
        from django_layuix.rbac.models import SystemConfig
        db_config = SystemConfig.objects.filter(key='webssh_url').first()
        if db_config and db_config.value:
            webssh_url = db_config.value
    except Exception:
        pass
    
    # 回退到 settings.py 中的 LAYUI_CONFIG
    if not webssh_url:
        webssh_url = getattr(settings, 'LAYUI_CONFIG', {}).get('webssh_url', '/webssh/')
    
    query_string = request.META.get('QUERY_STRING', '')
    
    # 构建完整的重定向 URL
    if query_string:
        redirect_url = f"{webssh_url}?{query_string}"
    else:
        redirect_url = webssh_url
    
    return redirect(redirect_url)

urlpatterns = [
    path('admin/', layui_admin_site.urls),
    # WebSSH 路由 - 重定向到独立的 WebSSH 服务
    path('webssh/', webssh_proxy, name='webssh'),
]

# 开发模式下提供 media 文件（头像、上传图片等）的访问
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
