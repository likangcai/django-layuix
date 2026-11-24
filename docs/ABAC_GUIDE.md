# ABAC 表达式权限使用指南

版本：v1.0　适用版本：django-layuix 1.4.2+

## 结论（TL;DR）
【事实】1.4.2 提供 `AbacPolicy` 与无外部依赖的安全表达式引擎，支持行级和字段级控制。
【判断】未配置任何策略时全部放行；命中 deny 时拒绝；超级管理员默认豁免。
【待确认】是否后续把表达式下推为 ORM `Q` 对象，以提升大数据量过滤性能。
【待确认】是否增加策略模拟回放与命中日志。
【待确认】是否提供策略模板市场或更多内置模板。

---

## 1. 表达式语法

| 类型 | 示例 | 说明 |
|---|---|---|
| 逻辑运算 | `and` / `or` / `not` | 支持括号调整优先级 |
| 比较运算 | `==` `!=` `>` `>=` `<` `<=` | 数字、字符串、布尔值比较 |
| 包含判断 | `'finance' in user.roles` | 判断右侧列表/字符串是否包含左侧值 |
| 包含判断 | `user.roles contains 'finance'` | 与上例等价 |
| 路径访问 | `resource.amount`、`user.department` | 只能读取上下文中的字段 |
| 字面量 | `'文本'`、`123`、`true`、`false`、`null` | 不使用 `eval` |

表达式不能调用函数、导入模块或访问上下文外的 Python 对象。非法表达式会在 API 保存时被拒绝。

## 2. 后台 UI 示例

进入：

```text
权限管理 → ABAC 策略
```

新建策略示例：

```text
名称:     大额订单需财务角色
资源:     store.Order
动作:     view
字段:     （留空，表示行级）
效果:     拒绝
优先级:   10
表达式:   resource.amount > 10000 and 'finance' not in user.roles
```

保存后，普通用户查看 `store.Order` 时：

- `amount <= 10000`：允许。
- `amount > 10000` 且没有 `finance` 角色：拒绝。
- 超级管理员：默认豁免。

## 3. API 创建示例

```http
POST /admin/api/rbac/abac-policies/
Content-Type: application/json
```

```json
{
  "name": "大额订单需财务角色",
  "resource": "store.Order",
  "action": "view",
  "field": "",
  "effect": "deny",
  "expression": "resource.amount > 10000 and 'finance' not in user.roles",
  "priority": 10,
  "is_active": true
}
```

其它端点：

```text
GET    /admin/api/rbac/abac-policies/
GET    /admin/api/rbac/abac-policies/<id>/
PUT    /admin/api/rbac/abac-policies/<id>/
DELETE /admin/api/rbac/abac-policies/<id>/
POST   /admin/api/rbac/abac-check/
```

## 4. 行级权限示例

在业务 API 中替换普通查询：

```python
from django_layuix.rbac.abac import filter_queryset


def order_list(request):
    queryset = filter_queryset(
        Order.objects.all(),
        request.user,
        'view',
        'store.Order',
    )
    return JsonResponse({'data': list(queryset.values())})
```

当前实现为 Python 层逐行评估，并按主键生成过滤后的 QuerySet。数据量大时建议先按业务条件缩小 QuerySet，再调用 `filter_queryset()`。

## 5. 字段级权限示例

先创建字段白名单策略：

```text
名称:     成本字段仅财务可见
资源:     store.Order
动作:     view
字段:     cost
效果:     允许
优先级:   10
表达式:   'finance' in user.roles
```

业务代码：

```python
from django_layuix.rbac.abac import filter_fields


def order_detail(request, pk):
    order = Order.objects.get(pk=pk)
    fields = filter_fields(
        request.user,
        'view',
        'store.Order',
        ['id', 'amount', 'cost'],
    )
    data = {field: getattr(order, field) for field in fields}
    return JsonResponse(data)
```

没有 `finance` 角色时，`cost` 会从返回字段中移除。

## 6. 策略调试

```http
POST /admin/api/rbac/abac-check/
```

```json
{
  "user_id": 3,
  "action": "view",
  "resource": "store.Order",
  "context": {
    "resource": {"amount": 20000}
  }
}
```

返回：

```json
{
  "code": 200,
  "data": {
    "allowed": false,
    "matched": [12],
    "errors": []
  }
}
```

`matched` 是命中的策略 ID；`errors` 返回表达式求值错误，便于排查策略配置问题。

## 7. 常见策略模板

### 7.1 只看本人创建的数据

```text
字段:     （留空）
效果:     允许
表达式:   resource.owner_id == user.id
```

### 7.2 只在本部门查看

```text
字段:     （留空）
效果:     允许
表达式:   resource.department == user.department
```

### 7.3 工作时间限制

```text
字段:     （留空）
效果:     拒绝
表达式:   time.hour < 9 or time.hour >= 18
```

### 7.4 敏感字段需要审批角色

```text
字段:     salary
效果:     允许
表达式:   'hr' in user.roles or 'admin' in user.roles
```

## 8. 决策规则

1. 没有匹配策略：允许。
2. 命中任意 `deny`：拒绝。
3. 字段白名单：存在字段级 `allow` 策略时，必须至少命中一条才可见。
4. 超级管理员：默认豁免。
5. 表达式错误：记录到检查结果，不直接放开或拒绝业务请求。
