# 发布流程说明

版本：v1.0　适用：GitHub Actions

## 1. 结论

已提发布流程：推送 `v*` Tag 后自动运行测试、构建 `sdist`/`wheel` 并发布到 PyPI，不再需要本地手动 `twine upload`。

工作流文件：`.github/workflows/release.yml`

## 2. 触发方式

```bash
# 先确认 pyproject.toml 的 version，例如 1.4.0
git tag v1.4.0
git push origin v1.4.0
```

Tag 版本必须与 `pyproject.toml` 的 `[project].version` 完全一致，否则构建任务会失败。

也可以在 GitHub Actions 页面手动触发 `Release`，此时只执行测试与构建，不发布（因为 `publish` job 要求 Tag ref）。

## 3. 发布前配置（二选一）

### 方式 A：PyPI API Token（推荐先用这个）

在 GitHub 仓库 `Settings → Secrets and variables → Actions` 新建 Secret：

- 名称：`PYPI_API_TOKEN`
- 值：PyPI 账户的 API Token（`pypi-` 开头）

工作流检测到该 Secret 后自动使用 Token 发布。

### 方式 B：Trusted Publishing（OIDC，无需长期 Token）

1. 在 PyPI 项目页面添加 Trusted Publisher：
   - Owner：`likangcai`（按实际仓库所属账号填写）
   - Repository：`django-layuix`
   - Workflow：`release.yml`
   - Environment：`pypi`
2. 不要配置 `PYPI_API_TOKEN`，工作流会使用 OIDC 发布。

## 4. 流程阶段

| 阶段 | 内容 | 失败处理 |
|---|---|---|
| test | Python 3.10–3.13 安装依赖、Django check、22 项 RBAC 测试 | 修复代码后重推 Tag |
| build | 校验 Tag 与版本号、构建 sdist/wheel、`twine check` | 修正版本号或打包配置 |
| publish | 下载构建产物并发布到 PyPI | 检查 Token/OIDC 配置后重跑 job |

## 5. 发布后验证

```bash
pip install --upgrade django-layuix
python -c "import django_layuix; print(django_layuix.__version__)"
```

同时检查 PyPI 页面是否出现对应版本，以及 `sdist`/`wheel` 是否都上传成功。

## 6. 回滚

PyPI 不支持删除已发布版本。若版本有严重问题：

1. 在 PyPI 后台将该版本标记为 yanked；
2. 修复后发布新补丁版本；
3. 不要删除已推送的 Git Tag，避免用户校验来源失败。
