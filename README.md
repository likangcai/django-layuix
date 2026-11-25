# django-layuix

基于 Layui 的 Django Admin 主题，它使用现代化的 Layui 界面替换 Django 默认的后台管理界面，并结合ai功能实现日志分析。

## 功能特性

- 🌗 现代化 Layui 后台管理界面（深色/浅色主题切换）
- 🌐 **完整国际化支持**（中文/英文），前端 JS + 后端 Django i18n 双层翻译，菜单多语言字段
- 🔐 RBAC3 权限管理（菜单管理、角色管理、用户管理、按钮级权限控制、角色继承、SSD/DSD 约束、前置角色与人数限制）
- 📊 Dashboard 仪表盘（CPU/内存折线图、磁盘饼图、网络监控）
- 📝 操作日志（自动记录用户操作，支持自定义路径前缀，可记录前端 API）
- ⚙️ 系统配置（键值对配置，数据库动态管理，实时生效）
- 🖼️ 图片上传（Logo、Favicon 等配置项支持本地上传）
- 🌐 Favicon 自定义（支持 ICO/PNG/SVG 格式）
- 👤 个人中心（修改资料、更换头像、修改密码）
- 📝 用户注册 API（前端注册用户自动绑定默认角色）
- 🚪 AJAX 登出（确认弹窗 + 自动跳转）
- 🔗 前端页面入口（顶部“查看站点”按钮）
- 📱 响应式设计
- 🔧 极简配置，开箱即用

---

## 快速开始

### 1. 安装

```bash
# 基础安装（包含 RBAC + 系统配置 + 操作日志 + Dashboard）
pip install django-layuix

# 安装所有功能（含运维管理 + AI 日志分析）
pip install django-layuix[all]

# 或按需安装
pip install django-layuix[ops]   # 运维管理（服务器管理、SSH 终端）
pip install django-layuix[ai]    # AI 日志分析
```

### 2. 标准配置（必需步骤）

> ⚠️ **重要说明**：django-layuix 由两个**必需组件**组成：
>
> | 组件 | 包名 | 功能 |
> |------|------|------|
> | **基础框架** | `django_layuix` | 模板替换、AdminSite、静态文件、国际化 |
> | **RBAC 引擎** | `django_layuix.rbac` | API 路由、用户模型、权限系统、菜单管理 |
>
> `django_layuix.rbac` **不是可选扩展**！前端页面必须通过 RBAC API 获取用户信息、菜单数据、系统配置等。缺少此组件会导致 404 错误和功能异常。

#### Step 1: 配置 settings.py

在 `INSTALLED_APPS` 中将 `django_layuix` 和 `django_layuix.rbac` 添加到 `django.contrib.admin` **之前**：

```python
# settings.py
INSTALLED_APPS = [
    'django_layuix',                    # 必须放在 django.contrib.admin 之前
    'django_layuix.rbac',               # ⭐ 必需！提供 API 路由和数据模型
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # ... 你的应用
]

# 使用自定义用户模型（推荐）
AUTH_USER_MODEL = 'django_layuix_rbac.UserProfile'
```

> **注意**：如果需要 iframe 嵌入功能，请从 `MIDDLEWARE` 中移除 `django.middleware.clickjacking.XFrameOptionsMiddleware`。
>
> ⚠️ **关键提醒**：`AUTH_USER_MODEL` 必须在项目创建之初就设置好，中途切换会导致数据库迁移问题。

#### Step 2: 配置 urls.py

django-layuix 使用自定义的 `LayuiAdminSite`（即 `layui_admin_site`）替代 Django 默认的 `admin.site`。当 `'django_layuix'` 在 `INSTALLED_APPS` 中时，Django 启动时会自动将 `admin.site` 替换为 `layui_admin_site`。

```python
# urls.py

# ✅ 方式一：使用 admin.site（推荐，最简单）
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),  # 实际指向 layui_admin_site.urls
]

# ✅ 方式二：显式使用 layui_admin_site（更明确）
# from django_layuix.admin import layui_admin_site
# urlpatterns = [
#     path('admin/', layui_admin_site.urls),
# ]
```

> **⚠️ 重要提示**：如果遇到 `/admin/api/rbac/userinfo/` 404 错误，请检查：
> - [ ] `INSTALLED_APPS` 中包含 `'django_layuix'` 和 `'django_layuix.rbac'`
> - [ ] 已运行 `python manage.py migrate`
> - [ ] 已运行 `python manage.py init_menu`
> - [ ] 重启服务器并清除浏览器缓存 (Ctrl+F5)

> 💡 想直接体验角色继承、SSD、数据范围、ABAC 与前端 SDK，请先阅读：[新增功能快速上手示例](docs/NEW_FEATURES_QUICKSTART.md)。

#### Step 3: 初始化数据库

运行迁移命令创建数据表，然后初始化默认数据：

```bash
# 创建数据库表（用户、菜单、角色、权限、系统配置等）
python manage.py makemigrations
python manage.py migrate

# 初始化默认菜单、角色、权限、系统配置（仅首次运行）
python manage.py init_menu

# 需要同步创建测试数据的也可以执行以下命令
python manage.py init_data

# 演示应用（商品分类/商品/订单）需要单独初始化示例数据
python manage.py init_demo_data

# 一键初始化全部权限示例（继承/SSD/Scope/组织节点/ABAC/demo app）
python manage.py init_permission_demo
```

`init_menu` 命令会自动创建：

| 数据类型 | 创建内容 | 说明 |
|---------|---------|------|
| **默认菜单** | 权限管理、系统管理 | 包含子菜单：菜单/角色/用户、个人中心/操作日志/系统配置 |
| **按钮权限** | 25 个权限项 | 菜单/角色/用户/配置/服务器/AI 的按钮级权限 |
| **管理员角色** | `管理员` | 绑定所有菜单和按钮权限 |
| **注册角色** | `注册用户` | 仅个人中心权限（前端注册用户默认绑定） |
| **系统配置** | 17 个配置项 | 系统信息、Logo、登录背景、首页卡片/链接、WebSSH、RBAC 策略等 |

#### Step 4: 创建管理员账号

```bash
python manage.py createsuperuser
# 输入用户名: admin
# 输入邮箱: admin@example.com
# 输入密码: admin123 (或其他强密码)
# 再次输入密码确认
```

#### Step 5: 启动并验证

```bash
# 启动开发服务器
python manage.py runserver
```

访问 http://127.0.0.1:8000/admin/ ，使用刚创建的管理员账号登录即可看到完整的 Layui 后台管理系统。

**验证清单**：
- [ ] 登录页面显示 Layui 风格界面
- [ ] 登录后左侧菜单正常显示（权限管理、系统管理等）
- [ ] 控制台无 `/admin/api/rbac/userinfo/` 404 错误
- [ ] Dashboard 仪表盘正常加载
- [ ] 用户信息（头像、昵称）正确显示

### 3. 高级配置

#### 4.1 settings.py 配置（默认值）

