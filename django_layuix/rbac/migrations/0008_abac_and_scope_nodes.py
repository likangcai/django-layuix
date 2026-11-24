from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('django_layuix_rbac', '0007_sod_compat'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScopeNode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=100, unique=True, verbose_name='节点编码')),
                ('name', models.CharField(max_length=100, verbose_name='节点名称')),
                ('sort', models.IntegerField(default=0, verbose_name='排序')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='child_nodes', to='django_layuix_rbac.scopenode', verbose_name='上级节点')),
            ],
            options={
                'verbose_name': '组织节点',
                'verbose_name_plural': '组织节点',
                'db_table': 'sys_scope_node',
                'ordering': ['sort', 'id'],
            },
        ),
        migrations.CreateModel(
            name='AbacPolicy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='策略名称')),
                ('resource', models.CharField(max_length=150, verbose_name='资源标识')),
                ('action', models.CharField(default='view', max_length=50, verbose_name='动作')),
                ('field', models.CharField(blank=True, default='', max_length=100, verbose_name='字段（空表示行级）')),
                ('effect', models.CharField(choices=[('allow', '允许'), ('deny', '拒绝')], default='allow', max_length=10, verbose_name='效果')),
                ('expression', models.TextField(verbose_name='表达式')),
                ('priority', models.IntegerField(default=100, verbose_name='优先级（越小越高）')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
            options={
                'verbose_name': 'ABAC 策略',
                'verbose_name_plural': 'ABAC 策略',
                'db_table': 'sys_abac_policy',
                'ordering': ['priority', 'id'],
            },
        ),
    ]
