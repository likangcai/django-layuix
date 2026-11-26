# 前端组件与设计 Token 规范

版本：v1.0　适用版本：django-layuix 1.4.2+

## 结论（TL;DR）
【事实】后台统一使用 `admin.css` 中的设计 token 与 `common.js` 暴露的 `LayuiUI.table/dialog/virtualTable` 组件。
【判断】通用列表和表单弹窗应复用组件，树、卡片、图表、详情内嵌表格等特殊情况保留独立实现。
【事实】大数据量只读列表可改用 `LayuiUI.virtualTable()`，只渲染可视行。
【本期不做】强制重写所有历史页面为虚拟滚动表格；不引入新的前端框架。
【待确认】是否发布独立 npm 包。
【待确认】是否为虚拟滚动表格增加列宽拖拽与列配置持久化。
【待确认】是否提供虚拟滚动表格的服务端分页混合模式。

---

## 1. 设计 Token

| 类别 | Token | 值 | 用途 |
|---|---|---|---|
| 间距 | `--space-1` ~ `--space-6` | 4 / 8 / 12 / 16 / 20 / 24px | 所有组件间距 |
| 控件高度 | `--control-height-sm/md/lg` | 30 / 36 / 38px | 输入框、下拉框、按钮 |
| 按钮高度 | `--button-height-xs/sm/md` | 24 / 30 / 38px | 行内操作、工具栏、主操作 |
| 圆角 | `--radius-sm/md/lg` | 4 / 6 / 8px | 小标签、输入框、卡片 |
| 表单标签 | `--form-label-width` | 120px | 表单与查询区标签 |
| 查询控件 | `--search-input-width` / `--search-select-width` | 200 / 160px | 默认查询输入宽度 |

禁止在页面中重复写固定高度、内边距和圆角；优先使用上述变量。

## 2. 按钮规范

| 场景 | 类名 | 高度 | 使用方式 |
|---|---|---:|---|
| 行内操作 | `layui-btn layui-btn-xs` | 24px | 表格操作列 |
| 工具栏/查询按钮 | `layui-btn layui-btn-sm` | 30px | 新增、刷新、查询、重置 |
| 弹窗主按钮 | `layui-btn` | 38px | 弹窗保存/确认 |

按钮样式由 `.layui-btn` 统一控制：

- 圆角：`var(--button-radius)`
- 焦点：`focus-visible` 显示主色轮廓
- 主按钮：`layui-btn-normal`
- 次级按钮：`layui-btn-primary`
- 危险操作：`layui-btn-danger`
- 行内禁用：`btn-disabled`，透明度 0.4 且不可点击

## 3. 查询区规范

查询区使用 `.search-bar` 或 `.search-card`：

```html
<div class="search-bar">
  <form class="layui-form" lay-filter="searchForm">
    <div class="layui-form-item">
      <div class="layui-inline">
        <label class="layui-form-label">关键词</label>
        <div class="layui-input-inline">
          <input name="keyword" class="layui-input">
        </div>
      </div>
      <div class="layui-inline search-btns">
        <button class="layui-btn layui-btn-sm">查询</button>
        <button class="layui-btn layui-btn-sm layui-btn-primary">重置</button>
      </div>
    </div>
  </form>
</div>
```

规范：

- 查询区与表格间距：16px。
- 查询项之间横向间距：16px，纵向换行间距：8px。
- 输入框默认宽度 200px，下拉框默认宽度 160px。
- 查询按钮与输入框同高。
- 查询结束后表格重置到第一页。

## 4. 列表组件

通用组件：

```js
LayuiUI.table({
    elem: '#demoTable',
    url: '/admin/api/demo/',
    request: {pageName: 'page', limitName: 'page_size'},
    parseData: function(res) {
        return {code: res.code, msg: res.msg, count: res.count, data: res.data};
    },
    cols: [[/* columns */]]
});
```

默认配置：

