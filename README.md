# django-layui

基于 Layui 的 Django Admin 主题，它使用现代化的 Layui 界面替换 Django 默认的后台管理界面，并结合ai功能实现日志分析。

## 功能特性

- 🎨 现代化 Layui 后台管理界面（暗色/亮色主题）
- 🌗 深色/浅色主题切换
- 🌐 **完整国际化支持**（中文/英文），前端 JS + 后端 Django i18n 双层翻译，菜单多语言字段
- 🔐 RBAC 权限管理（菜单管理、角色管理、用户管理、按钮级权限控制）
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
# 基础安装（RBAC + 系统配置 + 操作日志 + Dashboard）
pip install django-layui

# 安装所有功能（含运维管理 + AI 日志分析）
pip install django-layui[all]

# 或按需安装
pip install django-layui[ops]   # 运维管理（服务器管理、SSH 终端）
pip install django-layui[ai]    # AI 日志分析
```

### 2. 最简配置（仅换肤）

在 `INSTALLED_APPS` 中将 `django_layui` 添加到 `django.contrib.admin` **之前**：

```python
# settings.py
INSTALLED_APPS = [
    'django_layui',                    # 必须放在 django.contrib.admin 之前
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # ... 你的应用
]
```

仅此而已！访问 `/admin/` 即可看到 Layui 风格的后台管理界面。

> **注意**：如果需要 iframe 嵌入功能，请从 `MIDDLEWARE` 中移除 `django.middleware.clickjacking.XFrameOptionsMiddleware`。

### 3. 启用 RBAC 扩展（推荐）

如果需要用户管理、菜单管理、角色管理、操作日志、Dashboard 等完整功能：

> **重要**：`AUTH_USER_MODEL` 必须在项目创建之初就设置好，中途切换会导致数据库迁移问题。

```python
# settings.py
INSTALLED_APPS = [
    'django_layui',
    'django_layui.rbac',               # RBAC 扩展
    'django.contrib.admin',
    # ...
]

# 使用自定义用户模型
AUTH_USER_MODEL = 'django_layui_rbac.UserProfile'
```

然后运行迁移并初始化数据：

```bash
python manage.py migrate
python manage.py init_menu
```

初始化命令会自动创建：
- **默认菜单**：权限管理（菜单/角色/用户）、系统管理（个人中心/操作日志/系统配置）
- **按钮级权限**：每个菜单下的增删改查按钮权限（15 个按钮权限项）
- **管理员角色**：绑定所有菜单权限
- **注册用户角色**：前端注册用户默认角色（仅个人中心权限）
- **系统配置**：system_name、logo_icon、logo_url、favicon_url、frontend_url 等 8 个默认配置项

默认管理员账号：`admin / admin123`

### 4. 高级配置

#### 4.1 settings.py 配置（默认值）

```python
# settings.py
LAYUI_CONFIG = {
    # 系统信息
    'system_name': 'Django Layui Admin',
    'system_version': '1.0.0',         # 系统版本号（显示在侧边栏）
    'system_description': '',          # 系统描述（显示在登录页）

    # Logo
    'logo_url': '',                    # 自定义 Logo URL（设置后替换图标）
    'logo_icon': 'layui-icon-code-circle',  # Layui 图标类名

    # 登录页面
    'login_bg_type': 'gradient',       # gradient / color / image
    'login_bg_value': 'linear-gradient(135deg, #2d3a4b 0%, #1a1a2e 100%)',
    'login_bg_image': '',              # 背景图片 URL

    # 前端项目
    'frontend_url': '',                # 前端项目 URL（顶部"查看站点"按钮）

    # 版权信息
    'copyright': '',
    
    # 首页自定义快速链接（类似 django-simpleui 的 SIMPLEUI_HOME_QUICK）
    'home_quick_links': [
        {'name': '个人中心', 'icon': 'layui-icon-user', 'url': '/static/layui/pages/profile.html'},
        {'name': '修改密码', 'icon': 'layui-icon-password', 'url': 'javascript:openChangePassword();'},
        {'name': '操作日志', 'icon': 'layui-icon-log', 'url': '/static/layui/pages/log.html'},
        {'name': '系统配置', 'icon': 'layui-icon-set', 'url': '/static/layui/pages/config.html'},
        # 外部链接示例
        # {'name': 'Django官网', 'icon': 'layui-icon-website', 'url': 'https://www.djangoproject.com/'},
        # {'name': 'Layui文档', 'icon': 'layui-icon-template', 'url': 'https://layui.dev/'},
        # {'name': 'GitHub', 'icon': 'layui-icon-github', 'url': 'https://github.com/'},
    ],
}

