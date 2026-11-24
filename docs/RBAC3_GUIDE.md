# RBAC3 权限体系使用指南

版本：v1.0　适用版本：django-layuix 1.4.1+

## 结论（TL;DR）
【事实】RBAC3 内核统一由 `rbac/engine.py` 计算继承、约束与有效权限。
【判断】所有新能力均通过追加字段或端点提供，旧接口行为保持不变。
【本期不做】多租户隔离、字段级权限与 ABAC；数据行级范围见 `PERMISSION_UPGRADE_1_4_1.md`。

---

## 1. 能力总览

| 等级 | 能力 | 本项目实现 |
|---|---|---|
| RBAC0 | 用户—角色—权限 | 原有 `sys_user` / `sys_role` / `sys_menu` |
| RBAC1 | 角色继承 | `Role.parent_roles` 多父节点 DAG，权限沿父链展开 |
| RBAC2 | 约束 | SSD/DSD 互斥、前置角色、角色人数上限、用户角色数上限 |
| RBAC3 | RBAC1 + RBAC2 | 上述能力叠加，权限判定统一走 `rbac/engine.py` |
| RBAC4（项目扩展） | RBAC3 + 权限级互斥 + Token + 插件化 | 见 `docs/TOKEN_AUTH_GUIDE.md`、`docs/PLUGIN_GUIDE.md` |

【判断】无继承、无约束时，行为与升级前完全一致：未配置 DSD 时默认激活全部已分配角色。

## 2. 升级与迁移

```bash
python manage.py migrate django_layuix_rbac
python manage.py init_menu
python manage.py collectstatic --noinput
```

`0002_rbac3.py` 与 `0003_rbac4_extensions.py` 仅新增字段与表，不删列；回滚可执行：

```bash
python manage.py migrate django_layuix_rbac 0001
```

> 回滚前请先清空互斥组、前置角色及角色继承关系，否则相关配置会被删除。

## 3. 配置

系统配置键 `rbac_max_roles_per_user` 控制全局角色数上限，`0` 表示不限；也可在 `settings.py` 中配置 `LAYUI_RBAC_MAX_ROLES_PER_USER` 作为兜底。

```python
LAYUI_RBAC_MAX_ROLES_PER_USER = 0
```

角色级上限在「角色管理 → 人数上限」中设置，留空或 `0` 表示不限。

RBAC4 新增两个策略配置：

| 配置键 | 可选值 | 默认 | 说明 |
|---|---|---|---|
| `rbac_prerequisite_strategy` | `auto_grant` / `reject` | `auto_grant` | 缺少前置角色时自动补齐，或直接拒绝分配 |
| `rbac_dsd_strategy` | `greedy` / `explicit` | `greedy` | 贪心激活无冲突角色集，或仅激活一个角色由前端显式切换 |

## 4. 典型场景

### 4.1 角色继承（RBAC1）

「经理」继承「员工」后，只分配经理的用户自动获得员工的菜单与权限码。支持多继承，创建/编辑时会自动检测继承环。

### 4.2 静态职责分离（SSD）

在「约束管理」创建 SSD 互斥组，例如「出纳 / 会计」。此后任何用户都不能同时拥有这两个角色；若某角色继承了互斥组中的角色，同样会被拒绝。

### 4.3 前置角色

配置「经理 需要 员工」后，给用户分配经理时会自动补上员工角色；形成环的前置关系会被拒绝。

### 4.4 动态职责分离（DSD）

DSD 允许同时分配互斥角色，但同一会话只能激活其一。系统在登录/无显式选择时按角色 ID 顺序贪心选择不冲突的角色集合；可在「约束管理 → 当前会话激活角色」中切换。

### 4.5 人数限制

角色 `max_users=1` 时，第二人分配会被拒绝；全局 `rbac_max_roles_per_user` 控制单个用户最多角色数。

## 5. API

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/admin/api/rbac/constraints/` | 互斥组、前置角色与全局上限 |
| POST | `/admin/api/rbac/constraints/mutex/` | 创建互斥组（kind=ssd/dsd） |
| DELETE | `/admin/api/rbac/constraints/mutex/<id>/` | 删除互斥组 |
| POST | `/admin/api/rbac/constraints/prerequisite/` | 创建前置角色 |
| DELETE | `/admin/api/rbac/constraints/prerequisite/<id>/` | 删除前置角色 |
| GET/POST | `/admin/api/rbac/active-roles/` | 查询/切换当前会话激活角色 |

角色 API 新增 `parent_ids`、`max_users` 字段；用户 API 的 `role_ids` 会经过约束校验，失败时返回 `code=400` 与中文原因。

## 6. 服务端强制鉴权

以下写接口已挂权限校验，不再依赖前端按钮隐藏：

- 菜单：`menu:add` / `menu:edit` / `menu:delete`
- 角色：`role:add` / `role:edit` / `role:delete` / `role:copy`
- 用户：`user:add` / `user:edit`

管理员账号（`admin`）、超级管理员及拥有启用 `admin` 角色的用户拥有全域权限。普通角色需由管理员在「角色管理」中分配对应按钮权限。

## 7. 验收与测试

```bash
python manage.py test django_layuix.rbac
```

覆盖：继承授权、继承环、SSD 直接/间接冲突、前置自动补齐、前置环、角色人数上限、DSD 激活、激活角色权限隔离、后端装饰器 403、角色继承创建 API、SSD 拦截 API、约束与激活角色 API。

## 8. 已知边界

- 【本期不做】多租户隔离、字段/行级权限、ABAC。
- 权限级互斥已支持：在互斥组中同时选择“互斥角色”和“互斥权限”即可，校验基于继承展开后的有效权限。
- 继承展开按请求实时计算，角色数量极大时建议评估物化路径缓存。
- 前置角色策略与 DSD 策略可通过系统配置切换，详见第 3 节。