- 高度：`full-220`
- 分页：10 / 30 / 50 / 100
- 布局：`count prev page next skip limit`
- `defaultToolbar: []`
- 斑马纹开启

特殊页面允许覆盖：

```js
LayuiUI.table({elem: '#treeTable', data: rows, page: false, cols: [cols]});
```

不需要分页的例外：

- 树形菜单
- ABAC 策略卡片列表
- 组织节点树
- AI 配置全集列表
- 详情内嵌表格
- 明确要求一次展示全部数据的页面

除上述例外外，所有列表默认必须有分页。

### 4.1 虚拟滚动表格

大数据量只读列表使用：

```js
LayuiUI.virtualTable({
    elem: '#bigTable',
    height: 520,
    rowHeight: 38,
    buffer: 8,
    data: rows,
    cols: [[
        {field: 'id', title: 'ID', width: 80},
        {field: 'name', title: '名称', minWidth: 180}
    ]]
});
```

规则：

- 只渲染可视区域加上下缓冲行。
- `rowHeight` 必须与实际行高一致。
- `pageMode: 'server'` 为服务端分页混合模式，滚动到底部时按 `page/pageSize` 续载并保留已加载行。
- `parseData()` 可返回 `{data, total/count}`；`code` 支持 `0` 与 `200`。
- `tableKey` 开启列宽拖拽并持久化到 `localStorage`，列宽从本地读取时按白名单校验。
- 返回实例提供 `setData()` / `refresh()` / `rows()` / `loadPage()` / `retry()` / `state()`。
- HTTP 401 会触发统一登录过期流程；加载失败显示就地重试按钮。
- 模板函数返回值默认转义，确需输出 HTML 时返回 `{__html: html}`。
- 需要编辑、排序、分页的列表仍使用 `LayuiUI.table()`。

## 5. 弹窗组件

通用组件：

```js
LayuiUI.dialog({
    title: '编辑示例',
    tplId: 'editFormTpl',
    filter: 'editForm',
    data: row,
    area: ['620px', '520px'],
    onSubmit: function(layero, index) {
        // 校验并提交；返回 false 阻止关闭
    },
    success: function(layero, index) {
        // 可选：额外初始化联动
    }
});
```

规范：

- 1.4.4 起所有历史 `layer.open()` 已迁移到 `LayuiUI.dialog()`；组件会保留原有 `btn/yes/cancel/end` 行为，并统一回填表单、翻译与关闭逻辑。
- 1.4.5 角色授权使用独立授权弹窗：权限树、搜索、全展开/折叠、选中计数与幂等保存，避免与角色基本信息表单耦合。
- `standard: true` 时由组件提供保存/取消按钮，取消按钮会显式关闭当前弹窗。
- 弹窗内容区最大高度 `80vh`。
- 保存成功后精确关闭当前弹窗，不再使用 `layer.closeAll()`。
- 特殊弹窗（终端、日志实时刷新、图表）仍通过同一入口进入，但可保留业务专属回调。

## 6. 页面分类

| 类型 | 示例 | 是否通用列表 |
|---|---|---|
| 标准 CRUD 列表 | 用户、角色、配置、服务器、日志、商品、分类、订单 | 是 |
| 树形页面 | 菜单、组织节点 | 否 |
| 卡片列表 | ABAC 策略、约束管理 | 否 |
| 表单/详情 | 个人中心、前台首页、404 | 否 |
| 图表/监控 | 仪表盘 | 否 |

## 7. 迁移建议

1. 新页面必须先使用 `LayuiUI.table` 与 `LayuiUI.dialog`。
2. 老页面修改列表或弹窗时顺手迁移到组件。
3. 特殊页面保留独立样式，但必须使用 design token。
4. 禁止继续新增页面内联宽度/高度；使用 `.w-*` / `.h-*` 工具类或既有间距变量。
5. 问号提示必须提供 `aria-describedby` 指向隐藏说明文本，不能只依赖悬浮气泡。
6. 查询区按钮与输入框统一使用 md 高度。
