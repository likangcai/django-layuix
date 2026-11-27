# 交互与代码审查报告
> 【历史文档】本文记录当时版本的状态，不代表 1.9.0 当前能力；文中“待确认/本期不做/未实现”多数已在后续版本落地。当前以 `DOCS_INDEX.md`、`CHANGELOG.md` 和专项指南为准。

日期：2026-11-27
范围：权限目录、角色管理、菜单管理、统一弹窗、近期后端 API
方法：静态审查 + 浏览器实测 + 定向/全量回归

## 结论（TL;DR）

【事实】本轮确认并修复了 12 类问题，其中长表单弹窗显示不全是确定性 Bug，已从“逐页补高度”改为“公共层统一吸底 + 自适应高度”。
【判断】当前前端交互问题已基本收敛；后端仍有 1 项 P0 安全架构项（Session 写接口的 CSRF 面）和若干 P1 项，需要单独排期。
【事实】全量测试 143 项通过，浏览器验证 1280×600 视口下用户/角色/菜单长表单均可滚动且按钮常驻可见。
【建议】下一轮优先处理 Session 写接口 CSRF、`bindFormOnce` 实例绑定和角色复制提权面。
【待确认】Session 写接口是否改为强制 Token 认证，需要与现有前端统一请求封装一起评估。

## 一、已修复问题

| 分类 | 严重度 | 位置 | 问题 | 修复 |
|---|---|---|---|---|
| Bug | 🔴 P0 | `static/layui/pages/menu.html`、`role.html` | 长表单弹窗固定高度导致内容被裁切，按钮不可见 | 自适应高度 + `80vh` 限高 + 公共重新居中 + 吸底操作栏 |
| Bug | 🔴 P0 | `static/layui/pages/role.html`、`user.html`、`config.html`、`server.html`、`example/*` | 表单按钮在内容底部，长表单必须滚动到底才能提交 | `openStandardDialog` 自动给按钮行加 `.layui-dialog-actions`，统一吸底 |
| Bug | 🟡 P1 | `static/layui/pages/dashboard.html`、`menu.html`、`role.html`、`server.html`、`example/store/pages/order.html` | 修改密码、图标选择、角色权限查看、服务器日志、订单详情仍使用固定 px 高度 | 改为 `auto`，由公共 `maxHeight` 兜底 |
| Bug | 🟡 P1 | `static/layui/js/common.js` | `ensureCurrentUser` 无并发缓存，失败时写空用户回全局 | 增加 in-flight Promise；失败不覆盖用户；保留旧值 |
| Bug | 🟡 P1 | `static/layui/pages/role.html` | 授权弹窗使用旧 `roleData` 全量 PUT，覆盖并发修改 | 仅提交 `menu_ids`、`scope_node`、`scope_depth` |
| Bug | 🟡 P1 | `rbac/views.py` | `role_batch_delete` 校验与删除不在同一事务，ID 可重复 | ID 去重；校验与删除纳入同一事务；返回请求数/删除数/级联数 |
| Bug | 🟡 P1 | `rbac/views.py` | 角色状态切换成功不刷新表格 | 成功分支调用 `loadTable()` |
| Bug | 🟡 P1 | `rbac/views.py` | `scope_node` 可写任意字符串 | 校验 `ScopeNode` 存在且启用 |
| Bug | 🟡 P1 | `rbac/permission_catalog_views.py` | 业务按钮权限码可撞内置权限码；`replace` 参数被忽略 | 生成前拒绝内置权限码冲突；读取 `replace` |
| Bug | 🟡 P2 | `rbac/views.py`、`permission_catalog_views.py` | `bool('false')` 为真，表单布尔值语义反转 | 统一 `parse_bool_value`，拒绝模糊值 |
| Bug | 🟡 P2 | `role.html`、`menu.html` | 表格初始化早于用户信息就绪，工具栏按空权限渲染 | 初始化统一走 `ensureCurrentUser()` |

## 二、仍未修复的项

| 分类 | 严重度 | 位置 | 问题 | 建议 |
|---|---|---|---|---|
| 安全 | 🔴 P0 | `rbac/views.py`、`rbac/permission_catalog_views.py`、`rbac/permissions.py` | 写接口普遍 `csrf_exempt`，Session 身份可绕过 CSRF；虽有 Origin 校验，仍不应把 `csrf_exempt` 作为默认 | 对 Session 写请求强制 CSRF Token；Token 认证与 Session 认证分流；保留 SameSite/Origin 双重校验 |
| Bug | 🟡 P1 | `common.js` 的 `bindFormOnce` | 回调按 filter 全局只绑定一次，闭包可能持有旧 `layero`；菜单/配置/服务器弹窗二次打开可能联动旧 DOM | 改为实例级绑定：在 `success(layero)` 内对当前 `layero` 绑定 change/click；不要复用全局回调 |
| 安全 | 🟡 P1 | `rbac/views.py` 的 `role_copy` | 可复制系统角色权限集，且未调用 `validate_assignable_menus()` | 禁止复制 `is_system` 角色；按调用者权限过滤菜单 |
| 安全 | 🟡 P1 | `permission_catalog_buttons_delete` | 只校验 `plugin_key=''`，可能删除其他插件生成的业务按钮 | 为权限目录生成的按钮增加持久标记；删除前校验标记与引用 |
| 性能 | 🟡 P2 | `role_list`、`permission_catalog_list` | 角色列表 N+1；权限目录无分页且 Python 端聚合 | `prefetch_related`；目录接口分页与数据库聚合 |
| Bug | 🟡 P2 | `openStandardDialog` | 重新居中只在 success 时执行一次，resize 或异步内容变高后不会更新 | 增加 resize/ResizeObserver 重新居中，并在关闭时清理监听 |
| 可维护性 | 🟡 P2 | `permission_registry`、`permission_catalog_views` | 核心权限集合分散硬编码 | 在 `permission_registry` 定义单一 `CRITICAL_PERMISSIONS` 来源 |

【待确认】权限目录生成的按钮是否需要迁移到独立标记字段，而不是继续复用 `plugin_key`。
【待确认】角色列表与权限目录接口的分页改造是否放入 1.8.0，避免影响现有前端调用。

## 三、验证证据

- 1280×600 视口：
  - 用户新增弹窗：`scrollHeight=735`、`clientHeight=480`、按钮行 sticky 且可见
  - 角色新增弹窗：`scrollHeight=773`、`clientHeight=480`、弹窗 `top=34`、`bottom=566`
  - 菜单新增弹窗：`scrollHeight=836`、`clientHeight=480`、按钮常驻可见
- 浏览器控制台：0 业务错误
- 全量测试：143 项通过
- `manage.py check`：0 issues
- `makemigrations --check`：无缺失迁移
- 文档扫描：0 错误、0 review

## 四、综合评分

**82 / 100**

评分说明：

- 前端交互与长表单体验已从 P0 修复到可交付状态；
- 近期权限/角色改造的功能缺陷已修复并有回归覆盖；
- 扣分主要来自尚未治理的 CSRF 架构面、`bindFormOnce` 实例绑定问题、角色复制提权面和权限目录分页/聚合性能。
