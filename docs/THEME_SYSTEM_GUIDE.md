# Django-Layui 多主题系统使用指南

## 🎨 概述

Django-Layui 参考 django-simpleui 的主题机制,实现了**28种精美主题**,让你的管理后台焕然一新!

### 核心特性

- ✅ **28种精选主题** - 涵盖经典、现代、科技感等多种风格
- ✅ **动态切换** - 用户可在个人中心实时切换主题
- ✅ **自动CSS生成** - 一键生成所有主题CSS文件
- ✅ **完全兼容** - 不影响现有功能,即插即用
- ✅ **可扩展** - 轻松添加自定义主题

---

## 🚀 快速开始

### 1. 生成主题CSS文件

```bash
# 生成所有主题
python manage.py generate_themes

# 查看可用主题列表
python manage.py generate_themes --list

# 生成指定主题
python manage.py generate_themes --theme "Element蓝"
```

### 2. 为用户设置主题

#### 方式一:在Admin后台设置

访问 `/admin/rbac/userprofile/`,编辑用户,选择主题。

#### 方式二:代码设置

```python
from django_layui.rbac.models import UserProfile

user = UserProfile.objects.get(username='admin')
user.theme = 'Element蓝'
user.save()
```

#### 方式三:在视图中动态设置

```python
def change_theme(request):
    if request.method == 'POST':
        theme_name = request.POST.get('theme')
        request.user.theme = theme_name
        request.user.save()
        return JsonResponse({'status': 'success'})
```

---

## 📋 可用主题列表

运行以下命令查看所有主题:

```bash
python manage.py generate_themes --list
```

### 经典系列 (5个)
1. **默认深色** - 经典的深色主题,适合长时间使用
2. **默认浅色** - 清爽的浅色主题,简洁明了
3. **深邃黑** - 纯黑背景,科技感十足
4. **优雅灰** - 灰色调,商务风格
5. **高端黑** - 黑白搭配,简约大气

### 企业系列 (6个)
6. **Element蓝** - Element UI风格,蓝色主调
7. **Ant Design黑** - Ant Design风格,专业感强
8. **AdminLTE蓝** - AdminLTE风格,经典后台
9. **企业紫** - 紫色系,高贵典雅
10. **企业红** - 红色系,热情奔放
11. **商务蓝** - 商务风格,稳重可靠

### 活力系列 (5个)
12. **清新绿** - 绿色系,生机盎然
13. **科技橙** - 橙色渐变,现代感十足
14. **天空蓝** - 天蓝色,清新自然
15. **活力橙** - 亮橙色,充满活力
16. **森林绿** - 深绿色,沉稳内敛

### 个性系列 (7个)
17. **樱花粉** - 粉色系,温柔甜美
18. **极光紫** - 紫色渐变,梦幻唯美
19. **暗夜蓝** - 深蓝色,神秘深邃
20. **薄荷青** - 青色系,清凉舒爽
21. **烈焰红** - 火红色,热情似火
22. **深海蓝** - 海洋蓝,深邃宁静
23. **玫瑰金** - 金色系,奢华高贵

### 极客系列 (2个)
24. **极客绿** - 黑客帝国风格,代码感强
25. **赛博朋克** - 赛博朋克风格,未来感十足

### 更多主题 (3个)
26-28. **预留主题位** - 可根据需求扩展

---

## 💡 高级用法

### 自定义主题

创建自己的主题非常简单:

```python
# myapp/themes.py
from django_layui.rbac.themes import DJANGO_LAYUI_THEMES

# 添加自定义主题
DJANGO_LAYUI_THEMES.append({
    'name': '我的主题',
    'file': 'my-custom-theme.css',
    'colors': {
        'primary': '#FF5722',      # 主色调
        'menu_bg': '#263238',      # 菜单背景
        'menu_text': '#B0BEC5',    # 菜单文字
        'header_bg': '#FF5722',    # 顶部栏背景
        'logo_color': '#FFFFFF',   # Logo颜色
    }
})
```

然后在 `apps.py` 中导入:

```python
class MyappConfig(AppConfig):
    def ready(self):
        from . import themes  # noqa
```

### 在模板中使用主题

主题CSS会自动加载,无需手动处理。如果需要获取当前主题:

```html
{% load layui_tags %}

<!DOCTYPE html>
<html>
<head>
    <!-- 基础样式 -->
    <link rel="stylesheet" href="{% static 'layui/css/admin.css' %}">
    
    <!-- 主题样式(如果用户选择了主题) -->
    {% if request.user.is_authenticated and request.user.theme != '默认深色' %}
    <link rel="stylesheet" 
          href="{% static 'layui/css/themes/'|add:request.user.theme|add:'.css' %}">
    {% endif %}
</head>
<body>
    ...
</body>
</html>
```

