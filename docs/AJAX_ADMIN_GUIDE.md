# Django-Layui AJAX Admin 使用指南

## 概述

`LayuiAjaxAdmin` 是实现的AJAX功能增强类,为你的Django Admin添加强大的异步操作能力。

## 核心功能

### 1. AJAX批量操作

无需刷新页面即可执行批量操作,提升用户体验。

### 2. 自定义Action异步调用

将耗时的同步操作改为异步执行,避免页面卡顿。

### 3. Layer弹窗配置

动态配置弹窗参数,支持iframe、HTML内容等多种类型。

### 4. 智能过滤条件处理

自动应用搜索和过滤条件到批量操作中。

## 快速开始

### 基础用法

```python
from django.contrib import admin
from django_layuix.rbac import LayuiAjaxAdmin
from .models import Product


@admin.register(Product)
class ProductAdmin(LayuiAjaxAdmin):
    """商品管理 - 启用AJAX功能"""

    list_display = ['name', 'price', 'status']
    search_fields = ['name', 'sku']
    list_filter = ['status', 'category']

    # 定义批量操作action
    actions = ['batch_publish', 'batch_archive']

    def batch_publish(self, request, queryset):
        """批量发布商品"""
        count = queryset.update(status='published')
        return {
            'msg': f'成功发布 {count} 个商品'
        }

    batch_publish.short_description = '发布选中商品'

    def batch_archive(self, request, queryset):
        """批量归档商品"""
        count = queryset.update(status='archived')
        return {
            'msg': f'成功归档 {count} 个商品'
        }

    batch_archive.short_description = '归档选中商品'
```

### 高级用法:Layer弹窗

```python
from django_layuix.rbac import LayuiAjaxAdmin, layer


@admin.register(Order)
class OrderAdmin(LayuiAjaxAdmin):
    """订单管理"""

    @layer
    def batch_ship(self, request):
        """
        批量发货 - 显示自定义弹窗
        
        返回Layer配置字典
        """
        return {
            'type': 2,  # iframe类型
            'title': '批量发货',
            'content': '/admin/orders/ship-form/',
            'area': ['600px', '500px'],
            'btn': ['确认发货', '取消'],
            'yes': 'doShip()'  # 点击确定执行的JS函数
        }

    batch_ship.short_description = '批量发货'

    @layer
    def export_orders(self, request):
        """导出订单 - 带选项的弹窗"""
        return {
            'type': 1,  # 页面层
            'title': '导出订单',
            'content': '''
                <div style="padding: 20px;">
                    <form id="exportForm">
                        <label>导出格式:</label>
                        <select name="format">
                            <option value="xlsx">Excel</option>
                            <option value="csv">CSV</option>
                        </select>
                        
                        <label>时间范围:</label>
                        <input type="date" name="start_date" />
                        <input type="date" name="end_date" />
                        
                        <button type="button" onclick="doExport()">导出</button>
                    </form>
                </div>
            ''',
            'area': ['500px', '400px']
        }

    export_orders.short_description = '导出订单'
```

### 复杂场景:带确认的操作

```python
@admin.register(User)
class UserAdmin(LayuiAjaxAdmin):
    """用户管理"""
    
    def batch_activate(self, request, queryset):
        """批量激活用户"""
        # 可以在这里添加业务逻辑
        count = queryset.update(is_active=True)
        
        # 发送通知邮件
        for user in queryset:
            send_activation_email(user)
        
        return {
            'msg': f'已激活 {count} 个用户,并发送通知邮件'
        }
    batch_activate.short_description = '激活选中用户'
    
    def batch_delete_soft(self, request, queryset):
        """软删除用户(标记为删除状态)"""
        count = queryset.update(deleted_at=timezone.now())
        
        return {
            'msg': f'已将 {count} 个用户标记为删除',
            'icon': 'warning'  # 前端可根据此字段显示不同图标
        }
    batch_delete_soft.short_description = '软删除用户'
```

## 前端调用方式

### JavaScript调用

