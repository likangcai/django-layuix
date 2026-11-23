# 更新日志 (Changelog)

所有对 django-layuix 项目的更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [Unreleased]

### ✅ 名称统一与 RBAC4 扩展 (2026-11-23)

- ✅ **统一分发名为 `django-layuix`** — 文档、仓库/ Issue 链接、默认快捷链接、代码注释、Locale 头部全部更正
- ✅ **应用标签更正** — `django_layui_rbac/ops` → `django_layuix_rbac/ops`，提供 `rename_app_labels` 命令升级旧库
- ✅ **Token 认证接入 API** — `api_login_required` 支持 Bearer Token，满足纯跨域前端调用
- ✅ **RBAC4 扩展** — 前置/DSD 策略可配、权限级互斥、插件注册契约与 ops 标准插件
- ✅ **Tag 自动发布** — 推送 `v*` Tag 后自动测试、构建并发布到 PyPI，详见 `docs/RELEASE_GUIDE.md`
- ✅ **第三方插件体系** — `PluginConfig` 基类、entry_points 自动发现、版本/依赖校验、启停钩子、Admin 开关、前端插件清单接口
- ✅ **决策确认** — RBAC4 称谓、TestHub 用户模型迁移、Redis 共享缓存、Gitee 仓库链接均已按用户确认更新

### 🔧 示例 App 全面重构 (2026-06-09)

#### store 示例应用改用 Layui 前端 CRUD

- ✅ **废弃 Django admin 原生页面** — store 的增删改查改为 `Layui 表格 + layer.open 弹窗 + REST API` 模式
- ✅ **新增 REST API 视图** — Category/Product/Order 三个模型的完整 CRUD 接口（`store/views_api.py`）
- ✅ **新增 Layui 前端页面** — `category.html` / `product.html` / `order.html`，使用 Layui table 渲染列表
- ✅ **新增/编辑弹窗仅含「返回」「保存」按钮** — 其他原生按钮全部移除
- ✅ **菜单路径改为指向静态页面** — `/static/store/pages/*.html`

#### 🐛 Bug 修复

- ✅ **修复 API 路由被 `catch_all_view` 拦截** — 改为通过 `site.get_urls` 补丁注入 admin site 内部
- ✅ **修复分页总数显示错误** — `data: list + page.count` 模式下 Layui 忽略 `count`，改为 `url` 服务端分页模式
- ✅ **修复按钮权限变为孤儿菜单** — 6 个旧按钮 `parent=None`，已删除并由 `register_menus` 正确重建
- ✅ **修复全部 API 返回 UTC 时间而非本地时间** — `USE_TZ=True` 时 Django 以 UTC 存储时间，但代码直接用 `.strftime()` 未做时区转换
  - `example/store/views_api.py`：新增 `fmt_time()` 辅助函数，替换所有 `strftime()` 调用
  - `django_layuix/rbac/views.py`：菜单/角色/用户/日志/配置共 7 处修复
  - `django_layuix/ops/views.py`：服务器列表 1 处修复

#### 📚 文档更新

- ✅ **`docs/MENU_EXTENSION_GUIDE.md`** 完全重写 — 包含新建 app 的完整三步模板、常见问题排查
- ✅ **错误排查章节** — 分页问题、孤儿菜单、路由拦截、弹窗按钮等问题的根因与修复方案
- ✅ **README.md 优化** — 修复"25种主题"为"深色/浅色双模式"；添加缺失的 `FRONTEND_MENU_GUIDE.md` 索引；删除与"快速开始"重复的"配置项目"章节（去重 64 行）
- ✅ **删除旧的 `修复记录.txt`** — 内容已合并到 CHANGELOG.md

### 🎨 重大重构 (2026-05-07)

#### 主题系统全面升级：28主题 → 深色/浅色双模式
- ✅ **移除冗余的28种预设主题** - 简化为深色/浅色双模式设计
  - 删除 `themes.py` 中的旧主题定义和生成逻辑
  - 清理 `models.py` 中 theme 字段的 choices（仅保留深色/浅色）
  - 移除前端的多主题选择器和相关代码
  - **性能提升**: 减少80%的CSS文件和JavaScript代码

#### 新增向后兼容层
- ✅ **主题规范化函数** (`normalize_theme`, `get_display_theme`)
  - 自动将新格式 `'dark'`/`'light'` 转换为数据库值 `'默认深色'`/`'默认浅色'`
  - 支持旧版数据自动降级处理
  - API 接口同时接受新旧两种格式

