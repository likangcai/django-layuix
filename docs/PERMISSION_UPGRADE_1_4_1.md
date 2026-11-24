# django-layuix 权限系统升级说明（1.4.1）

作者：影子（Yingzi）  版本：v1.0  日期：2026-11-24

## 结论（TL;DR）
【事实】1.4.0 已实现多父角色继承、SSD/DSD、前置角色、权限级互斥与 RBAC4 扩展。
【判断】1.4.1 不重写现有 RBAC，而是补齐旧需求中的契约兼容层与数据权限层，保持现有行为不变。
【已确认】上述兼容层、Scope 层与 UI 配套已在 1.4.1 交付，默认关闭或不改变既有展示。

---

## 1. 现有实现与需求映射

| 原要求 | 当前 1.4.0 实现 | 偏差处理 |
|---|---|---|
| RBAC1 单父 FK | `Role.parent_roles` 多父 DAG | 新增兼容 `parent` FK，保留 `parent_roles` |
| effective_permissions | 内部 `get_effective_permissions()` | 新增只读 API |
| SoDConstraint | `RoleMutex(kind=ssd)` | 新增 proxy 与独立端点 |
| check_sod_conflict | `validate_assignment()` 内含校验 | 新增公开函数与预校验 API |
| 数据权限 | 未实现 | 新增 Scope 层，默认不启用 |
| 角色树 UI | 平铺列表 + 多父选择器 | 增加层级展示与父字段兼容 |
| SSD 实时提示 | 提交时后端校验 | 增加预校验端点与前端提示 |

## 2. 兼容性原则

- 现有接口路径不改。
- 现有返回字段不删除、不改语义，只追加字段。
- 现有 `parent_ids` / `RoleMutex` / `/constraints/` 继续可用。
- 未配置 `scope_node` / `LAYUIX_SCOPE_HIERARCHY` 时，数据查询与界面均无可见变化。
- 现有迁移不回滚、不删列；本次只追加字段与新表/代理模型。

## 3. 分阶段计划

### 阶段 1：RBAC1 兼容层
- 修改：`rbac/models.py`、`rbac/engine.py`、`rbac/views.py`、`rbac/urls.py`
- 新增：迁移 `0006_scope_and_parent.py`
- 新增字段：`Role.parent`、`Role.scope_node`、`Role.scope_depth`
- 新增端点：`GET /roles/<id>/effective_permissions/`
- 兼容字段：角色列表/详情追加 `parent_id`、`children_ids`

### 阶段 2：RBAC2 SoD 兼容层
- 新增：`SoDConstraint` proxy 模型、`check_sod_conflict()`
- 新增端点：
  - `GET/POST /sod-constraints/`
  - `GET/PUT/DELETE /sod-constraints/<id>/`
  - `POST /sod-constraints/check/`
- 旧端点 `/constraints/mutex/` 保持不变

### 阶段 3：数据权限 Scope
- 新增：`rbac/scopes.py`
- 配置：`LAYUIX_SCOPE_HIERARCHY`、可选 `LAYUIX_SCOPE_TREE`
- 提供：`ScopedManager.for_user()`、`ScopedModelMixin`
- 业务模型通过 `SCOPE_FIELD` 显式声明，默认不参与过滤

### 阶段 4：UI 配套
- 修改：`role.html`、`user.html`、`constraints.html`
- 新增：角色页“数据作用域”折叠面板、树形层级标识
- 新增：用户角色选择冲突提示
- 新增：SoD 模板快捷入口

## 4. 迁移顺序

1. `0006_scope_and_parent.py`：添加 `Role.parent`、`scope_node`、`scope_depth`，幂等回填 `parent`。
2. `0007_sod_compat.py`：注册 `SoDConstraint` proxy 模型。

## 5. 验收口径

- 既有测试全部通过。
- 新增测试覆盖：继承权限来源、环路检测、SSD 冲突结构、Scope 过滤。
- 未配置新字段时，现有角色、菜单、API 与页面行为保持一致。

## 6. 后续增强项
- 【本期不做】字段级/行级表达式权限（ABAC）。
- 【本期不做】独立组织节点管理页面。
- 【本期不做】前端 Vue/React 权限 SDK。
