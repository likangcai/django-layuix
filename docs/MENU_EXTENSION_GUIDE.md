# django-layuix 菜单扩展指南

## 结论（TL;DR）
【事实】外部 App 可通过 `register_menus()` 注册菜单与按钮权限，无需修改库源码。
【判断】菜单注册是幂等操作，适合插件与业务应用自包含接入。
【本期不做】自动为所有新菜单分配角色权限。
【待确认】是否提供菜单注册的命令式 dry-run。
【待确认】是否支持从 YAML/JSON 声明菜单。
【待确认】是否补充前端动态路由生成工具。

---

## 问题背景

每新增一个 app 就去修改 django-layuix 库的源码是不现实的。django-layuix 作为 pip 安装的第三方库，提供了**菜单注册 API**，允许外部项目动态添加菜单，无需修改库源码。

## 快速开始（三步完成）

### 第1步：创建 API 视图

```python
# myapp/views_api.py
import json
from decimal import Decimal
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django_layuix.rbac.views import api_login_required, get_request_body, success_response, error_response
from .models import MyModel


@csrf_exempt
@api_login_required
def mymodel_list(request):
   """GET /admin/api/myapp/mymodel/ - 列表（含分页/搜索）"""
   queryset = MyModel.objects.all().order_by('-id')

   keyword = request.GET.get('keyword', '').strip()
   if keyword:
      queryset = queryset.filter(name__icontains=keyword)

   total = queryset.count()
   try:
      page = int(request.GET.get('page', 1))
   except (ValueError, TypeError):
      page = 1
   try:
      page_size = int(request.GET.get('page_size', 10))
   except (ValueError, TypeError):
      page_size = 10
   page_size = max(1, min(page_size, 100))
   offset = (page - 1) * page_size
   items = queryset[offset:offset + page_size]

   data = [{'id': m.id, 'name': m.name} for m in items]
   return success_response({'list': data, 'total': total})


@csrf_exempt
@api_login_required
def mymodel_create(request):
   """POST /admin/api/myapp/mymodel/create/ - 创建"""
   if request.method != 'POST':
      return error_response('Method not allowed', 405)
   body = get_request_body(request)
   name = body.get('name', '').strip()
   if not name:
      return error_response('名称不能为空', 400)
   obj = MyModel.objects.create(name=name)
   return success_response({'id': obj.id}, msg='创建成功')


@csrf_exempt
@api_login_required
def mymodel_detail(request, pk):
   """GET/PUT/DELETE /admin/api/myapp/mymodel/<pk>/ - 详情/更新/删除"""
   try:
      obj = MyModel.objects.get(pk=pk)
   except MyModel.DoesNotExist:
      return error_response('记录不存在', 404)

   if request.method == 'GET':
      return success_response({'id': obj.id, 'name': obj.name})
   elif request.method == 'PUT':
      body = get_request_body(request)
      if 'name' in body:
         obj.name = body['name'].strip()
      obj.save()
      return success_response(msg='更新成功')
   elif request.method == 'DELETE':
      obj.delete()
      return success_response(msg='删除成功')
   return error_response('Method not allowed', 405)
```

### 第2步：注册 URL 路由（必须 patch 到 admin site 内部）

> ⚠ **重要**：必须通过 `site.get_urls` 补丁注入到 admin site 内部，**不能**写在项目级 `urls.py` 中！
> 否则路由会被 admin site 的 `catch_all_view` 拦截，返回 404 或登录页面。

```python
# myapp/urls.py
from django.urls import path
from . import views_api

urlpatterns = [
    path('mymodel/', views_api.mymodel_list, name='myapp_mymodel_list'),
    path('mymodel/create/', views_api.mymodel_create, name='myapp_mymodel_create'),
    path('mymodel/<int:pk>/', views_api.mymodel_detail, name='myapp_mymodel_detail'),
]
```

