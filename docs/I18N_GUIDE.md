# 国际化 (i18n) 使用指南

## 📋 概述

django-layui 支持完整的中英文双语切换，包括：
- **前端界面**：所有 HTML 页面文本通过 i18n.js 翻译
- **后端菜单**：数据库存储多语言字段，根据用户语言偏好动态返回
- **系统提示**：操作成功/失败等提示信息自动适配语言

---

## 🌐 语言支持

| 语言 | 代码 | 说明 |
|------|------|------|
| 简体中文 | `zh-hans` | 默认语言 |
| English | `en` | 英文 |

---

## 🔧 前端国际化

### 1. 翻译文件位置

```
django_layui/static/layui/js/i18n.js
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

### 3. 常用翻译键

#### 通用按钮和操作

```javascript
t('common.save')          // 保存 / Save
t('common.cancel')        // 取消 / Cancel
t('common.confirm')       // 确认 / Confirm
t('common.add')           // 新增 / Add
t('common.edit')          // 编辑 / Edit
t('common.delete')        // 删除 / Delete
t('common.view')          // 查看 / View
t('common.search')        // 搜索 / Search
t('common.reset')         // 重置 / Reset
t('common.refresh')       // 刷新 / Refresh
t('common.submit')        // 提交 / Submit
```

#### 状态和提示

```javascript
t('common.enable')        // 启用 / Enable
t('common.disable')       // 禁用 / Disable
t('common.success')       // 成功 / Success
t('common.fail')          // 失败 / Failed
t('common.addSuccess')    // 新增成功 / Added successfully
t('common.updateSuccess') // 修改成功 / Updated successfully
t('common.deleteSuccess') // 删除成功 / Deleted successfully
```

#### 表单验证

```javascript
t('common.required')      // 必填项 / Required
t('common.inputRequired', ['用户名'])  // 请输入用户名 / Please enter username
```

### 4. 各模块翻译键

#### Dashboard 仪表盘

```javascript
t('dashboard.welcome')      // 欢迎使用 {0}，祝您心情愉快！
t('dashboard.systemUsers')  // 用户数量 / User Count
t('dashboard.systemRoles')  // 系统角色 / System Roles
t('dashboard.menuCount')    // 菜单数量 / Menu Count
t('dashboard.operationLogs') // 操作日志 / Operation Logs
```

#### 菜单管理

```javascript
t('menu.title')             // 菜单管理 / Menu Management
t('menu.name')              // 菜单名称 / Name
t('menu.icon')              // 图标 / Icon
t('menu.type')              // 类型 / Type
t('menu.sort')              // 排序 / Sort
t('menu.visible')           // 可见 / Visible
```

#### 角色管理

```javascript
t('role.title')             // 角色管理 / Role Management
t('role.name')              // 角色名称 / Name
t('role.code')              // 角色编码 / Code
t('role.description')       // 描述 / Description
t('role.menuPermission')    // 菜单权限 / Menu Permission
```

#### 用户管理

```javascript
t('user.title')             // 用户管理 / User Management
t('user.username')          // 用户名 / Username
t('user.nickname')          // 昵称 / Nickname
t('user.phone')             // 手机号 / Phone
t('user.email')             // 邮箱 / Email
t('user.role')              // 角色 / Role
t('user.status')            // 状态 / Status
```

#### 个人中心

```javascript
t('profile.title')          // 个人中心 / Profile
t('profile.basicInfo')      // 基本信息 / Basic Info
t('profile.changePassword') // 修改密码 / Change Password
t('profile.avatar')         // 头像 / Avatar
```

#### 操作日志

```javascript
t('log.title')              // 操作日志 / Operation Logs
t('log.user')               // 操作用户 / User
t('log.module')             // 操作模块 / Module
t('log.action')             // 操作内容 / Action
t('log.ip')                 // IP地址 / IP
t('log.status')             // 状态 / Status
```

#### 系统配置

```javascript
t('config.title')           // 系统配置 / System Config
t('config.key')             // 配置键 / Key
t('config.value')           // 配置值 / Value
t('config.type')            // 配置类型 / Type
```

#### 服务器管理

```javascript
t('server.title')           // 服务器管理 / Server Management
t('server.name')            // 服务器名称 / Name
t('server.host')            // 主机地址 / Host
t('server.port')            // SSH端口 / SSH Port
t('server.testConnect')     // 测试连接 / Test Connection
t('server.terminal')        // 终端 / Terminal
```

#### AI 模型配置

```javascript
t('ai.title')               // AI模型配置 / AI Model Config
t('ai.addConfig')           // 新增模型配置 / Add Model Config
t('ai.configName')          // 配置名称 / Config Name
t('ai.apiKey')              // API Key / API Key
t('ai.baseUrl')             // API 地址 / API Base URL
t('ai.modelName')           // 模型名称 / Model Name
t('ai.setDefault')          // 设为默认 / Set as Default
t('ai.testConnection')      // 测试连接 / Test Connection
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

---

## 👤 用户语言设置

### 1. 修改用户语言

用户可以通过以下方式切换语言：

1. 点击右上角头像进入 **个人中心**
2. 在 **基本信息** 标签页找到 **语言设置**
3. 选择 **简体中文** 或 **English**
4. 点击 **保存**，刷新页面后生效

### 2. 默认语言

- 新用户默认语言：`zh-hans`（简体中文）
- 可在创建用户时指定语言

---

## 🛠️ 开发指南

### 1. 添加新的翻译键

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

### 2. 检查遗漏的国际化

检查 HTML 文件中是否有硬编码的中文文本：

```bash
# 查找未国际化的中文文本
grep -r "[\u4e00-\u9fa5]" static/layui/pages/*.html
```

确保所有中文文本都使用了以下之一：
- `data-i18n="key"` 属性
- `{{ t('key') }}` 模板语法
- JavaScript 中的 `t('key')` 调用

### 3. 翻译键命名规范

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
- [主题系统指南](THEME_SYSTEM_GUIDE.md)
- [AJAX 管理指南](AJAX_ADMIN_GUIDE.md)

---

## 🤝 贡献

欢迎提交 PR 改进翻译质量或添加新的语言支持！

---

**最后更新**: 2024年
**维护者**: django-layui 团队