# 可选：自定义 Layui CDN
LAYUI_CDN = 'https://cdn.jsdelivr.net/npm/layui@2.13.5/dist/'

# 可选：自定义 Layui 版本
LAYUI_VERSION = '2.13.5'
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

配置优先级：**数据库 `sys_config` 表 > `settings.LAYUI_CONFIG` > 默认值**

| 配置键 | 说明 | 默认值 |
|--------|------|--------|
| `system_name` | 系统名称（标题栏 + 侧边栏） | Django Layui Admin |
| `system_version` | 版本号 | 1.0.0 |
| `logo_icon` | 侧边栏 Logo 图标类名 | layui-icon-code-circle |
| `logo_url` | 侧边栏 Logo 图片 URL | （空） |
| `favicon_url` | 浏览器标签页图标 URL | （空） |
| `frontend_url` | "查看站点"按钮跳转地址 | （空） |
| `copyright` | 版权信息 | （空） |

支持的配置类型：字符串、整数、布尔、JSON、URL、图片、颜色、文本。

#### 4.4 首页自定义快速链接（类似 django-simpleui）

django-layui 支持在首页仪表盘显示自定义快速链接，方便用户快速访问常用页面或外部网站。

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
        {'name': 'Layui文档', 'icon': 'layui-icon-template', 'url': 'https://layui.dev/'},
        {'name': 'GitHub', 'icon': 'layui-icon-github', 'url': 'https://github.com/'},
        
        # 自定义应用页面
        {'name': '商品管理', 'icon': 'layui-icon-cart-simple', 'url': '/store/product'},
        {'name': '订单管理', 'icon': 'layui-icon-form', 'url': '/store/order'},
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

