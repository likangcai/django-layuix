# 第三方插件体系

版本：v2.0　适用版本：django-layuix 1.4.2+

## 1. 插件组成

| 部分 | 必需 | 说明 |
|---|---|---|
| Django App | 是 | 加入 `INSTALLED_APPS`，可带 models/migrations |
| `PluginConfig` 子类 | 是 | 统一元数据、校验、菜单注册与生命周期钩子 |
| 菜单与按钮权限 | 否 | 在 `plugin_menus` / `plugin_buttons` 中声明 |
| API 路由 | 否 | 通过 `site.get_urls` 补丁注入 |
| entry point | 否 | 独立 pip 包发布后自动被系统发现 |

## 2. 项目内插件示例

```python
# myapp/apps.py
from django_layuix.plugins import PluginConfig

class MyAppConfig(PluginConfig):
    name = 'myapp'
    label = 'myapp'

    plugin_key = 'my_crm'
    plugin_name = 'CRM 插件'
    plugin_version = '1.0.0'
    plugin_description = '客户与商机管理'
    plugin_api_prefix = '/admin/api/my_crm/'
    plugin_menu_path = '/mycrm/customers'
    plugin_dependencies = ('requests>=2.0',)
    min_layuix_version = '1.4.2'

    plugin_menus = [
        ('CRM 管理', 'layui-icon-component', '/mycrm/customers', 2, 1, None),
    ]
    plugin_buttons = [
        ('新增客户', 'CRM 管理', 'mycrm:add', 1),
    ]

    def on_enable(self):
        print('CRM enabled')

    def on_disable(self):
        print('CRM disabled')
```

```python
# settings.py
INSTALLED_APPS += ['myapp.apps.MyAppConfig']
```

执行 `python manage.py migrate && python manage.py init_menu` 即可。

## 3. 独立 pip 包插件（entry point）

第三方包在自己的 `pyproject.toml` 中声明：

```toml
[project.entry-points."django_layuix.plugins"]
my_crm = "my_crm.plugin:MyCrmPluginConfig"
```

安装该包后，django-layuix 启动时会自动：

1. 加载 `MyCrmPluginConfig`；
2. 校验依赖与版本；
3. 写入 `sys_plugin_registry`（`source='entry_point'`）；
4. 若依赖满足，自动注册声明的菜单与按钮权限。

> 注意：entry point 负责“发现与元数据注册”。若插件包含模型、迁移或需要完整的 Django App 生命周期，仍需把对应 App 加入 `INSTALLED_APPS`。

## 4. 版本与依赖校验

`plugin_dependencies` 支持 `package`、`package>=1.0`、`package==1.0` 等常见写法；`django-layuix` 与 `django_layuix` 等价。

`min_layuix_version` 用于声明最低 django-layuix 版本。

校验失败时：

- 插件在 `sys_plugin_registry.is_active` 被置为 `False`；
- 原因写入 `validation_error`；
- `on_enable()` 不会被调用；
- 系统不会因插件异常而拒绝启动。

## 5. 启用/停用

Django Admin「插件注册」提供 `is_active` 开关：

- 由停用改为启用时调用 `on_enable()`；
- 由启用改为停用时调用 `on_disable()`；
- 状态变化写入数据库，跨进程生效；
- `list_plugins()` 只返回启用且校验通过的插件。

也可编程调用：

```python
from django_layuix.rbac.plugins import set_plugin_active, unregister_plugin

set_plugin_active('my_crm', False)
unregister_plugin('my_crm')
```

## 6. API 路由注入

不要在根 `urls.py` 写业务 API，否则可能被 `/admin/` 的 catch-all 拦截：

```python
from django.contrib.admin import site
from django.urls import path, include

original = site.get_urls
def patched():
    return [path('api/my_crm/', include('my_crm.urls'))] + original()
site.get_urls = patched
```

## 7. 前端插件清单接口

```http
GET /admin/api/rbac/plugins/manifest/
```

返回每个启用插件的：

- 基础元数据：`key/name/version/api_prefix/menu_path`
- `menus`：该插件的菜单树（按 `plugin_key` 聚合）
- `permissions`：该插件的权限码列表

分离前端可据此动态挂载路由与按钮权限；服务端仍需在业务 API 上使用 `api_permission_required`。

## 8. 数据库表

| 表 | 用途 |
|---|---|
| `sys_plugin_registry` | 插件元数据、来源、依赖、校验错误、启停状态 |
| `sys_menu.plugin_key` | 菜单/按钮归属的插件标识 |

## 9. 约束

- 插件 API 必须自行挂 `api_permission_required`，否则只有登录校验。
- 插件菜单 `path` 若是业务路径，SPA 外壳的 `MENU_PATH_MAP` 需同步映射，或由前端自行映射。
- 插件带模型时仍需 Django 迁移；插件系统不是热插拔，状态变更需刷新进程内路由缓存。
