# 更新日志 (CHANGELOG)

本文档记录 django-layui 的重要更新和功能改进。

## [1.0.4] - 2026-04-29

### ✨ 新增功能

#### WebSSH 配置增强
- **系统配置支持**：`webssh_url` 现在可以通过「系统管理 → 系统配置」动态管理
- **配置优先级**：数据库配置 > settings.py > 默认值
- **向后兼容**：保留 settings.py 配置方式，确保旧项目不受影响

**配置示例**：
- **系统配置**（推荐）：在后台添加配置项 `webssh_url = http://localhost:8888/`
- **settings.py**（兼容）：`LAYUI_CONFIG = {'webssh_url': 'http://localhost:8888/'}`

#### 服务器管理优化
- **操作列宽度优化**：固定宽度 360px → 最小宽度 420px，所有操作按钮完整显示
- **日志查看器高度优化**：日志内容区域最大高度 400px → 480px，显示更多内容

### 🐛 Bug 修复

#### 查看日志弹窗
- **自动刷新开关**：修复 `lay-text` 文本过长导致超出边界问题，简化为 "ON|OFF" 并固定宽度
- **日志内容显示**：修复日志内容只显示一半的问题，增加显示区域高度

#### 服务器操作列
- **按钮截断问题**：修复操作列宽度不足导致按钮文本被截断显示"..."的问题

---

## [1.0.3] - 2026-04-29

### ✨ 新增功能

#### AI 模型配置增强
- **中英文厂商搜索**：AI 模型配置页面支持通过中文厂商名称（如"智谱"、"通义"、"Kimi"）或英文名称（如"zhipu"、"qwen"、"moonshot"）进行搜索过滤
- **搜索优化**：后端自动映射中文厂商名称到英文标识，提升用户体验

#### 应用菜单注册改进
- **显式 admin 导入**：在 AppConfig.ready() 中自动注册菜单前，必须显式导入 admin.py 模块，确保 @admin.register 装饰器生效
- **文档更新**：README 中增加重要提示和示例代码，说明正确的菜单注册流程

### 🐛 Bug 修复

#### 仪表盘 (Dashboard)
- **SSE 恢复**：修复 usePolling 配置错误，恢复 SSE (Server-Sent Events) 实时推送功能
  - SSE 推送间隔：3秒
  - 轮询降级间隔：5秒
  - 失败自动降级机制保持不变

- **图表类型修复**：
  - 网络流量图表：从折线图改回柱状图（bar chart）
  - 磁盘使用率图表：从折线图改回环形饼图（pie chart）
  
- **磁盘使用率显示优化**：
  - 右上角显示格式：`已用空间 / 总空间`（如 `50 GB / 200 GB`）
  - Tooltip 单位自动转换：根据数值大小自动选择 B/KB/MB/GB/TB
  - 饼图数据：使用原始字节数计算，确保精度

#### AI 模型配置页面 UI
- **按钮对齐**：修复"设为默认"开关与标签不在同一水平线的问题，移除多余的 padding-top
- **搜索框宽度**：优化搜索框宽度为固定 280px，避免过长
- **查看功能**：添加查看按钮的事件处理和弹窗功能
- **按钮位置**：弹窗按钮统一设置为右下角对齐（btnAlign: 'r'）
- **默认开关状态**：修复布尔值比较逻辑，使用严格相等（=== true）

#### 演示应用菜单 404
- **AppConfig 配置**：修复 store 应用模型未注册到 Django Admin 的问题
  - 在 store/__init__.py 添加 default_app_config
  - 在 settings.py 使用完整 AppConfig 路径
  - 在 ready() 中显式导入 admin.py

### 📚 文档更新

- **README.md**：
  - 在"自定义应用菜单注册"章节增加重要提示：必须在 ready() 中显式导入 admin.py
  - 在"AI 日志分析"章节增加搜索提示：支持中英文厂商名称搜索
  - 更新示例代码，包含 import admin 语句

---

## [1.0.2] - 2026-04-28

###  新增功能

#### 国际化 (i18n)
- 完整的中英文双语支持
- 菜单多语言字段（中文、英文、简体中文、繁体中文）
- 前端 JS + 后端 Django i18n 双层翻译机制

#### 主题系统
- 25种预设主题（深色/浅色/彩色）
- 在线主题切换
- 自定义主题生成工具

#### 首页自定义快速链接
- 类似 django-simpleui 的 SIMPLEUI_HOME_QUICK 功能
- 支持内部页面、外部链接、JavaScript 函数
- 可配置图标和名称

---

## [1.0.1] - 2026-04-25

### ✨ 新增功能

#### RBAC 权限系统
- 菜单管理（树形结构，支持目录/菜单/按钮）
- 角色管理（菜单权限绑定）
- 用户管理（自定义用户模型）
- 按钮级权限控制

#### 系统监控
- Dashboard 仪表盘
  - CPU 使用率（折线图）
  - 内存使用率（折线图）
  - 磁盘使用率（饼图）
  - 网络流量（柱状图）
- 实时数据更新（SSE + HTTP 轮询降级）

#### AI 日志分析
- 支持所有 OpenAI 兼容协议的服务
  - OpenAI
  - 智谱 GLM
  - DeepSeek
  - 通义千问
  - Moonshot (Kimi)
- Web 界面配置（推荐）
- settings.py 配置（可选）

---

## [1.0.0] - 2026-04-20

### ✨ 首次发布

#### 核心功能
- 基于 Layui 的 Django Admin 主题
- 深色/浅色主题切换
- 操作日志记录
- 系统配置（数据库动态管理）
- 图片上传
- Favicon 自定义
- 个人中心
- 用户注册 API
- AJAX 登出
- 前端页面入口
- 响应式设计

#### 技术栈
- Python >= 3.8
- Django >= 3.2
- Layui 2.13.5
- ECharts 5.x
- Paramiko (SSH)
- OpenAI API

---

## 版本说明

### 版本号规则

遵循 [语义化版本 2.0.0](https://semver.org/lang/zh-CN/)

- **主版本号 (MAJOR)**：不兼容的 API 修改
- **次版本号 (MINOR)**：向下兼容的功能性新增
- **修订号 (PATCH)**：向下兼容的问题修正

### 符号说明

-  新增功能
- 🐛 Bug 修复
- 📚 文档更新
- ⚡ 性能优化
- 🔧 配置更改
- 🗑️ 废弃功能


{
  "configs": [
    {
      "id": "ef12e298",
      "name": "智谱47",
      "provider": "zhipu",
      "api_key": "f58f22eea5db49929e64baf11b598856.4dHSKvQHI2gFhPIw",
      "base_url": "https://open.bigmodel.cn/api/paas/v4/",
      "model": "glm-4-flash",
      "is_default": false
    },
    {
      "id": "ddfef492",
      "name": "美团logcat",
      "provider": "custom",
      "api_key": "ak_1u725L5sG3Ta0EV1aY0xC1kK4OZ3B",
      "base_url": "https://api.longcat.chat/openai",
      "model": "LongCat-Flash-Lite",
      "is_default": true
    }
  ]
}
