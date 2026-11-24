# 前后端分离权限 SDK 使用指南

版本：v1.0　适用版本：django-layuix 1.4.2+

## 结论（TL;DR）
【事实】1.4.2 提供框架无关的 `permission-client.js`，并分别提供 Vue 3 与 React 适配层。
【判断】前端只负责展示控制，最终安全边界仍是后端 `has_permission()` / `api_permission_required()` / ABAC 策略。
【事实】当前 SDK 随 Django 静态文件分发，示例中的 `/static/sdk/...` 为可直接复制的 ES Module 路径，不是已发布的 npm 包。
【待确认】是否后续补充 Svelte 与 Angular 适配器。
【待确认】是否把动态路由组件映射也纳入 SDK。
【待确认】是否发布独立 npm 包。

---

## 1. 统一权限数据端点

```text
GET /admin/api/rbac/frontend/permissions/
```

返回：

```json
{
  "code": 200,
  "data": {
    "user": {"id": 1, "username": "admin", "language": "zh-hans"},
    "permissions": ["user:add", "user:edit"],
    "roles": [{"id": 1, "code": "admin", "name": "管理员"}],
    "menus": [],
    "plugins": [],
    "scope_nodes": [],
    "abac_policies": []
  }
}
```

`abac_policies` 只返回策略元数据，不返回表达式，避免把后端规则泄露给前端。

## 2. 框架无关客户端

文件：`django_layuix/static/sdk/core/permission-client.js`

```js
import { createPermissionClient } from '/static/sdk/core/permission-client.js';

const permission = createPermissionClient({
  endpoint: '/admin/api/rbac/frontend/permissions/',
  credentials: 'include',
  token: localStorage.getItem('token'),
});

await permission.load();

permission.can('user:add');
permission.canAny(['user:add', 'user:edit']);
permission.menuTree();
permission.pluginManifest();
```

同域项目使用 Session Cookie；跨域项目传入 `token`，默认读取 `Authorization: Bearer <token>`。

## 3. Vue 3

文件：`django_layuix/static/sdk/vue/permission.js`

```js
import { createApp } from 'vue';
import { PermissionPlugin } from '/static/sdk/vue/permission.js';

const app = createApp(App);
app.use(PermissionPlugin, { endpoint: '/admin/api/rbac/frontend/permissions/' });
```

组件：

```vue
<button v-permission="'user:add'">新增用户</button>
```

组合式 API：

```js
import { usePermission } from '/static/sdk/vue/permission.js';

const { ready, can, menus } = usePermission();
```

路由守卫：

```js
import { createPermissionClient } from '/static/sdk/core/permission-client.js';
import { createPermissionGuard } from '/static/sdk/vue/permission.js';

const client = createPermissionClient();
router.beforeEach(createPermissionGuard(client));
```

在路由 `meta` 中声明权限：

```js
{ path: '/users', component: Users, meta: { permissions: 'user:view' } }
```

## 4. React

文件：`django_layuix/static/sdk/react/permission.js`

```jsx
import { PermissionProvider, usePermission, Can } from '/static/sdk/react/permission.js';

root.render(
  <PermissionProvider>
    <App />
  </PermissionProvider>
);
```

Hook：

```jsx
const { ready, can, canAny } = usePermission();
```

条件渲染：

```jsx
<Can perm="user:add">
  <button>新增用户</button>
</Can>
```

路由组件包装：

```jsx
const GuardedUsers = withPermission(UsersPage, 'user:view');
```

## 5. 后端仍必须校验

SDK 只隐藏按钮、控制路由，不能阻止用户直接调用 API。所有业务接口仍需：

```python
@api_permission_required('order:edit')
def order_update(request, pk):
    ...
```

ABAC 场景还需调用：

```python
from django_layuix.rbac.abac import evaluate_policies, filter_fields, filter_queryset

decision = evaluate_policies(request.user, 'edit', order)
visible = filter_fields(request.user, 'view', order, ['amount', 'cost'])
rows = filter_queryset(Order.objects.all(), request.user, 'view', 'store.Order')
```