```python
# settings.py
LAYUI_CONFIG = {
    # 系统信息
    'system_name': 'Django Layuix Admin',
    'system_version': '1.4.4',         # 系统版本号（显示在侧边栏）
    'system_description': '',          # 系统描述（显示在登录页）

    # Logo
    'logo_url': '',                    # 自定义 Logo URL（设置后替换图标）
    'logo_icon': 'layui-icon-code-circle',  # Layui 图标类名

    # 登录页面背景（三选一，通过 login_bg_type 切换）
    #   type='gradient'  → 使用 login_bg_value（CSS渐变值）+ ✨ 粒子动画叠加
    #   type='color'     → 使用 login_bg_value（纯色值，如 #1a1a2e）+ 无粒子
    #   type='image'     → 使用 login_bg_image（图片URL）+ 无粒子
    #   其他/空值        → 默认深色渐变 + ✨ 粒子动画（不做处理）
    'login_bg_type': 'gradient',       # gradient / color / image（字符串，仅此3个值有效）
    'login_bg_value': 'linear-gradient(135deg, #2d3a4b 0%, #1a1a2e 100%)',
    'login_bg_image': '',              # 背景图片 URL（仅当 type=image 且有值时生效）

    # 前端项目
    'frontend_url': '',                # 前端项目 URL（顶部"查看站点"按钮）
    'webssh_url': '/webssh/',          # WebSSH 服务地址（服务器终端功能）

    # 版权信息
    'copyright': '',

    # 首页自定义快速链接（与 init_menu 落库默认值一致）
    'home_quick_links': [
        {'name': 'Django官网', 'icon': 'layui-icon-website', 'url': 'https://www.djangoproject.com/'},
        {'name': 'Layui文档', 'icon': 'layui-icon-template', 'url': 'https://www.layui.dev/'},
        {'name': 'GitHub', 'icon': 'layui-icon-github', 'url': 'https://github.com/likangcai/django-layuix'},
        {'name': 'Gitee', 'icon': 'layui-icon-gitee', 'url': 'https://gitee.com/yingzi_shadow/django-layuix'},
    ],

    # 首页统计卡片（与 init_menu 落库默认值一致）
    'home_stats_cards': [
        {'title': '系统用户', 'icon': 'layui-icon-user', 'color': '#1E9FFF', 'api_field': 'user_count'},
        {'title': '系统角色', 'icon': 'layui-icon-template-1', 'color': '#5FB878', 'api_field': 'role_count'},
        {'title': '菜单数量', 'icon': 'layui-icon-app', 'color': '#FFB800', 'api_field': 'menu_count'},
        {'title': '操作日志', 'icon': 'layui-icon-log', 'color': '#FF5722', 'api_field': 'log_count'},
    ],

    # Layui 2.13.9+：是否从表单提交取值中排除 disabled 字段
    # 默认 false，保持项目历史行为
    'form_filter_disabled': False,
}

# 可选：自定义 Layui CDN
LAYUI_CDN = 'https://cdn.jsdelivr.net/npm/layui@2.13.9/dist/'

# 可选：自定义 Layui 版本
LAYUI_VERSION = '2.13.9'

# RBAC 策略（可被 SystemConfig 中同名键覆盖）
LAYUI_RBAC_MAX_ROLES_PER_USER = 0          # 每用户最多角色数，0 不限
LAYUI_RBAC_PREREQ_STRATEGY = 'auto_grant'  # auto_grant / reject
LAYUI_RBAC_DSD_STRATEGY = 'greedy'         # greedy / explicit
```

#### 4.2 操作日志配置（可选）

操作日志中间件默认记录 `/admin/api/rbac/` 和 `/admin/api/ops/` 下的 POST/PUT/DELETE 请求。

如果需要记录前端 API（如 Django + Vue3 前后端分离项目中的 `/api/` 接口），可在 `settings.py` 中配置：

```python
# settings.py
OPERATION_LOG = {
    # 需要记录的路径前缀（默认已包含 rbac 和 ops）
    'PREFIXES': ['/admin/api/rbac/', '/admin/api/ops/', '/api/'],

    # 需要忽略的路径关键字（高频非业务接口）
    'IGNORE_KEYWORDS': ['login', 'logout', 'register', 'upload', 'system/info', 'system/config', 'stats'],

    # 需要排除的路径前缀（优先级高于 PREFIXES，如公开 API）
    'EXCLUDE_PREFIXES': ['/api/public/', '/api/health/'],
}
```

#### 4.3 系统配置（数据库动态管理）

安装 RBAC 后，可在后台「系统管理 → 系统配置」页面动态管理系统参数，**修改后实时生效，无需重启服务**。

**配置优先级：** 数据库 `sys_config` 表 > `settings.LAYUI_CONFIG` > 默认值

**业务逻辑说明：**

1. **默认值**：`django_layuix/rbac/defaults.py` 中定义的初始值，由 `apps.py` 与 `init_menu` 共同引用
2. **settings.py 配置**：开发者在项目中自定义的默认值
3. **数据库配置**：通过后台界面动态修改的值（**最高优先级**）

**工作流程：**
- 用户登录时，系统首先从 `settings.LAYUI_CONFIG` 读取默认配置
- 然后查询数据库 `sys_config` 表，如果存在同名配置，则覆盖 settings.py 中的值
- 最终将合并后的配置传递给前端模板

**示例场景：**
```python
# settings.py 中配置
LAYUI_CONFIG = {
    'home_quick_links': [
        {'name': '个人中心', 'icon': 'layui-icon-user', 'url': '/static/layui/pages/profile.html'},
    ],
}

# 数据库中 sys_config 表配置（通过后台界面修改）
key: home_quick_links
value: '[{"name":"仪表盘","icon":"layui-icon-home","url":"/static/layui/pages/dashboard.html"}]'

# 最终生效的是数据库中的配置（仪表盘链接）
```

**支持的配置类型：** 字符串、整数、布尔、JSON、URL、图片、颜色、文本。

**重要提示：**
- 使用 `python manage.py init_menu --force` 会重置所有系统配置为代码中的默认值
- 如需保留自定义配置，请避免使用 `--force` 参数，或直接在后台界面修改

| 配置键 | 说明 | 默认值 |
|--------|------|--------|
| `system_name` | 系统名称（标题栏 + 侧边栏） | Django Layuix Admin |
| `system_version` | 版本号 | 包版本（当前 1.4.4） |
| `system_description` | 系统描述 | （空） |
| `logo_icon` | 侧边栏 Logo 图标类名 | layui-icon-code-circle |
| `logo_url` | 侧边栏 Logo 图片 URL | （空） |
| `favicon_url` | 浏览器标签页图标 URL | （空） |
| `copyright` | 版权信息 | （空） |
| `frontend_url` | "查看站点"按钮跳转地址 | （空） |
| `webssh_url` | WebSSH 服务地址 | `/webssh/` |
| `login_bg_type` | 登录背景类型 | gradient |
| `login_bg_value` | 登录背景渐变/颜色值 | 深色渐变 |
| `login_bg_image` | 登录背景图片 URL | （空） |
| `home_stats_cards` | 首页统计卡片（JSON） | 用户/角色/菜单/日志 4 项 |
| `home_quick_links` | 首页快捷链接（JSON） | Django/Layui/GitHub/Gitee 4 项 |
| `rbac_max_roles_per_user` | 每用户最多角色数 | 0（不限） |
| `rbac_prerequisite_strategy` | 前置角色策略 | auto_grant |
| `rbac_dsd_strategy` | DSD 激活策略 | greedy |

