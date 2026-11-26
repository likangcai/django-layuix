# 数据管理模块指南

作者：影子（Yingzi）　版本：v1.0　日期：2026-11-26

## 结论（TL;DR）

【事实】1.4.9 在字典管理之外新增部门、岗位、地区、会员等级四个通用数据模块。
【判断】四类模块共用同一套数据管理布局、状态徽章、删除确认和权限判断，避免继续按页面复制 UI。
【事实】所有模块均接入字段白名单、页面权限和按钮权限，未注册权限默认拒绝。
【待确认】是否预置完整省市县地区数据。
【待确认】是否把部门与用户档案建立组织归属关系。
【待确认】是否增加批量导入导出。

## 1. 模块清单

| 模块 | 页面 | 页面权限 | 核心能力 |
|---|---|---|---|
| 字典管理 | `/static/layui/pages/dict.html` | `dict:view` | 字典与字典项 |
| 部门管理 | `/static/layui/pages/dept.html` | `dept:view` | 组织层级、负责人、联系方式 |
| 岗位管理 | `/static/layui/pages/position.html` | `position:view` | 岗位编码、排序、状态 |
| 地区管理 | `/static/layui/pages/region.html` | `region:view` | 省/市/县区/街道层级 |
| 会员等级 | `/static/layui/pages/member-level.html` | `member_level:view` | 积分门槛、折扣、图标 |

## 2. 公共层

前端公共资源：

- `/static/layui/css/data-admin.css`：分栏、树、工具栏、行操作、表单网格、响应式布局。
- `/static/layui/js/data-admin.js`：权限判断、树构建、后代节点、状态徽章、删除确认。
- `LayuiUI.dialog()`：统一弹窗皮肤、表单回填、按钮与最大高度。

后端公共约定：

- 列表返回 `{list, total}`。
- 成功响应统一 `{code, msg, data}`。
- 字段通过 `field_whitelisted()` 过滤。
- 创建、更新、删除分别使用 `add/edit/delete` 权限码。
- 层级模块禁止把自身或后代设为上级；存在下级时禁止删除。

## 3. 部门管理

字段：名称、编码、类型、上级部门、负责人、电话、邮箱、排序、状态、备注。

交互：

- 左侧树按层级展示部门。
- 右侧表格支持关键词、状态筛选。
- 行操作支持添加下级、编辑、删除。
- 新增/编辑使用统一弹窗，上级下拉自动排除自身和后代。

## 4. 岗位管理

字段：名称、编码、排序、状态、备注。

用于维护岗位字典，后续可扩展到用户任职关系、岗位职责和编制数量。

## 5. 地区管理

字段：名称、行政编码、层级、上级地区、区号、邮编、拼音、排序、状态、备注。

交互与部门一致：左侧树、右侧表格、添加下级、编辑和删除保护。

## 6. 会员等级

字段：名称、编码、最低积分、折扣比例、图标、排序、状态、说明。

折扣比例使用百分比：

- `100` 表示不打折
- `95` 表示 95 折
- 允许范围 `0~100`

## 7. API

```text
GET/POST  /admin/api/rbac/departments/
GET/POST  /admin/api/rbac/departments/create/
GET/PUT/DELETE /admin/api/rbac/departments/<id>/

GET/POST  /admin/api/rbac/positions/
GET/POST  /admin/api/rbac/positions/create/
GET/PUT/DELETE /admin/api/rbac/positions/<id>/

GET/POST  /admin/api/rbac/regions/
GET/POST  /admin/api/rbac/regions/create/
GET/PUT/DELETE /admin/api/rbac/regions/<id>/

GET/POST  /admin/api/rbac/member-levels/
GET/POST  /admin/api/rbac/member-levels/create/
GET/PUT/DELETE /admin/api/rbac/member-levels/<id>/
```

## 8. 初始化

执行：

```bash
python manage.py migrate
python manage.py init_menu
```

`init_menu` 会幂等补齐“数据管理”分组及五个子菜单，并把页面权限写入权限目录。
