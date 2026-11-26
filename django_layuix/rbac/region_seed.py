# -*- coding: utf-8 -*-

"""Load the bundled China region seeds into Region.

The base file contains official MCA province/city/county data. The optional
street file contains level-4 towns/streets and is kept separate so the MCA
update script can refresh levels 1-3 without deleting street data.
"""
import gzip
import json
from pathlib import Path

from django.db import transaction

DATA_DIR = Path(__file__).resolve().parent / 'data'
DEFAULT_SEED_PATH = DATA_DIR / 'china_regions.json'
DEFAULT_STREET_PATH = DATA_DIR / 'china_streets.json'
DEFAULT_VILLAGE_PATH = DATA_DIR / 'china_villages.json.gz'


def _read_rows(path):
    path = Path(path)
    if path.suffix == '.gz':
        raw = gzip.decompress(path.read_bytes())
    else:
        raw = path.read_bytes()
    payload = json.loads(raw.decode('utf-8'))
    rows = payload.get('regions') if isinstance(payload, dict) else payload
    if not isinstance(rows, list) or not rows:
        raise ValueError('region seed is empty or invalid: %s' % path)
    return rows


def _merged_rows(path=None, include_streets=True, include_villages=False):
    source = Path(path) if path else DEFAULT_SEED_PATH
    rows = list(_read_rows(source))
    is_default = source.resolve() == DEFAULT_SEED_PATH.resolve()
    if include_streets and is_default and DEFAULT_STREET_PATH.exists():
        rows.extend(_read_rows(DEFAULT_STREET_PATH))
    if include_villages and is_default and DEFAULT_VILLAGE_PATH.exists():
        rows.extend(_read_rows(DEFAULT_VILLAGE_PATH))
    return rows


def load_regions_from_file(
    path=None, truncate=False, dry_run=False, include_streets=True,
    include_villages=False,
):
    from .models import Region

    rows = _merged_rows(
        path, include_streets=include_streets, include_villages=include_villages,
    )
    codes = [str(row.get('code') or '').strip() for row in rows]
    if any(not code for code in codes) or len(codes) != len(set(codes)):
        raise ValueError('region seed contains empty or duplicate codes')

    if dry_run:
        levels = {}
        for row in rows:
            level = int(row.get('level') or 1)
            levels[level] = levels.get(level, 0) + 1
        return {
            'total': len(rows),
            'levels': levels,
            'created': 0,
            'updated': 0,
            'deleted': 0,
            'dry_run': True,
        }

    batch_size = 500
    created = updated = 0
    update_fields = ['name', 'level', 'sort', 'note', 'parent']
    code_to_id = {}
    ordered = sorted(rows, key=lambda row: (int(row.get('level') or 1), str(row.get('code') or '')))

    with transaction.atomic():
        if truncate:
            deleted = Region.objects.count()
            Region.objects.all().delete()
        else:
            deleted = 0

        for start in range(0, len(ordered), batch_size):
            batch = ordered[start:start + batch_size]
            batch_codes = [str(row.get('code')).strip() for row in batch]
            existing = {
                obj.code: obj
                for obj in Region.objects.filter(code__in=batch_codes)
            }
            to_create = []
            to_update = []
            for row in batch:
                code = str(row.get('code')).strip()
                parent_code = str(row.get('parent_code') or '').strip()
                parent_id = code_to_id.get(parent_code)
                obj = existing.get(code)
                if obj is None:
                    obj = Region(
                        code=code,
                        name=str(row.get('name') or '').strip(),
                        level=int(row.get('level') or 1),
                        sort=int(row.get('sort') or 0),
                        note=str(row.get('note') or row.get('type') or '')[:255],
                        status=bool(row.get('status', True)),
                        parent_id=parent_id,
                    )
                    to_create.append(obj)
                else:
                    obj.name = str(row.get('name') or '').strip()
                    obj.level = int(row.get('level') or obj.level)
                    obj.sort = int(row.get('sort') or obj.sort)
                    obj.note = str(row.get('note') or row.get('type') or '')[:255]
                    obj.parent_id = parent_id
                    to_update.append(obj)

            if to_create:
                Region.objects.bulk_create(to_create, batch_size=batch_size)
                created += len(to_create)
            if to_update:
                Region.objects.bulk_update(to_update, update_fields, batch_size=batch_size)
                updated += len(to_update)

            persisted = Region.objects.filter(code__in=batch_codes).values_list('code', 'id')
            code_to_id.update({code: pk for code, pk in persisted})

    return {
        'total': len(rows),
        'created': created,
        'updated': updated,
        'deleted': deleted,
        'dry_run': False,
    }


def seed_regions_if_empty(include_streets=True, include_villages=False):
    from .models import Region

    if Region.objects.exists():
        return None
    return load_regions_from_file(
        include_streets=include_streets, include_villages=include_villages,
    )
