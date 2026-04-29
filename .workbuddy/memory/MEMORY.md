# MEMORY.md - 长期记忆

## 项目背景

用户专注于 Django 生态的 Admin 后台定制化开发，核心项目是 `django-layui`（PyPI 包），基于 Layui 实现现代化 Django Admin 主题替换。

同时维护：
- **QualiFlow**：Vue3 + Django，RBAC 权限平台
- **TestHub**：Django + Vue3，API/UI 自动化平台

## django-layui 项目信息

- **位置**：`d:\chengxu\TestProject\django_layui\`
- **版本**：1.0.2（系统已安装，本地为开发源码）
- **Python**：3.13.5 (`D:\Program Files\Python313\python.exe`)
- **Django**：6.0.4

### 核心功能模块
- `django_layui`：主包，Layui 主题模板覆盖
- `django_layui.rbac`：RBAC 扩展（菜单/角色/用户/操作日志/系统配置）
- `django_layui.ops`：运维扩展（服务器管理/AI日志分析），依赖 paramiko/openai

### 关键设计决策
- `rbac.AppConfig.ready()` 自动注入大量配置（MIDDLEWARE、模板目录、静态文件、API 路由）
- API 路由自动注册到 `/admin/api/rbac/` 和 `/admin/api/ops/`，**不要**在 urls.py 手动配置 ops 路由
- 不能加 `XFrameOptionsMiddleware`，否则侧边栏 iframe 子页面无法加载
- `AUTH_USER_MODEL = 'django_layui_rbac.UserProfile'` 必须项目初始就设置

### example 示例项目
- **位置**：`d:\chengxu\TestProject\django_layui\example\`
- **运行**：`cd example; python manage.py runserver 8000`（http://127.0.0.1:8000/admin/）
- **账号**：admin / admin123
- **演示应用**：`store`（商品分类/商品/订单管理，含 init_demo_data 命令）
- **初始化顺序**：migrate → init_menu → init_demo_data

### 常用命令
```bash
python manage.py migrate            # 建表
python manage.py init_menu          # 初始化 RBAC 菜单/角色/系统配置
python manage.py init_demo_data     # 初始化 store 演示数据
python manage.py runserver 8000
```

## 用户风格偏好

- 务实型，需要解决方案 + 根因分析
- 反馈 Bug 时提供截图 + curl 命令
- 重视注释和文档的可读性