```python
# myapp/apps.py
from django.apps import AppConfig


class MyappConfig(AppConfig):
   default_auto_field = 'django.db.models.BigAutoField'
   name = 'myapp'
   verbose_name = '我的应用'

   def ready(self):
      try:
         from django_layuix.rbac.menu_registry import register_menus
         # 必须先导入 admin.py 确保模型注册
         import myapp.admin  # noqa: F401

         # 注册菜单与按钮
         register_menus(
            menus_data=[
               # (名称, 图标, 路径, 类型, 排序, 父菜单)
               ('我的应用', 'layui-icon-app', '', 1, 10, None),
               ('数据管理', 'layui-icon-table',
                '/static/myapp/pages/mymodel.html', 2, 1, '我的应用'),
            ],
            buttons_data=[
               # (按钮名, 所属菜单, 权限标识, 排序)
               ('新增数据', '数据管理', 'mymodel:add', 1),
               ('编辑数据', '数据管理', 'mymodel:edit', 2),
               ('删除数据', '数据管理', 'mymodel:delete', 3),
            ]
         )

         # 注册 API 路由到 admin site 内部
         self._register_api_urls()

      except Exception as e:
         print(f"Warning: Could not initialize myapp: {e}")

   def _register_api_urls(self):
      """⚠ 必须通过 site.get_urls 补丁注入"""
      from django.contrib.admin import site
      from django.urls import path, include
      from . import urls as myapp_urls

      original_get_urls = site.get_urls

      def patched_get_urls():
         urls = original_get_urls()
         custom_urls = [
            path('api/myapp/', include((myapp_urls.urlpatterns, 'myapp'))),
         ]
         return custom_urls + urls

      site.get_urls = patched_get_urls
```

### 第3步：创建前端页面

前端页面放在 `myapp/static/myapp/pages/mymodel.html`，访问路径为 `/static/myapp/pages/mymodel.html`。

**核心要点 — 使用 `url` 服务端分页模式（不要用 `data: list`）：**

```html
<script src="/static/layui/lib/layui.js"></script>
<script src="/static/layui/js/common.js"></script>
<script>
inheritTheme();

layui.use(['table', 'form', 'layer'], function(){
    var table = layui.table;
    var form = layui.form;
    var layer = layui.layer;
    var $ = layui.$;

    var tableIns = null;

    // ✅ 使用 url 参数（服务端分页）
    // 不要使用 data: list + page.count，那会导致分页总数不准
    function loadTable() {
        tableIns = table.render({
            elem: '#mytable',
            url: '/admin/api/myapp/mymodel/',
            toolbar: '#toolbarTpl',
            defaultToolbar: [],
            where: getSearchParams(),
            height: 'full-220',
            page: {
                limit: 10,
                limits: [10, 30, 50, 100],
                layout: ['count', 'prev', 'page', 'next', 'skip', 'limit']
            },
            parseData: function(res) {
                return {
                    "code": res.code === 200 ? 0 : res.code,
                    "msg": res.msg,
                    "count": res.data ? res.data.total : 0,
                    "data": res.data ? res.data.list : []
                };
            },
            // ✅ 告诉 Layui 使用 ?page=&page_size= 参数名
            request: {
                pageName: 'page',
                limitName: 'page_size'
            },
            cols: [[
                {field: 'id', title: 'ID', width: 70, align: 'center'},
                {field: 'name', title: '名称', minWidth: 200},
                {title: '操作', width: 250, align: 'center', toolbar: '#operateTpl'}
            ]]
        });
    }
});
</script>
```

---

## 菜单注册参数说明

### menus_data — 菜单列表

每个元素为元组：`(name, icon, path, menu_type, sort, parent_name_or_None)`

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| name | str | 菜单名称 | `'数据管理'` |
| icon | str | Layui图标类名 | `'layui-icon-table'` |
| path | str | 前端页面地址 | `'/static/myapp/pages/mymodel.html'` |
| menu_type | int | 1=目录, 2=菜单, 3=按钮 | `2` |
| sort | int | 排序号（越小越靠前） | `1` |
| parent_name | str/None | 父菜单名称，顶级为None | `'我的应用'` |

