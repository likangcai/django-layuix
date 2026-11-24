# 新增功能快速上手示例

版本：v1.0　适用版本：django-layuix 1.4.2+

## 结论（TL;DR）
【事实】本文用最小可运行示例串起 1.4.1/1.4.2 新增能力：角色继承、SSD、数据范围、组织节点、ABAC 与前端 SDK。
【判断】所有新能力默认关闭或平级兼容；不配置新字段时，旧接口与旧页面行为保持不变。
【已确认】每个示例都可通过后台 UI 或 API 验证，详细语法见对应专项指南。
【已确认】已提供 `init_permission_demo` 一键命令和 `example/permission_demo/` 可复制应用。
【待确认】是否补充视频或交互式演示页面。
【待确认】是否把 demo app 发布为独立 pip 包。
【待确认】是否提供多租户版本的示例应用。

---

## 0. 准备环境

```bash
pip install django-layuix
cd example
python manage.py migrate
python manage.py init_menu
python manage.py init_demo_data
python manage.py runserver
```

后台地址：`http://127.0.0.1:8000/admin/`

默认管理员由 `init_data` 创建，默认 `admin / admin123`；已有数据库可用 `python manage.py changepassword admin` 重置。

## 1. RBAC1：角色继承

### 场景

`区域经理` 继承 `普通用户` 的菜单/按钮权限，用户分配 `区域经理` 后自动拥有两者权限。

### UI 操作

1. 进入「权限管理 → 角色管理」。
2. 新建角色 `普通用户`，勾选菜单权限。
3. 新建角色 `区域经理`，在「继承角色」中勾选 `普通用户`。
4. 点击「查看权限」：
   - 自有权限：当前角色直接分配。
   - 继承权限：来自 `普通用户`，只读。

### API 示例

创建父角色：

```http
POST /admin/api/rbac/roles/create/
```

```json
{
  "name": "普通用户",
  "code": "demo_base",
  "menu_ids": [2, 3],
  "status": true
}
```

创建子角色并继承：

```json
{
  "name": "区域经理",
  "code": "demo_manager",
  "parent_id": 12,
  "menu_ids": [4],
  "status": true
}
```

查看有效权限：

```text
GET /admin/api/rbac/roles/13/effective_permissions/
```

返回示例：

```json
{
  "code": 200,
  "data": {
    "role_id": 13,
    "role_name": "区域经理",
    "own": [{"id": 4, "name": "用户管理", "permission": "user:view"}],
    "inherited": [{"id": 2, "name": "菜单管理", "permission": "menu:view", "source_role_id": 12, "source_role_name": "普通用户"}],
    "all_permissions": ["menu:view", "user:view"]
  }
}
```

环路提交会被拒绝：

```json
{"parent_id": 13}
```

对角色 12 提交以上请求会返回 400。

## 2. RBAC2：SSD 互斥角色

### 场景

`制单员` 与 `审核员` 不能同时分配给同一用户。

### UI 操作

1. 进入「权限管理 → 约束管理」。
2. 创建互斥组：
   - 组名称：`制单/审核互斥`
   - 类型：`SSD 静态互斥`
   - 互斥角色：勾选 `制单员`、`审核员`
3. 进入用户编辑页，同时勾选两个角色。
4. 页面显示 SSD 冲突红字并阻止提交。

### API 示例

创建互斥组：

```http
POST /admin/api/rbac/sod-constraints/
```

```json
{
  "name": "制单/审核互斥",
  "role_ids": [21, 22],
  "description": "同一用户不能同时制单和审核"
}
```

预校验：

```http
POST /admin/api/rbac/sod-constraints/check/
```

```json
{
  "user_id": 5,
  "role_ids": [21, 22]
}
```

返回：

```json
{
  "code": 200,
  "data": {
    "allowed": false,
    "exempt": false,
    "conflicts": [
      {"type": "role", "constraint_name": "制单/审核互斥"}
    ]
  }
}
```

分配用户时同样会返回 400，并附带冲突信息。超级管理员豁免，但实际操作会记录审计日志。

