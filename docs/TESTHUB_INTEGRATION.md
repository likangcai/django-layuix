# TestHub 平台集成评估

版本：v1.0　评估日期：2026-11-23

## 1. 结论

【判断】可以集成，但不是“装个主题就自动获得完整权限”。需要分四层处理：后台外观、权限数据模型、认证体系统一、业务 API 鉴权。

## 2. 目标项目现状

- 后端：Django 4.2 + DRF + SimpleJWT + MySQL 8 + Redis + Celery/Channels + simpleui。
- 前端：Vue 3 + Vite + Element Plus + Pinia + Vue Router + Axios。
- 用户模型：`AUTH_USER_MODEL='users.User'`，继承 AbstractUser，无自定义 Role 表，部门为字符串。
- 路由：`/admin/` 与 `/api/...` 平行；前端 SPA 独立部署。

## 3. 四层方案

### 第 1 层：替换 Admin 外观
移除 `simpleui`，加入 `django_layuix` 与 `django_layuix.rbac`，放在 `django.contrib.admin` 之前，移除 `XFrameOptionsMiddleware`，执行迁移与 `init_menu`。

### 第 2 层：权限数据模型（方案已确认）
【已确认】允许迁移 `AUTH_USER_MODEL` 到 `django_layuix_rbac.UserProfile`；本次仅确认方案，不实施代码适配。

### 第 3 层：认证体系统一
保留 TestHub 的 SimpleJWT，不改成项目自带 Token。使用通用桥接：

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'django_layuix.integrations.drf.SimpleJWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'django_layuix.integrations.drf.LayuiRBACPermission',
    ],
}
```

详见 `docs/INTEGRATION_GUIDE.md`。

### 第 4 层：业务 API 鉴权
在 TestHub DRF 视图声明 `layui_permission` 或 `layui_permission_map`，由 `LayuiRBACPermission` 强制校验；前端菜单/按钮由 `/userinfo/`、`/menus/frontend/` 提供。

## 4. 验收清单

- [ ] `/admin/` 使用 Layui 主题，simpleui 已移除。
- [ ] 同一账号在后台与 Vue 前端看到一致的菜单和权限码。
- [ ] 直接调用 TestHub 业务 API 越权返回 403。
- [ ] JWT 与 RBAC API 认证不冲突，无双 Token 并存问题。

## 5. 风险

| 风险 | 等级 | 缓解 |
|---|---|---|
| AUTH_USER_MODEL 迁移失败 | 高 | 测试库全量演练，准备回滚脚本 |
| JWT 与自带 Token 并存 | 中 | 统一使用通用认证桥接 |
| 按钮权限漏配 | 中 | 从核心模块逐步挂权限码 |
| simpleui 残留 | 低 | 检查 INSTALLED_APPS 与静态收集 |
