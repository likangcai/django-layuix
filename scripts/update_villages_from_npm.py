#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-26 22:19
# @FileName  : update_villages_from_npm.py
# -----------------------------
"""Refresh level-5 village/community seed data from the china-division package.

The output is gzip-compressed because the raw JSON is about 75MB. Villages whose
street parent is absent from the current bundled streets are skipped.
"""
from __future__ import annotations

import argparse
import gzip
import io
import json
import sys
import tarfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / 'django_layuix' / 'rbac' / 'data' / 'china_regions.json'
STREET_PATH = ROOT / 'django_layuix' / 'rbac' / 'data' / 'china_streets.json'
OUTPUT_PATH = ROOT / 'django_layuix' / 'rbac' / 'data' / 'china_villages.json.gz'
REGISTRY_URL = 'https://registry.npmmirror.com/china-division/latest'


def fetch_json(url: str, timeout: int = 60):
    request = urllib.request.Request(url, headers={'User-Agent': 'django-layuix-region-updater/1.0'})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode('utf-8'))


def extract_member(tarball: bytes, name: str):
    with tarfile.open(fileobj=io.BytesIO(tarball), mode='r:gz') as archive:
        member = archive.extractfile(name)
        if member is None:
            raise ValueError('%s not found' % name)
        return json.loads(member.read().decode('utf-8'))


def main() -> int:
    parser = argparse.ArgumentParser(description='Refresh village/community seed from china-division')
    parser.add_argument('--base', default=str(BASE_PATH))
    parser.add_argument('--streets', default=str(STREET_PATH))
    parser.add_argument('--output', default=str(OUTPUT_PATH))
    parser.add_argument('--registry', default=REGISTRY_URL)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    base = json.loads(Path(args.base).read_text(encoding='utf-8'))
    base_rows = base.get('regions') if isinstance(base, dict) else base
    street_payload = json.loads(Path(args.streets).read_text(encoding='utf-8'))
    street_rows = street_payload.get('regions') if isinstance(street_payload, dict) else street_payload
    parent_codes = {
        str(row.get('code') or '').strip()
        for row in (base_rows or []) + (street_rows or [])
        if row.get('code')
    }

    metadata = fetch_json(args.registry)
    tarball_url = metadata.get('dist', {}).get('tarball')
    if not tarball_url:
        raise ValueError('npm metadata does not contain dist.tarball')
    request = urllib.request.Request(tarball_url, headers={'User-Agent': 'django-layuix-region-updater/1.0'})
    with urllib.request.urlopen(request, timeout=180) as response:
        tarball = response.read()

    villages = extract_member(tarball, 'package/dist/villages.json')
    rows = []
    skipped = 0
    for item in villages:
        parent = str(item.get('streetCode') or '').strip()
        code = str(item.get('code') or '').strip()
        name = str(item.get('name') or '').strip()
        if not code or not name:
            continue
        if parent not in parent_codes:
            skipped += 1
            continue
        rows.append({
            'code': code,
            'name': name,
            'level': 5,
            'parent_code': parent,
            'sort': int(code),
            'status': True,
        })
    codes = [row['code'] for row in rows]
    if not rows or len(codes) != len(set(codes)):
        raise ValueError('village rows are empty or contain duplicate codes')

    payload = {
        'source': 'npm china-division %s / 国家统计局行政区划整理' % metadata.get('version', ''),
        'source_name': '国家统计局行政区划（china-division 整理）',
        'fetched_at': datetime.now(timezone.utc).isoformat(),
        'max_level': 5,
        'count': len(rows),
        'skipped_unmatched': skipped,
        'regions': rows,
    }
    if not args.dry_run:
        raw = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        Path(args.output).write_bytes(gzip.compress(raw, 6))
    print('%s %s rows to %s (skipped=%s)' % (
        'would write' if args.dry_run else 'wrote',
        len(rows), args.output, skipped,
    ))
    print('levels=%s' % {1: 0, 2: 0, 3: 0, 4: 0, 5: len(rows)})
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        print('ERROR: %s' % exc, file=sys.stderr)
        raise SystemExit(1)
