# 文档索引与有效性说明
作者：影子（Yingzi）　版本：v1.0　日期：2026-11-27

## 1. 结论（TL;DR）
【事实】当前项目版本为 1.9.0；判断功能是否已实现，以 `CHANGELOG.md`、本索引和对应专项指南为准。
【判断】历史版本评审报告保留作演进记录，但其中“待确认/下一期”项多数已在后续版本落地，不能当作当前缺口。
【建议】新增功能说明只更新专项指南与 CHANGELOG，不再复制大段历史评审内容。
【待确认】是否将历史版本评审报告归档到 `docs/archive/` 子目录，需先确认外部链接引用情况。

## 2. 当前权威文档（1.9.0）

| 文档 | 状态 | 用途 |
|---|---|---|
| `CHANGELOG.md` | 权威 | 版本变更、已实现能力、破坏性变更 |
| `RELEASE_1_9_0_REVIEW.md` | 权威 | 1.9.0 生命周期评审、验证证据、回滚方案 |
| `TOKEN_AUTH_GUIDE.md` | 权威 | Token 认证、写接口强制 Token、跨域接入 |
| `PERMISSION_SYSTEM_GUIDE.md` | 权威 | RBAC 权限总体能力与边界 |
| `RBAC3_GUIDE.md` | 权威 | 角色继承、SSD/DSD、约束与强制鉴权 |
| `ABAC_GUIDE.md` | 权威 | ABAC 表达式、行级/字段级过滤 |
| `DATA_MANAGEMENT_GUIDE.md` | 权威 | 字典、部门、岗位、地区、会员等级 |
| `FRONTEND_COMPONENT_GUIDE.md` | 权威 | 设计 token、公共表格/弹窗、虚拟表格与分页 |
| `I18N_GUIDE.md` | 权威 | 中英文前端字典、Django 模板翻译 |
| `RELEASE_GUIDE.md` | 权威 | Tag 触发测试、构建与 PyPI 发布 |
| `COMPATIBILITY.md` | 权威 | Python/Django 支持矩阵 |
| `HOME_QUICK_LINKS_GUIDE.md` | 权威 | 首页快捷链接配置 |
| `THEME_SYSTEM_GUIDE.md` | 权威 | 深浅主题与广播机制 |
| `FRONTEND_MENU_GUIDE.md` | 权威 | 前后台菜单可见性 |
| `INTEGRATION_GUIDE.md` | 权威 | 认证桥接、DRF/Ninja 适配器 |
| `PLUGIN_GUIDE.md` | 权威 | 插件注册、菜单与 API 扩展 |
| `TESTHUB_INTEGRATION.md` | 权威 | TestHub 集成评估 |
| `AJAX_ADMIN_GUIDE.md` | 权威 | AJAX Admin 增强能力 |
| `FRONTEND_SDK_GUIDE.md` | 权威 | 前后端分离权限 SDK |

## 3. 历史文档（仅作演进记录）

以下文档记录当时版本的状态。其中的“待确认/本期不做/未实现”不表示 1.9.0 仍未实现：

| 文档 | 已由后续版本落地的典型项 |
|---|---|
| `PERMISSION_MENU_INTERACTION_REVIEW.md` | 权限目录集中管理按钮权限、角色数据范围并入授权弹窗、角色批量操作（1.8.0） |
| `CODE_REVIEW_2026_11_27.md` | Session 写接口强制 Token、实例级表单绑定、角色复制提权保护、权限来源字段、服务端分页（1.9.0） |
| `RELEASE_1_8_0_REVIEW.md` | 上述 1.9.0 三项待确认 |
| `RELEASE_1_4_5_REVIEW.md` | 虚拟表格列配置持久化（1.4.6） |
| `RELEASE_1_4_6_REVIEW.md` | Angular standalone 示例、内置按钮权限预注册、角色树精确回显（1.4.7） |
| `RELEASE_1_4_7_REVIEW.md` | 权限目录独立页面、内置权限码唯一键（1.6.0） |
| `RELEASE_1_4_8_REVIEW.md` | 部门/岗位/地区/会员等级集成（1.4.9） |
| `RELEASE_1_4_9_REVIEW.md` | 完整地区数据、部门岗位归属、导入导出与批量操作（1.5.0） |
| `RELEASE_1_5_0_REVIEW.md` | 街道/乡镇、Excel、用户多岗位（1.6.0/1.7.0） |
| `RELEASE_1_6_0_REVIEW.md` | 村/社区、Excel、任职有效期与主岗变更历史（1.7.0） |
| `RELEASE_1_7_0_REVIEW.md` | 网格/小区未实现；任职历史批量导出与审批流仍未实现 |
| `PERMISSION_UPGRADE_1_4_1.md` | 表中“数据权限 未实现”指 1.4.0 基线；1.4.1 已新增 Scope 层 |

## 4. 当前仍未实现/待确认（截至 1.9.0）

| 项 | 状态 | 说明 |
|---|---|---|
| 繁体中文 / 日语 | 未实现 | 需同时扩展菜单字段、前端字典与用户偏好 |
| 多租户隔离 | 明确不做 | 权限系统指南与 RBAC3 指南均已注明 |
| OAuth2 / OpenID Connect 服务端 | 明确不做 | Token 指南注明 |
| 插件热插拔与运行时卸载 | 明确不做 | 插件指南注明 |
| 【待确认】网格/小区级地区数据 | 待确认 | 当前地区到村/社区级 |
| 【待确认】任职历史批量导出、调岗审批流/附件 | 待确认 | 数据管理指南注明 |
| API 中文文案英文化 | 待确认 | 需先用 `gettext_lazy` 包裹后端文案 |
| 高对比度无障碍主题 | 待确认 | 主题指南注明 |
| 【待确认】设备维度 Token 管理页 | 待确认 | Token 指南注明 |
| 【待确认】职级管理独立实体 | 未实现 | 当前用会员等级承载，不等同于独立职级体系 |

## 5. 去重原则

- 同一能力只在一个专项指南中维护详细说明；其他文档只保留链接。
- 版本评审报告不回头改写历史事实，只增加“历史文档”提示并链接到本索引。
- README 的详细文档索引链接本文件，不再重复列出历史评审报告。
