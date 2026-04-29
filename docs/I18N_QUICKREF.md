# 国际化 (i18n) 快速参考

## 🚀 快速开始

### 在 HTML 中使用翻译

```html
<!-- 方法一：data-i18n 属性（最简单） -->
<span data-i18n="common.save">保存</span>

<!-- 方法二：模板语法（Layui 模板中） -->
<script type="text/html" id="toolbarTpl">
    <button>{{ t('common.add') }}</button>
</script>

<!-- 方法三：JavaScript 调用 -->
<script>
layer.msg(t('common.success'));
</script>
```

---

## 📖 常用翻译键速查表

### 通用按钮和操作

| 翻译键 | 中文 | 英文 |
|--------|------|------|
| `common.save` | 保存 | Save |
| `common.cancel` | 取消 | Cancel |
| `common.confirm` | 确认 | Confirm |
| `common.add` | 新增 | Add |
| `common.edit` | 编辑 | Edit |
| `common.delete` | 删除 | Delete |
| `common.view` | 查看 | View |
| `common.search` | 搜索 | Search |
| `common.reset` | 重置 | Reset |
| `common.refresh` | 刷新 | Refresh |
| `common.submit` | 提交 | Submit |
| `common.enable` | 启用 | Enable |
| `common.disable` | 禁用 | Disable |

### 状态和提示

| 翻译键 | 中文 | 英文 |
|--------|------|------|
| `common.success` | 成功 | Success |
| `common.fail` | 失败 | Failed |
| `common.addSuccess` | 新增成功 | Added successfully |
| `common.updateSuccess` | 修改成功 | Updated successfully |
| `common.deleteSuccess` | 删除成功 | Deleted successfully |
| `common.required` | 必填项 | Required |

### 表单验证

| 翻译键 | 说明 | 示例 |
|--------|------|------|
| `common.inputRequired` | 请输入{0} | `t('common.inputRequired', ['用户名'])` → "请输入用户名" |

---

## 📊 各模块翻译键

### Dashboard 仪表盘

```javascript
'dashboard.welcome'          // 欢迎使用 {0}，祝您心情愉快！
'dashboard.systemUsers'      // 用户数量 / User Count
'dashboard.systemRoles'      // 系统角色 / System Roles
'dashboard.menuCount'        // 菜单数量 / Menu Count
'dashboard.operationLogs'    // 操作日志 / Operation Logs
```

### 菜单管理

```javascript
'menu.title'                 // 菜单管理 / Menu Management
'menu.name'                  // 菜单名称 / Name
'menu.icon'                  // 图标 / Icon
'menu.type'                  // 类型 / Type
'menu.sort'                  // 排序 / Sort
'menu.visible'               // 可见 / Visible
'menu.status'                // 状态 / Status
'menu.permission'            // 权限标识 / Permission
'menu.parent'                // 上级菜单 / Parent Menu
'menu.path'                  // 路由地址 / Path
'menu.component'             // 组件路径 / Component
```

### 角色管理

```javascript
'role.title'                 // 角色管理 / Role Management
'role.name'                  // 角色名称 / Name
'role.code'                  // 角色编码 / Code
'role.description'           // 描述 / Description
'role.isSystem'              // 系统内置 / Built-in
'role.menuPermission'        // 菜单权限 / Menu Permission
'role.copy.title'            // 复制角色权限 / Copy Role Permission
```

### 用户管理

```javascript
'user.title'                 // 用户管理 / User Management
'user.username'              // 用户名 / Username
'user.nickname'              // 昵称 / Nickname
'user.phone'                 // 手机号 / Phone
'user.email'                 // 邮箱 / Email
'user.role'                  // 角色 / Role
'user.tester'                // 测试人员 / Tester
'user.status'                // 状态 / Status
'user.createTime'            // 创建时间 / Created
'user.addForm.title'         // 新增用户 / Add User
'user.editForm.title'        // 编辑用户 / Edit User
'user.resetPassword'         // 重置密码 / Reset Password
```

### 个人中心

```javascript
'profile.title'              // 个人中心 / Profile
'profile.basicInfo'          // 基本信息 / Basic Info
'profile.changePassword'     // 修改密码 / Change Password
'profile.roleInfo'           // 角色信息 / Role Info
'profile.avatar'             // 头像 / Avatar
'profile.oldPassword'        // 原密码 / Current Password
'profile.newPassword'        // 新密码 / New Password
'profile.confirmPassword'    // 确认密码 / Confirm Password
'profile.changeAvatar'       // 更换头像 / Change Avatar
```

### 操作日志

```javascript
'log.title'                  // 操作日志 / Operation Logs
'log.user'                   // 操作用户 / User
'log.module'                 // 操作模块 / Module
'log.action'                 // 操作内容 / Action
'log.ip'                     // IP地址 / IP
'log.method'                 // 请求方法 / Method
'log.url'                    // 请求URL / URL
'log.status'                 // 状态 / Status
'log.time'                   // 操作时间 / Time
'log.search.user'            // 操作用户 / User
'log.search.module'          // 操作模块 / Module
'log.search.status'          // 操作状态 / Status
'log.search.timeRange'       // 时间范围 / Time Range
```

