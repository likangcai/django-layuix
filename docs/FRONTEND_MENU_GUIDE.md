# 前台菜单可见性控制说明

## 📋 概述

`frontend_visible` 字段用于控制菜单在**前台应用**中的显示，与 `backend_visible`（后台可见性）独立控制。

## 🎯 设计理念

**权限与可见性分离**：
- **权限（Permission）**：控制"能不能做"，不分前后台
- **可见性（Visibility）**：控制"看不看得到"，分前后台

## 📊 字段说明

| 字段 | 作用范围 | 说明 |
|------|----------|------|
| `visible` | 前后台通用 | 总开关，关闭后前后台都不显示 |
| `status` | 前后台通用 | 是否启用，关闭后所有用户都不可用 |
| `backend_visible` | 仅后台 | 控制后台侧边栏是否显示 |
| `frontend_visible` | 仅前台 | 控制前台应用是否显示 |

## 🔧 API 接口

### 1. 获取后台菜单树
```
GET /admin/api/rbac/menus/tree/
```
- 用途：后台管理页面使用
- 返回：所有菜单（包括 `backend_visible=False` 的）
- 认证：需要登录

### 2. 获取前台菜单树
```
GET /admin/api/rbac/menus/frontend/
```
- 用途：前台页面使用
- 返回：只返回 `frontend_visible=True` 的菜单
- 认证：需要登录

## 💡 使用场景

### 场景1: 仅后台管理的功能
```
菜单：用户管理
backend_visible: ✅ True
frontend_visible: ❌ False
效果：只在后台显示，前台不显示
```

### 场景2: 仅前台业务的功能
```
菜单：商品浏览
backend_visible: ❌ False
frontend_visible: ✅ True
效果：只在"前台应用"显示，后台侧边栏不显示
```

### 场景3: 前后都需要的功能
```
菜单：系统配置
backend_visible: ✅ True
frontend_visible: ✅ True
效果：前后台都显示
```

### 场景4: 临时隐藏的功能
```
菜单：数据分析
visible: ❌ False
效果：前后台都不显示（总开关）
```

## 📁 文件结构

```
django_layui/
├── rbac/
│   ├── views.py              # 包含 _get_frontend_menus() 和 frontend_menu_tree()
│   └── urls.py               # 添加了 /menus/frontend/ 路由
├── static/layui/pages/
│   └── frontend.html         # 前台页面示例
└── docs/
    └── FRONTEND_MENU_GUIDE.md # 本文档
```

## 🚀 开发指南

### 后端实现

**views.py** 中新增了两个函数：

```python
def _get_frontend_menus(user):
    """获取前台菜单树（只返回 frontend_visible=True 的菜单）"""
    # 过滤条件：status=True, visible=True, frontend_visible=True
    # 根据用户角色获取有权限的菜单
```

```python
@csrf_exempt
@api_login_required
def frontend_menu_tree(request):
    """API: 获取前台菜单树"""
    menus = _get_frontend_menus(request.user)
    return success_response(menus)
```

### 前端实现

**frontend.html** 示例展示了：

1. 调用 `/admin/api/rbac/menus/frontend/` 获取前台菜单
2. 根据返回的菜单数据渲染导航栏
3. 只渲染 `menu_type=2`（菜单类型）的项目
4. 支持点击导航切换内容

### 在你的前台项目中集成

```javascript
// 1. 获取前台菜单
fetch('/admin/api/rbac/menus/frontend/')
    .then(res => res.json())
    .then(data => {
        if (data.code === 200) {
            var menus = data.data;
            // 2. 渲染到你的前台导航中
            renderMyFrontendNav(menus);
        }
    });

// 3. 渲染函数示例
function renderMyFrontendNav(menus) {
    menus.forEach(menu => {
        if (menu.menu_type === 2 && menu.path) {
            // 创建导航项
            createNavItem(menu.name, menu.path, menu.icon);
        }
    });
}
```

## ⚙️ 测试步骤

1. **登录后台管理系统**
   - 访问：`http://127.0.0.1:8000/admin/`

2. **进入菜单管理**
   - 路径：权限管理 > 菜单管理

3. **编辑任意菜单**
   - 关闭"前台可见"开关
   - 保存

4. **访问前台示例页面**
   - 路径：`http://127.0.0.1:8000/static/layui/pages/frontend.html`
   - 该菜单不会出现在前台导航中

5. **重新开启"前台可见"**
   - 保存后刷新前台页面
   - 该菜单会出现在前台导航中

## 🔒 权限说明

- **权限不受可见性影响**：即使 `frontend_visible=False`，只要用户有该权限，仍然可以访问对应API
- **可见性只影响菜单显示**：菜单不在导航中显示，但不阻止直接访问URL
- **如需完全禁止访问**：应从角色中移除对应菜单的权限，而不是只设置 `frontend_visible=False`

## 📝 注意事项

1. **默认值**：所有新建菜单的 `frontend_visible` 默认为 `True`
2. **已有数据**：执行迁移后，已有菜单的 `frontend_visible` 会自动设为 `True`
3. **级联关系**：如果父目录的 `frontend_visible=False`，其子菜单也不会显示
4. **语言支持**：前台菜单也支持多语言（中文/英文）

## 🤝 扩展建议

当前 `frontend.html` 是一个示例页面，你可以根据实际需求扩展：

- [ ] 添加左侧边栏导航（类似后台）
- [ ] 添加 Tab 标签页功能
- [ ] 集成到你的 Vue/React 前台项目中
- [ ] 添加面包屑导航
- [ ] 实现响应式布局（移动端适配）

## 📖 相关文档

- [权限系统指南](./PERMISSION_SYSTEM_GUIDE.md)
- [菜单扩展指南](./MENU_EXTENSION_GUIDE.md)
