# 数据管理模块指南

作者：影子（Yingzi）　版本：v1.3　日期：2026-11-26

## 结论（TL;DR）

【事实】1.7.0 在字典管理之外提供部门、岗位、地区、会员等级四个通用数据模块。
【判断】四类模块共用同一套数据管理布局、状态徽章、删除确认、CSV/Excel 导入导出和批量操作，避免继续按页面复制 UI。
【事实】所有模块均接入字段白名单、页面权限和按钮权限，未注册权限默认拒绝。
【事实】地区模块内置 657848 条数据，其中省 34、地 333、县 2847、街道/乡镇 40842、村/社区 613792。
【事实】用户档案支持主岗 + 兼任岗位多选，任职有效期与主岗变更历史写入 `PositionAssignment`。
【待确认】是否扩展到网格/小区级数据。
【待确认】是否为任职历史增加批量导出。
【待确认】是否为岗位任职增加附件或调岗审批流。

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

用于维护岗位字典。用户档案通过 `position` 保存主岗，通过 `positions` 保存兼任岗位；用户列表返回 `position_ids` 与 `position_names`，新增/编辑弹窗支持主岗和兼任岗位多选。

任职有效期与历史由 `PositionAssignment` 保存：

- `start_date`：生效日期
- `end_date`：结束日期，空表示当前有效
- `is_primary`：是否主岗
- `changed_by`：操作人
- `change_reason`：变更原因

用户列表行操作“任职记录”可查看历史并结束当前任职。结束主岗时会自动选择下一条有效任职作为主岗；删除岗位时主岗置空、兼任关系移除，历史保留岗位名称快照。

## 5. 地区管理

字段：名称、行政编码、层级、上级地区、区号、邮编、拼音、排序、状态、备注。

数据规模：

- 总计 657848 条
- 省级 34
- 地级 333
- 县级 2847
- 街道/乡镇 40842
- 村/社区 613792

交互与部门一致：左侧树、右侧表格、添加下级、编辑和删除保护。地区列表使用服务端分页，树接口单独加载省、市及直辖市县区；街道和村社区可通过层级筛选、搜索和逐级节点定位。

街道与村社区数据来源为 `china-division` 整理的统计局行政区划，分别保存在 `china_streets.json` 和 `china_villages.json.gz`。更新命令：

```bash
python scripts/update_streets_from_npm.py --dry-run
python scripts/update_streets_from_npm.py
python scripts/update_villages_from_npm.py --dry-run
python scripts/update_villages_from_npm.py
```

村社区默认不参与 `init_menu` 初始化，避免新安装导入 61 万行；需要完整数据时执行：

```bash
python manage.py load_regions --include-villages
```

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
GET       /admin/api/rbac/regions/tree/
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

`init_menu` 会幂等补齐“数据管理”分组及五个子菜单，并把页面权限写入权限目录。地区表为空时默认导入 44056 条省市县街道种子；设置 `LAYUI_RBAC_SEED_VILLAGES=True` 可一并导入村社区。已有地区数据时可执行：

```bash
python manage.py load_regions --truncate
python manage.py load_regions --truncate --include-villages
```

## 9. 导入导出

四个数据页面表格顶部统一提供：

- 导入 CSV / Excel
- 导出 CSV / Excel
- 批量启用
- 批量停用
- 批量删除

导入方式：

- `upsert`：按 code 新增并更新同编码记录
- `insert`：仅新增，已存在编码跳过

CSV 编码必须为 UTF-8；XLSX 读取首个工作表。表头使用系统导出格式。

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