### 系统配置

```javascript
'config.title'               // 系统配置 / System Config
'config.key'                 // 配置键 / Key
'config.value'               // 配置值 / Value
'config.description'         // 描述 / Description
'config.type'                // 配置类型 / Type
'config.sort'                // 排序 / Sort
'config.addForm.title'       // 新增配置 / Add Config
'config.editForm.title'      // 编辑配置 / Edit Config
```

### 服务器管理

```javascript
'server.title'               // 服务器管理 / Server Management
'server.name'                // 服务器名称 / Name
'server.host'                // 主机地址 / Host
'server.port'                // SSH端口 / SSH Port
'server.username'            // SSH用户名 / SSH Username
'server.authType'            // 认证方式 / Auth Type
'server.password'            // SSH密码 / SSH Password
'server.privateKey'          // 私钥内容 / Private Key
'server.description'         // 描述 / Description
'server.testConnect'         // 测试连接 / Test Connection
'server.viewLog'             // 查看日志 / View Logs
'server.terminal'            // 终端 / Terminal
'server.addForm.title'       // 新增服务器 / Add Server
'server.editForm.title'      // 编辑服务器 / Edit Server
```

### AI 模型配置

```javascript
'ai.title'                   // AI模型配置 / AI Model Config
'ai.addConfig'               // 新增模型配置 / Add Model Config
'ai.configName'              // 配置名称 / Config Name
'ai.apiKey'                  // API Key / API Key
'ai.baseUrl'                 // API 地址 / API Base URL
'ai.modelName'               // 模型名称 / Model Name
'ai.setDefault'              // 设为默认 / Set as Default
'ai.testConnection'          // 测试连接 / Test Connection
'ai.providerHint'            // 支持同一厂商配置多个模型...
'ai.selectProvider'          // 快速选择厂商：/ Quick Select Provider:
'ai.provider.zhipu'          // 智谱 GLM / Zhipu GLM
'ai.provider.qwen'           // 通义千问 / Qwen
'ai.provider.custom'         // 自定义 / Custom
```

---

## 🔧 开发检查清单

### ✅ 添加新功能时

- [ ] 所有 HTML 中的中文文本使用 `data-i18n` 或 `{{ t() }}`
- [ ] Layui 模板中的文本使用 `{{ t() }}`
- [ ] JavaScript 中的提示使用 `t()`
- [ ] 在 `i18n.js` 中添加中英文翻译
- [ ] 测试中文显示
- [ ] 切换到英文测试显示

### ❌ 常见错误

```html
<!-- 错误：硬编码中文 -->
<button>保存</button>
<span>ID</span>

<!-- 正确：使用翻译 -->
<button data-i18n="common.save">保存</button>
<span>{{ t('common.id') }}</span>
```

---

## 🌐 用户语言切换

### 步骤
1. 点击右上角头像 → **个人中心**
2. **基本信息** 标签页 → **语言设置**
3. 选择语言：**简体中文** 或 **English**
4. 点击 **保存** → 刷新页面

### 默认语言
- 新用户默认：`zh-hans`（简体中文）

---

## 🗄️ 菜单多语言

### 后台配置
访问 **权限管理 → 菜单管理**，编辑菜单：

- **菜单名称（中文）**：必填
- **英文名称**：选填
- **简体中文**：选填
- **繁体中文**：选填

> 如果某个语言缺失，自动回退到中文

### API 返回
```python
# 根据用户 language 字段自动返回对应语言
user_lang = user.language  # 'zh-hans' or 'en'
menu_name = menu.get_name_by_lang(user_lang)
```

---

## 📝 添加新翻译键

在 `static/layui/js/i18n.js` 中添加：

```javascript
// 中文翻译（约第 80-350 行）
var translations = {
    'zh-hans': {
        // ... 现有翻译 ...
        'my.new.key': '我的翻译',
    },
    
    // 英文翻译（约第 460-730 行）
    'en': {
        // ... existing translations ...
        'my.new.key': 'My Translation',
    }
};
```

---

## 🔍 检查遗漏

### 查找未国际化的中文
```bash
# 在项目根目录执行
grep -r "[\u4e00-\u9fa5]" static/layui/pages/*.html
```

确保所有中文都使用了：
- `data-i18n="key"` 属性
- `{{ t('key') }}` 模板语法
- JavaScript 中的 `t('key')` 调用

---

## 📚 相关文档

- [完整国际化指南](I18N_GUIDE.md)
- [README - 国际化章节](../README.md#45-国际化-i18n-支持)

---

**最后更新**: 2024年
**版本**: v1.0.3