## 3. 数据权限 Scope

### 场景

角色配置 `scope_node=east_region`、`scope_depth=1`，用户只能看到华东区域及其下一级节点的数据。

### 配置作用域层级

```python
# settings.py
LAYUIX_SCOPE_HIERARCHY = ['global', 'region', 'team']
LAYUIX_SCOPE_TREE = {
    'global': ['east_region', 'west_region'],
    'east_region': ['east_team_a', 'east_team_b'],
}
```

### UI 操作

编辑角色 → 展开「数据作用域（高级）」：

```text
作用域节点: east_region
向下层数:   1
```

预览会显示：

```text
该角色在 east_region 授予，向下覆盖 1 层
```

### 业务模型接入

```python
from django.db import models
from django_layuix.rbac.scopes import ScopedModelMixin


class Order(ScopedModelMixin, models.Model):
    SCOPE_FIELD = 'department'
    department = models.CharField(max_length=100)
    title = models.CharField(max_length=100)
```

业务 API 使用：

```python
orders = Order.objects.for_user(request.user)
```

未配置 `SCOPE_FIELD` 或角色未配置 `scope_node` 时，`for_user()` 返回原始查询集。

## 4. 组织节点管理

### 场景

用数据库维护组织树，代替只靠 settings 写死层级。

### UI 操作

进入「系统管理 → 组织节点」：

1. 新建根节点：`global / 全局`
2. 新建子节点：`east_region / 华东区域`，上级选择 `global`
3. 新建子节点：`east_team_a / 华东一组`，上级选择 `east_region`

### API 示例

```http
POST /admin/api/rbac/scope-nodes/
```

```json
{"code": "global", "name": "全局"}
```

```json
{"code": "east_region", "name": "华东区域", "parent_id": 1}
```

查看树：

```text
GET /admin/api/rbac/scope-nodes/
```

手动展开层级：

```python
from django_layuix.rbac.scopes import visible_scope_nodes

visible_scope_nodes('east_region', 1)
# {'east_region', 'east_team_a', 'east_team_b'}
```

## 5. ABAC 表达式权限

### 场景

金额大于 10000 的订单只有财务角色能查看。

### 快速创建策略

进入「权限管理 → ABAC 策略」：

```text
名称:     大额订单需财务角色
资源:     store.Order
动作:     view
字段:     （留空）
效果:     拒绝
表达式:   resource.amount > 10000 and 'finance' not in user.roles
```

### API 示例

```http
POST /admin/api/rbac/abac-policies/
```

```json
{
  "name": "大额订单需财务角色",
  "resource": "store.Order",
  "action": "view",
  "effect": "deny",
  "expression": "resource.amount > 10000 and 'finance' not in user.roles",
  "priority": 10
}
```

### 业务代码

```python
from django_layuix.rbac.abac import filter_queryset, filter_fields

rows = filter_queryset(Order.objects.all(), request.user, 'view', 'store.Order')
fields = filter_fields(request.user, 'view', 'store.Order', ['id', 'amount', 'cost'])
```

调试接口：

```http
POST /admin/api/rbac/abac-check/
```

```json
{
  "user_id": 5,
  "action": "view",
  "resource": "store.Order",
  "context": {"resource": {"amount": 20000}}
}
```

详细语法与更多模板见 [ABAC_GUIDE.md](ABAC_GUIDE.md)。

## 6. 前端权限 SDK

### 统一权限数据

```text
GET /admin/api/rbac/frontend/permissions/
```

一次返回：

```text
user / permissions / roles / menus / plugins / scope_nodes / abac_policies
```

### Vue 3

```js
import { createApp } from 'vue';
import { PermissionPlugin } from '@layuix/permission/vue';

const app = createApp(App);
app.use(PermissionPlugin, { endpoint: '/admin/api/rbac/frontend/permissions/' });
```

模板中：

```vue
<button v-permission="'user:add'">新增用户</button>
```

### React