独立的 settings 变量（不写入 `sys_config`）：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LAYUI_CDN` | Layui 静态资源路径 | `/static/layui/lib/` |
| `LAYUI_VERSION` | Layui 版本 | 2.13.9 |
| `LAYUI_LANGUAGES` | 语言列表 | 简体中文 / English |
| `LAYUI_CONFIG.form_filter_disabled` | 表单取值是否排除 disabled 字段 | False |
| `LAYUI_RBAC_MAX_ROLES_PER_USER` | 每用户最多角色数（无 DB 配置时生效） | 0 |
| `LAYUI_RBAC_PREREQ_STRATEGY` | 前置角色策略（无 DB 配置时生效） | auto_grant |
| `LAYUI_RBAC_DSD_STRATEGY` | DSD 激活策略（无 DB 配置时生效） | greedy |
| `LAYUI_RBAC_AUTHENTICATORS` | 自定义认证器导入路径 | `[]` |
| `LAYUI_ALLOW_REGISTRATION` | 是否开放匿名注册接口 | False |
| `LAYUIX_DISABLE_API_ORIGIN_GUARD` | 禁用管理 API 跨站来源防护（不推荐） | False |
| `LAYUIX_API_ALLOWED_ORIGINS` | 管理 API 允许的来源主机白名单 | 未设置（使用 `ALLOWED_HOSTS`） |
| `LAYUIX_API_PREFIXES` | 应用来源防护的管理 API 路径前缀 | `['/admin/api/']` |
| `TOKEN_EXPIRE_SECONDS` | Token 有效期（秒） | 86400 |
| `LAYUI_JWT_ISSUER` | JWT `iss` 声明 | `django-layuix` |
| `LAYUIX_ALLOW_LEGACY_TOKEN` | 是否兼容升级前两段式 Token | True |
| `LAYUIX_TOKEN_CACHE_PREFIX` | Token 状态缓存键前缀 | `layuix:auth:` |
| `LAYUI_ALLOW_QUERY_TOKEN` | 是否允许普通 API 通过 `?token=` 传 Token（不推荐） | False |
| `LAYUIX_SCOPE_HIERARCHY` | 数据作用域层级 | `[]` |
| `LAYUIX_SCOPE_TREE` | 数据作用域节点树 | `{}` |
| `OPERATION_LOG` | 操作日志前缀/忽略/排除规则 | 见 4.2 节 |
| `LAYUI_AI_*` | AI 日志分析配置 | 见 4.6 节 |
| `DJANGO_LAYUIX_THEMES` | 自定义主题定义 | 内置主题 |

ABAC 策略、组织节点、插件状态和前端 SDK 权限数据分别持久化在各自数据库表中，不属于 `sys_config` 项。

支持的配置类型：字符串、整数、布尔、JSON、URL、图片、颜色、文本。

#### 4.4 首页自定义快速链接

django-layuix 支持在首页仪表盘显示自定义快速链接，方便用户快速访问常用页面或外部网站。

**配置示例：**

```python
# settings.py
LAYUI_CONFIG = {
    # ... 其他配置 ...
    
    'home_quick_links': [
        # 内部页面（推荐）
        {'name': '个人中心', 'icon': 'layui-icon-user', 'url': '/static/layui/pages/profile.html'},
        {'name': '修改密码', 'icon': 'layui-icon-password', 'url': 'javascript:openChangePassword();'},
        {'name': '操作日志', 'icon': 'layui-icon-log', 'url': '/static/layui/pages/log.html'},
        {'name': '系统配置', 'icon': 'layui-icon-set', 'url': '/static/layui/pages/config.html'},
        
        # 外部链接
        {'name': 'Django官网', 'icon': 'layui-icon-website', 'url': 'https://www.djangoproject.com/'},
        {'name': 'Layui文档', 'icon': 'layui-icon-template', 'url': 'https://www.layui.dev/'},
        {'name': 'GitHub', 'icon': 'layui-icon-github', 'url': 'https://github.com/likangcai/django-layuix'},
        {'name': 'Gitee', 'icon': 'layui-icon-gitee', 'url': 'https://gitee.com/yingzi_shadow/django-layuix'},
        
        # 自定义应用页面
        {'name': '商品管理', 'icon': 'layui-icon-cart-simple', 'url': '/store/product'},
        {'name': '订单管理', 'icon': 'layui-icon-form', 'url': '/store/order'},
        # {'name': '自定义页面', 'icon': 'layui-icon-app', 'url': '/custom-page/'},
    ],
}
```

**配置项说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | ✅ | 链接显示名称 |
| `icon` | string | ✅ | Layui图标类名（如 `layui-icon-user`） |
| `url` | string | ✅ | 跳转地址（支持内部路径或外部URL） |

**支持的URL类型：**

1. **内部静态页面**：`/static/layui/pages/profile.html`
2. **内部路由**：`/store/product`（会自动在Tab中打开）
3. **JavaScript函数**：`javascript:openChangePassword();`
4. **外部链接**：`https://www.djangoproject.com/`（会在新窗口打开）

**常用Layui图标：**

- `layui-icon-user` - 用户
- `layui-icon-password` - 密码
- `layui-icon-log` - 日志
- `layui-icon-set` - 设置
- `layui-icon-website` - 网站
- `layui-icon-template` - 模板
- `layui-icon-github` - GitHub
- `layui-icon-cart-simple` - 购物车
- `layui-icon-form` - 表单
- `layui-icon-app` - 应用
- `layui-icon-component` - 组件
- `layui-icon-file` - 文件
- `layui-icon-chart` - 图表
- `layui-icon-chart-screen` - 数据大屏

**效果预览：**

配置后，首页仪表盘的“快捷入口”区域会显示您配置的链接卡片，点击即可快速跳转。

#### 4.5 国际化 (i18n) 支持

django-layuix 提供完整的中英文双语切换功能，包括前端界面和后端菜单。

**语言切换：**

1. 点击右上角头像进入 **个人中心**
2. 在 **基本信息** 标签页找到 **语言设置**
3. 选择 **简体中文** 或 **English**
4. 点击 **保存**，刷新页面后生效

**菜单多语言：**

在后台 **权限管理 → 菜单管理** 中可以为每个菜单配置多语言名称：
- **菜单名称（中文）**：必填，默认显示
- **英文名称**：选填，英文用户显示
- **简体中文**：选填，简体中文用户显示

系统会根据用户的语言偏好自动返回对应的菜单名称。如果某个语言的翻译缺失，会自动回退到中文名称。

**前端国际化开发：**

所有 HTML 页面中的文本都应使用 i18n 翻译函数：

```html
<!-- 方法一：data-i18n 属性 -->
<button data-i18n="common.save">保存</button>

<!-- 方法二：模板语法 -->
<script type="text/html" id="toolbarTpl">
    <button>{{ t('common.add') }}</button>
</script>

<!-- 方法三：JavaScript 调用 -->
<script>
var msg = t('common.success');
layer.msg(t('common.addSuccess'));
</script> 
```

详细的国际化开发指南请参考：[docs/I18N_GUIDE.md](docs/I18N_GUIDE.md)

### 5. 启用运维管理（可选）

如果需要服务器管理、日志查看、AI 日志分析功能：

```bash
pip install django-layuix[ops]
```

```python
# settings.py
INSTALLED_APPS = [
    'django_layuix',                    # 必须放在 django.contrib.admin 之前
    'django_layuix.rbac',               # RBAC 扩展（用户/角色/菜单管理）
    'django_layuix.ops',                # 运维管理扩展（服务器管理/AI分析）
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # ... 你的应用
]
```

> ops 模块的 API 路由会自动注册到 `/admin/api/ops/`，无需手动配置 urls.py。

安装后可在「菜单管理」中添加运维管理相关菜单项（服务器管理、AI 配置等）。

**功能说明：**
- **服务器管理**：添加/编辑/删除服务器（SSH 连接信息）
- **连接测试**：一键测试 SSH 连接是否正常
- **日志查看**：远程查看服务器日志文件，支持自动刷新
- **命令执行**：单次命令执行（带危险命令拦截）

### 5.1 自定义应用菜单注册（无需修改库源码）

django-layuix 提供了手动注册菜单的 API，允许外部项目动态添加菜单，无需修改库源码。

> ⚠️ **推荐使用 `register_menus` 手动注册**，不要使用已废弃的 `auto_register_admin_apps`。
> 手动注册可以完全控制菜单结构、路径、图标和按钮权限，且避免孤儿菜单问题。

#### 方式一（推荐）：手动注册菜单 + API 路由

