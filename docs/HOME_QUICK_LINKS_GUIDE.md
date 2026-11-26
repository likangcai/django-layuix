# 首页自定义快速链接配置指南

## 结论（TL;DR）
【事实】首页快捷链接通过 `LAYUI_CONFIG['home_quick_links']` 配置，支持内部路径与外部 URL。
【判断】若链接包含 `javascript:` 协议，仅允许用户显式声明的白名单无参函数，避免任意脚本执行。
【本期不做】复杂带参快捷调用；如需动态操作，请在页面代码中注册具名函数后再配置。

---

## 📋 功能概述

django-layuix 支持在首页仪表盘显示自定义快速链接，方便用户快速访问常用页面或外部网站。

## ⚙️ 配置位置

**文件**: `settings.py`  
**配置项**: `LAYUI_CONFIG['home_quick_links']`

## 📝 基本语法

```python
LAYUI_CONFIG = {
    # ... 其他配置 ...
    
    'home_quick_links': [
        {'name': '显示名称', 'icon': 'layui-icon-xxx', 'url': '跳转地址'},
    ],
}
```

**注意**：执行 `init_menu` 后，`sys_config` 会写入默认 4 项快捷链接（Django/Layui/GitHub/Gitee）；数据库配置优先于 settings。只有清空数据库中的 `home_quick_links` 且 settings 未配置时，首页才不显示快捷链接区域。

## 🔗 支持的 URL 类型

### 1. 内部静态页面

```python
{'name': '个人中心', 'icon': 'layui-icon-user', 'url': '/static/layui/pages/profile.html'}
```

点击后在当前 Tab 中打开内部页面。

### 2. 内部路由（自动在 Tab 中打开）

```python
{'name': '菜单管理', 'icon': 'layui-icon-menu-fill', 'url': '/permission/menu'}
```

系统会自动识别并在新 Tab 中打开对应的页面（需要菜单已配置）。

### 3. JavaScript 函数调用

```python
{'name': '修改密码', 'icon': 'layui-icon-password', 'url': 'javascript:openChangePassword();'}
```

执行 JavaScript 代码，通常用于调用父窗口的函数。

### 4. 外部链接

```python
{'name': 'Django官网', 'icon': 'layui-icon-website', 'url': 'https://www.djangoproject.com/'}
```

点击后会在新窗口打开外部网站。

| 类型 | 示例 | 说明 |
|------|------|------|
| 内部静态页面 | `/static/layui/pages/profile.html` | 直接访问静态HTML文件 |
| 内部路由 | `/store/product` | 在Tab中打开（需菜单已配置） |
| JavaScript函数 | `javascript:openChangePassword();` | 执行JS代码 |
| 外部链接 | `https://www.djangoproject.com/` | 新窗口打开 |

## 🎨 常用图标

Layui 内置图标类名：

```
layui-icon-home          - 主页
layui-icon-user          - 用户
layui-icon-password      - 密码
layui-icon-log           - 日志
layui-icon-set           - 设置
layui-icon-menu-fill     - 菜单
layui-icon-group         - 群组
layui-icon-app           - 应用
layui-icon-website       - 网站
layui-icon-github        - GitHub
layui-icon-template      - 模板
layui-icon-component     - 组件
layui-icon-more          - 更多
layui-icon-cart-simple   - 购物车
layui-icon-form          - 表单
layui-icon-chart         - 图表
```

