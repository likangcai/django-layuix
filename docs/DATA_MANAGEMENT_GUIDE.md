# 数据管理模块指南

作者：影子（Yingzi）　版本：v1.1　日期：2026-11-26

## 结论（TL;DR）

【事实】1.5.0 在字典管理之外提供部门、岗位、地区、会员等级四个通用数据模块。
【判断】四类模块共用同一套数据管理布局、状态徽章、删除确认、导入导出和批量操作，避免继续按页面复制 UI。
【事实】所有模块均接入字段白名单、页面权限和按钮权限，未注册权限默认拒绝。
【事实】地区模块内置 3214 条官方省、地、县数据，并提供民政部官方数据更新脚本。
【待确认】是否预置街道/乡镇级数据。
【待确认】是否把岗位任职关系扩展到用户多岗位。
【待确认】是否增加 Excel 格式导入导出。

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

`init_menu` 会幂等补齐“数据管理”分组及五个子菜单，并把页面权限写入权限目录。地区表为空时会自动导入内置省市县种子。

## 9. 导入导出

四个数据页面表格顶部统一提供：

- 导入 CSV
- 导出 CSV
- 批量启用
- 批量停用
- 批量删除

导入方式：

- `upsert`：按 code 新增并更新同编码记录
- `insert`：仅新增，已存在编码跳过

CSV 编码必须为 UTF-8；表头使用系统导出格式。

## 10. 用户部门岗位

用户档案新增：

- `department`：所属部门
- `position`：所属岗位

用户新增/编辑弹窗可选择启用状态的部门和岗位；用户列表展示部门与岗位名称。部门/岗位停用后不再出现在新分配选项中。

## 11. 官方地区数据更新

内置种子：

```text
django_layuix/rbac/data/china_regions.json
```

抓取官方数据：

```bash
python scripts/update_regions_from_mca.py --dry-run
python scripts/update_regions_from_mca.py
```

写入数据库：

```bash
python example/manage.py load_regions --truncate
```

或一步完成：

```bash
python scripts/update_regions_from_mca.py --apply
```

来源说明：

- 民政部国家地名信息库公开接口
- `maxLevel=3`，覆盖省、地、县三级
- 脚本会校验数据量、重复编码和层级分布，异常时拒绝覆盖
- `--truncate` 会删除现有地区记录，执行前应确认没有自定义地区数据
