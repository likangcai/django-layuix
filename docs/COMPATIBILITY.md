# 版本兼容性说明

作者：影子（Yingzi）　版本：v1.2　更新日期：2026-11-27

## 1. 结论

【事实】项目自身 67 个 Python 文件已用 Python 3.8 语法解析器全量检查，0 语法错误；未使用 `list[str]`、`X | Y` 注解、`match`、PEP 604/585 等 3.9+ 语法。

【判断】核心包支持 **Python 3.8–3.13** 与 **Django 4.2–6.0**，但 Django 版本受 Python 版本约束，不能任意组合。

- 声明最低：Python 3.8、Django 4.2。
- CI 实际验证：Python 3.10–3.13（安装全部可选依赖）。
- Python 3.8/3.9 已做语法与 API 审计，但不在当前 CI 矩阵中，因为部分可选依赖（如较新版本 `webssh`）可能不再支持旧 Python。
- 【待确认】是否需要把 CI 扩展到 Python 3.8/3.9；如需扩展，建议只测核心依赖并单独验证可选依赖。

## 2. 推荐组合矩阵

| Python | 推荐 Django | 说明 |
|---|---|---|
| 3.8 | 4.2 | Django 5.0+ 要求 Python >=3.10；Django 4.2 是该 Python 版本下唯一受支持组合 |
| 3.9 | 4.2 | Django 5.0+ 要求 Python >=3.10 |
| 3.10 | 4.2 / 5.0 / 5.1 / 5.2 / 6.0 | 全功能可用，CI 覆盖 |
| 3.11 | 4.2 / 5.0 / 5.1 / 5.2 / 6.0 | 全功能可用，CI 覆盖 |
| 3.12 | 4.2 / 5.0 / 5.1 / 5.2 / 6.0 | 全功能可用，CI 覆盖 |
| 3.13 | 5.1 / 5.2 / 6.0 | Django 5.1+ 支持，CI 覆盖 |

【判断】新项目建议直接使用 **Python 3.12 + Django 5.2/6.0**；需要长期维护且受旧环境约束时使用 **Python 3.8/3.9 + Django 4.2 LTS**。

## 3. 关键兼容处理

| 场景 | 处理方式 |
|---|---|
| Django 4.2–5.x 语言切换 | 写 `request.session['_language']` |
| Django 6 语言切换 | LocaleMiddleware 只认 Cookie，代码同时写 `django_language` Cookie |
| Django 6 移除 `LANGUAGE_SESSION_KEY` | 不再 import 该常量 |
| Django 4.2–6.x 迁移记录器差异 | `MigrationRecorder.migration_qs` 与 `Migration.objects` 双入口 |
| Python 3.8 entry_points | 同时兼容 `.select(group=...)` 与 `.get(group, [])` |
| Python 3.8 无 `tomllib` | 运行时代码不使用；仅 CI 3.13 工作流使用 |

## 4. 可选依赖

| 依赖 | Python 3.8/3.9 | 说明 |
|---|---|---|
| `Django>=4.2` | Python 3.8/3.9 固定解析到 Django 4.2 LTS | Python 3.13 需 Django 5.1+ |
| `psutil>=5.9.0` | 支持 | 核心依赖，Dashboard 使用 |
| `Pillow>=9.0.0` | 支持，pip 自动解析到兼容版本 | 核心依赖，`UserProfile.avatar` 的 `ImageField` 需要 |
| `paramiko>=2.0` | 支持 | `ops` extra |
| `webssh>=1.6.0` | 需按实际版本确认 | 新版可能要求 Python >=3.10 |
| `openai>=1.0` | 需按实际版本确认 | `ai` extra，建议 Python >=3.10 |

## 5. 前端依赖

| 资源 | 当前内置版本 | 说明 |
|---|---|---|
| Layui | 2.13.9 | 内置 `layui.js` / `layui.css` / 字体资源均来自官方 2.13.9 发行包 |
| ECharts | 项目内现有版本 | Dashboard 使用，未随 Layui 升级改动 |

### 2.13.9 兼容处理

- 新增 `form.filterDisabled` 配置，默认显式设置为 `false`，保持旧版本中 disabled 字段参与取值的行为。
- 如需排除 disabled 字段，可在 `LAYUI_CONFIG` 中设置 `form_filter_disabled: True`。
- 本项目未使用 2.13.9 修复的 `treeTable.addNodes()` 与 `tabs.add(mode)` 路径；表格、树、Tab、表单渲染已在冒烟中回归。
- 2.13.8 起 `layui.extend` 路径拼接、table 表头宽度、table 内嵌 form 动态渲染、`form.getValue` 同名字段数组处理均有修复；本项目相关页面需按最新资源回归。

### API 跨站来源防护

- 管理 API 同时支持会话与 Bearer Token，因此框架默认注入 `ApiOriginGuardMiddleware`。
- 会话 Cookie 的写请求如果带有跨站 `Origin` / `Referer`，会被拒绝；Bearer Token 请求不受影响。
- 跨域前端推荐使用 Bearer Token，不需要放宽 Session Cookie 的 `SameSite` 行为。
- 如需临时关闭，可设置 `LAYUIX_DISABLE_API_ORIGIN_GUARD = True`，但不建议在生产环境使用。
- 反向代理场景若外部域名与内部 `Host` 不同，请设置 `USE_X_FORWARDED_HOST = True` 或显式配置 `LAYUIX_API_ALLOWED_ORIGINS = ['admin.example.com']`。
- 修改 Admin 挂载路径时，同步设置 `LAYUIX_API_PREFIXES = ['/new-admin/api/']`，否则来源防护不会覆盖新路径。

【判断】Python 3.8/3.9 用户建议只安装核心包；如使用 `ops`/`ai`，请先在目标环境验证可选依赖可用性。
- 【待确认】是否给 `Django` 增加 `<7` 上限，以避免未来主版本升级造成静默破坏。
- 【待确认】是否在 `ops` / `ai` extras 中标注最低 Python 版本，减少 pip 解析到不兼容版本的概率。

## 6. 升级建议

- 如果当前 Django < 4.2：必须先升级到 4.2 LTS；低于 4.2 的版本已不在支持范围内。
- 如果当前 Python < 3.10：不要直接安装 Django 5/6；先确认 pip 解析结果。
- 升级前执行：
  ```bash
  python manage.py check
  python manage.py makemigrations --check --dry-run django_layuix_rbac
  python manage.py test django_layuix.rbac
  ```

## 7. 文档索引

- `pyproject.toml`：声明 `requires-python`、依赖与分类器。
- `README.md`：环境要求摘要。
- `docs/RELEASE_GUIDE.md`：CI 发布矩阵。