#### 文档全面更新
- ✅ **THEME_SYSTEM_GUIDE.md** - 从"28主题使用指南"重写为"深色/浅色双模式系统指南"
  - 更新技术架构说明（CSS变量驱动）
  - 添加完整的升级迁移指南
  - 提供详细的API接口文档
  - 包含颜色规范、最佳实践、测试清单

---

### 🐛 Bug 修复 & 功能优化 (2026-05-07)

#### 菜单图标显示修复
- ✅ **目录菜单图标不显示** - 修复左侧菜单栏目录（一级/二级菜单）无图标问题
  - 根因：`renderDirectory()` 函数未渲染 `icon` 字段
  - 修复：添加 `<i class="layui-icon menu-dir-icon">` 图标元素
  - 新增 CSS 样式 `.menu-dir-icon`（15px，次要文字颜色）

#### 系统配置功能完善
- ✅ **system_description 未展示** - 修复管理后台底部不显示系统描述
  - 改用 JS 动态加载配置到 footer（避免 iframe 布局裁剪）
  - 同时支持 system_description / system_version / copyright 动态显示

- ✅ **登录页 logo_icon 配置无效** - 修复登录页图标无法通过数据库配置修改
  - 新增公开 API `/admin/api/rbac/system/public-config/`（无需登录）
  - 登录页 JS 动态获取并应用：system_name / logo_icon / logo_url / favicon / version / copyright / login_bg_*

- ✅ **login_bg_image 上传后登录页未生效**
  - 根因1：模板内联 `background: transparent !important` 覆盖 JS 设置的背景
  - 根因2：之前逻辑不严谨，只需 image 有值就显示（忽略 type）
  - 修复：
    1. 移除 CSS `!important` 强制透明
    2. **严格按5条业务规则实现**：
       - type=gradient → 渐变背景 + ✨ 粒子飘动（始终保留粒子）
       - type=color + value有值 → 纯色背景 + 无粒子
       - type=image + image有值 → 全屏图片 + 无粒子
       - type必须是字符串且仅gradient/color/image有效
       - 异常值/条件不满足 → 默认渐变+粒子（不做处理）

- ✅ **系统配置初始化缺失** - 修复 `python manage.py init_menu` 不创建完整配置项
  - 补全 3 个登录页背景配置：`login_bg_type` / `login_bg_value` / `login_bg_image`
  - `AppConfig.ready()` 自动检测并补全缺失配置项（幂等操作）

#### 图片预览功能修复
- ✅ **编辑模式图片预览无法点击**
  - 根因：`setCurrentValue()` 使用 `.text()` 设置纯文本，非可点击链接
  - 修复：改用 `.html()` 添加 `.preview-link` 可点击样式

#### UI 样式优化
- ✅ **登录页版权信息颜色过淡** - 从 60% → 95% 透明度 + 增强阴影
- ✅ **菜单收起/展开图标优化** - 尺寸缩小至 20px + 移至右侧

#### 国际化修复
- ✅ **登录按钮"登录中"显示原始键名** - 修复 `login.loading` 翻译缺失
  - 根因1：中文翻译键拼写错误 `login.logging` ≠ `login.loading`
  - 根因2：英文完全缺少该翻译键
  - 修复：统一为 `login.loading`，中文 `'登录中...'` / 英文 `'Logging in...'`

#### 数据模型清理
- ✅ **删除 name_zh_hant（繁体中文）字段**
  - Menu 模型移除该字段
  - `get_name_by_lang()` 移除繁体映射
  - `init_menu.py` 创建菜单时不再传入该字段
  - `0001_initial.py` 迁移文件同步更新（从源头删除）
  - 删除冗余的 `0002_remove_menu_name_zh_hant.py`

#### UserProfile theme 字段精简
- ✅ choices 从 27 个旧主题精简为 2 个（默认深色/默认浅色）
- ✅ `0001_initial.py` 同步更新

---

### 📝 本次修改文件清单（源代码 django_layuix/）

| 文件路径 | 修改内容 |
|----------|----------|
| `rbac/models.py` | 删除 name_zh_hant 字段 + get_name_by_lang() 精简 |
| `rbac/views.py` | 新增 public_config 公开 API（含 login_bg_*） |
| `rbac/urls.py` | 注册 /system/public-config/ 路由 |
| `rbac/apps.py` | 新增 _ensure_default_configs() 自动初始化 12 个配置项 |
| `rbac/migrations/0001_initial.py` | 移除 name_zh_hant + theme choices 精简为 2 个 |
| `rbac/migrations/0002_*.py` | 已删除（合并到 0001） |
| `rbac/management/commands/init_menu.py` | 补全 12 个配置项 + 移除 name_zh_hant |
| `templates/admin/index.html` | 目录菜单图标渲染 + footer 动态加载 |
| `templates/admin/login.html` | 版权颜色优化 + 5条业务规则背景逻辑 + 移除!important |
| `static/layui/css/admin.css` | menu-dir-icon 样式 + admin-footer 样式 |
| `static/layui/pages/config.html` | 编辑模式图片预览可点击 |
| `static/layui/js/i18n.js` | 修复 login.loading 翻译键缺失+拼写错误 |

