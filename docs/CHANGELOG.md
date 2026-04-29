# 更新日志 (Changelog)

所有对 django-layui 项目的更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [Unreleased]

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
- 包名: `django_layui-1.0.3-py3-none-any.whl`
- 安装命令: `pip install django-layui --upgrade`

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

感谢所有为 django-layui 做出贡献的开发者！

如需贡献代码或报告问题，请访问项目仓库提交 Issue 或 Pull Request。

---

**最后更新**: 2024年
**维护者**: django-layui 团队
