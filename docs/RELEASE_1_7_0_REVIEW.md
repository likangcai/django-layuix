# 1.7.0 软件生命周期评审报告
> 【历史文档】本文记录当时版本的状态，不代表 1.9.0 当前能力；文中“待确认/本期不做/未实现”多数已在后续版本落地。当前以 `DOCS_INDEX.md`、`CHANGELOG.md` 和专项指南为准。

作者：影子（Yingzi）　版本：v1.0　日期：2026-11-26

## 1. 结论（TL;DR）

【事实】本轮完成村/社区数据、Excel 导入导出、岗位任职有效期与主岗变更历史，并修复启动阶段查库告警。
【判断】地区数据达到 657848 条后，按层级分批写入、服务端分页和独立树接口是必要结构，不能继续全量下发。
【事实】岗位任职历史使用独立 `PositionAssignment` 表，保留主岗、起止日期、操作人和岗位名称快照。
【事实】CSV 继续保留，XLSX 通过 `openpyxl` 支持，导入导出均使用同一表头。
【待确认】是否扩展到网格/小区级数据。
【待确认】是否为任职历史增加批量导出。
【待确认】是否为调岗增加审批流或附件。

## 2. 需求与范围

| 项 | 内容 |
|---|---|
| 基线 | 1.6.0 |
| 目标版本 | 1.7.0 |
| 范围 | 村社区种子、Excel、岗位任职历史、scripts 打包、启动告警 |
| 验收 | 数据完整性、分页性能、导入导出、任职历史、启动日志、文档与提交 |

## 3. 实现记录

### 3.1 村/社区数据

- 新增 `china_villages.json.gz`，613792 条村/社区。
- 地区总量 657848 条：省 34、地 333、县 2847、街道 40842、村社区 613792。
- 新增 `update_villages_from_npm.py`，按街道编码匹配并生成 gzip 种子。
- `load_regions` 增加 `--include-villages`；默认不导入 61 万行。
- `LAYUI_RBAC_SEED_VILLAGES` 控制空库初始化是否包含村社区。
- 地区模型增加第 5 级，地区页增加层级筛选。
- 地区种子加载改为按层级 500 条分批写入，657848 行导入峰值内存约 600MB。
- 地区列表分页接口约 0.65 秒，树接口约 0.22 秒。

### 3.2 Excel 导入导出

- `pyproject.toml` 增加 `openpyxl>=3.1.0`。
- 导出支持 `format=csv|xlsx`；CSV 保持流式写入，XLSX 使用只写工作簿。
- 导入按扩展名/MIME 识别 CSV 与 XLSX，数字编码和日期单元格做规范化。
- 前端导出按钮打开 CSV/Excel 选择弹窗。
- 导入弹窗接受 `.csv` 与 `.xlsx`。

### 3.3 岗位任职有效期与历史

- 新增 `PositionAssignment`：
  - 用户、岗位、岗位名称快照
  - 主岗标记、生效日期、结束日期
  - 变更原因、操作人
- 用户创建/更新岗位时自动写入任职历史：
  - 新增岗位创建有效记录
  - 移除岗位关闭记录
  - 主岗变化关闭旧主岗并创建新主岗记录
- 新增 API：
  - `GET /admin/api/rbac/users/<id>/position-assignments/`
  - `POST /admin/api/rbac/position-assignments/<id>/end/`
- 用户行新增“任职记录”，可查看历史并结束任职。
- 结束主岗后自动选择下一条有效任职作为主岗。

### 3.4 启动告警与脚本打包

- `StoreConfig.ready()` 只注册 URL，菜单注册改为 `post_migrate`。
- `PluginConfig.ready()` 只注册插件类，插件元数据与菜单改为 `post_migrate`。
- `RbacConfig.ready()` 默认配置改为 `post_migrate`。
- entry point 插件发现改为 `post_migrate`。
- `MANIFEST.in` 包含 `scripts/*.py`、`scripts/*.md`、地区 JSON 与 GZ。
- wheel package-data 增加 `data/*.gz`。
- 新增 `scripts/README.md` 说明 sdist/wheel 边界。

## 4. 风险与修复

| 级别 | 风险 | 处理 |
|---|---|---|
| 🔴 | 61 万村社区一次性载入内存 | 按层级 500 条分批写入 |
| 🔴 | 村社区全量接口过大 | 服务端分页与层级筛选 |
| 🔴 | 迁移回填使用迭代器与预取冲突 | 改为普通遍历 |
| 🔴 | 任职历史与主岗不同步 | 统一由 `_sync_user_positions()` 写历史和 M2M |
| 🟡 | Excel 导出大表占用内存 | XLSX 使用只写工作簿，CSV 保持流式 |
| 🟡 | 启动阶段查库告警 | 全部改为 `post_migrate` |
| 🟡 | scripts 不随 wheel 安装 | sdist 包含脚本，wheel 只带种子和管理命令 |

## 5. 验证证据

| 验证项 | 结果 |
|---|---|
| 全量测试 | 139 项，138 通过、1 跳过 |
| `manage.py check` | 0 issues |
| `makemigrations --check` | 无缺失迁移 |
| 地区数据 | 657848 条，34/333/2847/40842/613792 |
| 地区分页 | 第 5 级 20 行，约 0.65 秒 |
| 地区树 | 约 0.22 秒 |
| Excel 导出 | XLSX 表头正确 |
| Excel 导入 | 成功创建岗位记录 |
| 任职历史 | 2 条有效记录，主岗 1 条 |
| 结束任职 | 结束日期写入，历史保留 |
| 启动日志 | 不再出现 ready 阶段数据库告警 |
| 浏览器控制台 | 0 业务错误 |
| 文档扫描 | 0 错误、0 review |

## 6. 回滚方案

1. 代码回退：`git revert <commit>`。
2. 迁移回退：回滚 `0019_position_assignment_history`、`0020_region_level_index`。
3. 地区回退：删除村社区行或执行 `load_regions --truncate` 仅保留基础种子。
4. 依赖回退：移除 `openpyxl` 并恢复 CSV-only 代码。

## 7. 发布检查清单

- [x] 需求与范围明确
- [x] 独立审查并修复问题
- [x] 全量测试通过
- [x] 文档扫描通过
- [x] 浏览器验收通过
- [x] 本地 Git 提交完成
