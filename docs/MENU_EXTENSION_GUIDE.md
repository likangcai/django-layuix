# django-layui 菜单扩展指南

## 问题背景

在真实项目中（如 Django 6 + Vue3 的软件测试平台），每新增一个 app 就去修改 django-layui 库的源码是不现实的。django-layui 作为 pip 安装的第三方库，应该提供可扩展的 API。

## 解决方案

django-layui v1.0.2+ 提供了**菜单注册 API**，允许外部项目动态添加菜单，无需修改库源码。

## 使用方法

### 1. 在你的应用中注册菜单

```python
# myapp/apps.py
from django.apps import AppConfig

class MyappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myapp'
    verbose_name = '我的应用'
    
    def ready(self):
        """
        应用启动时注册菜单
        这是 django-layui 扩展菜单的标准方式，无需修改库源码
        """
        try:
            from django_layui.rbac import register_menus
            
            # 注册菜单
            register_menus(
                menus_data=[
                    # 目录：演示应用
                    ('演示应用', 'layui-icon-app', '', 1, 4, None),
                    # 子菜单：商品管理
                    ('商品管理', 'layui-icon-cart-simple', '/store/product', 2, 1, '演示应用'),
                    # 子菜单：订单管理
                    ('订单管理', 'layui-icon-form', '/store/order', 2, 2, '演示应用'),
                ],
                buttons_data=[
                    # 商品管理按钮权限
                    ('新增商品', '商品管理', 'product:add', 1),
                    ('编辑商品', '商品管理', 'product:edit', 2),
                    ('删除商品', '商品管理', 'product:delete', 3),
                    # 订单管理按钮权限
                    ('查看订单', '订单管理', 'order:view', 1),
                    ('订单发货', '订单管理', 'order:ship', 2),
                ]
            )
        except Exception as e:
            # 如果数据库还未迁移或 rbac 未安装，忽略错误
            print(f"Warning: Could not register menus: {e}")
```

### 2. 参数说明

#### menus_data - 菜单列表

每个元素为元组：`(name, icon, path, menu_type, sort, parent_name_or_None)`

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| name | str | 菜单名称 | `'商品管理'` |
| icon | str | Layui图标类名 | `'layui-icon-cart-simple'` |
| path | str | 路由地址 | `'/store/product'` |
| menu_type | int | 1=目录, 2=菜单, 3=按钮 | `2` |
| sort | int | 排序号（越小越靠前） | `1` |
| parent_name | str/None | 父菜单名称，顶级菜单为None | `'演示应用'` |

#### buttons_data - 按钮权限列表（可选）

每个元素为元组：`(btn_name, parent_menu_name, permission, sort)`

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| btn_name | str | 按钮名称 | `'新增商品'` |
| parent_menu_name | str | 所属菜单名称 | `'商品管理'` |
| permission | str | 权限标识 | `'product:add'` |
| sort | int | 排序号 | `1` |

### 3. 前端页面映射（可选）

如果你的应用有自定义的前端页面，需要在模板中添加路径映射。可以通过继承 `admin/index.html` 来实现：

```html
<!-- templates/admin/index.html -->
{% extends "admin/index.html" %}

{% block extra_js %}
{{ block.super }}
<script>
// 扩展菜单路径映射
Object.assign(menuPathMap, {
    '/store/category': '/static/myapp/pages/store-category.html',
    '/store/product': '/static/myapp/pages/store-product.html',
    '/store/order': '/static/myapp/pages/store-order.html',
});
</script>
{% endblock %}
```

### 4. 高级用法

#### 注销菜单

```python
from django_layui.rbac import unregister_menus

# 谨慎使用，会删除菜单及其子菜单
unregister_menus(['演示应用'])
```

#### 条件注册

```python
def ready(self):
    from django.conf import settings
    from django_layui.rbac import register_menus
    
    # 根据配置决定是否注册
    if getattr(settings, 'ENABLE_STORE_APP', False):
        register_menus(...)
```

## 特性说明

### 幂等性

菜单注册是**幂等的**，多次调用不会重复创建菜单。内部使用 `get_or_create()` 方法，已存在的菜单会被跳过。

### 自动权限分配

新创建的菜单和按钮权限会**自动分配给管理员角色**，确保管理员可以立即访问新功能。

### 异常处理

建议在 `ready()` 方法中使用 `try-except` 包裹注册代码，避免在数据库未迁移或 RBAC 未安装时导致应用启动失败。

## 完整示例

参考 `example/store/apps.py` 文件，这是一个完整的菜单注册示例。

## 对比传统方式

| 方式 | 优点 | 缺点 |
|------|------|------|
| **菜单注册 API** ✅ | 无需修改库源码，支持 pip 安装，易于维护 | 需要编写少量 Python 代码 |
| 修改库源码 ❌ | 直观 | 每次更新库都会丢失，不支持 pip 安装 |
| 手动在后台添加 ❌ | 可视化操作 | 繁琐，容易出错，不适合批量操作 |

## 最佳实践

1. **在 AppConfig.ready() 中注册**：确保应用启动时自动执行
2. **使用 try-except**：避免启动失败
3. **保持幂等性**：可安全地多次调用
4. **权限命名规范**：使用 `app_name:action` 格式，如 `product:add`
5. **参考示例代码**：查看 `example/store/apps.py` 获取完整示例

## 总结

通过菜单注册 API，你可以：
- ✅ 无需修改 django-layui 库源码
- ✅ 支持 pip 安装和版本升级
- ✅ 在多个项目中复用
- ✅ 灵活控制菜单结构
- ✅ 自动化部署和初始化

这正是 django-layui 设计的核心理念：**开箱即用，灵活扩展**。
