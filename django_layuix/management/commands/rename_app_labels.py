# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-26 22:19
# @FileName  : rename_app_labels.py
# -----------------------------
"""One-off helper for upgrading databases created before the django-layuix rename."""
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder

LABEL_RENAMES = {
    'django_layui_rbac': 'django_layuix_rbac',
    'django_layui_ops': 'django_layuix_ops',
}


class Command(BaseCommand):
    help = 'Rename legacy django-layui app labels in migrations and content types'

    def handle(self, *args, **options):
        recorder = MigrationRecorder(connection)
        migration_qs = getattr(recorder, 'migration_qs', None) or recorder.Migration.objects
        for old, new in LABEL_RENAMES.items():
            old_migrations = migration_qs.filter(app=old)
            new_migrations = migration_qs.filter(app=new).exists()

            if old_migrations.exists() and new_migrations:
                self.stderr.write(
                    self.style.WARNING(
                        'Both %s and %s migrations exist; skipping %s.' % (old, new, old)
                    )
                )
            elif old_migrations.exists():
                count = old_migrations.update(app=new)
                self.stdout.write(self.style.SUCCESS('Updated %s migration rows: %s' % (old, count)))

            content_types = ContentType.objects.filter(app_label=old)
            ct_count = content_types.count()
            if ct_count:
                content_types.update(app_label=new)
                self.stdout.write(self.style.SUCCESS('Updated %s content types: %s' % (old, ct_count)))

        ContentType.objects.clear_cache()
        self.stdout.write(self.style.SUCCESS('Legacy app labels renamed. Run migrate to confirm.'))
