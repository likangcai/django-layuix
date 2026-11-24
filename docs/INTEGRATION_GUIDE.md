# 认证与权限桥接指南

版本：v1.0　适用版本：django-layuix 1.4.0+

## 1. 结论

【事实】核心桥接层只依赖 Django，不依赖 DRF 或 Django Ninja；DRF/Ninja 均为可选适配器。
【判断】认证/权限桥接应当是**通用能力**，不是 TestHub 专用。核心层不引入第三方 Web 框架，而是提供两个标准入口：

1. `django_layuix.integrations.auth`：通用认证桥接。
2. `django_layuix.rbac.permissions.has_permission()`：统一权限判定。

需要 DRF 的项目安装 DRF 后，可选用 `django_layuix.integrations.drf` 适配器；不需要 DRF 的项目继续使用现有 Django 原生视图。

## 2. 通用认证桥接

所有 RBAC API 的登录装饰器都委托给 `authenticate_request()`，它按优先级遍历已注册认证器：

| 认证器 | 默认优先级 | 说明 |
|---|---|---|
| `session` | 0 | Django Session |
| `settings:*` | 50+ | `LAYUI_RBAC_AUTHENTICATORS` 配置 |
| `simplejwt` | 50 | 仅在 DRF/SimpleJWT 已安装时注册 |
| `layuix_token` | 100 | 项目自带的 Bearer Token |

自定义认证器示例：

```python
# myproject/auth_bridge.py
def authenticate_by_header(request):
    token = request.META.get('HTTP_X_API_TOKEN')
    if not token:
        return None
    # 返回已认证的 Django User 对象
    return MyTokenService.verify(token)
```

```python
# settings.py
LAYUI_RBAC_AUTHENTICATORS = [
    'myproject.auth_bridge.authenticate_by_header',
]
```

也可以运行时注册：

```python
from django_layuix.integrations.auth import register_authenticator

register_authenticator(authenticate_by_header, name='my_header', priority=40)
```

## 3. 统一权限判定

```python
from django_layuix.rbac.permissions import has_permission

has_permission(request.user, 'project:create', request)
```

该函数对任意 Django User 对象生效，内部仍走 `UserProfile.has_perm()`，因此 RBAC1 继承、SSD/DSD、前置角色和角色级基数都保持一致。

## 4. DRF 适配器（可选）

安装 DRF 后：

```python
# settings.py
INSTALLED_APPS += ['rest_framework']

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'django_layuix.integrations.drf.SimpleJWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'django_layuix.integrations.drf.LayuiRBACPermission',
    ],
}
```

视图声明权限码：

```python
class ProjectViewSet(ModelViewSet):
    layui_permission = 'project:view'

    layui_permission_map = {
        'create': 'project:add',
        'update': 'project:edit',
        'destroy': 'project:delete',
    }
```

`LayuiRBACPermission.has_object_permission()` 默认复用同一判定；如需对象级规则，可在视图中覆盖。

## 5. TestHub 场景

TestHub 已有 SimpleJWT + DRF，无需改造成项目自带 Token：

1. 保留 `rest_framework_simplejwt` 作为前端登录方式。
2. 在 TestHub 的 DRF 视图使用 `LayuiRBACPermission`。
3. 将 TestHub 业务菜单写入 `sys_menu.permission`，例如 `testcase:add`。
4. 前端菜单/按钮由 `/admin/api/rbac/userinfo/` 与 `/admin/api/rbac/menus/frontend/` 提供。
5. 服务端由 `LayuiRBACPermission` 强制校验，前端隐藏只是体验优化。

这样两边共享同一套用户、角色和权限数据，但认证方式各自保留。

## 6. Django Ninja 适配器（可选）

Django Ninja 直接使用 Django `HttpRequest`，因此通用认证桥接天然可用。额外提供两个可选工具，且不在核心依赖中引入 Ninja：

```python
# ninja_project/api.py
from ninja import NinjaAPI
from django_layuix.integrations.ninja import LayuiNinjaAuth, ninja_permission_required

api = NinjaAPI(auth=LayuiNinjaAuth())

@api.get('/projects/')
@ninja_permission_required('project:view')
def list_projects(request):
    return {'user': request.user.username}
```

- `LayuiNinjaAuth`：复用认证器注册表（Session、项目 Token、SimpleJWT 等）。
- `ninja_permission_required(code)`：校验失败时抛 Ninja `HttpError`（401/403），同时支持同步与异步视图。
- Ninja 未安装时，导入该模块会给出明确 `ImportError`，核心启动不受影响。

【判断】不需要为 Ninja 单独维护第二套权限数据；它与 DRF、原生视图共用 `has_permission()` 与 RBAC3/RBAC4 引擎。
- 【本期不做】独立 Ninja 示例项目：当前指南已给出可直接复用的配置片段。
- 【本期不做】Ninja 对象级权限钩子：当前仅提供操作级权限装饰器。
- 【本期不做】SimpleJWT 适配独立拆包：当前按需导入，不增加核心依赖。

## 7. 是否需要引入 DRF

【判断】不需要为了桥接而把 DRF 引入核心依赖：

- 当前 django-layuix 是轻量 Django App，核心 API 用原生视图已足够。
- DRF 项目通过可选适配器接入，不污染非 DRF 用户。
- 统一的是认证和权限协议，不是 Web 框架。

只有当你的项目本身已经重度依赖 DRF 的 Serializer、ViewSet、Router 和 OpenAPI 时，才需要安装 DRF；django-layuix 不要求也不强制。