---

#### 核心功能修复
- ✅ **左侧菜单收缩展开功能** - 修复点击按钮无反应问题
  - 使用 IIFE + 双重事件绑定（jQuery + 内联 onclick）
  - 添加详细调试日志便于排查
  - 设置 `z-index:9999` 确保按钮可点击

- ✅ **菜单目录收缩展开** - 修复点击目录标题无响应
  - **根本原因**: CSS 中 `.sub-menu` 默认 `display:block` 导致移除 `.open` 类后仍显示
  - **修复**: 改为 `display:none`，仅当有 `.open` 类时才显示
  - 增强事件委托绑定（命名空间 `.menuGroup`）
  - 添加 `e.preventDefault()` 和 `e.stopPropagation()`

- ✅ **搜索功能修复** - 修复关键词搜索不生效
  - 使用事件委托重新绑定搜索/重置/回车事件
  - 添加错误处理和回调函数

#### 国际化修复
- ✅ **语言切换国际化翻译** - 修复英文模式下仍显示中文
  - 为 Header 下拉菜单添加 `data-i18n` 属性：
    - `header.personalCenter` / `header.changePassword` / `header.logout`
  - 修复 `updateLangUI` 函数的 JavaScript 错误
    - 添加 `try-catch` 异常捕获
    - 检查 `t()` 函数是否存在
    - 验证返回值类型为字符串

- ✅ **操作日志页面模块下拉框国际化**
  - 新增翻译键：`log.module.languageSwitch`
  - 中文："语言切换" → English: "Language Switch"
  - 使用动态 JS 翻译替代 Django 模板语法（避免 `{{ t() }}` 无法执行）

#### 主题系统重大修复
- ✅ **深色主题全局同步切换** - 修复 Header/Sidebar/Tabs 不同步
  - **问题**: 切换深色主题时，只有内容区域变暗，Header 和 Sidebar 保持浅色
  - **原因**: CSS 变量优先级低于 Layui 默认样式，无法覆盖
  - **解决方案**: 使用硬编码颜色值 + `!important` 强制覆盖

- ✅ **浅色主题切换残留 Bug** - 修复从深色切回浅色时样式不恢复
  - **原因**: 深色规则使用 `!important`，但浅色规则没有对应覆盖
  - **解决方案**: 添加完整的 `[data-theme-mode="light"]` 规则集，全部带 `!important`

- ✅ **表格边框样式优化**
  - 改为"田字框"样式（横竖边框都有）
  - 外边框 + 单元格右边框 + 底边框
  - 颜色使用 `var(--border-color)` 适配双主题

##### 深色主题完整覆盖清单
| 组件 | 背景色 | 边框 | 文字 |
|------|--------|------|------|
| Header | `#1d1e22` | `#2e3035` | `#e5eaf3` |
| Sidebar | `#1a1b1f` | `#2e3035` | `#a6adb6` |
| Tab栏 | `#1d1e22` | `#2e3035` | `#a6adb6` |
| Body | `#14161a` | - | - |
| Dropdown | `#26272b` | `#363840` | `#e5eaf3` |

##### 浅色主题完整覆盖清单
| 组件 | 背景色 | 边框 | 文字 |
|------|--------|------|------|
| Header | `#ffffff` | `#dee0e3` | `#1f2329` |
| Sidebar | `#ffffff` | `#dee0e3` | `#646a73` |
| Tab栏 | `#f6f7f9` | `#dee0e3` | `#646a73` |
| Body | `#f0f2f5` | - | - |
| Dropdown | `#ffffff` | `#dee0e3` | `#1f2329` |

### 📝 修改文件清单

| 文件路径 | 修改内容 |
|----------|----------|
| `templates/admin/index.html` | Sidebar Toggle、Menu Group、Lang UI、Theme 同步 |
| `static/layui/css/admin.css` | 深色/浅色主题全局样式、表格田字框、过渡动画 |
| `static/layui/js/i18n.js` | 新增 `log.module.languageSwitch` 翻译键 |
| `static/layui/pages/log.html` | 操作模块下拉框动态国际化 |
| `static/layui/pages/user.html` | 搜索事件绑定、loadTable 错误处理 |

