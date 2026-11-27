# 数据字典使用指南

作者：影子（Yingzi）　版本：v1.1　日期：2026-11-26

## 结论（TL;DR）

【事实】数据字典用于统一维护下拉选项、状态值与业务枚举，字典和字典项都受后端 RBAC 权限控制。
【判断】新业务枚举应先建字典，再由页面或 API 读取启用项，避免在前端复制常量。
【待确认】是否把字典选择器封装为公共表单组件，供所有业务弹窗复用。
【待确认】是否提供按字典生成前端表单选项的 SDK 方法。
【待确认】是否将部门、岗位、地区也纳入统一数据管理模块。

## 1. 定位

数据字典用于统一维护下拉选项、状态值、业务枚举和前后端共用常量。它不是一个页面私有配置，而是后端注册、前端消费的共享数据层。

字典分两级：

- 字典：`code`、名称、描述、状态、排序、是否系统内置。
- 字典项：显示名称、数据值、排序、状态、默认项、样式类、备注。

同一字典内的 `value` 唯一；一个字典项可以标记为默认项。

## 2. 权限与菜单

内置权限码：

| 权限码 | 用途 |
|---|---|
| `dict:view` | 查看字典、读取启用选项 |
| `dict:add` | 新增字典 |
| `dict:edit` | 编辑字典、新增/编辑字典项 |
| `dict:delete` | 删除字典/字典项 |

初始化菜单：

```bash
python manage.py migrate
python manage.py init_menu
```

会补齐：

```text
数据管理
└── 字典管理
```

页面路径：

```text
/static/layui/pages/dict.html
```

菜单路由：

```text
/data/dictionary
```

## 3. 接口

### 3.1 字典列表

```http
GET /admin/api/rbac/dictionaries/?page=1&page_size=20&keyword=order&status=1
```

### 3.2 新增字典

```http
POST /admin/api/rbac/dictionaries/create/
Content-Type: application/json

{"code":"order_status","name":"订单状态","description":"订单流转状态","sort":1,"status":true}
```

### 3.3 编辑/删除字典

```http
PUT    /admin/api/rbac/dictionaries/<id>/
DELETE /admin/api/rbac/dictionaries/<id>/
```

系统内置字典不允许修改编码，也不允许删除。

### 3.4 字典项

```http
GET  /admin/api/rbac/dictionaries/<id>/items/
POST /admin/api/rbac/dictionaries/<id>/items/create/
PUT  /admin/api/rbac/dictionary-items/<id>/
DELETE /admin/api/rbac/dictionary-items/<id>/
```

### 3.5 业务页面读取启用项

```http
GET /admin/api/rbac/dictionaries/options/<code>/
```

只返回启用字典中的启用项，适合前端下拉框、状态映射和业务枚举：

```json
{
  "code": 200,
  "data": [
    {"label": "待支付", "value": "pending", "is_default": true, "sort": 1, "css_class": ""}
  ]
}
```

该接口需要登录并具备 `dict:view`。

## 4. 内置字典

`init_menu` 会幂等补齐：

- `sys_common_status`：启用 / 停用
- `sys_user_gender`：男 / 女 / 保密
- `sys_notice_type`：通知 / 公告

已有字典项不会被覆盖，后续可在字典管理页继续维护。

## 5. 开发约定

- 新业务枚举先建字典，再写页面和表单，避免选项散落在多个页面。
- 状态、类型、级别等可复用值使用字典，不要在前端复制常量表。
- 需要跨前后端协议时，只传稳定 `value`，展示文案由 `label` 或前端翻译提供。
- 系统字典作为基础设施，不建议删除；业务字典可按权限删除。