django-layui 提供完整的中英文双语切换功能，包括前端界面和后端菜单。

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
- **繁体中文**：选填，繁体中文用户显示

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
pip install django-layui[ops]
```

```python
# settings.py
INSTALLED_APPS = [
    'django_layui',                    # 必须放在 django.contrib.admin 之前
    'django_layui.rbac',               # RBAC 扩展（用户/角色/菜单管理）
    'django_layui.ops',                # 运维管理扩展（服务器管理/AI分析）
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

django-layui 提供了两种菜单注册方式，允许外部项目动态添加菜单，无需修改库源码。

> **重要**：在 `ready()` 方法中调用 `auto_register_admin_apps()` 之前，**必须先导入应用的 `admin.py` 模块**，否则 `@admin.register` 装饰器不会生效，模型不会被注册到 Admin 中。

```python
# myapp/apps.py
from django.apps import AppConfig

class MyappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myapp'
    verbose_name = '我的应用'
    
    def ready(self):
        """
        自动扫描并注册所有已注册到 Admin 的模型
        这是推荐的方式，类似于 django-simpleui
        """
        try:
            from django_layui.rbac import auto_register_admin_apps
            
            # ⚠️ 重要：必须先导入 admin.py，确保 @admin.register 装饰器生效
            # Django 不会自动导入应用的 admin 模块
            import myapp.admin  # noqa: F401
            
            # 自动扫描 Admin 中的模型
            auto_register_admin_apps(
                exclude_apps=['auth', 'contenttypes', 'sessions'],  # 排除不需要显示的 app
                menu_sort_order={
                    'store': 1,           # store 应用排在第1位
                    'myapp': 2,           # myapp 应用排在第2位
                    'django_layui.rbac': 3,  # RBAC 管理排在第3位
                }
            )
        except Exception as e:
            print(f"Warning: Could not register menus: {e}")
```

**特性：**
- ✅ 自动识别 `admin.site.register()` 注册的所有模型
- ✅ 自动生成目录（App）和子菜单（Model）结构
- ✅ 自动创建增删改查按钮权限
- ✅ 支持自定义排序和排除特定 app
- ✅ 幂等性，多次调用不会重复创建
- ⚠️ **重要**：必须在 `ready()` 中显式导入 `admin.py`（如 `import myapp.admin`）

#### 方式二：手动注册菜单

如果需要更精细的控制（自定义图标、路径、嵌套结构），可以手动定义菜单。

```python
# myapp/apps.py
from django.apps import AppConfig

class MyappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myapp'
    verbose_name = '我的应用'
    
    def ready(self):
        """
        手动注册菜单
        适用于需要自定义图标、路径、排序等场景
        """
        try:
            from django_layui.rbac import register_menus
            
            # 注册菜单
            register_menus(
                menus_data=[
                    # 目录：演示应用
                    ('演示应用', 'layui-icon-app', '', 1, 4, None),
                    # 子菜单：商品管理
                    ('商品管理', 'layui-icon-cart-simple', '/store/product', 2, 1, '演示应用'),
                    # 子菜单：订单管理
                    ('订单管理', 'layui-icon-form', '/store/order', 2, 2, '演示应用'),
                ],
                buttons_data=[
                    # 商品管理按钮权限
                    ('新增商品', '商品管理', 'product:add', 1),
                    ('编辑商品', '商品管理', 'product:edit', 2),
                    ('删除商品', '商品管理', 'product:delete', 3),
                    # 订单管理按钮权限
                    ('查看订单', '订单管理', 'order:view', 1),
                    ('订单发货', '订单管理', 'order:ship', 2),
                ]
            )
        except Exception as e:
            print(f"Warning: Could not register menus: {e}")
```

**参数说明：**

- `menus_data`: 菜单列表，每个元素为元组：
  ```python
  (name, icon, path, menu_type, sort, parent_name_or_None)
  ```
  - `name`: 菜单名称
  - `icon`: Layui图标类名（如 `'layui-icon-app'`）
  - `path`: 路由地址（如 `'/store/product'`）
  - `menu_type`: 1=目录, 2=菜单, 3=按钮
  - `sort`: 排序号
  - `parent_name`: 父菜单名称，顶级菜单为None
  
- `buttons_data`: 按钮权限列表（可选），每个元素为元组：
  ```python
  (btn_name, parent_menu_name, permission, sort)
  ```
  - `btn_name`: 按钮名称
  - `parent_menu_name`: 所属菜单名称
  - `permission`: 权限标识（如 `'product:add'`）
  - `sort`: 排序号

#### 前端页面映射（可选）

如果你的应用有自定义的前端页面，需要在模板中添加路径映射。可以通过继承 `admin/index.html` 来实现：

```html
<!-- templates/admin/index.html -->
{% extends "admin/index.html" %}

{% block extra_js %}
{{ block.super }}
<script>
// 扩展菜单路径映射
Object.assign(menuPathMap, {
    '/store/category': '/static/myapp/pages/store-category.html',
    '/store/product': '/static/myapp/pages/store-product.html',
    '/store/order': '/static/myapp/pages/store-order.html',
});
</script>
{% endblock %}
```

#### 高级用法

**注销菜单：**

```python
from django_layui.rbac import unregister_menus

# 谨慎使用，会删除菜单及其子菜单
unregister_menus(['演示应用'])
```

**条件注册：**

```python
def ready(self):
    from django.conf import settings
    from django_layui.rbac import auto_register_admin_apps
    
    # 根据配置决定是否注册
    if getattr(settings, 'ENABLE_STORE_APP', False):
        auto_register_admin_apps()
```

#### 对比两种方式

| 方式 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **自动扫描** ✅ | 零配置，类似 django-simpleui，自动识别新模型 | 自定义程度较低 | 大部分场景，特别是快速开发 |
| **手动注册** | 完全控制菜单结构、图标、路径 | 需要手动维护 | 需要复杂嵌套或自定义图标的场景 |

#### 注意事项

- 菜单注册是**幂等的**，多次调用不会重复创建
- 新创建的菜单会自动分配给管理员角色
- 建议在 `ready()` 方法中使用 `try-except` 包裹，避免启动失败
- 示例代码参考：`example/store/apps.py`

---### 6. 启用 Web SSH 终端（可选）

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
pip install django-layui[ai]
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
| 智谱AI | `https://open.bigmodel.cn/api/paas/v4/` | glm-4-flash |
| DeepSeek | `https://api.deepseek.com/v1/` | deepseek-chat |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1/` | qwen-turbo |
| Moonshot | `https://api.moonshot.cn/v1/` | moonshot-v1-8k |

在日志查看器中点击「AI 分析」按钮即可自动分析日志内容，输出包括：
- 日志概览（类型、时间范围、总体状态）
- 异常检测（错误、警告、异常模式）
- 根因分析
- 修复建议和命令

---

## 工作原理

django-layui 利用 Django 的模板覆盖机制。通过将包放在 `INSTALLED_APPS` 中 `django.contrib.admin` 之前，Django 的模板加载器会优先查找 `django_layui/templates/admin/` 中的模板，从而有效替换默认的 Admin 模板。

### 自动注册机制

`django_layui.rbac` 的 `AppConfig.ready()` 会自动完成以下操作，用户无需手动配置：

1. **INSTALLED_APPS**：自动注入 `django_layui`
2. **LocaleMiddleware**：自动注入国际化中间件
3. **模板目录**：自动注册模板覆盖目录
4. **静态文件**：自动注册静态文件查找器
5. **模板标签**：自动注册 `layui_tags` 模板标签库
6. **API 路由**：自动注册 `/admin/api/rbac/` 路由
7. **Ops 路由**：自动注册 `/admin/api/ops/` 路由（如果 ops 模块已安装）

### 模板覆盖链

```
django_layui/templates/admin/base.html      → 主布局（Layui）
django_layui/templates/admin/base_site.html  → 站点布局
django_layui/templates/admin/login.html      → 登录页面
django_layui/templates/admin/index.html      → 仪表盘（Tab 布局 + iframe）
django_layui/templates/admin/change_list.html → 模型列表页
django_layui/templates/admin/change_form.html → 模型编辑页
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
| `{% login_bg_type %}` | 登录背景类型 |
| `{% login_bg_value %}` | 登录背景值 |
| `{% login_bg_image %}` | 登录背景图片 URL |
| `{% copyright_text %}` | 版权信息 |
| `{% layui_config key default %}` | 根据键获取配置值 |

---

## RBAC 模型

使用 RBAC 扩展（`django_layui.rbac`）时，提供以下模型：

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

## 管理命令

| 命令 | 说明 |
|------|------|
| `python manage.py init_menu` | 初始化默认菜单、角色和系统配置 |

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

django-layui 支持中英文双语，分两层实现：

1. **后端（Django i18n）**：模板中使用 `{% trans %}` 标签，翻译文件位于 `django_layui/locale/zh_Hans/LC_MESSAGES/django.po`
2. **前端（JS i18n）**：子页面通过 `t('key')` 函数和 `data-i18n` 属性实现动态翻译，翻译字典位于 `static/layui/js/i18n.js`

`LocaleMiddleware` 会自动注入，用户无需手动配置。

---

## 环境要求

- Python >= 3.8
- Django >= 3.2

---

## 可选依赖

| 安装方式 | 命令 | 包含功能 |
|---------|------|---------|
| 基础 | `pip install django-layui` | RBAC + 系统配置 + 操作日志 + Dashboard |
| 运维 | `pip install django-layui[ops]` | + 服务器管理 + SSH 终端 |
| AI | `pip install django-layui[ai]` | + AI 日志分析 |
| 全部 | `pip install django-layui[all]` | 所有功能 |
| 开发 | `pip install django-layui[dev]` | + build + twine |

---

## 配置项目

### urls.py 最简配置

```python
# urls.py
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # 你的应用路由 ...
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

> **注意**：无需手动注册 `django_layui.ops.urls`，ops 模块的 API 路由（`/admin/api/ops/`）由 `AppConfig.ready()` 自动注册。手动重复注册反而会导致路由冲突。

### 执行数据库迁移

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 收集静态文件

```bash
python manage.py collectstatic
```

### 启动项目

```bash
python manage.py runserver
```

访问 http://127.0.0.1:8000/admin/ 即可看到 Layui 风格的后台。

---

## 三、功能开启对照表

| 功能 | 需要的包 | 需要的配置 |
|------|---------|-----------|
| Layui 主题（必装） | django-layui | INSTALLED_APPS 加 django_layui |
| RBAC 用户管理 | django-layui | 加 django_layui.rbac + AUTH_USER_MODEL |
| 服务器管理 + 日志查看 | paramiko | 加 django_layui.ops（API 路由自动注册） |
| Web SSH 终端 | webssh | 运行 wssh 命令 + 配置 webssh_url |
| AI 日志分析 | openai | 配置 AI Key（后台界面或 settings.py） |

---

## 四、详细文档索引

更多详细使用指南和最佳实践，请参考 `docs/` 目录下的文档：

### 核心功能
- [首页自定义快速链接配置](docs/HOME_QUICK_LINKS_GUIDE.md) - 仪表盘的快速入口配置
- [首页快速链接速查表](docs/HOME_QUICK_LINKS_QUICKREF.md) - 快速参考和常用示例
- [菜单扩展指南](docs/MENU_EXTENSION_GUIDE.md) - 如何添加自定义应用菜单
- [**权限系统使用指南**](docs/PERMISSION_SYSTEM_GUIDE.md) - RBAC 权限管理、字段说明、实战示例 ⭐ **新增**
- [AJAX Admin 使用指南](docs/AJAX_ADMIN_GUIDE.md) - AJAX 增强功能
- [**国际化 (i18n) 使用指南**](docs/I18N_GUIDE.md) - 中英文双语切换与多语言开发
- [**国际化 (i18n) 快速参考**](docs/I18N_QUICKREF.md) - i18n 翻译键速查表

### 高级特性
- [多主题系统使用指南](docs/THEME_SYSTEM_GUIDE.md) - 25种主题的切换与定制
- [主题集成总结](docs/THEME_INTEGRATION_SUMMARY.md) - 主题系统的实现原理

### 版本信息
- [**更新日志 (CHANGELOG)**](CHANGELOG.md) - 版本历史和更新记录

---

## 许可证

MIT License