```jsx
import { PermissionProvider, Can } from '@layuix/permission/react';

root.render(
  <PermissionProvider>
    <Can perm="user:add">
      <button>新增用户</button>
    </Can>
  </PermissionProvider>
);
```

详细适配器说明见 [FRONTEND_SDK_GUIDE.md](FRONTEND_SDK_GUIDE.md)。

## 7. Layui 2.13.9 表单兼容

```python
LAYUI_CONFIG = {
    'form_filter_disabled': False,  # 保持旧行为：disabled 字段参与取值
}
```

如需排除 disabled 字段：

```python
LAYUI_CONFIG = {
    'form_filter_disabled': True,
}
```

说明见 [COMPATIBILITY.md](COMPATIBILITY.md)。

## 8. 系统配置与 settings 变量

初始化/同步系统配置：

```bash
python manage.py init_menu
```

后台可动态管理 17 项 `sys_config`：

```text
系统管理 → 系统配置
```

settings 级变量示例：

```python
LAYUI_RBAC_MAX_ROLES_PER_USER = 0
LAYUI_RBAC_PREREQ_STRATEGY = 'auto_grant'
LAYUI_RBAC_DSD_STRATEGY = 'greedy'
LAYUIX_SCOPE_HIERARCHY = ['global', 'region', 'team']
TOKEN_EXPIRE_SECONDS = 86400
```

完整变量表见 [README.md](../README.md)。

## 9. 一键初始化与可复制 demo app

### 一键初始化全部示例数据

```bash
python manage.py migrate
python manage.py init_permission_demo
```

该命令幂等，重复执行不会创建重复数据。它会创建：

```text
角色继承：demo_base → demo_manager
SSD 互斥：demo_maker_checker_sod
组织节点：demo_global → demo_region → demo_team
数据范围：demo_sales(scope_node=demo_region, scope_depth=1)
ABAC 策略：大额订单拒绝、成本字段白名单
示例用户：demo_manager_user / demo_finance_user / demo_scope_user
示例订单：permission_demo 应用的 3 条订单
```

默认密码为 `Demo@2026`，可通过环境变量覆盖：

```powershell
$env:DEMO_PASSWORD='YourStrongPassword'
python manage.py init_permission_demo
```

### 可复制 demo app

完整示例应用位于：

```text
example/permission_demo/
```

复制到你的项目：

```bash
cp -r example/permission_demo /path/to/your/project/
```

注册应用：

```python
INSTALLED_APPS = [
    'django_layuix',
    'django_layuix.rbac',
    'permission_demo.apps.PermissionDemoConfig',
]
```

然后执行：

```bash
python manage.py migrate
python manage.py init_permission_demo
```

示例应用包含：

```text
models.py                         ScopedModelMixin 业务模型
views_api.py                      filter_queryset / filter_fields 示例
apps.py                           菜单与 API 路由自动注册
management/commands/...           示例订单数据命令
static/permission_demo/pages/     Layui 示例页面
README.md                         单独复制与运行说明
```

详见 [permission_demo/README.md](../example/permission_demo/README.md)。

## 10. 功能与示例对照表

| 功能 | 快速示例 | 详细文档 |
|---|---|---|
| 角色继承 | 第 1 节 | `RBAC3_GUIDE.md` |
| SSD 互斥角色 | 第 2 节 | `PERMISSION_UPGRADE_1_4_1.md` |
| 数据 Scope | 第 3 节 | `PERMISSION_UPGRADE_1_4_1.md` |
| 组织节点 | 第 4 节 | `PERMISSION_UPGRADE_1_4_1.md` |
| ABAC 表达式权限 | 第 5 节 | `ABAC_GUIDE.md` |
| Vue/React SDK | 第 6 节 | `FRONTEND_SDK_GUIDE.md` |
| Layui 2.13.9 兼容 | 第 7 节 | `COMPATIBILITY.md` |
| 配置变量 | 第 8 节 | `README.md` |
| 一键初始化示例 | 第 9 节 | `python manage.py init_permission_demo` |
| 可复制 demo app | 第 9 节 | `example/permission_demo/README.md` |
