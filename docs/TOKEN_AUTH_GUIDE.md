# 纯跨域 Token 认证接入指南

版本：v1.0　适用版本：django-layuix 1.4.2+

## 结论（TL;DR）
【事实】`api_login_required` 与 `api_permission_required` 统一通过 `resolve_api_user()` 解析 Session 或 Bearer Token。
【判断】跨域前端推荐使用 Bearer Token，避免依赖会话 Cookie 的 SameSite 行为。
【本期不做】OAuth2 / OpenID Connect 服务端能力。
【待确认】是否提供 Token 撤销列表。
【待确认】是否支持刷新 Token。
【待确认】是否补充设备维度的 Token 管理页。

---

## 1. 结论

`api_login_required` 与 `api_permission_required` 现已统一走 `resolve_api_user()`：**Session 优先，未登录时自动解析 Bearer Token**。因此 Vue/React 独立前端可以在不携带 Cookie 的情况下调用所有 RBAC API。

## 2. 获取 Token

```javascript
const res = await fetch('/admin/api/rbac/login/', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({username: 'admin', password: '***'})
});
const token = (await res.json()).data.token;
```

Token 有效期默认 24 小时（`TOKEN_EXPIRE_SECONDS`），密码变更后立即失效。停用用户无法通过 Token 认证。

## 3. 请求携带

```javascript
fetch('/admin/api/rbac/userinfo/', {
  headers: {Authorization: 'Bearer ' + token}
});
```

同时支持 `X-Token` 请求头与 `?token=` 查询参数（后者仅供 SSE 等无法设置请求头的场景，生产不推荐）。

## 4. 前端权限数据流

1. 用 Token 调 `/admin/api/rbac/userinfo/` 获取 `permissions` 与后台 `menus`。
2. 用 Token 调 `/admin/api/rbac/menus/frontend/` 获取前台菜单树。
3. 前端路由守卫按 `path`/`component` 映射到本地路由；按钮用权限码控制 `v-if` / `disabled`。
4. 所有业务 API 必须在服务端挂 `api_permission_required('模块:动作')`，前端隐藏不可替代后端校验。

## 5. DSD 激活角色

Token 场景下没有 Cookie，激活角色写入服务端缓存（键含用户 ID，有效期同 Token）。切换后下一次请求即生效。

- 单实例默认使用 Django 本地内存缓存即可。
- 【已确认】多实例部署引入 Redis 共享缓存，否则各实例看到的激活角色不一致。

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

## 6. 跨域配置

```python
CORS_ALLOWED_ORIGINS = ['http://localhost:5173']
CORS_ALLOW_HEADERS += ['authorization', 'x-token']
```

Token 模式不需要 `CORS_ALLOW_CREDENTIALS=True`；若同时保留 Session，才需要开启并配置 SameSite。

## 7. 安全边界

- 仅 HTTPS 传输 Token。
- 不把 Token 写入日志、URL 或 localStorage 之外的持久化位置（视安全要求可选内存存储）。
- 权限判定始终以服务端为准，前端权限码只用于体验优化。
