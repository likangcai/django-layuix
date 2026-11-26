# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError

from django_layuix.rbac.region_seed import DEFAULT_SEED_PATH, load_regions_from_file


class Command(BaseCommand):
    help = 'Load the bundled China province/city/county seed into Region'

    def add_arguments(self, parser):
        parser.add_argument('--file', default=str(DEFAULT_SEED_PATH))
        parser.add_argument('--truncate', action='store_true', help='delete existing regions before import')
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        try:
            result = load_regions_from_file(
                options['file'],
                truncate=options['truncate'],
                dry_run=options['dry_run'],
            )
        except (FileNotFoundError, ValueError) as exc:
            raise CommandError(str(exc)) from exc
        if result.get('dry_run'):
            self.stdout.write(self.style.WARNING(
                'dry-run: %s rows would be loaded' % result['total']
            ))
            return
        self.stdout.write(self.style.SUCCESS(
            'regions total=%s created=%s updated=%s deleted=%s' % (
                result['total'], result['created'], result['updated'], result['deleted'],
            )
        ))