#### 登录页面修复
- ✅ **登录页面内容居中** - 修复 Logo、标题、版本号全部靠左显示的问题
  - 添加 CSS 样式使 `.login-card` 内容居中对齐
  - Logo 图标设置 `margin: 0 auto` 居中

- ✅ **登录后重定向404错误** - 修复跳转到 `/admin/undefined` 的问题
  - 根本原因：变量名引用错误（`window.ADMIN_LOGIN_URL` 不存在）
  - 解决方案：改为使用 `window.LAYUI_CONFIG.admin_login_url`
  - 添加 fallback URL `/admin/login/` 防止配置缺失

#### AI 配置测试增强
- ✅ **"model is not found" 错误处理** - 改进 AI 配置测试的错误提示
  - 自动清理配置值（去除空格、引号、反引号）
  - 增强错误消息：包含调试信息、可能原因、解决建议
  - 前端支持多行错误信息显示（使用弹窗）

#### 服务器连接测试增强
- ✅ **"getaddrinfo failed" 错误诊断** - SSH 连接失败时提供详细诊断
  - 支持6种常见错误的智能识别：
    - DNS 解析失败（`getaddrinfo failed`）
    - 连接被拒绝（`Connection refused`）
    - 认证失败（`Authentication failed`）
    - 连接超时（`timeout`）
    - 私钥文件格式错误
    - 其他未知错误
  - 每种错误提供：
    - 服务器详细信息（名称、主机、端口、用户名）
    - 可能的原因分析（3-4条）
    - 建议的解决方案（具体操作步骤）
  - 前端优化：长错误信息使用可滚动弹窗显示

#### UI 文案优化
- ✅ **AI 日志分析按钮文案修正**
  - 修改前：`{{ t('server.aiAnalyzing') }}` → 显示 "AI 正在分析日志，请稍候..."（语义错误）
  - 修改后：`{{ t('server.aiAnalyzeBtn') }}` → 显示 "AI 日志分析"（正确）
  - 新增翻译键：中文 `'AI 日志分析'` / 英文 `'AI Log Analysis'`

#### Base URL 自动标准化
- ✅ **API 配置 Base URL 清理功能**
  - 自动去除尾部斜杠（`https://api.xxx.com/v1/` → `https://api.xxx.com/v1`）
  - 自动去除首尾空格和特殊字符（反引号、单双引号）
  - 在保存和测试时自动应用，用户无需手动处理

### 📝 修改文件清单（续）

### 待发布功能

---

## [1.0.3] - 2024-XX-XX

### ✨ 新增功能

#### 国际化增强
- ✅ 完整的菜单多语言支持（数据库字段方案）
  - Menu 模型添加 `name_en`, `name_zh_hans`, `name_zh_hant` 字段
  - API 根据用户语言偏好返回对应菜单名称
  - 后台管理界面支持编辑多语言菜单名称
  - 缺失翻译时自动回退到中文

- ✅ AI 配置管理页面完整国际化
  - 新增 20+ 个翻译键
  - 所有表单标签、按钮、提示文本支持中英文
  - 厂商选择器多语言支持（智谱 GLM、通义千问等）

- ✅ 通用翻译键补充
  - `common.id` - ID 列标题统一国际化
  - `common.save` - 保存按钮标准化

### 🐛 Bug 修复

#### 前端国际化遗漏修复
修复了以下页面中硬编码的中文文本：

1. **ai-config.html** (19 处修复)
   - 工具栏按钮："新增模型配置" → `{{ t('ai.addConfig') }}`
   - 快速选择厂商标题和厂商标签
   - 表单所有标签和占位符
   - 操作列按钮文本

2. **log.html** (1 处修复)
   - 表格列标题："ID" → `t('common.id')`

3. **role.html** (1 处修复)
   - 表格列标题："ID" → `t('common.id')`

4. **user.html** (1 处修复)
   - 表格列标题："ID" → `t('common.id')`

5. **config.html** (1 处修复)
   - 表格列标题："ID" → `t('common.id')`

6. **profile.html** (1 处修复)
   - 修正保存按钮翻译键：`profile.save.success` → `common.save`
   - 原因：原键是成功提示消息，不是按钮文本

#### 翻译文件更新
在 `i18n.js` 中添加完整的中英文翻译：

