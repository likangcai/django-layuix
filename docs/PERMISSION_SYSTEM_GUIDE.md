# django-layuix 权限系统使用指南

## 结论（TL;DR）
【事实】权限内核统一走 `rbac/engine.py`，支持菜单、按钮权限码、角色继承与 SSD/DSD 约束。
【判断】前端隐藏按钮只改善体验，真正安全边界是服务端 `has_permission()` / `api_permission_required`。
【本期不做】字段级权限、ABAC 与多租户隔离；1.4.2 已支持行级数据范围（Scope 层）、权限级互斥、策略可配与跨框架认证桥接。

---

## 目录

- [1. 概述](#1-概述)
- [2. 菜单模型字段详解](#2-菜单模型字段详解)
- [3. 权限标识规范](#3-权限标识规范)
- [4. 权限工作流程](#4-权限工作流程)
- [5. 前端权限控制](#5-前端权限控制)
- [6. 后端API权限](#6-后端api权限)
- [7. 实战示例](#7-实战示例)
- [8. 常见问题](#8-常见问题)

---

## 1. 概述

django-layuix 的 RBAC（基于角色的访问控制）系统提供三级权限控制：

| 级别 | 说明 | 示例 |
|------|------|------|
| **菜单级** | 控制用户能看到哪些菜单 | 权限管理、系统管理 |
| **页面级** | 控制用户能访问哪些页面 | 菜单管理页面 |
| **按钮级** | 控制用户能执行哪些操作 | 新增、编辑、删除按钮 |

---

## 2. 菜单模型字段详解

### Menu 模型定义

```python
class Menu(models.Model):
    parent = models.ForeignKey('self', ...)      # 父级菜单
    name = models.CharField(...)                 # 菜单名称（中文）
    name_en = models.CharField(...)              # 菜单名称（英文）
    name_zh_hans = models.CharField(...)         # 菜单名称（简体中文）
    icon = models.CharField(...)                 # 图标
    path = models.CharField(...)                 # 路由地址
    component = models.CharField(...)            # 组件路径
    menu_type = models.IntegerField(...)         # 类型：1=目录, 2=菜单, 3=按钮
    permission = models.CharField(...)           # 权限标识
    sort = models.IntegerField(...)              # 排序
    visible = models.BooleanField(...)           # 是否显示
    status = models.BooleanField(...)            # 是否启用
```

### 字段详细说明

#### 2.1 基础信息字段

| 字段名 | 类型 | 必填 | 说明 | 示例值 |
|--------|------|------|------|--------|
| `name` | CharField(50) | ✅ 是 | 菜单名称（中文，主名称） | `'菜单管理'` |
| `name_en` | CharField(50) | ❌ 否 | 英文名称（用于国际化） | `'Menu Management'` |
| `name_zh_hans` | CharField(50) | ❌ 否 | 简体中文名称 | `'菜单管理'` |

**多语言优先级**：
```
用户选择 en → 使用 name_en (为空则回退到 name)
用户选择 zh-hans → 使用 name_zh_hans (为空则回退到 name)
其他语言代码 → 回退到 name
```

#### 2.2 显示相关字段

| 字段名 | 类型 | 必填 | 说明 | 示例值 |
|--------|------|------|------|--------|
| `icon` | CharField(50) | ❌ 否 | Layui 图标类名 | `'layui-icon-menu-fill'` |
| `sort` | IntegerField | ❌ 否 | 排序号（越小越靠前） | `1`, `2`, `3` |
| `visible` | BooleanField | ❌ 否 | 是否在侧边栏显示 | `True` / `False` |
| `status` | BooleanField | ❌ 否 | 是否启用（禁用后不可访问） | `True` / `False` |

**图标注意事项**：
- 必须使用 Layui 内置图标，完整列表见 [Layui 官方图标库](https://layui.dev/docs/2/icon/)
- 常用有效图标：
  - 目录类：`layui-icon-auz`（权限）、`layui-icon-set`（设置）、`layui-icon-console`（运维）
  - 页面类：`layui-icon-app`（应用）、`layui-icon-user`（用户）、`layui-icon-file`（文件）
  - 操作类：`layui-icon-add-1`（新增）、`layui-icon-edit`（编辑）、`layui-icon-delete`（删除）

#### 2.3 路由与组件字段 ⭐ 重要

| 字段名 | 类型 | 必填 | 用途说明 | 示例值 |
|--------|------|------|----------|--------|
| `path` | CharField(200) | ⚠️ 菜单必填 | **路由地址/URL路径** | `'/permission/menu'` |
| `component` | CharField(200) | ❌ 可选 | **前端组件路径（预留）** | `'/pages/menu/index.vue'` |

##### path 字段详解

`path` 是**最核心的字段**，决定了点击菜单后跳转到哪个页面：

```python
# 内置页面（直接使用）
path='/static/layui/pages/dashboard.html'     # 仪表盘
path='/static/layui/pages/user.html'          # 用户管理
path='/static/layui/pages/menu.html'          # 菜单管理
path='/static/layui/pages/server.html'        # 服务器管理
path='/static/layui/pages/config.html'        # 系统配置
path='/static/layui/pages/profile.html'       # 个人中心

# 自定义页面（需要配置映射）
path='/store/product'                         # 商品管理（自定义）
path='/store/order'                           # 订单管理（自定义）
```

**自定义页面映射方式**：
```python
# 方式1: 在模板中继承 index.html
{% extends "admin/index.html" %}
{% block extra_js %}
{{ block.super }}
<script>
Object.assign(menuPathMap, {
    '/store/product': '/static/myapp/pages/product.html',
    '/store/order': '/static/myapp/pages/order.html',
});
</script>
{% endblock %}

# 方式2: 通过 settings.py 配置
LAYUI_CONFIG = {
    'menu_path_map': {
        '/store/product': '/static/myapp/pages/product.html',
    }
}
```

##### component 字段详解

`component` 是**预留字段**，当前版本暂未使用：

| 适用场景 | 说明 |
|----------|------|
| Vue/React SPA | 存储组件文件路径，如 `/views/system/menu/index.vue` |
| 微前端架构 | 存储子应用的路由地址 |
| iframe 嵌入 | 存储 iframe src 地址 |

> 💡 **提示**：当前版本只需关注 `path` 字段即可，`component` 可以留空。

#### 2.4 类型与权限字段 ⭐ 核心字段

| 字段名 | 类型 | 必填 | 说明 | 示例值 |
|--------|------|------|------|--------|
| `menu_type` | IntegerField | ✅ 是 | 菜单类型 | `1`=目录, `2`=菜单, `3`=按钮 |
| `permission` | CharField(100) | ⚠️ 按钮必填 | **权限标识字符串** | `'menu:add'` |

##### menu_type 三种类型

```
┌─────────────────────────────────────────────────────────────┐
│  menu_type=1: 目录                                          │
│  ┌──────────────────────────────────────┐                   │
│  │ 📁 权限管理                          │ ← 侧边栏分组标题   │
│  │   ├─ 📄 菜单管理 (type=2)            │                    │
│  │   ├─ 👥 角色管理 (type=2)            │                    │
│  │   └─ 👤 用户管理 (type=2)            │                    │
│  └──────────────────────────────────────┘                   │
│                                                             │
│  menu_type=2: 菜单                                          │
│  ┌──────────────────────────────────────┐                   │
│  │ 📄 菜单管理                          │ ← 可点击的页面入口 │
│  │   ├─ ➕ 新增菜单 (type=3)            │                    │
│  │   ├─ ✏️ 编辑菜单 (type=3)            │                    │
│  │   └─ 🗑️ 删除菜单 (type=3)            │                    │
│  └──────────────────────────────────────┘                   │
│                                                             │
│  menu_type=3: 按钮                                          │
│  ┌──────────────────────────────────────┐                   │
│  │ [➕ 新增] [✏️ 编辑] [🗑️ 删除]        │ ← 页面内的操作按钮 │
│  └──────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

| 类型 | permission必填 | 显示位置 | 典型用途 |
|------|-----------------|----------|----------|
| **目录(1)** | ❌ 可选 | 侧边栏分组 | 权限管理、系统管理 |
| **菜单(2)** | ❌ 可选 | 侧边栏菜单项 | 菜单管理、用户管理 |
| **按钮(3)** | ✅ **必填** | 页面内操作按钮 | 新增、编辑、删除 |

---

## 3. 权限标识规范

### 3.1 命名规则

```
格式：模块:操作
规则：小写字母 + 冒号 + 小写字母/数字/下划线
长度：建议不超过 30 个字符
```

### 3.2 命名示例

#### ✅ 正确示例

```python
# 格式：模块:操作
'menu:add'              # 菜单-新增
'menu:edit'             # 菜单-编辑
'menu:delete'           # 菜单-删除
'user:create'           # 用户-创建
'user:update'           # 用户-更新
'role:assign'           # 角色-分配权限
'server:connect'        # 服务器-连接测试
'server:ssh'            # 服务器-SSH终端'ai_config:set_default' # AI配置-设为默认
'order:ship'            # 订单-发货
'product:publish'       # 商品-发布
'log:export'            # 日志-导出
'config:upload_image'   # 配置-上传图片
```

#### ❌ 错误示例

```python
'Menu:Add'              # ❌ 大写开头（大小写敏感）
'menu add'              # ❌ 包含空格
'menu-add'              # ❌ 使用横线而非冒号
'menu:'                 # ❌ 缺少操作部分
':add'                  # ❌ 缺少模块部分
'a_very_long_permission_name_that_exceeds_reasonable_length'  # ❌ 过长
```

### 3.3 操作动词推荐

| 动词 | 含义 | 适用场景 |
|------|------|----------|
| `add` / `create` | 新增 | 创建新记录 |
| `edit` / `update` | 编辑 | 修改已有记录 |
| `delete` / `remove` | 删除 | 删除记录 |
| `view` / `list` | 查看 | 查看列表或详情 |
| `export` | 导出 | 导出数据（Excel/PDF） |
| `import` | 导入 | 批量导入数据 |
| `publish` | 发布 | 发布内容 |
| `approve` | 审核 | 审批流程 |
| `assign` | 分配 | 分配权限/任务 |
| `config` | 配置 | 系统配置 |
| `connect` | 连接 | 连接外部服务 |
| `set_default` | 设默认 | 设置默认项 |

### 3.4 特殊权限标识

```python
# 超级管理员特殊标识（无需配置，自动拥有所有权限）
# is_superuser=True 的用户自动拥有所有权限

# 系统内置权限（由 init_menu 自动创建）
'menu:add', 'menu:edit', 'menu:delete', 'menu:copy'
'role:add', 'role:edit', 'role:delete', 'role:copy'
'user:add', 'user:edit', 'user:delete', 'user:reset_password', 'user:disable'
'log:view', 'log:export', 'log:delete'
'config:add', 'config:edit', 'config:delete', 'config:upload'
'server:add', 'server:edit', 'server:delete', 'server:test_connect', 'server:ssh'
'ai_config:add', 'ai_config:edit', 'ai_config:delete', 'ai_config:set_default'
```

---

## 4. 权限工作流程

### 4.1 完整权限检查流程

```
用户登录
    ↓
获取用户角色
    ↓
查询角色关联的菜单和按钮权限
    ↓
返回权限列表给前端
    ↓
前端根据权限控制 UI 显示
    ↓
用户发起 API 请求
    ↓
后端验证用户是否有该权限
    ↓
返回结果（有权限→执行，无权限→拒绝）
```

### 4.2 系统配置优先级逻辑

**配置加载顺序：**

1. **默认值**：代码中定义的初始值（在 `init_menu` 命令中设置）
2. **settings.py 配置**：开发者在项目中自定义的默认值
3. **数据库配置**：通过后台界面动态修改的值（**最高优先级**）

**业务场景示例：**

```python
# settings.py 中的默认配置
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

**实现原理：**

在 [`admin.py`](../django_layuix/admin.py) 的 `LayuiAdminSite.each_context()` 方法中：

```python
# 1. 从 settings.py 读取默认配置
layui_config = getattr(settings, 'LAYUI_CONFIG', {})

# 2. 从数据库读取配置并覆盖
try:
    from .rbac.models import SystemConfig
    db_configs = SystemConfig.objects.all()
    for cfg in db_configs:
        if cfg.config_type == 'text' and cfg.key in ('home_quick_links', 'home_stats_cards'):
            import json
            try:
                layui_config[cfg.key] = json.loads(cfg.value)
            except (json.JSONDecodeError, TypeError):
                layui_config[cfg.key] = cfg.value
        else:
            layui_config[cfg.key] = cfg.value
except Exception:
    pass
```

**重要提示：**
- 使用 `python manage.py init_menu --force` 会重置所有系统配置为代码中的默认值
- 如需保留自定义配置，请避免使用 `--force` 参数，或直接在后台界面修改

### 4.3 数据关系图

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│   User      │──────▶│    Role     │──────▶│    Menu      │
│  (用户表)   │  N:1  │  (角色表)   │  M:N  │  (菜单表)    │
└─────────────┘       └─────────────┘       └─────────────┘
                            │                       │
                            ▼                       ▼
                     ┌─────────────┐       ┌─────────────┐
                     │ permissions │       │ permission  │
                     │  (权限列表)  │       │ (权限标识)   │
                     └─────────────┘       └─────────────┘
```

### 4.4 权限继承规则

| 规则 | 说明 |
|------|------|
| **超级管理员** | 自动拥有所有权限，无需显式分配 |
| **普通用户** | 只拥有其角色被分配的权限 |
| **多角色合并** | 用户有多个角色时，权限取并集 |
| **父级权限** | 拥有父级目录权限不等于拥有子级权限（需单独分配） |

---

## 5. 前端权限控制

### 5.1 获取当前用户权限

```javascript
// 从全局变量获取当前用户信息
var currentUser = window.parent.currentUser || {};
var permissions = currentUser.permissions || [];

// permissions 示例:
// ['menu:add', 'menu:edit', 'user:list', 'server:connect']
```

### 5.2 Layui 模板引擎判断权限

```html
<!-- 工具栏按钮权限控制 -->
<script type="text/html" id="toolbarTpl">
    <div class="layui-btn-container">
        {{# var cu = (window.parent && window.parent.currentUser) || {}; var perms = cu.permissions || []; }}
        
        {{# if(layui.$.inArray('menu:add', perms) > -1){ }}
        <button class="layui-btn" lay-event="add">新增</button>
        {{# } }}
        
        {{# if(layui.$.inArray('menu:edit', perms) > -1){ }}
        <button class="layui-btn" lay-event="edit">编辑</button>
        {{# } }}
        
        {{# if(layui.$.inArray('menu:delete', perms) > -1){ }}
        <button class="layui-btn" lay-event="delete">删除</button>
        {{# } }}
    </div>
</script>

<!-- 表格行操作列权限 -->
<script type="text/html" id="operateTpl">
    {{# var cu = (window.parent && window.parent.currentUser) || {}; var perms = cu.permissions || []; }}
    
    <a class="layui-btn-xs" lay-event="view">查看</a>
    
    {{# if(layui.$.inArray('menu:edit', perms) > -1){ }}
    <a class="layui-btn-xs layui-btn-normal" lay-event="edit">编辑</a>
    {{# } }}
    
    {{# if(layui.$.inArray('menu:delete', perms) > -1){ }}
    <a class="layui-btn-xs layui-btn-danger" lay-event="del">删除</a>
    {{# } }}
</script>
```

### 5.3 JavaScript 中判断权限

```javascript
// 封装权限检查函数
function hasPermission(perm) {
    var currentUser = window.parent && window.parent.currentUser;
    var permissions = currentUser ? currentUser.permissions : [];
    return permissions.indexOf(perm) > -1;
}

// 使用示例
if (hasPermission('server:ssh')) {
    // 显示 SSH 终端按钮
    $('#sshBtn').show();
}

if (hasPermission('config:upload')) {
    // 启用上传功能
    enableUpload();
}
```

### 5.4 页面加载时动态隐藏元素

```javascript
$(document).ready(function() {
    var permissions = (window.parent.currentUser || {}).permissions || [];
    
    // 隐藏无权限的按钮
    if (permissions.indexOf('menu:add') === -1) {
        $('[lay-event="add"]').hide();
    }
    if (permissions.indexOf('menu:edit') === -1) {
        $('[lay-event="edit"]').hide();
    }
    if (permissions.indexOf('menu:delete') === -1) {
        $('[lay-event="del"]').hide();
    }
});
```

---

## 6. 后端 API 权限

### 6.1 当前权限实现方式

django-layuix 当前的权限控制是**前端展示层**的权限控制：

```python
# views.py - 返回用户权限列表
def _get_user_permissions(user):
    """Get user permission strings"""
    from .models import Menu
    
    if user.is_superuser:
        # 超级管理员拥有所有权限
        perms = list(Menu.objects.filter(
            status=True, 
            permission__gt=''  # 只返回有权限标识的菜单
        ).values_list('permission', flat=True))
    else:
        # 普通用户通过角色获取权限
        perms = list(Menu.objects.filter(
            status=True,
            permission__gt='',
            roles__users=user  # 通过角色关联
        ).distinct().values_list('permission', flat=True))
    
    return perms
```

### 6.2 API 接口认证装饰器

```python
# 登录验证（已实现）
@api_login_required
def some_api(request):
    # 仅验证是否登录，未验证具体权限
    pass

# 如需添加权限验证，可以这样扩展：
def api_permission_required(permission):
    """权限验证装饰器"""
    def decorator(view_func):
        @wraps(view_func)
        @api_login_required
        def wrapper(request, *args, **kwargs):
            user = request.user
            if user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # 检查用户是否有指定权限
            user_perms = _get_user_permissions(user)
            if permission not in user_perms:
                return JsonResponse({
                    'code': 403, 
                    'msg': f'缺少权限: {permission}'
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

# 使用示例
@api_permission_required('menu:delete')
def delete_menu(request):
    # 只有拥有 menu:delete 权限的用户才能访问
    pass
```

### 6.3 获取用户信息的 API

**请求：**
```
GET /admin/api/rbac/user/info/
Authorization: Bearer <session_id 或 token>
```

**响应：**
```json
{
    "code": 200,
    "data": {
        "id": 1,
        "username": "admin",
        "nickname": "管理员",
        "avatar": "/media/avatar/admin.jpg",
        "roles": ["超级管理员"],
        "permissions": [
            "menu:add", "menu:edit", "menu:delete",
            "user:add", "user:edit", "user:delete",
            "role:add", "role:edit", "role:delete",
            ...
        ],
        "language": "zh-hans"
    }
}
```

---

## 7. 实战示例

### 7.1 创建新的业务模块（以"商品管理"为例）

#### 步骤1：注册菜单

```python
# myapp/apps.py
from django.apps import AppConfig


class MyappConfig(AppConfig):
  default_auto_field = 'django.db.models.BigAutoField'
  name = 'myapp'
  verbose_name = '商品管理'

  def ready(self):
    try:
      from django_layuix.rbac import register_menus

      register_menus(
        menus_data=[
          # 一级目录
          ('电商管理', 'layui-icon-cart', '', 1, 5, None),

          # 二级菜单
          ('商品管理', 'layui-icon-cart-simple', '/store/product', 2, 1, '电商管理'),
          ('订单管理', 'layui-icon-form', '/store/order', 2, 2, '电商管理'),
          ('分类管理', 'layui-icon-folder', '/store/category', 2, 3, '电商管理'),
        ],

        buttons_data=[
          # 商品管理按钮权限
          ('新增商品', '商品管理', 'product:add', 1),
          ('编辑商品', '商品管理', 'product:edit', 2),
          ('删除商品', '商品管理', 'product:delete', 3),
          ('导出商品', '商品管理', 'product:export', 4),
          ('上架商品', '商品管理', 'product:publish', 5),

          # 订单管理按钮权限
          ('查看订单', '订单管理', 'order:view', 1),
          ('发货', '订单管理', 'order:ship', 2),
          ('取消订单', '订单管理', 'order:cancel', 3),

          # 分类管理按钮权限
          ('新增分类', '分类管理', 'category:add', 1),
          ('编辑分类', '分类管理', 'category:edit', 2),
          ('删除分类', '分类管理', 'category:delete', 3),
        ]
      )
    except Exception as e:
      print(f"Warning: Could not register menus: {e}")
```

#### 步骤2：创建前端页面

```html
<!-- templates/store/product.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>商品管理</title>
    <link rel="stylesheet" href="/static/layui/lib/layui.css">
    <link rel="stylesheet" href="/static/layui/css/admin.css">
</head>
<body>
<div class="page-container">
    <table id="productTable" lay-filter="productTable"></table>
</div>

<!-- 工具栏模板 -->
<script type="text/html" id="toolbarTpl">
    <div class="layui-btn-container">
        {{# var cu = (window.parent && window.parent.currentUser) || {}; var perms = cu.permissions || []; }}
        
        {{# if(layui.$.inArray('product:add', perms) > -1){ }}
        <button class="layui-btn layui-btn-sm layui-btn-normal" lay-event="add">
            <i class="layui-icon layui-icon-add-1"></i> 新增商品
        </button>
        {{# } }}
        
        {{# if(layui.$.inArray('product:export', perms) > -1){ }}
        <button class="layui-btn layui-btn-sm layui-btn-primary" lay-event="export">
            <i class="layui-icon layui-icon-export"></i> 导出
        </button>
        {{# } }}
    </div>
</script>

<!-- 行操作模板 -->
<script type="text/html" id="operateTpl">
    {{# var cu = (window.parent && window.parent.currentUser) || {}; var perms = cu.permissions || []; }}
    
    {{# if(layui.$.inArray('product:edit', perms) > -1){ }}
    <a class="layui-btn-xs layui-btn-normal" lay-event="edit">编辑</a>
    {{# } }}
    
    {{# if(layui.$.inArray('product:publish', perms) > -1){ }}
    <a class="layui-btn-xs layui-btn-warm" lay-event="publish">上架</a>
    {{# } }}
    
    {{# if(layui.$.inArray('product:delete', perms) > -1){ }}
    <a class="layui-btn-xs layui-btn-danger" lay-event="del">删除</a>
    {{# } }}
</script>

<script src="/static/layui/layui.js"></script>
<script>
layui.use(['table', 'form'], function(){
    var table = layui.table;
    var form = layui.form;
    
    table.render({
        elem: '#productTable',
        url: '/admin/api/store/products/',
        toolbar: '#toolbarTpl',
        cols: [[
            {field: 'id', title: 'ID'},
            {field: 'name', title: '商品名称'},
            {field: 'price', title: '价格'},
            {title: '操作', toolbar: '#operateTpl'}
        ]]
    });
});
</script>
</body>
</html>
```

#### 步骤3：配置页面路径映射

```python
# urls.py 或 settings.py

# 方式A: 在 settings.py 中配置
LAYUI_CONFIG = {
    'menu_path_map': {
        '/store/product': '/static/store/product.html',
        '/store/order': '/static/store/order.html',
        '/store/category': '/static/store/category.html',
    }
}

# 方式B: 继承 admin/index.html
# templates/admin/index.html
{% extends "admin/index.html" %}
{% block extra_js %}
{{ block.super }}
<script>
Object.assign(window.menuPathMap || {}, {
    '/store/product': '/static/store/product.html',
    '/store/order': '/static/store/order.html',
    '/store/category': '/static/store/category.html',
});
</script>
{% endblock %}
```

#### 步骤4：运行迁移和初始化

```bash
cd your_project
python manage.py migrate

# 初始化菜单、角色和系统配置（已存在则跳过）
python manage.py init_menu

# 强制更新所有菜单、角色权限和系统配置（重置为默认值）
python manage.py init_menu --force

# 创建超级管理员 + 初始化菜单
python manage.py init_data

# 强制重新初始化所有数据
python manage.py init_data --force

# 修复无效的 Layui 图标
python manage.py init_menu --fix-icons
```

> **注意**：使用 `--force` 参数会重置系统配置为代码中的默认值（包括 `home_quick_links`、`home_stats_cards` 等）。

### 7.2 为现有角色分配权限

```bash
# 方法1: Django Shell
python manage.py shell

>>> from django_layuix.rbac.models import Role, Menu
>>> 
>>> # 获取角色
>>> operator_role = Role.objects.get(name='运营人员')
>>> 
>>> # 获取要分配的权限（按钮级菜单）
>>> product_perms = Menu.objects.filter(
...     permission__startswith='product:',
...     menu_type=3
... )
>>> 
>>> # 分配权限
>>> operator_role.menus.add(*product_perms)
>>> print(f'已为 {operator_role.name} 分配 {product_perms.count()} 个权限')

# 方法2: 后台界面
# 1. 进入「权限管理 → 角色管理」
# 2. 点击「编辑」目标角色
# 3. 在权限树中勾选需要的权限
# 4. 保存
```

### 7.3 多语言菜单配置

```python
register_menus(
  menus_data=[
    ('商品管理', 'layui-icon-cart-simple', '/store/product', 2, 1, '电商管理'),
  ],
)

# 创建后，在后台或代码中更新多语言字段
from django_layuix.rbac.models import Menu

menu = Menu.objects.get(name='商品管理')
menu.name_en = 'Product Management'
menu.name_zh_hans = '商品管理'
menu.save()
```

---

## 8. 常见问题

### Q1: 为什么修改了权限但前端没变化？

**原因**：浏览器缓存了旧的权限列表。

**解决方案**：
1. 清除浏览器缓存（Ctrl+Shift+Delete）
2. 或者强制刷新（Ctrl+F5）
3. 或者重新登录（退出再登录）

### Q2: 超级管理员看不到某些按钮？

**原因**：超级管理员应该看到所有按钮。如果看不到，可能是：

1. **前端代码问题**：检查 `toolbarTpl` 和 `operateTpl` 模板中的权限判断逻辑
2. **权限列表未正确返回**：打开浏览器控制台，输入 `console.log(currentUser.permissions)` 查看权限列表

### Q3: 如何批量添加权限？

```python
from django_layuix.rbac.models import Menu, Role

# 批量创建按钮权限
buttons = [
  ('批量导入', '商品管理', 'product:import', 10),
  ('批量下架', '商品管理', 'product:unpublish', 11),
]

for btn_name, parent_name, perm, sort in buttons:
  parent_menu = Menu.objects.get(name=parent_name)
  Menu.objects.get_or_create(
    name=btn_name,
    defaults={
      'icon': '',
      'path': '',
      'component': '',
      'menu_type': 3,  # 按钮
      'permission': perm,
      'sort': sort,
      'parent': parent_menu,
      'visible': False,  # 按钮通常不在侧边栏显示
      'status': True,
    }
  )
```

### Q4: 权限标识可以重复吗？

**不建议重复**。虽然系统不会阻止你使用相同的权限标识，但会导致：
- 无法精确区分不同操作的权限
- 角色授权时出现混乱

**正确做法**：每个操作使用唯一的权限标识。

### Q5: 如何实现数据级别的权限控制？

当前 RBAC 系统是**功能级别**的权限控制（能否执行某个操作），不是**数据级别**的控制（只能看自己的数据）。

如需数据级别控制，可以在后端 API 中添加过滤条件：

```python
def product_list(request):
    queryset = Product.objects.all()
    
    # 数据权限过滤
    if not request.user.is_superuser:
        # 普通用户只能看自己部门的数据
        queryset = queryset.filter(department=request.user.department)
    
    return success_response(list(queryset.values()))
```

---

## 附录

### A. 完整权限标识速查表

| 模块 | 权限标识 | 说明 |
|------|----------|------|
| **菜单管理** | `menu:add` | 新增菜单 |
| | `menu:edit` | 编辑菜单 |
| | `menu:delete` | 删除菜单 |
| | `menu:copy` | 复制菜单 |
| **角色管理** | `role:add` | 新增角色 |
| | `role:edit` | 编辑角色 |
| | `role:delete` | 删除角色 |
| | `role:copy` | 复制角色 |
| **用户管理** | `user:add` | 新增用户 |
| | `user:edit` | 编辑用户 |
| | `user:delete` | 删除用户 |
| | `user:reset_password` | 重置密码 |
| | `user:disable` | 启用/禁用 |
| **日志管理** | `log:view` | 查看日志 |
| | `log:export` | 导出日志 |
| | `log:delete` | 删除日志 |
| **系统配置** | `config:add` | 新增配置 |
| | `config:edit` | 编辑配置 |
| | `config:delete` | 删除配置 |
| | `config:upload` | 上传图片 |
| **服务器管理** | `server:add` | 新增服务器 |
| | `server:edit` | 编辑服务器 |
| | `server:delete` | 删除服务器 |
| | `server:test_connect` | 连接测试 |
| | `server:ssh` | SSH终端 |
| **AI配置** | `ai_config:add` | 新增配置 |
| | `ai_config:edit` | 编辑配置 |
| | `ai_config:delete` | 删除配置 |
| | `ai_config:set_default` | 设为默认 |

### B. 常用 Layui 图标速查表

| 图标类名 | 显示效果 | 适用场景 |
|----------|----------|----------|
| `layui-icon-home` | 🏠 首页 | 仪表盘 |
| `layui-icon-app` | 📱 应用 | 通用菜单 |
| `layui-icon-user` | 👤 用户 | 用户管理 |
| `layui-icon-template` | 📋 模板 | 菜单管理 |
| `layui-icon-group` | 👥 组群 | 角色管理 |
| `layui-icon-auz` | 🔐 权限 | 权限管理 |
| `layui-icon-set` | ⚙️ 设置 | 系统管理/配置 |
| `layui-icon-console` | 💻 控制台 | 运维/服务器 |
| `layui-icon-engine` | ⚡ 引擎 | AI/分析 |
| `layui-icon-light` | ☀️ 太阳 | AI/智能 |
| `layui-icon-chart` | 📊 图表 | 统计/报表 |
| `layui-icon-log` | 📝 日志 | 操作日志 |
| `layui-icon-cart` | 🛒 购物车 | 电商/订单 |
| `layui-icon-file` | 📄 文件 | 文档/商品 |
| `layui-icon-folder` | 📁 文件夹 | 分类/目录 |
| `layui-icon-form` | 📝 表单 | 表单/订单 |
| `layui-icon-upload` | ⬆️ 上传 | 上传功能 |
| `layui-icon-export` | 📤 导出 | 导出功能 |
| `layui-icon-search` | 🔍 搜索 | 搜索功能 |
| `layui-icon-refresh` | 🔄 刷新 | 刷新功能 |
| `layui-icon-add-1` | ➕ 新增 | 新增按钮 |
| `layui-icon-edit` | ✏️ 编辑 | 编辑按钮 |
| `layui-icon-delete` | 🗑️ 删除 | 删除按钮 |
| `layui-icon-menu-fill` | ☰ 菜单 | 菜单管理 |
| `layui-icon-set-sm` | ⚙️ 小设置 | 配置项 |

---

**文档版本**: v1.1
**最后更新**: 2026-11-24
**适用版本**: django-layuix >= 1.4.2