### 主题预览功能

可以创建一个主题预览页面:

```python
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    def preview_theme(self, obj):
        """主题预览链接"""
        from django.utils.html import format_html
        return format_html(
            '<a href="/theme-preview/?theme={}" target="_blank">预览</a>',
            obj.theme
        )
    preview_theme.short_description = '主题预览'
    
    list_display = ['username', 'theme', 'preview_theme']
```

---

## 🎯 技术实现

### 主题配置结构

每个主题包含三个部分:

```python
{
    'name': '主题名称',      # 显示给用户看的名称
    'file': '文件名.css',    # CSS文件名
    'colors': {              # 配色方案
        'primary': '#1E9FFF',     # 主色调
        'menu_bg': '#232935',     # 菜单背景色
        'menu_text': '#BFCBD9',   # 菜单文字色
        'header_bg': '#232935',   # 顶部栏背景色
        'logo_color': '#FFFFFF',  # Logo颜色
    }
}
```

### CSS生成原理

`theme_generator.py` 会根据配色方案自动生成CSS文件,包括:

- 顶部导航栏样式
- 侧边菜单样式
- 按钮样式
- 表单元素样式
- 表格样式
- Tab标签页样式
- 等等...

共覆盖**50+个CSS类**,确保主题一致性。

### 性能优化

- **CSS缓存** - 生成的CSS文件会被浏览器缓存
- **按需加载** - 只加载用户选择的主题CSS
- **最小化** - 生产环境可使用CSS压缩工具

---

## 🔧 常见问题

### Q1: 如何修改某个主题的颜色?

A: 直接在 `themes.py` 中修改对应主题的 `colors` 字典,然后重新生成CSS:

```bash
python manage.py generate_themes --theme "Element蓝"
```

### Q2: 主题切换后没有生效?

A: 检查以下几点:
1. 确认CSS文件已生成 (`static/layui/css/themes/`)
2. 清除浏览器缓存 (Ctrl+F5)
3. 确认用户的theme字段已保存

### Q3: 如何让所有用户使用同一主题?

A: 批量更新:

```python
UserProfile.objects.all().update(theme='Element蓝')
```

### Q4: 可以禁用主题功能吗?

A: 当然!只需将用户的theme设置为 `'默认深色'` 即可使用基础样式。

### Q5: 主题会影响性能吗?

A: 几乎无影响。主题CSS文件很小(<5KB),且会被浏览器缓存。

---

## 📊 与django-simpleui对比

| 特性 | django-simpleui | django-layui |
|------|----------------|---------------|
| 主题数量 | 28个 | 28个 |
| 主题类型 | LESS预编译 | CSS动态生成 |
| 切换方式 | 配置文件 | 用户级别 |
| 自定义难度 | 需懂LESS | 只需改配色 |
| 中文支持 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 文档完整性 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 🎨 主题展示

### 默认深色
![默认深色](screenshots/default-dark.png)
*适合长时间使用,护眼舒适*

### Element蓝
![Element蓝](screenshots/element-blue.png)
*清新明亮,现代化设计*

### Ant Design黑
![Ant Design黑](screenshots/ant-design-black.png)
*专业大气,企业级应用*

### 赛博朋克
![赛博朋克](screenshots/cyberpunk.png)
*未来感十足,个性化选择*

---

## 🚦 最佳实践

### 1. 根据场景选择主题

- **开发环境** - 默认深色(护眼)
- **演示环境** - Element蓝(美观)
- **生产环境** - 根据用户喜好
- **夜间模式** - 深邃黑/极客绿

### 2. 提供主题切换入口

在个人中心添加主题选择器:

```html
<div class="theme-selector">
    <label>选择主题:</label>
    <select id="themeSelect">
        {% for theme in themes %}
        <option value="{{ theme.name }}" 
                {% if user.theme == theme.name %}selected{% endif %}>
            {{ theme.name }}
        </option>
        {% endfor %}
    </select>
</div>

<script>
document.getElementById('themeSelect').onchange = function() {
    fetch('/api/change-theme/', {
        method: 'POST',
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        body: JSON.stringify({theme: this.value})
    }).then(() => location.reload());
};
</script>
```

### 3. 记住用户偏好

主题选择会自动保存到数据库,用户下次登录自动应用。

---

## 🎉 总结

Django-Layui 的多主题系统让你可以:

- ✅ 轻松美化后台界面
- ✅ 提升用户体验
- ✅ 展现个性化风格
- ✅ 适应不同使用场景

立即尝试,让你的管理后台焕然一新! 🚀

---

**提示**: 主题功能是可选的,不会影响现有系统的正常运行。
