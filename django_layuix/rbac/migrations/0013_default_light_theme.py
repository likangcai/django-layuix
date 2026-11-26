from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_layuix_rbac', '0012_auth_token_state'),
    ]

    def migrate_theme(apps, schema_editor):
        UserModel = apps.get_model('django_layuix_rbac', 'UserProfile')
        UserModel.objects.filter(theme='默认深色').update(theme='默认浅色')

    operations = [
        migrations.RunPython(migrate_theme, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='userprofile',
            name='theme',
            field=models.CharField(
                choices=[('默认浅色', '默认浅色'), ('默认深色', '默认深色')],
                default='默认浅色', max_length=20, verbose_name='主题',
            ),
        ),
    ]
