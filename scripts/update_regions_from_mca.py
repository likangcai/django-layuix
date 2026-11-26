#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-26 22:19
# @FileName  : update_regions_from_mca.py
# -----------------------------
"""从民政部公开接口获取官方省/市/县数据。用法：python scripts/update_regions_from_mca.py 或 python scripts/update_regions_from_mca.py --apply。默认接口为民政部国家地名信息库公开接口，maxLevel=3 时返回省、地、县三级数据。"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

DEFAULT_URL = (
    'https://dmfw.mca.gov.cn/xzqh/getList'
    '?code=0&trimCode=true&maxLevel=3'
)
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / 'django_layuix' / 'rbac' / 'data' / 'china_regions.json'


def fetch_payload(url: str, timeout: int = 30) -> dict:
    request = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 django-layuix-region-updater',
        'Referer': 'https://dmfw.mca.gov.cn/XzqhVersionPublish.html',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'X-Requested-With': 'XMLHttpRequest',
    })
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode('utf-8'))


def normalize_code(code: str, name: str) -> str:
    code = str(code or '').strip()
    if code.isdigit():
        return code.ljust(6, '0')
    if name == '台湾省':
        return '710000'
    raise ValueError('unexpected non-numeric region code: %r (%s)' % (code, name))


def flatten(root: dict) -> list[dict]:
    rows = []

    def walk(node: dict, parent_code: str | None) -> None:
        name = str(node.get('name') or '').strip()
        code = normalize_code(node.get('code'), name)
        level = int(node.get('level') or (1 if parent_code is None else 3))
        row = {
            'code': code,
            'name': name,
            'level': level,
            'parent_code': parent_code,
            'type': str(node.get('type') or '').strip(),
            'sort': int(code) if code.isdigit() else 0,
            'note': str(node.get('type') or '').strip(),
            'status': True,
        }
        rows.append(row)
        for child in (node.get('children') or []):
            walk(child, code)

    for province in (root.get('data', {}).get('children') or []):
        walk(province, None)
    return rows


def validate(rows: list[dict]) -> None:
    if len(rows) < 3000:
        raise RuntimeError('official data returned only %s rows; refusing to overwrite seed' % len(rows))
    codes = [row['code'] for row in rows]
    if len(codes) != len(set(codes)):
        raise RuntimeError('official data contains duplicate region codes')
    levels = {}
    for row in rows:
        levels[row['level']] = levels.get(row['level'], 0) + 1
    if levels.get(1, 0) < 30 or levels.get(3, 0) < 2000:
        raise RuntimeError('official data level distribution is abnormal: %r' % levels)


def main() -> int:
    parser = argparse.ArgumentParser(description='Update official China region seed data.')
    parser.add_argument('--url', default=DEFAULT_URL, help='MCA region endpoint')
    parser.add_argument('--output', default=str(DEFAULT_OUTPUT), help='seed JSON path')
    parser.add_argument('--timeout', type=int, default=30)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--apply', action='store_true', help='load seed after writing')
    parser.add_argument(
        '--manage-py', default=str(ROOT / 'example' / 'manage.py'),
        help='manage.py used by --apply',
    )
    args = parser.parse_args()

    payload = fetch_payload(args.url, args.timeout)
    rows = flatten(payload)
    validate(rows)
    output = Path(args.output)
    document = {
        'source': args.url,
        'source_name': '民政部国家地名信息库',
        'fetched_at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'max_level': 3,
        'count': len(rows),
        'regions': rows,
    }
    print('rows=%s levels=%s' % (
        len(rows), {level: sum(1 for row in rows if row['level'] == level) for level in (1, 2, 3)},
    ))
    print('sample=%s ... %s' % (rows[0]['code'], rows[-1]['code']))
    if args.dry_run:
        return 0

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8',
    )
    print('wrote %s' % output)

    if args.apply:
        command = [
            sys.executable, args.manage_py, 'load_regions',
            '--file', str(output), '--truncate',
        ]
        print('running: %s' % ' '.join(command))
        subprocess.run(command, check=True)
    else:
        print('next: python example/manage.py load_regions --file "%s" --truncate' % output)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
