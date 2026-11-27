# 前后端分离权限 SDK 使用指南

版本：v2.0　适用版本：django-layuix 1.4.6+

## 结论（TL;DR）
【事实】1.4.6 提供框架无关的 `permission-client.js`，并提供 Vue 3、React、Svelte 与 Angular 适配层。
【判断】前端只负责展示控制，最终安全边界仍是后端 `has_permission()` / `api_permission_required()` / ABAC 策略。
【事实】当前 SDK 随 Django 静态文件分发，示例中的 `/static/sdk/...` 为可直接复制的模块路径。
【本期不做】发布独立 npm 包；自动把动态路由组件映射纳入 SDK。
【事实】1.4.7 提供 Angular standalone 启动助手、函数式路由守卫与核心 SDK TypeScript 声明。
【待确认】是否提供 Vue Router 与 React Router 的 SSR 预取示例。
【待确认】是否在 SDK 中内置权限刷新按钮与状态组件。
【待确认】是否提供路由权限映射的可视化检查工具。

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
    "user": {"id": 1, "username": "admin", "language": "zh-hans", "is_superuser": true},
    "permissions": ["user:add", "user:edit"],
    "roles": [{"id": 1, "code": "admin", "name": "管理员"}],
    "menus": [],
    "plugins": [],
    "scope_nodes": [],
    "abac_policies": []
  }
}
```

`abac_policies` 只返回策略元数据，不返回表达式；且仅超级管理员或拥有 `role:edit` 权限的用户会拿到非空列表，普通用户始终为空数组。

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

## 5. Svelte

文件：

```text
/static/sdk/svelte/permission.js
/static/sdk/svelte/Can.svelte
```

在根组件提供权限 store：

```svelte
<script>
  import { createPermissionStore, providePermission, createPermissionAction } from '/static/sdk/svelte/permission.js';
  const permission = createPermissionStore();
  providePermission(permission);
  const permissionAction = createPermissionAction(permission);
</script>

<button use:permissionAction={'user:add'}>新增用户</button>
```

条件组件：

```svelte
<script>
  import Can from '/static/sdk/svelte/Can.svelte';
</script>

<Can perm="user:view">
  <UserList />
</Can>
```

### 5.1 SvelteKit SSR 服务端预取

在 `+layout.server.js` 中使用框架提供的 `fetch`，让 Cookie、Bearer Token 与 X-Token 在服务端请求中自动转发：

```js
import { prefetchServerPermissions } from '/static/sdk/svelte/server.js';

export async function load(event) {
  return {
    permissionSnapshot: await prefetchServerPermissions(event)
  };
}
```

在 `+layout.svelte` 中把预取快照直接注入 store，避免 SSR 阶段的权限闪烁：

```svelte
<script>
  import { createPermissionStore, providePermission } from '/static/sdk/svelte/permission.js';
  export let data;
  const permission = createPermissionStore({ bootstrap: data.permissionSnapshot });
  providePermission(permission);
</script>
```

`refresh()` 会强制重新拉取；`invalidate()` 会在退出登录或切换 Token 后清空快照。

## 6. Angular

文件：

```text
/static/sdk/angular/permission.ts
```

模块或根组件中配置 endpoint：

```ts
import { PermissionService } from '/static/sdk/angular/permission.ts';

permissionService.configure({
  endpoint: '/admin/api/rbac/frontend/permissions/',
  credentials: 'include',
});
```

模板指令：

```html
<button [layuiPermission]="'user:add'">新增用户</button>
<button [layuiPermission]="['user:edit', 'role:edit']">编辑</button>
<button [layuiPermission]="['user:add', 'role:add']" [requireAll]="true">全部满足</button>
```

`PermissionService` 同时提供 `can / canAny / canAll / hasRole / menus / plugins / scopeNodes / abacPolicies / pagePermissions / buttonActions / permissionCatalog / canLoadPage`。

### 6.1 Angular standalone 启动

`/static/sdk/angular/standalone.ts` 提供 3 个能力：

```ts
import { bootstrapLayuiStandalone, layuiPermissionGuard } from '/static/sdk/angular/standalone';

bootstrapLayuiStandalone(AppComponent, {
  endpoint: '/admin/api/rbac/frontend/permissions/',
}, routes);
```

路由可以显式声明权限码，也可以走页面路径映射：

```ts
const routes: Routes = [
  {
    path: 'users',
    component: UserListComponent,
    canActivate: [layuiPermissionGuard],
    data: { permissions: 'user:view' },
  },
];
```

`layuiPermissionGuard` 会先加载权限快照，失败时自动重试一次；仍未通过则跳转 `/403`。

### 6.2 TypeScript 类型

`/static/sdk/core/permission-client.d.ts` 提供 `PermissionClientOptions`、`PermissionSnapshot` 与客户端方法类型，Angular/React/Vue 项目可直接获得类型提示。

## 7. 后端仍必须校验

SDK 只隐藏按钮、控制路由，不能阻止用户直接调用 API。所有业务接口仍需：

```python
@api_permission_required('order:edit')
def order_update(request, pk):
    ...
```

字段级响应优先使用统一白名单序列化器：

```python
from django_layuix.rbac.serializers import field_whitelisted

@api_login_required
@api_permission_required('order:view')
@field_whitelisted('store.Order')
def order_detail(request, pk):
    ...
```

`field_whitelisted()` 会根据 `API_FIELD_REGISTRY` 过滤字段；显式传入字段只能收窄，不能放大白名单。ABAC 字段策略可以进一步隐藏已注册字段。

ABAC 场景也可直接调用底层方法：

```python
from django_layuix.rbac.abac import evaluate_policies, filter_fields, filter_queryset

decision = evaluate_policies(request.user, 'edit', order)
visible = filter_fields(request.user, 'view', order, ['amount', 'cost'])
rows = filter_queryset(Order.objects.all(), request.user, 'view', 'store.Order')
```
