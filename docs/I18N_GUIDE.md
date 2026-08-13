# 国际化 (i18n) 使用指南

## 📋 概述

django-layui 支持完整的中英文双语切换，包括：
- **前端界面**：所有 HTML 页面文本通过 i18n.js 翻译
- **后端菜单**：数据库存储多语言字段，根据用户语言偏好动态返回
- **系统提示**：操作成功/失败等提示信息自动适配语言

---

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

## 🌐 语言支持

| 语言 | 代码 | 说明 |
|------|------|------|
| 简体中文 | `zh-hans` | 默认语言 |
| English | `en` | 英文 |

### 用户语言切换步骤

1. 点击右上角头像 → **个人中心**
2. **基本信息** 标签页 → **语言设置**
3. 选择语言：**简体中文** 或 **English**
4. 点击 **保存** → 刷新页面

> **默认语言**: 新用户默认 `zh-hans`（简体中文）

---

## 🔧 前端国际化

### 1. 翻译文件位置

```
django_layuix/static/layui/js/i18n.js
```

该文件包含所有前端页面的中英文翻译。

### 2. 在 HTML 中使用翻译

#### 方法一：data-i18n 属性（推荐）

```html
<!-- 自动翻译 -->
<span data-i18n="common.save">保存</span>
<button data-i18n="common.delete">删除</button>
<h3 data-i18n="dashboard.welcome">欢迎</h3>
```

#### 方法二：模板语法 {{ t() }}

```html
<!-- Layui 模板中使用 -->
<script type="text/html" id="toolbarTpl">
    <button>{{ t('common.add') }}</button>
    <button>{{ t('common.edit') }}</button>
    <button>{{ t('common.delete') }}</button>
</script>
```

#### 方法三：JavaScript 调用

```javascript
// 在 JS 代码中获取翻译
var msg = t('common.saveSuccess');
layer.msg(t('common.addSuccess'));

// 带参数的翻译
var text = t('common.inputRequired', ['用户名']);
// 输出："请输入用户名"
```

### 3. 常用翻译键速查表

#### 通用按钮和操作

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

#### 状态和提示

| 翻译键 | 中文 | 英文 |
|--------|------|------|
| `common.success` | 成功 | Success |
| `common.fail` | 失败 | Failed |
| `common.addSuccess` | 新增成功 | Added successfully |
| `common.updateSuccess` | 修改成功 | Updated successfully |
| `common.deleteSuccess` | 删除成功 | Deleted successfully |
| `common.required` | 必填项 | Required |

#### 表单验证

| 翻译键 | 说明 | 示例 |
|--------|------|------|
| `common.inputRequired` | 请输入{0} | `t('common.inputRequired', ['用户名'])` → "请输入用户名" |

### 4. 各模块翻译键

#### Dashboard 仪表盘

```javascript
'dashboard.welcome'          // 欢迎使用 {0}，祝您心情愉快！
'dashboard.systemUsers'      // 用户数量 / User Count
'dashboard.systemRoles'      // 系统角色 / System Roles
'dashboard.menuCount'        // 菜单数量 / Menu Count
'dashboard.operationLogs'    // 操作日志 / Operation Logs
```

#### 菜单管理

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

#### 角色管理

```javascript
'role.title'                 // 角色管理 / Role Management
'role.name'                  // 角色名称 / Name
'role.code'                  // 角色编码 / Code
'role.description'           // 描述 / Description
'role.isSystem'              // 系统内置 / Built-in
'role.menuPermission'        // 菜单权限 / Menu Permission
'role.copy.title'            // 复制角色权限 / Copy Role Permission
```

#### 用户管理

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

#### 个人中心

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

#### 操作日志

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

#### 系统配置

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

#### 服务器管理

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

#### AI 模型配置

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

## 🗄️ 后端菜单国际化

### 1. 数据库设计

Menu 模型包含多语言字段：

```python
class Menu(models.Model):
    name = models.CharField(max_length=50, verbose_name='菜单名称（中文）')
    name_en = models.CharField(max_length=50, blank=True, default='', verbose_name='菜单名称（英文）')
    name_zh_hans = models.CharField(max_length=50, blank=True, default='', verbose_name='菜单名称（简体中文）')
    name_zh_hant = models.CharField(max_length=50, blank=True, default='', verbose_name='菜单名称（繁体中文）')
    # ... 其他字段
```

### 2. 获取本地化菜单名称

```python
# 在视图函数中
def _get_user_menus(user):
    from .models import Menu
    
    # 获取用户语言偏好
    user_lang = getattr(user, 'language', 'zh-hans') if hasattr(user, 'language') else 'zh-hans'
    
    menus = Menu.objects.filter(status=True, visible=True).order_by('sort', 'id')
    
    menu_list = []
    for m in menus:
        # 使用本地化菜单名称
        menu_name = m.get_name_by_lang(user_lang)
        
        menu_list.append({
            'id': m.id,
            'name': menu_name,  # 根据用户语言返回对应名称
            'name_zh_hans': m.name_zh_hans,
            'name_zh_hant': m.name_zh_hant,
            'name_en': m.name_en,
            # ... 其他字段
        })
    
    return _build_menu_tree(menu_list)
```

### 3. 在后台管理菜单

访问 **权限管理 → 菜单管理**，可以编辑每个菜单的多语言名称：

- **菜单名称（中文）**：必填，默认显示
- **英文名称**：选填，英文用户显示
- **简体中文**：选填，简体中文用户显示
- **繁体中文**：选填，繁体中文用户显示

