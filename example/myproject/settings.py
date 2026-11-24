"""
Django settings for example project using django-layuix
展示 django-layuix 完整功能的示例配置
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# 开发模式：将 django-layuix 源码目录添加到 Python 路径
# 这样 example 项目会优先使用本地的 django-layuix 源码，而不是 pip 安装的包
django_layuix_src = str(BASE_DIR.parent)  # 指向 django_layuix 项目根目录
if django_layuix_src not in sys.path:
    sys.path.insert(0, django_layuix_src)

SECRET_KEY = 'django-insecure-example-key-for-development-only'

DEBUG = True

ALLOWED_HOSTS = ['*']

# ============================================================
# ① INSTALLED_APPS：django_layuix 必须在 django.contrib.admin 之前
#    django_layuix.rbac：开启 RBAC 用户/角色/菜单/权限管理
#    django_layuix.ops：开启运维管理（服务器/AI日志分析），可选
# ============================================================
INSTALLED_APPS = [
    'django_layuix',           # 必须放在 django.contrib.admin 之前！
    'django_layuix.rbac',      # RBAC 扩展（用户/角色/菜单/操作日志/系统配置）
    'django_layuix.ops',       # 运维管理扩展（服务器管理/AI日志分析），可选
    'store.apps.StoreConfig',  # 演示应用：商品管理（必须在 admin 之前，确保在 django_layuix ready() 前导入 admin.py）
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

AUTH_USER_MODEL = 'django_layuix_rbac.UserProfile'

# ============================================================
# ② 中间件：不要加 XFrameOptionsMiddleware（否则 iframe 子页面无法加载）
# ============================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django_layuix.rbac.middleware.ForceUtf8Middleware',  # 强制 UTF-8 编码，解决中文乱码
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',     # 国际化（rbac apps.py 会自动注入，手动加也没问题）
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # 注意：不加 XFrameOptionsMiddleware，否则侧边菜单 iframe 无法显示
]

ROOT_URLCONF = 'myproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
# 开发环境：让 example 使用主项目的静态文件（指向 django_layuix/static）
STATICFILES_DIRS = [
    BASE_DIR.parent / 'django_layuix' / 'static',
    BASE_DIR / 'store' / 'static',
]
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================================
# ③ RBAC 自定义用户模型
#    注意：AUTH_USER_MODEL 必须在项目创建之初就设置好，不可中途修改！
# ============================================================
AUTH_USER_MODEL = 'django_layuix_rbac.UserProfile'

# ============================================================
# ④ django-layuix 界面配置（所有配置均有默认值，不填也能正常运行）
# ============================================================
LAYUI_CONFIG = {
    'system_name': 'Layui Admin 演示',
    'system_version': '1.4.2',
    'system_description': 'django-layuix 功能演示项目',
    'logo_icon': 'layui-icon-code-circle',
    # 使用自定义图片
    # 'logo_url': '/static/your-logo.png',
    'login_bg_type': 'gradient',                    # gradient / color / image
    'login_bg_value': 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
    'copyright': 'Yingzi © 2026 Django Layuix Admin',
    
    # 首页自定义链接
    'home_quick_links': [
        {'name': 'Django官网', 'icon': 'layui-icon-website', 'url': 'https://www.djangoproject.com/'},
        {'name': 'Layui文档', 'icon': 'layui-icon-template', 'url': 'https://www.layui.dev/'},
        {'name': 'GitHub', 'icon': 'layui-icon-github', 'url': 'https://github.com/likangcai/django-layuix'},
        {'name': 'Gitee', 'icon': 'layui-icon-gitee', 'url': 'https://gitee.com/yingzi_shadow/django-layuix'}
        # {'name': '自定义页面', 'icon': 'layui-icon-app', 'url': '/custom-page/'},
    ],
    
    # 首页统计卡片（默认显示，可自定义）
    'home_stats_cards': [
        {'title': '用户总数', 'icon': 'layui-icon-user', 'color': '#1E9FFF', 'api_field': 'user_count'},
        {'title': '角色数量', 'icon': 'layui-icon-group', 'color': '#5FB878', 'api_field': 'role_count'},
        {'title': '菜单数量', 'icon': 'layui-icon-menu-fill', 'color': '#FFB800', 'api_field': 'menu_count'},
        {'title': '操作日志', 'icon': 'layui-icon-log', 'color': '#FF5722', 'api_field': 'log_count'},
    ],
    
    # 'frontend_url': 'http://localhost:3000/',     # 前端项目地址（顶部"访问前台"按钮）
    'webssh_url': 'http://localhost:8897/',        # WebSSH 服务地址（可选）
}

# ============================================================
# ⑤ 操作日志配置（可选，不填使用默认值）
#    默认记录 /admin/api/rbac/ 和 /admin/api/ops/ 下的写操作
# ============================================================
# OPERATION_LOG = {
#     'PREFIXES': ['/admin/api/rbac/', '/admin/api/ops/', '/api/'],
#     'IGNORE_KEYWORDS': ['login', 'logout', 'register', 'upload', 'system/info', 'stats'],
#     'EXCLUDE_PREFIXES': ['/api/public/'],
# }

# ============================================================
# ⑥ AI 日志分析配置（可选，也可在后台"AI 配置"页面配置）
#    支持 OpenAI、智谱AI、DeepSeek、通义千问、Moonshot 等 OpenAI 兼容协议
# ============================================================
# LAYUI_AI_API_KEY = 'sk-xxx'
# LAYUI_AI_BASE_URL = 'https://open.bigmodel.cn/api/paas/v4/'   # 智谱AI 示例
# LAYUI_AI_MODEL = 'glm-4-flash'

# ============================================================
# ⑦ 多实例部署：共享缓存（可选，Token 场景 DSD 激活角色需要）
#    单实例可不配置，默认使用本地内存缓存
# ============================================================
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.redis.RedisCache',
#         'LOCATION': 'redis://127.0.0.1:6379/1',
#     }
# }

# ============================================================
# ⑧ 数据权限（1.4.2 可选，不配置时行为与旧版本一致）
# ============================================================
# LAYUIX_SCOPE_HIERARCHY = ['global', 'region', 'team']
# LAYUIX_SCOPE_TREE = {
#     'global': ['east_region', 'west_region'],
#     'east_region': ['east_team_a', 'east_team_b'],
# }
