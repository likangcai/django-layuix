from django.db import migrations, models
import django.db.models.deletion


def backfill_parent(apps, schema_editor):
    Role = apps.get_model('django_layuix_rbac', 'Role')
    for role in Role.objects.all().iterator():
        parent_id = role.parent_roles.order_by('id').values_list('id', flat=True).first()
        if parent_id and parent_id != role.pk:
            Role.objects.filter(pk=role.pk).update(parent_id=parent_id)


class Migration(migrations.Migration):

    dependencies = [
        ('django_layuix_rbac', '0005_plugin_system'),
    ]

    operations = [
        migrations.AddField(
            model_name='role',
            name='parent',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='children',
                to='django_layuix_rbac.role',
                verbose_name='上级角色（兼容）',
            ),
        ),
        migrations.AddField(
            model_name='role',
            name='scope_node',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='数据作用域节点'),
        ),
        migrations.AddField(
            model_name='role',
            name='scope_depth',
            field=models.PositiveIntegerField(default=0, verbose_name='作用域向下层数'),
        ),
        migrations.RunPython(backfill_parent, migrations.RunPython.noop),
    ]