> **路径格式说明**：`path` 指向静态 HTML 页面，格式为 `/static/<app_label>/pages/<page>.html`。
> 页面文件放在 `myapp/static/myapp/pages/` 目录下，Django 会自动发现。

### buttons_data — 按钮权限列表

每个元素为元组：`(btn_name, parent_menu_name, permission, sort)`

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| btn_name | str | 按钮名称 | `'新增数据'` |
| parent_menu_name | str | 所属菜单名称（必须与 menus_data 中的 name 一致） | `'数据管理'` |
| permission | str | 权限标识（建议 `app:action` 格式） | `'mymodel:add'` |
| sort | int | 排序号 | `1` |

---

## 常见问题排查

### ❌ 分页显示"共 N 条"不正确

**症状**：API 返回 `total=33`，但页面显示"共 10 条"。

**原因**：使用了 `data: list`（客户端数据），`page.count` 被 Layui 忽略，
分页数取决于传入数组长度。

**修复**：改用 `url` 参数 + `parseData` + `request` 服务端分页模式。

### ❌ 按钮权限变为"孤儿菜单"（parent=None）

**症状**：菜单管理页面中按钮显示为顶级菜单而不是挂在对应菜单下。

**原因**：`register_menus` 内部使用 `get_or_create(name=btn_name)`，
如果同名按钮已存在（如之前被 `auto_register_admin_apps` 创建过），
`get_or_create` **不会更新 parent 字段**。

**修复**：先删除孤儿按钮，再重启让 `register_menus` 重新创建：

```python
# 修复脚本
from django_layuix.rbac.models import Menu

Menu.objects.filter(name__in=['新增数据', '编辑数据', '删除数据'], parent__isnull=True).delete()
```

然后重启 Django 进程（`AppConfig.ready()` 会重新执行）。

### ❌ API 路由返回登录页面而不是 JSON

**症状**：访问 `/admin/api/myapp/mymodel/` 返回 HTML 登录页面。

**原因**：路由被 admin site 的 `catch_all_view` 拦截。

**修复**：必须将路由通过 `site.get_urls` 补丁注册到 admin site 内部，
**不能**放在项目级 `urls.py` 中。

### ❌ 弹窗新增/编辑按钮只有「返回」「保存」

在 HTML 模板中为弹窗底部设置两个按钮：

```html
<div class="layui-form-item" style="display:flex;justify-content:flex-end;gap:8px;border-top:1px solid var(--border-color);padding-top:15px;margin-top:10px;">
    <button type="button" class="layui-btn layui-btn-sm layui-btn-primary" id="addFormCancel">返回</button>
    <button type="button" class="layui-btn layui-btn-sm" lay-submit lay-filter="addSubmit">保存</button>
</div>
```

---

## 完整示例

参考 `example/store/` 目录：

| 文件 | 说明 |
|------|------|
| `store/apps.py` | 菜单注册 + API 路由注册 |
| `store/views_api.py` | Category/Product/Order 三个模型的 CRUD API |
| `store/urls.py` | API 路由 |
| `store/admin.py` | Django admin 注册（精简，仅保留基础配置） |
| `store/static/store/pages/category.html` | 商品分类前端页面 |
| `store/static/store/pages/product.html` | 商品管理前端页面 |
| `store/static/store/pages/order.html` | 订单管理前端页面 |

---

## 注意事项

1. **不要混用 `auto_register_admin_apps` 和 `register_menus`** — 前者为同一 app 注册后，
   后者再用同名按钮会因 `get_or_create` 不会更新 parent 而导致菜单关联错乱。
2. **不要在主 `urls.py` 中挂载 app 的 API 路由** — 必须通过 `site.get_urls` 补丁注入。
3. **不要使用 `data: list` 模式渲染表格** — 分页总数显示不正确，请用 `url` 服务端分页。
4. **前端页面必须通过 `inheritTheme()` 同步父页面主题**（已在模板中提供）。
5. **使用 `layer.open` 弹窗做新增/编辑**，弹窗底部只有「返回」「保存」两个按钮。