如果你的应用需要自定义前端页面（Layui 静态页面），需要完成**三步**：

**Step 1：创建 REST API 视图**

```python
# myapp/views_api.py
from django.views.decorators.csrf import csrf_exempt
from django_layuix.rbac.views import api_login_required, get_request_body, success_response, error_response
from .models import MyModel


@csrf_exempt
@api_login_required
def mymodel_list(request):
    """GET /admin/api/myapp/mymodel/ - 列表"""
    queryset = MyModel.objects.all().order_by('-id')
    total = queryset.count()
    # 分页...
    data = [{'id': m.id, 'name': m.name} for m in queryset]
    return success_response({'list': data, 'total': total})
```

**Step 2：注册 URL + 菜单（在 apps.py 中）**

```python
# myapp/urls.py
from django.urls import path
from . import views_api

urlpatterns = [
    path('mymodel/', views_api.mymodel_list, name='myapp_mymodel_list'),
    path('mymodel/create/', views_api.mymodel_create, name='myapp_mymodel_create'),
    path('mymodel/<int:pk>/', views_api.mymodel_detail, name='myapp_mymodel_detail'),
]
```

```python
# myapp/apps.py
from django.apps import AppConfig


class MyappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myapp'
    verbose_name = '我的应用'

    def ready(self):
        try:
            from django_layuix.rbac.menu_registry import register_menus

            import myapp.admin  # noqa: F401

            # 注册菜单，path 指向 Layui 静态页面
            register_menus(
                menus_data=[
                    ('我的应用', 'layui-icon-app', '', 1, 10, None),
                    ('数据管理', 'layui-icon-table',
                     '/static/myapp/pages/mymodel.html', 2, 1, '我的应用'),
                ],
                buttons_data=[
                    ('新增数据', '数据管理', 'mymodel:add', 1),
                    ('编辑数据', '数据管理', 'mymodel:edit', 2),
                    ('删除数据', '数据管理', 'mymodel:delete', 3),
                ]
            )

            # ⚠️ 必须通过 site.get_urls 补丁注入到 admin site 内部
            self._register_api_urls()

        except Exception as e:
            print(f"Warning: Could not initialize myapp: {e}")

    def _register_api_urls(self):
        """注册 API 路由到 admin site 内部（不能写在项目级 urls.py）"""
        from django.contrib.admin import site
        from django.urls import path, include
        from . import urls as myapp_urls

        original_get_urls = site.get_urls

        def patched_get_urls():
            urls = original_get_urls()
            custom_urls = [
                path('api/myapp/', include((myapp_urls.urlpatterns, 'myapp'))),
            ]
            return custom_urls + urls

        site.get_urls = patched_get_urls
```

**Step 3：创建 Layui 前端页面**

前端页面放在 `myapp/static/myapp/pages/mymodel.html`，访问路径为 `/static/myapp/pages/mymodel.html`。

> **重要**：表格渲染必须使用 `url` 服务端分页模式，不要用 `data: list` + `page.count`，
> 否则分页总数显示不准确。

```javascript
// myapp/static/myapp/pages/mymodel.html 中的 table.render
tableIns = table.render({
    elem: '#mytable',
    url: '/admin/api/myapp/mymodel/',      // ✅ 服务端分页
    page: {limit: 10},
    parseData: function(res) {
        return {
            "code": res.code === 200 ? 0 : res.code,
            "count": res.data ? res.data.total : 0,
            "data": res.data ? res.data.list : []
        };
    },
    request: { pageName: 'page', limitName: 'page_size' },  // ✅ 参数映射
    cols: [[/* ... */]]
});
```

#### 方式二：自动扫描（已废弃，不推荐）

> ⚠️ `auto_register_admin_apps` **已废弃**，不推荐使用。它创建的按钮权限在菜单重建后
> 会变为"孤儿菜单"（parent=None），且只能使用 Django admin 原生页面作为菜单路径，
> 无法利用 Layui 前端 CRUD 的优势。请使用方式一手动注册。

#### 参数说明

**menus_data 格式：** `(name, icon, path, menu_type, sort, parent_name)`

| 参数 | 说明 | 示例 |
|------|------|------|
| name | 菜单名称 | `'数据管理'` |
| icon | Layui图标类名 | `'layui-icon-table'` |
| path | 前端页面路径 | `'/static/myapp/pages/mymodel.html'` |
| menu_type | 1=目录, 2=菜单 | `2` |
| sort | 排序号 | `1` |
| parent_name | 父菜单名 | `'我的应用'` |

**buttons_data 格式：** `(btn_name, parent_menu_name, permission, sort)`

| 参数 | 说明 | 示例 |
|------|------|------|
| btn_name | 按钮名称 | `'新增数据'` |
| parent_menu_name | 所属菜单 | `'数据管理'` |
| permission | 权限标识 | `'mymodel:add'` |
| sort | 排序号 | `1` |

#### 常见问题

**❌ 菜单显示有了，但页面访问不到？**
检查 `path` 格式是否以 `/static/` 开头，且页面文件放在 `<app>/static/<app>/pages/` 目录下。

**❌ 按钮权限在菜单管理中显示为顶级菜单（孤儿菜单）？**
旧版 `auto_register_admin_apps` 创建的按钮在菜单重建后 parent 字段丢失。
解决方案：先删除孤儿按钮（`Menu.objects.filter(parent__isnull=True, menu_type=3).delete()`），
然后重启 Django 让 `register_menus` 重新创建。

**❌ API 路由返回登录页面？**
路由必须通过 `site.get_urls` 补丁注册到 admin site 内部，**不能**写在项目级 `urls.py` 中。

#### 完整示例代码

参考 `example/store/` 目录：

| 文件 | 说明 |
|------|------|
| `store/apps.py` | 菜单注册 + API 路由注册 |
| `store/views_api.py` | Category/Product/Order 三个模型的 CRUD API |
| `store/urls.py` | API 路由 |
| `store/admin.py` | Django admin 注册（精简） |
| `store/static/store/pages/*.html` | Layui 前端页面 |

详细文档请参考：[docs/MENU_EXTENSION_GUIDE.md](docs/MENU_EXTENSION_GUIDE.md)

### 6. 启用 Web SSH 终端（可选）