**中文翻译新增**：
```javascript
'ai.title': 'AI模型配置',
'ai.addConfig': '新增模型配置',
'ai.providerHint': '支持同一厂商配置多个模型...',
'ai.selectProvider': '快速选择厂商：',
'ai.provider.zhipu': '智谱 GLM',
'ai.provider.qwen': '通义千问',
'ai.provider.custom': '自定义',
'ai.manualInput': '手动填写',
'ai.configName': '配置名称',
'ai.apiKey': 'API Key',
'ai.baseUrl': 'API 地址',
'ai.modelName': '模型名称',
'ai.setDefault': '设为默认',
'ai.testConnection': '测试连接',
'common.id': 'ID',
'common.save': '保存',
```

**英文翻译新增**：
```javascript
'ai.title': 'AI Model Config',
'ai.addConfig': 'Add Model Config',
'ai.providerHint': 'Support multiple models from same provider...',
'ai.selectProvider': 'Quick Select Provider:',
'ai.provider.zhipu': 'Zhipu GLM',
'ai.provider.qwen': 'Qwen',
'ai.provider.custom': 'Custom',
'ai.manualInput': 'Manual Input',
'ai.configName': 'Config Name',
'ai.apiKey': 'API Key',
'ai.baseUrl': 'API Base URL',
'ai.modelName': 'Model Name',
'ai.setDefault': 'Set as Default',
'ai.testConnection': 'Test Connection',
'common.id': 'ID',
'common.save': 'Save',
```

### 📚 文档更新

#### 新增文档
- ✅ [docs/I18N_GUIDE.md](docs/I18N_GUIDE.md) - 国际化使用指南
  - 完整的前端国际化开发教程
  - 后端菜单多语言实现说明
  - 常用翻译键速查表
  - 最佳实践和常见问题

#### README 更新
- ✅ 功能特性中强调"完整国际化支持"
- ✅ 新增 4.5 节：国际化 (i18n) 支持
  - 语言切换步骤
  - 菜单多语言配置方法
  - 前端国际化开发示例
- ✅ 文档索引中添加 I18N 指南链接

### 🔧 技术改进

#### 代码质量
- 统一所有表格的 "ID" 列使用 `t('common.id')`
- 修正翻译键命名规范，避免语义混淆
- 完善 i18n.js 翻译键组织结构

#### 用户体验
- 英文用户界面完全可用
- 菜单名称根据用户语言自动切换
- 所有操作提示和表单验证支持双语

### 📦 打包信息
- 版本号: `1.0.3`
- 包名: `django_layuix-1.0.3-py3-none-any.whl`
- 安装命令: `pip install django-layuix --upgrade`

---

## [1.0.2] - 2024-XX-XX

### ✨ 新增功能
- 首页自定义快速链接配置 (`home_quick_links`)
- Dashboard 仪表盘动态统计卡片配置 (`home_stats_cards`)
- 系统配置支持图片上传（Logo、Favicon）
- AJAX 登出功能（确认弹窗 + 自动跳转）

### 🐛 Bug 修复
- 修复首页卡片文案修改后未生效问题（i18n 覆盖）
- 修复 home_stats_cards 配置不生效问题
- 修复迁移冲突问题

### 📚 文档更新
- [docs/HOME_QUICK_LINKS_GUIDE.md](docs/HOME_QUICK_LINKS_GUIDE.md)
- [docs/AJAX_ADMIN_GUIDE.md](docs/AJAX_ADMIN_GUIDE.md)

---

## [1.0.1] - 2024-XX-XX

### ✨ 新增功能
- RBAC 权限管理系统
- 菜单管理（树形结构）
- 角色管理（支持复制权限）
- 用户管理（支持角色分配）
- 操作日志记录
- Dashboard 仪表盘（系统监控）
- 个人中心（资料修改、密码修改）

### 🎨 主题系统
- 深色/浅色主题切换
- 25+ 种预设主题
- 主题定制能力

### 🌐 国际化基础
- 前端 i18n.js 翻译系统
- 中英文双语支持

---

## [1.0.0] - 2024-XX-XX

### 🎉 初始版本
- 基于 Layui 的 Django Admin 主题
- 现代化后台管理界面
- 极简配置，开箱即用

---

## 版本类型说明

- **主版本号 (MAJOR)**: 不兼容的 API 变更
- **次版本号 (MINOR)**: 向后兼容的功能性新增
- **修订号 (PATCH)**: 向后兼容的问题修正

---

## 贡献者

感谢所有为 django-layuix 做出贡献的开发者！

如需贡献代码或报告问题，请访问项目仓库提交 Issue 或 Pull Request。

---

**最后更新**: 2026年
**维护者**: django-layuix 团队
