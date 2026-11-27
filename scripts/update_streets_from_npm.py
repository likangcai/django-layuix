#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-26 22:19
# @FileName  : update_streets_from_npm.py
# -----------------------------
"""从 china-division 数据包刷新第 4 级乡镇/街道种子。update_regions_from_mca.py 使用的民政部官方接口只提供省/市/县三级数据；本脚本不修改基础文件，只写入 django_layuix/rbac/data/china_streets.json。县区父级不在当前基础种子中的行会被跳过。"""
from __future__ import annotations

import argparse
import io
import json
import sys
import tarfile
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / 'django_layuix' / 'rbac' / 'data' / 'china_regions.json'
OUTPUT_PATH = ROOT / 'django_layuix' / 'rbac' / 'data' / 'china_streets.json'
REGISTRY_URL = 'https://registry.npmmirror.com/china-division/latest'


def fetch_json(url: str, timeout: int = 60):
    request = urllib.request.Request(url, headers={'User-Agent': 'django-layuix-region-updater/1.0'})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode('utf-8'))


def extract_pcas(tarball: bytes) -> list:
    with tarfile.open(fileobj=io.BytesIO(tarball), mode='r:gz') as archive:
        member = archive.extractfile('package/dist/pcas-code.json')
        if member is None:
            raise ValueError('package/dist/pcas-code.json not found')
        return json.loads(member.read().decode('utf-8'))


def collect_streets(nodes: list, county_codes: set[str]) -> tuple[list[dict], dict[str, int]]:
    streets: list[dict] = []
    skipped: dict[str, int] = {}

    def walk(items: list, parent_code: str | None = None):
        for item in items:
            code = str(item.get('code') or '').strip()
            name = str(item.get('name') or '').strip()
            children = item.get('children') or []
            if len(code) == 9:
                if parent_code and parent_code in county_codes:
                    streets.append({
                        'code': code,
                        'name': name,
                        'level': 4,
                        'parent_code': parent_code,
                        'sort': int(code),
                        'status': True,
                    })
                else:
                    skipped[parent_code or ''] = skipped.get(parent_code or '', 0) + 1
            walk(children, code)

    walk(nodes)
    return streets, skipped


def main() -> int:
    parser = argparse.ArgumentParser(description='Refresh town/street region seed from china-division')
    parser.add_argument('--base', default=str(BASE_PATH), help='base province/city/county seed')
    parser.add_argument('--output', default=str(OUTPUT_PATH), help='street seed output path')
    parser.add_argument('--registry', default=REGISTRY_URL, help='npm registry metadata URL')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    base = json.loads(Path(args.base).read_text(encoding='utf-8'))
    base_rows = base.get('regions') if isinstance(base, dict) else base
    county_codes = {
        str(row.get('code') or '').strip()
        for row in base_rows or []
        if int(row.get('level') or 0) in (1, 2, 3)
    }

    metadata = fetch_json(args.registry)
    tarball_url = metadata.get('dist', {}).get('tarball')
    if not tarball_url:
        raise ValueError('npm metadata does not contain dist.tarball')
    request = urllib.request.Request(tarball_url, headers={'User-Agent': 'django-layuix-region-updater/1.0'})
    with urllib.request.urlopen(request, timeout=120) as response:
        tarball = response.read()

    pcas = extract_pcas(tarball)
    streets, skipped = collect_streets(pcas, county_codes)
    if not streets:
        raise ValueError('no street rows matched the current county seed')
    codes = [row['code'] for row in streets]
    if len(codes) != len(set(codes)):
        raise ValueError('duplicate street codes found')

    payload = {
        'source': 'npm china-division %s / 国家统计局行政区划整理' % metadata.get('version', ''),
        'source_name': '国家统计局行政区划（china-division 整理）',
        'fetched_at': datetime.now(timezone.utc).isoformat(),
        'max_level': 4,
        'count': len(streets),
        'skipped_unmatched': sum(skipped.values()),
        'regions': streets,
    }
    action = 'would write' if args.dry_run else 'wrote'
    if not args.dry_run:
        Path(args.output).write_text(
            json.dumps(payload, ensure_ascii=False, separators=(',', ':')),
            encoding='utf-8',
        )
    print('%s %s rows to %s (skipped=%s)' % (
        action, len(streets), args.output, payload['skipped_unmatched'],
    ))
    print('levels=%s' % {1: 0, 2: 0, 3: len(county_codes), 4: len(streets)})
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        print('ERROR: %s' % exc, file=sys.stderr)
        raise SystemExit(1)
