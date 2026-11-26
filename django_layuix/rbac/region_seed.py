# -*- coding: utf-8 -*-
"""Load the bundled China province/city/county seed into Region."""
import json
from pathlib import Path

from django.db import transaction

DEFAULT_SEED_PATH = Path(__file__).resolve().parent / 'data' / 'china_regions.json'


def load_regions_from_file(path=None, truncate=False, dry_run=False):
    from .models import Region

    seed_path = Path(path) if path else DEFAULT_SEED_PATH
    if not seed_path.exists():
        raise FileNotFoundError('region seed not found: %s' % seed_path)
    payload = json.loads(seed_path.read_text(encoding='utf-8'))
    rows = payload.get('regions') if isinstance(payload, dict) else payload
    if not isinstance(rows, list) or not rows:
        raise ValueError('region seed is empty or invalid')

    codes = [str(row.get('code') or '').strip() for row in rows]
    if any(not code for code in codes) or len(codes) != len(set(codes)):
        raise ValueError('region seed contains empty or duplicate codes')

    if dry_run:
        return {
            'total': len(rows),
            'created': 0,
            'updated': 0,
            'deleted': 0,
            'dry_run': True,
        }

    with transaction.atomic():
        if truncate:
            deleted = Region.objects.count()
            Region.objects.all().delete()
        else:
            deleted = 0

        existing = {row.code: row for row in Region.objects.all()}
        to_create = []
        to_update = []
        update_fields = [
            'name', 'level', 'sort', 'note',
        ]

        for row in rows:
            code = str(row.get('code')).strip()
            obj = existing.get(code)
            if obj is None:
                obj = Region(
                    code=code,
                    name=str(row.get('name') or '').strip(),
                    level=int(row.get('level') or 1),
                    sort=int(row.get('sort') or 0),
                    note=str(row.get('note') or row.get('type') or '')[:255],
                    status=bool(row.get('status', True)),
                )
                to_create.append(obj)
            else:
                obj.name = str(row.get('name') or '').strip()
                obj.level = int(row.get('level') or obj.level)
                obj.sort = int(row.get('sort') or obj.sort)
                obj.note = str(row.get('note') or row.get('type') or '')[:255]
                to_update.append(obj)

        if to_create:
            Region.objects.bulk_create(to_create, batch_size=500)
        if to_update:
            Region.objects.bulk_update(to_update, update_fields, batch_size=500)

        by_code = {
            row.code: row for row in Region.objects.filter(code__in=codes)
        }
        parent_updates = []
        for row in rows:
            obj = by_code.get(str(row.get('code')).strip())
            if obj is None:
                continue
            parent_code = row.get('parent_code')
            parent = by_code.get(str(parent_code).strip()) if parent_code else None
            if obj.parent_id != getattr(parent, 'pk', None):
                obj.parent_id = getattr(parent, 'pk', None)
                parent_updates.append(obj)
        if parent_updates:
            Region.objects.bulk_update(parent_updates, ['parent'], batch_size=500)

    return {
        'total': len(rows),
        'created': len(to_create),
        'updated': len(to_update),
        'deleted': deleted,
        'dry_run': False,
    }


def seed_regions_if_empty():
    from .models import Region

    if Region.objects.exists():
        return None
    return load_regions_from_file(DEFAULT_SEED_PATH)