更多图标请参考：[Layui 图标文档](https://layui.dev/docs/2/icon/)

## 💡 完整配置示例

### 示例 1：基础配置

```python
LAYUI_CONFIG = {
    'system_name': '我的管理系统',
    'system_version': '1.4.9',
    'logo_icon': 'layui-icon-code-circle',
    
    # 首页自定义快速链接
    'home_quick_links': [
        # 系统管理类
        {'name': '个人中心', 'icon': 'layui-icon-user', 'url': '/static/layui/pages/profile.html'},
        {'name': '修改密码', 'icon': 'layui-icon-password', 'url': 'javascript:openChangePassword();'},
        {'name': '操作日志', 'icon': 'layui-icon-log', 'url': '/static/layui/pages/log.html'},
        {'name': '系统配置', 'icon': 'layui-icon-set', 'url': '/static/layui/pages/config.html'},
        
        # 业务管理类
        {'name': '产品管理', 'icon': 'layui-icon-app', 'url': '/store/product'},
        {'name': '订单管理', 'icon': 'layui-icon-cart', 'url': '/store/order'},
        
        # 外部资源
        {'name': 'Django官网', 'icon': 'layui-icon-website', 'url': 'https://www.djangoproject.com/'},
        {'name': 'Layui文档', 'icon': 'layui-icon-template', 'url': 'https://layui.dev/'},
    ],
}
```

### 示例 2：电商后台

```python
LAYUI_CONFIG = {
    'home_quick_links': [
        {'name': '商品管理', 'icon': 'layui-icon-cart-simple', 'url': '/store/product'},
        {'name': '订单管理', 'icon': 'layui-icon-form', 'url': '/store/order'},
        {'name': '客户管理', 'icon': 'layui-icon-user', 'url': '/store/customer'},
        {'name': '数据统计', 'icon': 'layui-icon-chart', 'url': '/store/stats'},
        {'name': 'Django官网', 'icon': 'layui-icon-website', 'url': 'https://www.djangoproject.com/'},
    ],
}
```

### 示例 3：混合配置

```python
LAYUI_CONFIG = {
    'home_quick_links': [
        # 内部页面（推荐）
        {'name': '个人中心', 'icon': 'layui-icon-user', 'url': '/static/layui/pages/profile.html'},
        {'name': '修改密码', 'icon': 'layui-icon-password', 'url': 'javascript:openChangePassword();'},
        {'name': '操作日志', 'icon': 'layui-icon-log', 'url': '/static/layui/pages/log.html'},
        {'name': '系统配置', 'icon': 'layui-icon-set', 'url': '/static/layui/pages/config.html'},
        
        # 外部链接
        {'name': 'Django官网', 'icon': 'layui-icon-website', 'url': 'https://www.djangoproject.com/'},
        {'name': 'Layui文档', 'icon': 'layui-icon-template', 'url': 'https://layui.dev/'},
        {'name': 'GitHub', 'icon': 'layui-icon-github', 'url': 'https://github.com/'},
    ],
}
```

## ✅ 验证步骤

1. 修改 `settings.py` 添加配置
2. 重启 Django 服务
3. 登录后台管理系统
4. 查看首页仪表盘的"快捷入口"区域
5. 点击链接测试跳转是否正常

## ⚠️ 注意事项

1. **配置位置**：必须在 `settings.py` 的 `LAYUI_CONFIG` 字典中配置
2. **格式要求**：每个链接必须包含 `name`、`icon`、`url` 三个字段
3. **动态生效**：修改配置后需要重启 Django 服务才能生效
4. **默认值**：`init_menu` 会写入 4 项默认链接；数据库优先于 settings
5. **权限控制**：快速链接不检查权限，建议只配置当前用户有权限访问的页面
6. **图标必须存在**：确保使用的图标类名是有效的 Layui 图标
7. **路径正确性**：内部路径必须以 `/` 开头
8. **数量建议**：建议配置 4-8 个链接，过多会影响美观
9. **外部链接安全**：建议使用 HTTPS 协议

## 🔍 故障排查

### Q: 配置后没有生效？

**A**: 检查以下几点：
- 确认 `settings.py` 已保存
- 确认已重启 Django 服务
- 清除浏览器缓存（Ctrl+F5 强制刷新）
- 检查控制台是否有 JavaScript 错误

### Q: 点击链接没有反应？

**A**: 检查以下几点：
- 确认 URL 格式正确
- 内部路径必须以 `/` 开头
- JavaScript 协议需要使用 `javascript:` 前缀
- 检查浏览器控制台是否有错误信息

### Q: 如何恢复默认链接？

**A**: 执行 `python manage.py init_menu` 会恢复系统配置中的默认 4 项链接；若只想隐藏链接，请将数据库 `home_quick_links` 与 settings 中的值都设为空数组。

## 🛠️ 技术实现

### 后端实现

- 通过自定义 `LayuiAdminSite` 扩展 Django Admin
- 在 `each_context()` 方法中将 `LAYUI_CONFIG` 传递到模板上下文
- 模板中使用 `{{ layui_config.home_quick_links|default:"[]"|safe }}` 渲染配置

### 前端实现

- `dashboard.html` 从父窗口的 `window.LAYUI_CONFIG.home_quick_links` 读取配置
- 动态生成快速链接 HTML
- 智能处理不同类型的 URL：
  - JavaScript 协议：直接执行代码
  - 外部链接（http/https）：在新窗口打开
  - 内部链接：在父窗口的 Tab 中打开

## 📂 相关文件

| 文件 | 作用 |
|------|------|
| `django_layuix/admin.py` | 自定义 AdminSite，传递配置到模板 |
| `django_layuix/apps.py` | 应用配置，替换默认 admin.site |
| `django_layuix/templates/admin/index.html` (第181行) | 主框架模板，传递配置到前端 |
| `django_layuix/static/layui/pages/dashboard.html` (第364-430行) | 首页仪表盘，渲染快速链接 |
| `example/myproject/settings.py` (第103行) | 配置示例 |
| `README.md` (第183-249行) | 快速入门和详细说明 |

## 📚 更多资源

- [Layui 图标文档](https://layui.dev/docs/2/icon/)
- [Django 官方文档](https://docs.djangoproject.com/)
- [README 配置说明](../README.md)
