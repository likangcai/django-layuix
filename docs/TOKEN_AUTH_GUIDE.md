# 纯跨域 Token 认证接入指南

版本：v3.0　适用版本：django-layuix 1.4.5+

## 结论（TL;DR）
【事实】`api_login_required` 与 `api_permission_required` 统一通过 `resolve_api_user()` 解析 Session 或 Bearer Token。
【事实】1.4.4 起签发标准 HS256 JWT，包含 `jti`，状态写入 `sys_auth_token` 与 Django cache（可配置为 Redis）。
【判断】跨域前端推荐使用 Bearer Token，避免依赖会话 Cookie 的 SameSite 行为。
【本期不做】OAuth2 / OpenID Connect 服务端能力；刷新 Token。
【待确认】是否补充设备维度的 Token 管理页。
【待确认】是否提供定期清理过期 Token 的定时任务。
【待确认】是否增加 `aud`/`nbf` 声明。

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

Token 为三段式标准 JWT：

```text
base64url(header).base64url(payload).base64url(HMAC-SHA256)
```

payload 包含 `sub / user_id / username / iat / exp / jti / iss`，以及可选 `active_roles`。`TOKEN_EXPIRE_SECONDS` 控制有效期，默认 24 小时；`iss` 由 `LAYUI_JWT_ISSUER` 配置。

每次签发都会在 `sys_auth_token` 写入 `jti`、签发/过期时间和来源信息，并同步写入 Django cache。配置为 Redis 后，多实例共享撤销状态。撤销操作先验签并绑定当前用户，防止伪造 `jti` 吊销他人 Token；旧版两段式 Token 的撤销指纹同样落库。退出登录撤销当前 Token；修改密码、管理员重置密码、禁用用户会撤销该用户全部 Token。

## 3. 请求携带

```javascript
fetch('/admin/api/rbac/userinfo/', {
  headers: {Authorization: 'Bearer ' + token}
});
```

同时支持 `X-Token` 请求头。显式 Token 优先于 Session，避免同一请求携带两种身份时主体混淆。普通 API 不再从 POST body 读取 Token。

`?token=` 查询参数默认关闭。SSE 使用短时 `stream_ticket`：先调用 `/admin/api/rbac/system/info/stream-ticket/` 获取 60 秒票据，再用 `?stream_ticket=...` 建立 EventSource，避免把 JWT 写入 URL、浏览器历史或访问日志。

## 4. 前端权限数据流

1. 用 Token 调 `/admin/api/rbac/userinfo/` 获取 `permissions` 与后台 `menus`。
2. 用 Token 调 `/admin/api/rbac/menus/frontend/` 获取前台菜单树。
3. 前端路由守卫按 `path`/`component` 映射到本地路由；按钮用权限码控制 `v-if` / `disabled`。
4. 所有业务 API 必须在服务端挂 `api_permission_required('模块:动作')`，前端隐藏不可替代后端校验。

## 5. DSD 激活角色

Token 场景下没有 Cookie，激活角色直接签入 JWT 的 `active_roles` 声明。切换后必须替换本地 Token，否则仍使用旧角色集合。

单实例默认使用 Django 本地内存缓存即可；多实例部署请配置 Redis，使 Token 撤销状态在所有实例间共享。

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

会话写请求必须携带 `Origin` 或 `Referer`。相关配置：

```python
TOKEN_EXPIRE_SECONDS = 86400
LAYUI_JWT_ISSUER = 'django-layuix'
LAYUIX_ALLOW_LEGACY_TOKEN = True
LAYUIX_TOKEN_CACHE_PREFIX = 'layuix:auth:'
LAYUIX_API_PREFIXES = ['/admin/api/']
LAYUIX_PUBLIC_API_PATHS = ['/admin/api/rbac/login/', '/admin/api/rbac/register/']
LAYUIX_API_ALLOWED_ORIGINS = ['admin.example.com']
```

`LAYUIX_DISABLE_API_ORIGIN_GUARD=True` 仅用于临时排障，生产不建议开启。

## 7. 安全边界

- 仅 HTTPS 传输 Token。
- 不把 Token 写入日志、URL 或 localStorage 之外的持久化位置（视安全要求可选内存存储）。
- 权限判定始终以服务端为准，前端权限码只用于体验优化。