```javascript
// 在列表页调用AJAX action
function callAjaxAction(actionName) {
    var selected = getSelectedIds();  // 获取选中的ID
    
    $.ajax({
        url: '/admin/app/model/ajax/',
        type: 'POST',
        data: {
            _action: actionName,
            _selected: selected.join(','),
            select_across: selected.length > 0 ? '1' : '0',
            _search: $('#searchInput').val(),  // 搜索条件
            _filter: JSON.stringify(getFilters())  // 过滤条件
        },
        success: function(res) {
            if (res.status === 'success') {
                layer.msg(res.msg, {icon: 1});
                reloadTable();
            } else if (res.status === 'redirect') {
                window.location.href = res.url;
            } else {
                layer.msg(res.msg, {icon: 2});
            }
        },
        error: function(xhr) {
            layer.msg('操作失败: ' + xhr.responseText, {icon: 2});
        }
    });
}
```

### 获取Layer配置

```javascript
// 获取弹窗配置并打开
function openLayerPopup(actionName) {
    $.ajax({
        url: '/admin/app/model/layer/',
        type: 'POST',
        data: {
            _action: actionName
        },
        success: function(config) {
            layer.open(config);
        }
    });
}
```

## 返回值说明

### 成功响应

```python
# 方式1: 简单消息
return {'msg': '操作成功'}

# 方式2: 带额外数据
return {
    'msg': '处理完成',
    'data': {
        'processed': 100,
        'failed': 5
    }
}
```

### 重定向响应

```python
from django.http import HttpResponseRedirect

def my_action(self, request, queryset):
    # ... 处理逻辑
    return HttpResponseRedirect('/admin/success-page/')
```

### 直接返回JsonResponse

```python
from django.http import JsonResponse

def my_action(self, request, queryset):
    # 完全自定义响应
    return JsonResponse({
        'custom_field': 'value',
        'another_field': [1, 2, 3]
    })
```

## 与django-simpleui对比

| 特性 | django-simpleui | django-layui |
|------|----------------|---------------|
| AJAX批量操作 | ✅ | ✅ |
| Layer弹窗配置 | ✅ | ✅ |
| 搜索条件过滤 | ✅ | ✅ |
| 自定义过滤 | ✅ | ✅ |
| 返回值灵活性 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 错误处理 | 基础 | 完善(日志+traceback) |
| 文档完整性 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 代码注释 | 英文 | 中文+详细示例 |

## 最佳实践

### 1. 耗时操作使用异步

```python
import threading

def batch_process(self, request, queryset):
    """批量处理 - 异步执行"""
    
    def process_async():
        for obj in queryset:
            # 耗时操作
            heavy_processing(obj)
    
    thread = threading.Thread(target=process_async)
    thread.start()
    
    return {
        'msg': '后台处理中,请稍后查看结果',
        'async': True
    }
```

### 2. 事务保护

```python
from django.db import transaction

def batch_update(self, request, queryset):
    """批量更新 - 事务保护"""
    try:
        with transaction.atomic():
            count = queryset.update(status='updated')
            log_batch_operation(request.user, count)
        
        return {'msg': f'成功更新 {count} 条记录'}
    except Exception as e:
        return {
            'status': 'error',
            'msg': f'更新失败: {str(e)}'
        }
```

### 3. 权限检查

```python
def sensitive_operation(self, request, queryset):
    """敏感操作 - 权限检查"""
    if not request.user.is_superuser:
        return {
            'status': 'error',
            'msg': '只有管理员可以执行此操作'
        }
    
    # 执行操作...
```

## 常见问题

### Q: 如何获取当前选中的数据?

A: 通过 `_get_queryset_with_filters()` 方法自动获取,已应用所有过滤条件。

### Q: 返回值必须是字典吗?

A: 可以是字典、JsonResponse、HttpResponseRedirect或None,框架会自动处理。

### Q: 如何处理大量数据?

A: 建议使用异步处理或分页处理,避免阻塞请求。

### Q: Layer弹窗如何传递参数?

A: 在layer配置的content中使用URL参数,或在JS中通过postMessage传递。

## 总结

`LayuiAjaxAdmin` 提供了强大而灵活的AJAX功能,让Django Admin的交互体验更加流畅。相比django-simpleui,我们提供了:

- ✅ 更完善的错误处理和日志记录
- ✅ 更灵活的返回值类型
- ✅ 更详细的中文文档和示例
- ✅ 更好的代码可读性和可维护性

开始使用吧,让你的Admin后台焕然一新! 🚀
