# 版本兼容性说明

版本：v1.0　更新日期：2026-11-23

## 1. 结论

【事实】项目自身 67 个 Python 文件已用 Python 3.8 语法解析器全量检查，0 语法错误；未使用 `list[str]`、`X | Y` 注解、`match`、PEP 604/585 等 3.9+ 语法。

【判断】核心包支持 **Python 3.8–3.13** 与 **Django 3.2–6.0**，但 Django 版本受 Python 版本约束，不能任意组合。

- 声明最低：Python 3.8、Django 3.2。
- CI 实际验证：Python 3.10–3.13（安装全部可选依赖）。
- Python 3.8/3.9 已做语法与 API 审计，但不在当前 CI 矩阵中，因为部分可选依赖（如较新版本 `webssh`）可能不再支持旧 Python。
- 【待确认】是否需要把 CI 扩展到 Python 3.8/3.9；如需扩展，建议只测核心依赖并单独验证可选依赖。

## 2. 推荐组合矩阵

| Python | 推荐 Django | 说明 |
|---|---|---|
| 3.8 | 3.2 / 4.2 | Django 5.0+ 要求 Python >=3.10；建议使用 Django 4.2 LTS |
| 3.9 | 3.2 / 4.2 | Django 5.0+ 要求 Python >=3.10 |
| 3.10 | 4.2 / 5.0 / 5.1 / 5.2 / 6.0 | 全功能可用，CI 覆盖 |
| 3.11 | 4.2 / 5.0 / 5.1 / 5.2 / 6.0 | 全功能可用，CI 覆盖 |
| 3.12 | 4.2 / 5.0 / 5.1 / 5.2 / 6.0 | 全功能可用，CI 覆盖 |
| 3.13 | 5.1 / 5.2 / 6.0 | Django 5.1+ 支持，CI 覆盖 |

【判断】新项目建议直接使用 **Python 3.12 + Django 5.2/6.0**；需要长期维护且受旧环境约束时使用 **Python 3.8/3.9 + Django 4.2 LTS**。

## 3. 关键兼容处理

| 场景 | 处理方式 |
|---|---|
| Django 3.2–5.x 语言切换 | 写 `request.session['_language']` |
| Django 6 语言切换 | LocaleMiddleware 只认 Cookie，代码同时写 `django_language` Cookie |
| Django 6 移除 `LANGUAGE_SESSION_KEY` | 不再 import 该常量 |
| Django 3.2–6.x 迁移记录器差异 | `MigrationRecorder.migration_qs` 与 `Migration.objects` 双入口 |
| Python 3.8 entry_points | 同时兼容 `.select(group=...)` 与 `.get(group, [])` |
| Python 3.8 无 `tomllib` | 运行时代码不使用；仅 CI 3.13 工作流使用 |

## 4. 可选依赖

| 依赖 | Python 3.8/3.9 | 说明 |
|---|---|---|
| `Django>=3.2` | 支持，pip 自动解析到兼容版本 | 新项目建议 Django 4.2 LTS |
| `psutil>=5.9.0` | 支持 | 核心依赖，Dashboard 使用 |
| `paramiko>=2.0` | 支持 | `ops` extra |
| `webssh>=1.6.0` | 需按实际版本确认 | 新版可能要求 Python >=3.10 |
| `openai>=1.0` | 需按实际版本确认 | `ai` extra，建议 Python >=3.10 |

【判断】Python 3.8/3.9 用户建议只安装核心包；如使用 `ops`/`ai`，请先在目标环境验证可选依赖可用性。
- 【待确认】是否给 `Django` 增加 `<7` 上限，以避免未来主版本升级造成静默破坏。
- 【待确认】是否在 `ops` / `ai` extras 中标注最低 Python 版本，减少 pip 解析到不兼容版本的概率。

## 5. 升级建议

- 如果当前 Django < 4.2：建议先升级到 4.2 LTS，再升级 Python。
- 如果当前 Python < 3.10：不要直接安装 Django 5/6；先确认 pip 解析结果。
- 升级前执行：
  ```bash
  python manage.py check
  python manage.py makemigrations --check --dry-run django_layuix_rbac
  python manage.py test django_layuix.rbac
  ```

## 6. 文档索引

- `pyproject.toml`：声明 `requires-python`、依赖与分类器。
- `README.md`：环境要求摘要。
- `docs/RELEASE_GUIDE.md`：CI 发布矩阵。
