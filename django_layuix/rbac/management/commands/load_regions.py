# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-26 22:19
# @FileName  : load_regions.py
# -----------------------------
from django.core.management.base import BaseCommand, CommandError

from django_layuix.rbac.region_seed import (
    DEFAULT_SEED_PATH, DEFAULT_STREET_PATH, load_regions_from_file,
)


class Command(BaseCommand):
    help = '加载捆绑的中国地区种子，包括可选的城镇/街道数据'

    def add_arguments(self, parser):
        parser.add_argument('--file', default=str(DEFAULT_SEED_PATH))
        parser.add_argument('--truncate', action='store_true', help='delete existing regions before import')
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument(
            '--skip-streets', action='store_true',
            help='load only province/city/county rows from %s' % DEFAULT_STREET_PATH.name,
        )
        parser.add_argument(
            '--include-villages', action='store_true',
            help='also load the optional 600k village/community seed',
        )

    def handle(self, *args, **options):
        try:
            result = load_regions_from_file(
                options['file'],
                truncate=options['truncate'],
                dry_run=options['dry_run'],
                include_streets=not options['skip_streets'],
                include_villages=options['include_villages'],
            )
        except (FileNotFoundError, ValueError) as exc:
            raise CommandError(str(exc)) from exc
        if result.get('dry_run'):
            levels = result.get('levels') or {}
            self.stdout.write(self.style.WARNING(
                'dry-run: %s rows would be loaded (%s)' % (
                    result['total'],
                    ', '.join('L%s=%s' % (key, levels[key]) for key in sorted(levels)),
                )
            ))
            return
        self.stdout.write(self.style.SUCCESS(
            'regions total=%s created=%s updated=%s deleted=%s' % (
                result['total'], result['created'], result['updated'], result['deleted'],
            )
        ))
