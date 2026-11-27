# 地区维护脚本

这些脚本用于维护仓库内的地区种子，不是运行时依赖。

## 打包说明

- `sdist` 会包含 `scripts/*.py` 和 `docs/`，便于从源码包更新种子。
- `wheel` 只包含 `django_layuix/rbac/data/*.json` 与 `*.gz`，不会把维护脚本安装到虚拟环境。
- 已安装用户可使用管理命令加载种子：

```bash
python manage.py load_regions --include-villages
```

## 脚本

```bash
# 民政部官方省/市/县
python scripts/update_regions_from_mca.py --dry-run
python scripts/update_regions_from_mca.py

# 街道/乡镇
python scripts/update_streets_from_npm.py --dry-run
python scripts/update_streets_from_npm.py

# 村/社区（输出 gzip）
python scripts/update_villages_from_npm.py --dry-run
python scripts/update_villages_from_npm.py
```

街道与村庄脚本依赖 `registry.npmmirror.com` 的 `china-division` 包；网络不可用时可保留现有种子，不影响安装和运行。

## 建议

如果希望发布后也能直接更新，请把脚本逻辑抽到 `django_layuix.rbac` 包内，并新增管理命令；当前只把种子数据打进 wheel，避免在用户环境中写入仓库路径。