> **注意**：如果某个语言的翻译缺失，系统会自动回退到中文名称。

### 4. API 返回示例

```python
# 根据用户 language 字段自动返回对应语言
user_lang = user.language  # 'zh-hans' or 'en'
menu_name = menu.get_name_by_lang(user_lang)
```

---

## 🛠️ 开发指南

### 1. 开发检查清单

#### ✅ 添加新功能时

- [ ] 所有 HTML 中的中文文本使用 `data-i18n` 或 `{{ t() }}`
- [ ] Layui 模板中的文本使用 `{{ t() }}`
- [ ] JavaScript 中的提示使用 `t()`
- [ ] 在 `i18n.js` 中添加中英文翻译
- [ ] 测试中文显示
- [ ] 切换到英文测试显示

#### ❌ 常见错误

```html
<!-- 错误：硬编码中文 -->
<button>保存</button>
<span>ID</span>

<!-- 正确：使用翻译 -->
<button data-i18n="common.save">保存</button>
<span>{{ t('common.id') }}</span>
```

### 2. 添加新的翻译键

在 `i18n.js` 中添加翻译：

```javascript
// 中文翻译（约第 80-350 行）
var translations = {
    'zh-hans': {
        // ... 现有翻译 ...
        'my.new.key': '我的新翻译',
    },
    
    // 英文翻译（约第 460-730 行）
    'en': {
        // ... existing translations ...
        'my.new.key': 'My New Translation',
    }
};
```

### 3. 检查遗漏的国际化

检查 HTML 文件中是否有硬编码的中文文本：

```bash
# 查找未国际化的中文文本
grep -r "[\u4e00-\u9fa5]" static/layui/pages/*.html
```

确保所有中文文本都使用了以下之一：
- `data-i18n="key"` 属性
- `{{ t('key') }}` 模板语法
- JavaScript 中的 `t('key')` 调用

### 4. 翻译键命名规范

建议使用层级结构：

```
模块名.功能名.具体项
```

示例：
- `dashboard.systemUsers` - Dashboard 的系统用户数
- `user.addForm.title` - 用户新增表单标题
- `common.save` - 通用的保存按钮

---

## ✅ 最佳实践

### 1. 始终使用翻译函数

❌ **错误做法**：
```html
<button>保存</button>
<span>ID</span>
```

✅ **正确做法**：
```html
<button data-i18n="common.save">保存</button>
<span>{{ t('common.id') }}</span>
```

### 2. 为所有语言提供翻译

添加新功能时，同时更新中英文翻译：

```javascript
// i18n.js
'zh-hans': {
    'my.feature.button': '我的按钮',
},
'en': {
    'my.feature.button': 'My Button',
}
```

### 3. 使用占位符处理动态内容

```javascript
// 定义翻译
'user.greeting': '你好，{0}！',

// 使用
t('user.greeting', [username]);
// 输出："你好，张三！" 或 "Hello, John!"
```

### 4. 测试多语言切换

开发完成后：
1. 切换到英文，检查所有文本是否正确翻译
2. 切换回中文，确认显示正常
3. 检查菜单是否根据语言切换

---

## 🐛 常见问题

### Q1: 为什么有些文本没有翻译？

**原因**：可能是硬编码的中文文本，未使用 i18n 翻译。

**解决**：
1. 检查 HTML 中是否有直接写的中文
2. 替换为 `data-i18n` 或 `{{ t() }}`
3. 在 `i18n.js` 中添加对应的翻译键

### Q2: 菜单名称如何支持多语言？

**步骤**：
1. 在后台 **权限管理 → 菜单管理**
2. 编辑菜单，填写英文名称、简体中文等
3. 用户在个人中心切换语言后，菜单自动显示对应语言

### Q3: 如何添加新的语言支持？

**步骤**：
1. 在 `i18n.js` 中添加新语言的翻译对象
2. 在 UserProfile 模型的 language 字段 choices 中添加新语言
3. 在前端语言选择器中添加新语言选项

---

## 📝 更新日志

### v1.0.3 (2024)

**国际化增强**：
- ✅ 修复所有页面硬编码中文文本
- ✅ 新增 AI 配置管理页面完整翻译
- ✅ 统一表格列标题国际化（ID → common.id）
- ✅ 修正个人中心保存按钮翻译键
- ✅ 完善菜单多语言支持（数据库字段方案）
- ✅ 新增 20+ 个翻译键（AI 配置相关）

**修复的页面**：
- ai-config.html - 19 处中文文本国际化
- log.html - ID 列标题国际化
- role.html - ID 列标题国际化
- user.html - ID 列标题国际化
- config.html - ID 列标题国际化
- profile.html - 修正保存按钮翻译键

---

## 📚 相关文档

- [首页快速链接配置指南](HOME_QUICK_LINKS_GUIDE.md)
- [菜单扩展指南](MENU_EXTENSION_GUIDE.md)
- [主题系统指南](THEME_SYSTEM_GUIDE.md) - 深色/浅色双模式系统
- [AJAX 管理指南](AJAX_ADMIN_GUIDE.md)
- [权限系统指南](PERMISSION_SYSTEM_GUIDE.md)

---

## 🤝 贡献

欢迎提交 PR 改进翻译质量或添加新的语言支持！

---

**最后更新**: 2026-05-07  
**版本**: v1.0.4+  
**维护者**: django-layui 团队
