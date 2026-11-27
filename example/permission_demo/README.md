# permission_demo 可复制示例应用

该目录是一个最小可复制的 Django App，演示 django-layuix 1.4.2 的：

- 数据范围过滤：`ScopedModelMixin.for_user()`
- ABAC 行级过滤：`filter_queryset()`
- ABAC 字段级过滤：`filter_fields()`
- 按钮权限：`@api_permission_required('demo:order:view')`
- 菜单自动注册与静态 Layui 页面

## 1. 复制到你的项目

```bash
cp -r example/permission_demo /path/to/your/project/
```

## 2. 注册应用

```python
INSTALLED_APPS = [
    'django_layuix',
    'django_layuix.rbac',
    'permission_demo.apps.PermissionDemoConfig',
    # ...
]
```

如果使用静态文件目录，请保证应用静态资源可被发现：

```python
STATICFILES_DIRS = [
    BASE_DIR / 'permission_demo' / 'static',
]
```

## 3. 迁移并初始化示例

```bash
python manage.py migrate
python manage.py init_permission_demo
```

`init_permission_demo` 会创建（缺少超级管理员时也会先创建 `admin / admin123`）：

- 角色继承示例：`demo_base` → `demo_manager`
- SSD 互斥组：`demo_maker_checker_sod`
- 组织节点：`demo_global` → `demo_region` → `demo_team`
- Scope 角色：`demo_sales`（`scope_node=demo_region`, `scope_depth=1`）
- ABAC 策略：大额订单拒绝、成本字段白名单
- 示例用户：`demo_manager_user`、`demo_finance_user`、`demo_scope_user`
- 示例订单数据：`permission_demo` 应用的 3 条订单

默认密码：`Demo@2026`，可用环境变量覆盖：

```powershell
$env:DEMO_PASSWORD='YourStrongPassword'
python manage.py init_permission_demo
```

非 `DEBUG` 环境不会在命令行输出密码；如需查看，追加 `--show-password`。

## 4. 体验方式

1. 用 `admin / admin123` 登录后台。
2. 进入「演示应用 → 示例订单」，可看到全部数据。
3. 用 `demo_scope_user / Demo@2026` 登录：
   - 只能看到 `demo_region` 与 `demo_team` 节点的数据。
   - 大额订单根据 ABAC 策略被过滤。
4. 用 `demo_finance_user / Demo@2026` 登录：
   - 可看到 `cost` 字段。

预期可见数据：

| 用户 | 数据范围 | ABAC 结果 | 可见订单 |
|---|---|---|---|
| `admin` | 全部 | 超管豁免 | 3 条 |
| `demo_scope_user` | 华东区域 + 下一级 | 16000 订单被拒绝 | 1 条（9000） |
| `demo_finance_user` | 全部 | 财务角色豁免大额限制 | 3 条，含 `cost` 字段 |

## 5. API

```text
GET /admin/api/permission-demo/orders/
```

返回：

```json
{
  "code": 200,
  "data": [],
  "fields": ["id", "title", "owner_name", "department", "amount", "cost", "status"],
  "count": 3
}
```

`fields` 会随用户角色与 ABAC 策略动态变化。

## 6. 核心代码

- `models.py`：`ScopedModelMixin` 接入
- `views_api.py`：行级与字段级过滤
- `apps.py`：菜单与 API 路由自动注册
- `management/commands/init_permission_demo_data.py`：示例订单数据

详细示例说明见：[docs/NEW_FEATURES_QUICKSTART.md](../../docs/NEW_FEATURES_QUICKSTART.md)。