Web SSH 使用独立的 [webssh](https://pypi.org/project/webssh/) 服务：

```bash
pip install webssh

# 启动 webssh 服务（默认端口 8888）
wssh --port=8888
```

**配置 webssh 地址：**

**方式一：系统配置（推荐，动态管理）**

在后台「系统管理 → 系统配置」中添加配置项：
- **配置键**: `webssh_url`
- **配置值**: `http://localhost:8888/` （或您的 webssh 服务地址）
- **配置类型**: URL

**方式二：settings.py 配置（兼容旧版本）**

```python
LAYUI_CONFIG = {
    'webssh_url': 'http://localhost:8888/',  # WebSSH 服务地址
}
```

> **优先级**：系统配置（数据库） > settings.py > 默认值（`/webssh/`）

**自动填充连接信息：**

点击服务器列表的「终端」按钮时，系统会自动获取服务器的完整信息（包括密码/私钥），并通过 URL 参数传递给 webssh 服务：

- ✅ 主机地址、端口、用户名自动填入
- ✅ 密码认证：密码通过 Base64 编码传递，无需手动输入
- ✅ 密钥认证：私钥内容也会自动传递
- 🔒 安全机制：敏感信息先经过 `encodeURIComponent` 再 Base64 编码，防止特殊字符问题

> **注意**：密码和私钥在传输过程中使用双重编码（URL编码 + Base64），符合 [webssh 官方规范](https://github.com/huashengdun/webssh)。

### 7. 启用 AI 日志分析（可选）

支持所有 **OpenAI 兼容协议**的服务（OpenAI、智谱AI、DeepSeek、通义千问、Moonshot 等）：

```bash
pip install django-layuix[ai]
```

**方式一：Web 界面配置（推荐）**

在后台菜单中打开「AI 模型配置」页面，选择预设或手动填写：

| 配置项 | 说明 |
|--------|------|
| API Key | 必填，各服务的 API 密钥 |
| API 地址 | OpenAI 可留空，其他服务需填写 Base URL |
| 模型名称 | 如 gpt-4o-mini、glm-4-flash 等 |

配置保存在数据库中，支持多配置管理和默认配置切换。

**💡 搜索提示：**
AI 模型配置页面支持**中英文厂商名称搜索**，可直接输入中文（如"智谱"、"通义"、"Kimi"）或英文（如"zhipu"、"qwen"、"moonshot"）进行过滤。

**方式二：settings.py 配置**

```python
LAYUI_AI_API_KEY = 'sk-xxx'           # API Key
LAYUI_AI_MODEL = 'gpt-4o-mini'        # 模型（默认 gpt-4o-mini）
LAYUI_AI_BASE_URL = ''                # API 地址（OpenAI 可留空）
```

> 两种方式可同时使用，Web 界面配置优先级更高（数据库 > settings.py）。

**常见服务配置示例：**

| 服务 | API 地址 | 模型 |
|------|---------|------|
| OpenAI | （留空） | gpt-4o-mini |
| 智谱AI | `https://open.bigmodel.cn/api/paas/v4` | glm-4-flash |
| DeepSeek | `https://api.deepseek.com/v1` | deepseek-chat |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | qwen-turbo |
| Moonshot | `https://api.moonshot.cn/v1` | moonshot-v1-8k |

在日志查看器中点击「AI 分析」按钮即可自动分析日志内容，输出包括：
- 日志概览（类型、时间范围、总体状态）
- 异常检测（错误、警告、异常模式）
- 根因分析
- 修复建议和命令

---

## 工作原理

django-layuix 利用 Django 的模板覆盖机制。通过将包放在 `INSTALLED_APPS` 中 `django.contrib.admin` 之前，Django 的模板加载器会优先查找 `django_layuix/templates/admin/` 中的模板，从而有效替换默认的 Admin 模板。

### 自动注册机制

`django_layuix.rbac` 的 `AppConfig.ready()` 会自动完成以下操作，用户无需手动配置：

1. **INSTALLED_APPS**：自动注入 `django_layuix`
2. **LocaleMiddleware**：自动注入国际化中间件
3. **模板目录**：自动注册模板覆盖目录
4. **静态文件**：自动注册静态文件查找器
5. **模板标签**：自动注册 `layui_tags` 模板标签库
6. **API 路由**：自动注册 `/admin/api/rbac/` 路由
7. **Ops 路由**：自动注册 `/admin/api/ops/` 路由（如果 ops 模块已安装）

### 模板覆盖链

```
django_layuix/templates/admin/base.html      → 主布局（Layui）
django_layuix/templates/admin/base_site.html  → 站点布局
django_layuix/templates/admin/login.html      → 登录页面
django_layuix/templates/admin/index.html      → 仪表盘（Tab 布局 + iframe）
django_layuix/templates/admin/change_list.html → 模型列表页
django_layuix/templates/admin/change_form.html → 模型编辑页
```

---

## 模板标签

通过 `{% load layui_tags %}` 可以使用以下模板标签：

| 标签 | 说明 |
|------|------|
| `{% system_name %}` | 系统名称 |
| `{% system_version %}` | 系统版本 |
| `{% system_description %}` | 系统描述 |
| `{% logo_url %}` | Logo URL |
| `{% favicon_url %}` | Favicon URL |
| `{% logo_icon %}` | Logo 图标类名 |
| `{% layui_cdn %}` | Layui CDN 地址 |
| `{% layui_version %}` | Layui 版本号 |
| `{% frontend_url %}` | 前端项目 URL |
| `{% login_bg_type %}` | 登录背景类型（gradient/color/image，仅3个值有效） |
| `{% login_bg_value %}` | 登录背景值（渐变/颜色CSS值，type为gradient或color时使用） |
| `{% login_bg_image %}` | 登录背景图片URL（**仅当 type=image 且有值时生效**） |

> **登录页背景业务规则（5条）：**
> 1. `type='gradient'` → 深色渐变 + ✨ 粒子飘动（默认，最炫酷）
> 2. `type='color'` + value有值 → 纯颜色值 + 无粒子（简洁清爽）
> 3. `type='image'` + image有值 → 全屏图片 + 无粒子（自定义图片）
> 4. type 必须是字符串，且只能是 gradient / color / image 之一
> 5. 异常值/空值/条件不满足 → 默认深色渐变 + ✨ 粒子飘动
| `{% copyright_text %}` | 版权信息 |
| `{% layui_config key default %}` | 根据键获取配置值 |

---

## RBAC 模型

使用 RBAC 扩展（`django_layuix.rbac`）时，提供以下模型：

| 模型 | 表名 | 说明 |
|------|------|------|
| **Menu** | `sys_menu` | 树形结构菜单，支持目录/菜单/按钮三种类型，含图标、排序、可见性、权限标识 |
| **Role** | `sys_role` | 角色管理，支持菜单权限绑定，系统内置角色保护 |
| **UserProfile** | `sys_user` | 扩展用户模型，含昵称、手机号、头像、主题、语言偏好 |
| **OperationLog** | `sys_operation_log` | 自动记录用户操作日志 |
| **SystemConfig** | `sys_config` | 系统配置键值对，支持多种值类型 |

### Menu 模型字段详解

| 字段名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `name` | CharField(50) | ✅ | 菜单名称（中文） | `'菜单管理'` |
| `name_en` | CharField(50) | ❌ | 英文名称（国际化） | `'Menu Management'` |
| `name_zh_hans` | CharField(50) | ❌ | 简体中文名称 | `'菜单管理'` |
| `icon` | CharField(50) | ❌ | Layui 图标类名 | `'layui-icon-menu-fill'` |
| `path` | CharField(200) | ⚠️ | 路由地址（**核心字段**） | `'/permission/menu'` |
| `component` | CharField(200) | ❌ | 组件路径（预留字段） | `'/pages/menu.vue'` |
| `menu_type` | IntegerField | ✅ | 类型：1=目录, 2=菜单, 3=按钮 | `2` |
| `permission` | CharField(100) | ⚠️ | 权限标识（**按钮必填**） | `'menu:add'` |
| `sort` | IntegerField | ❌ | 排序号 | `1` |
| `visible` | BooleanField | ❌ | 是否显示 | `True` |
| `status` | BooleanField | ❌ | 是否启用 | `True` |

> 📖 **详细文档**: [权限系统使用指南](docs/PERMISSION_SYSTEM_GUIDE.md)
> - 权限标识命名规范
> - 前端权限控制示例
> - 实战案例：创建新业务模块
> - 常见问题解答

---

## 从 django-layui 升级

【判断】分发名已统一为 `django-layuix`，包名仍为 `django_layuix`。旧版本数据库中的应用标签为 `django_layui_rbac` / `django_layui_ops`，升级到新版本前请执行：

```bash
python manage.py rename_app_labels
python manage.py migrate
python manage.py init_menu
python manage.py collectstatic --noinput
```

该命令会同步更新 `django_migrations.app` 与 `django_content_type.app_label`，不会修改业务数据表。

## 数据权限（1.4.2+，可选）

业务模型只需声明 `SCOPE_FIELD` 并继承 `ScopedModelMixin`，即可按用户角色的 `scope_node/scope_depth` 过滤数据：

```python
from django.db import models
from django_layuix.rbac.scopes import ScopedModelMixin


class Order(ScopedModelMixin, models.Model):
    SCOPE_FIELD = 'owner'
    owner = models.CharField(max_length=100)
    title = models.CharField(max_length=100)
```

```python
orders = Order.objects.for_user(request.user)
```

未配置 `scope_node` 或未声明 `SCOPE_FIELD` 时，`for_user()` 返回原始查询集，行为与旧版本一致。

可选层级配置：

```python
LAYUIX_SCOPE_HIERARCHY = ['global', 'region', 'team']
LAYUIX_SCOPE_TREE = {
    'east_region': ['east_team_a', 'east_team_b'],
}
```

详细说明见 [权限升级说明](docs/PERMISSION_UPGRADE_1_4_1.md)。

## 管理命令

| 命令 | 说明 |
|------|------|
| `python manage.py init_menu` | 初始化默认菜单、角色和系统配置，并自动同步系统版本号 |
| `python manage.py init_data` | 快速初始化：创建超级管理员、内置角色、完整菜单树（含运维管理） |
| `python manage.py init_demo_data` | 初始化演示应用的分类/商品/订单示例数据 |
| `python manage.py init_permission_demo` | 一键初始化角色继承、SSD、Scope、组织节点、ABAC 与 demo app 示例数据 |
| `python manage.py rename_app_labels` | 升级旧库：把 `django_layui_rbac/ops` 应用标签迁移为 `django_layuix_rbac/ops` |

### init_data 命令详解

`init_data` 命令用于快速初始化系统数据，适合新项目快速上手：

```bash
# 执行初始化
python manage.py init_data
```

**执行效果：**

```
开始初始化系统数据...
  创建超级管理员...
    超级管理员创建成功
  创建系统内置角色...
    超级管理员角色创建成功
    注册用户角色创建成功
  创建基础菜单树...
    菜单创建: 权限管理
    菜单创建: 菜单管理
    菜单创建: 角色管理
    菜单创建: 用户管理
    菜单创建: 个人中心
    菜单创建: 系统监控
    菜单创建: 操作日志
    菜单创建: 系统信息
    菜单创建: 系统配置
    菜单创建: 运维管理
    菜单创建: 服务器管理
  关联角色菜单权限...
    超级管理员角色已关联所有菜单
    注册用户角色已关联个人中心
    超级管理员已绑定超级管理员角色
系统数据初始化完成!
超级管理员账号: admin / admin123
```

**创建的默认数据：**

| 类型 | 内容 | 说明 |
|------|------|------|
| **超级管理员** | `admin / admin123` | 内置超级管理员账号 |
| **角色** | 超级管理员、注册用户 | 两个内置角色 |
| **权限管理菜单** | 菜单管理、角色管理、用户管理 | 完整权限管理模块 |
| **系统监控菜单** | 操作日志、系统信息、系统配置 | 系统管理模块 |
| **运维管理菜单** | 服务器管理（含按钮权限） | 运维管理模块 |

> **注意**：命令具有幂等性，已存在的数据不会重复创建。

---

## API 接口

RBAC 模块提供以下 REST API（自动注册到 `/admin/api/rbac/`）：

| 接口 | 方法 | 说明 |
|------|------|------|
| `/admin/api/rbac/register/` | POST | 用户注册（无需登录，自动绑定注册角色） |
| `/admin/api/rbac/upload/image/` | POST | 通用图片上传（需登录，支持 JPG/PNG/GIF/WebP/ICO/SVG） |
| `/admin/api/rbac/system/info/` | GET | 系统信息（CPU/内存/磁盘/网络） |
| `/admin/api/rbac/system/config/` | GET | 系统配置 |
| `/admin/api/rbac/menus/tree/` | GET | 菜单树 |
| `/admin/api/rbac/roles/` | GET/POST | 角色列表/创建 |
| `/admin/api/rbac/users/` | GET | 用户列表 |
| `/admin/api/rbac/logs/` | GET | 操作日志 |
| `/admin/api/rbac/configs/` | GET | 系统配置列表 |

---

## 国际化

django-layuix 支持中英文双语，分两层实现：

1. **后端（Django i18n）**：模板中使用 `{% trans %}` 标签，翻译文件位于 `django_layuix/locale/zh_Hans/LC_MESSAGES/django.po`
2. **前端（JS i18n）**：子页面通过 `t('key')` 函数和 `data-i18n` 属性实现动态翻译，翻译字典位于 `static/layui/js/i18n.js`

`LocaleMiddleware` 会自动注入，用户无需手动配置。

---

## 主题系统

### 深色/浅色模式切换

> **版本**: 1.4.2+ | **更新**: 2026-11-24

django-layuix 内置深色/浅色双模式切换功能：

- **一键切换**：Header 右侧月亮/太阳图标按钮
- **全局同步**：Header、Sidebar、Tab栏、内容区域全部统一切换
- **自动保存**：用户偏好保存到数据库，下次登录自动应用
- **iframe 同步**：通过 postMessage 通知所有子页面同步主题
- **完整覆盖**：使用 `!important` 确保覆盖 Layui 默认样式

#### 颜色规范

| 组件 | 深色模式 | 浅色模式 |
|------|----------|----------|
| Header 背景 | `#1d1e22` | `#ffffff` |
| Sidebar 背景 | `#1a1b1f` | `#ffffff` |
| Tab 栏背景 | `#1d1e22` | `#f6f7f9` |
| Body 背景 | `#14161a` | `#f0f2f5` |
| 主文字颜色 | `#e5eaf3` | `#1f2329` |

详细文档见 [THEME_SYSTEM_GUIDE.md](docs/THEME_SYSTEM_GUIDE.md)

---

## 环境要求

- **Python**：3.8–3.13（CI 实际验证 3.10–3.13；3.8/3.9 已通过语法与 API 审计）
- **Django**：3.2–6.0，需按 Python 版本选择兼容组合
- 推荐组合：Python 3.12 + Django 5.2/6.0；旧环境建议 Python 3.8/3.9 + Django 4.2 LTS
- 核心依赖：`Django>=3.2`、`psutil>=5.9.0`、`Pillow>=9.0.0`（头像 `ImageField` 需要）

完整矩阵与兼容处理见 [COMPATIBILITY.md](docs/COMPATIBILITY.md)。

---

## 可选依赖

| 安装方式 | 命令 | 包含功能 |
|---------|------|---------|
| 基础 | `pip install django-layuix` | RBAC + 系统配置 + 操作日志 + Dashboard |
| 运维 | `pip install django-layuix[ops]` | + 服务器管理 + SSH 终端 |
| AI | `pip install django-layuix[ai]` | + AI 日志分析 |
| 全部 | `pip install django-layuix[all]` | 所有功能 |
| 开发 | `pip install django-layuix[dev]` | + build + twine |

---

## 三、功能开启对照表

| 功能 | 需要的包 | 需要的配置 | 必需性 |
|------|---------|-----------|--------|
| **Layui 基础框架** | django-layuix | INSTALLED_APPS 加 `django_layuix` | ✅ **必需** |
| **RBAC 引擎（API/用户/菜单）** | django-layuix（内置） | 加 `django_layuix.rbac` + `AUTH_USER_MODEL` | ✅ **必需** |
| 服务器管理 + 日志查看 | paramiko | 加 `django_layuix.ops`（API 路由自动注册） | 🔵 可选 |
| Web SSH 终端 | webssh | 运行 wssh 命令 + 配置 webssh_url | 🔵 可选 |
| AI 日志分析 | openai | 配置 AI Key（后台界面或 settings.py） | 🔵 可选 |

> **说明**：
> - ✅ **必需组件**：`django_layuix` 和 `django_layuix.rbac` 是使用 django-layuix 的**最低要求**
> - 🔵 **可选功能**：运维管理和 AI 分析需要额外安装依赖包
> - 完整安装命令：`pip install django-layuix[all]`（包含所有可选功能）

---

## 四、详细文档索引

更多详细使用指南和最佳实践，请参考 `docs/` 目录下的文档：

### 核心功能
- [首页自定义快速链接配置](docs/HOME_QUICK_LINKS_GUIDE.md) - 仪表盘的快速入口配置
- [菜单扩展指南](docs/MENU_EXTENSION_GUIDE.md) - 如何添加自定义应用菜单
- [权限系统使用指南](docs/PERMISSION_SYSTEM_GUIDE.md) - RBAC 权限管理、字段说明、实战示例
- [RBAC3 权限体系使用指南](docs/RBAC3_GUIDE.md) - 角色继承、SSD/DSD 约束、前置角色与后端强制鉴权
- [新增功能快速上手示例](docs/NEW_FEATURES_QUICKSTART.md) - 角色继承、SSD、Scope、组织节点、ABAC、SDK 的最小可运行示例
- [权限示例应用](example/permission_demo/README.md) - 可复制的业务模型、API、菜单与 Layui 页面示例
- [权限系统升级说明](docs/PERMISSION_UPGRADE_1_4_1.md) - SoD 兼容契约、数据权限 Scope、ABAC 与组织节点
- [前端权限 SDK 使用指南](docs/FRONTEND_SDK_GUIDE.md) - Vue/React 适配器、统一权限端点与 ABAC 调用
- [ABAC 表达式权限使用指南](docs/ABAC_GUIDE.md) - 策略语法、行级/字段级过滤与调试示例
- [前端组件与设计 Token 规范](docs/FRONTEND_COMPONENT_GUIDE.md) - 按钮、查询区、列表分页与弹窗统一规范
- [纯跨域 Token 认证指南](docs/TOKEN_AUTH_GUIDE.md) - Bearer Token 接入与分离前端对接
- [认证与权限桥接指南](docs/INTEGRATION_GUIDE.md) - 通用认证桥接、DRF 适配器与 TestHub 对接
- [插件化扩展契约](docs/PLUGIN_GUIDE.md) - 插件注册、菜单与 API 扩展
- [TestHub 平台集成评估](docs/TESTHUB_INTEGRATION.md) - 与前后端分离项目的集成方案
- [发布流程说明](docs/RELEASE_GUIDE.md) - Tag 触发测试、构建与 PyPI 自动发布
- [AJAX Admin 使用指南](docs/AJAX_ADMIN_GUIDE.md) - AJAX 增强功能
- [国际化 (i18n) 使用指南](docs/I18N_GUIDE.md) - 中英文双语切换与多语言开发

### 高级特性
- [多主题系统使用指南](docs/THEME_SYSTEM_GUIDE.md) - 深色/浅色双模式切换与定制
- [前台菜单可见性控制指南](docs/FRONTEND_MENU_GUIDE.md) - frontend_visible 前后台菜单独立控制

### 版本信息
- [版本兼容性说明](docs/COMPATIBILITY.md) - Python/Django 支持矩阵与升级建议
- [**更新日志 (CHANGELOG)**](docs/CHANGELOG.md) - 版本历史和更新记录

---

## 🆘 常见问题与故障排查

本章节汇总了用户在使用 django-layuix 时遇到的**高频问题**及解决方案。如果您遇到的问题未在此列出，请 [提交 Issue](https://github.com/likangcai/django-layuix/issues)。

---

### 🔴 问题 1：API 返回 404 错误

#### 症状
控制台显示以下错误：
```
Not Found: /admin/api/rbac/userinfo/
GET /admin/api/rbac/userinfo/ HTTP/1.1" 404 4356
```

页面在 `/admin/login/` 和 `/admin/` 之间循环重定向。

#### 原因
API 路由未正确注册。django-layuix 的 API 路由通过 `AppConfig.ready()` 自动注册，如果配置不正确会导致路由缺失。

#### 解决方案（按优先级排序）

**Step 1: 检查 INSTALLED_APPS**
```python
# settings.py
INSTALLED_APPS = [
    'django_layuix',           # ✅ 必须第一个（基础框架）
    'django_layuix.rbac',      # ✅ 必需！RBAC 引擎（提供 API 路由）
    'django.contrib.admin',
    'django.contrib.auth',
    # ... 其他应用
]
```

> **⚠️ 关键点**：
> - `'django_layuix'` 必须在 `django.contrib.admin` **之前**
> - `'django_layuix.rbac'` 是 **必需组件**（不是可选的），缺少它会导致所有 API 返回 404
> - 如果缺少 `'django_layuix.rbac'`，前端页面将无法获取用户信息、菜单数据、系统配置

**Step 2: 执行数据库迁移**
```bash
# 创建数据库表（包含菜单、角色、用户、系统配置等）
python manage.py makemigrations
python manage.py migrate

# 初始化默认数据（仅首次运行）
python manage.py init_menu
```

**Step 3: 验证路由已注册**
```bash
python manage.py shell

>>> from django.urls import reverse
>>> reverse('rbac_user_info')
'/admin/api/rbac/userinfo/'  # ✅ 成功：路由已注册

# 如果报错 NoReverseMatch，说明路由未注册，返回 Step 1 检查配置
```

**Step 4: 重启服务器并清除缓存**
```bash
# 重启 Django 开发服务器
# 按 Ctrl+C 停止当前服务器
python manage.py runserver

# 浏览器中强制刷新（清除缓存）
# Windows/Linux: Ctrl + F5
# Mac: Cmd + Shift + R
```

**Step 5: 检查 urls.py 配置**
```python
# urls.py - 确保使用正确的 AdminSite
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),  # ✅ 正确（会被自动替换为 layui_admin_site）
]

# 或者显式使用（更明确）
# from django_layuix.admin import layui_admin_site
# urlpatterns = [
#     path('admin/', layui_admin_site.urls),
# ]
```

#### 快速诊断命令
```bash
# 一键检查所有配置项
python manage.py shell << 'EOF'
from django.conf import settings
from django.urls import reverse

print("=" * 60)
print("django-layuix 配置诊断报告")
print("=" * 60)

# 1. 检查 INSTALLED_APPS
print("\n[1] INSTALLED_APPS 检查:")
apps_to_check = ['django_layuix', 'django_layuix.rbac']
for app in apps_to_check:
    status = "✅" if app in settings.INSTALLED_APPS else "❌"
    print(f"  {status} {app}")

# 2. 检查 API 路由
print("\n[2] API 路由检查:")
try:
    url = reverse('rbac_user_info')
    print(f"  ✅ /admin/api/rbac/userinfo/ -> {url}")
except Exception as e:
    print(f"  ❌ 路由未注册: {e}")

try:
    url = reverse('rbac_menu_tree')
    print(f"  ✅ /admin/api/rbac/menus/tree/ -> {url}")
except Exception as e:
    print(f"  ❌ 路由未注册: {e}")

# 3. 检查 AUTH_USER_MODEL
print("\n[3] 用户模型检查:")
user_model = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')
print(f"  当前模型: {user_model}")
if user_model == 'django_layuix_rbac.UserProfile':
    print("  ✅ 使用自定义 UserProfile")
else:
    print("  ⚠️ 使用默认 User 模型（RBAC功能可能受限）")

print("\n" + "=" * 60)
print("诊断完成！如果所有项目都显示 ✅，请尝试重启服务器")
print("=" * 60)
EOF
```

---

### 🟡 问题 2：循环重定向 (/admin/login/ → /admin/)

#### 症状
浏览器不断在登录页和首页之间跳转，无法进入后台。

#### 原因
1. **Session/Cookie 配置问题** - Session 无效或 Cookie 被阻止
2. **CSRF Token 失效** - CSRF 配置与 iframe 不兼容
3. **未完成登录流程** - 直接访问需要认证的页面

#### 解决方案

**方案 A: 清除 Cookie 并重新登录**
1. 打开浏览器开发者工具 (F12)
2. 切换到 **Application** 标签 → **Cookies**
3. 删除当前域名下的所有 Cookie
4. 访问 `/admin/login/` 重新登录

**方案 B: 检查 CSRF 配置**
```python
# settings.py
# iframe 嵌入场景必须禁用 SameSite
CSRF_COOKIE_SAMESITE = None
SESSION_COOKIE_SAMESITE = None

# 如果使用了 XFrameOptionsMiddleware，请移除它
MIDDLEWARE = [
    # ...
    # ❌ 移除这行: 'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

**方案 C: 使用隐私/无痕模式测试**
- 打开浏览器无痕窗口
- 访问 `http://127.0.0.1:8000/admin/login/`
- 登录后观察是否正常

---

### 🟠 问题 3：静态文件或样式未加载

#### 症状
- 页面显示但样式混乱（CSS 未加载）
- 图标显示为方块或乱码
- JavaScript 报错 404

#### 原因
静态文件路径配置错误或未收集。

#### 解决方案

**开发环境 (DEBUG=True)**
```bash
# Django 开发服务器会自动查找静态文件
# 确保设置正确：
# settings.py
STATIC_URL = '/static/'
STATICFILES_DIRS = []  # 可选：额外的静态文件目录

# 重启服务器即可
python manage.py runserver
```

**生产环境 (DEBUG=False)**
```bash
# 必须手动收集静态文件
python manage.py collectstatic --noinput

# 配置 Nginx/Apache 提供静态文件服务
# Nginx 示例:
# location /static/ {
#     alias /path/to/staticfiles/;
# }
```

**验证静态文件路径**
```bash
python manage.py shell

>>> from django.contrib.staticfiles.storage import staticfiles_storage
>>> staticfiles_storage.url('layui/css/admin.css')
'/static/layui/css/admin.css'  # ✅ 正确

# 检查文件是否存在
>>> import os
>>> from django.conf import settings
>>> os.path.exists(os.path.join(settings.STATIC_ROOT, 'layui/css/admin.css'))
True  # ✅ 文件存在
```

---

### 🟢 问题 4：菜单或权限数据缺失

#### 症状
- 登录后左侧菜单为空
- 显示"暂无菜单数据"
- 权限按钮不可见

#### 原因
未执行 `init_menu` 命令初始化默认数据。

#### 解决方案
```bash
# 初始化菜单、角色、权限、系统配置
python manage.py init_menu

# 输出示例:
# ✅ 创建目录: 权限管理
# ✅ 创建菜单: 菜单管理
# ✅ 创建菜单: 角色管理
# ✅ 创建菜单: 用户管理
# ✅ 创建角色: 管理员 (绑定所有权限)
# ✅ 创建角色: 注册用户 (仅个人中心权限)
# ✅ 创建系统配置: system_name, logo_icon, ...

# 默认管理员账号（仅 init_data 首次创建时生效）
# 用户名: admin
# 密码: admin123
```

> 如果已有数据库修改过 admin 密码，可用 `python manage.py changepassword admin` 重置；运行 `example/test_api.py` 时可通过 `DEMO_ADMIN_USERNAME` / `DEMO_ADMIN_PASSWORD` 环境变量指定凭据。

**如果 init_menu 命令不存在**:
```bash
# 检查是否正确安装了 django_layuix.rbac
python manage.py shell

>>> import django_layuix
>>> print(django_layuix.__version__)  # 如果报错，说明安装有问题

# 重新安装
pip install --force-reinstall django-layuix
```

---

### 🔵 问题 5：依赖包缺失错误

#### 常见错误信息

| 错误信息 | 缺失的依赖 | 安装命令 |
|---------|-----------|---------|
| `ModuleNotFoundError: No module named 'paramiko'` | paramiko (运维模块) | `pip install paramiko` |
| `ModuleNotFoundError: No module named 'openai'` | openai (AI模块) | `pip install openai` |
| `ModuleNotFoundError: No module named 'psutil'` | psutil (系统监控) | `pip install psutil` |
| `ImportError: cannot import name 'webssh'` | webssh (SSH终端) | `pip install webssh` |

#### 一键安装所有依赖
```bash
# 方式一：安装全部可选依赖
pip install django-layuix[all]

# 方式二：仅安装需要的
pip install django-layuix[ops]   # 运维管理
pip install django-layuix[ai]    # AI日志分析
```

> **注意**: 核心依赖 (`Django`, `psutil`) 会随 `pip install django-layuix` 自动安装，无需单独安装。

---

### 🟣 问题 6：Chrome DevTools 请求 404（可忽略）

#### 症状
控制台显示：
```
Not Found: /.well-known/appspecific/com.chrome.devtools.json
GET /.well-known/appspecific/com.chrome.devtools.json HTTP/1.1" 404 2341
```

#### 说明
这是 **Chrome 浏览器的自动请求**，用于检测 DevTools 功能，与您的应用无关。

#### 处理方式
✅ **可以安全忽略** - 不会影响应用功能

如果希望消除此错误，可以：
```python
# urls.py - 添加一个空响应（可选）
from django.http import JsonResponse

def chrome_devtools(request):
    return JsonResponse({}, status=404)

urlpatterns = [
    # ...
    path('.well-known/appspecific/com.chrome.devtools.json', chrome_devtools),
]
```

---

### 📋 完整安装检查清单

首次安装 django-layuix 后，请按顺序执行：

```bash
# ===== Step 1: 安装包 =====
pip install django-layuix
# 或完整版: pip install django-layuix[all]

# ===== Step 2: 配置 settings.py =====
# 编辑 your_project/settings.py:
#   INSTALLED_APPS = ['django_layuix', 'django_layuix.rbac', 'django.contrib.admin', ...]
#   ⚠️ 注意: 'django_layuix.rbac' 是必需的，不是可选的！
#   AUTH_USER_MODEL = 'django_layuix_rbac.UserProfile' (推荐，启用自定义用户模型)

# ===== Step 3: 配置 urls.py =====
# 编辑 your_project/urls.py:
#   from django.contrib import admin
#   urlpatterns = [path('admin/', admin.site.urls)]

# ===== Step 4: 数据库迁移 =====
python manage.py makemigrations
python manage.py migrate

# ===== Step 5: 初始化数据（首次） =====
python manage.py init_menu

# ===== Step 6: 创建管理员 =====
python manage.py createsuperuser
# 输入用户名: admin
# 输入密码: admin123 (或其他强密码)

# ===== Step 7: 启动服务 =====
python manage.py runserver

# ===== Step 8: 验证安装 =====
# 浏览器打开: http://127.0.0.1:8000/admin/
# 使用 admin/admin123 登录
# 检查: 左侧菜单正常显示、无控制台404错误
```

---

### 🆘 获取帮助

如果以上方法都无法解决您的问题：

1. **查看详细文档**: `docs/` 目录下的各专题指南
2. **搜索已知 Issues**: [GitHub Issues](https://github.com/likangcai/django-layuix/issues)
3. **提交新 Issue**: 请包含以下信息：
   - Django 版本 (`python -c "import django; print(django.VERSION)"`)
   - django-layuix 版本 (`pip show django-layuix`)
   - 完整的错误堆栈信息
   - `settings.py` 中相关的配置（隐藏敏感信息）
   - 操作系统和 Python 版本

---

## 许可证

MIT License

