from django_layuix.plugins import PluginConfig


class OpsConfig(PluginConfig):
    default = True
    name = 'django_layuix.ops'
    label = 'django_layuix_ops'
    verbose_name = 'Layui Ops Management'
    default_auto_field = 'django.db.models.BigAutoField'

    plugin_key = 'ops'
    plugin_name = '运维管理'
    plugin_version = '1.0.0'
    plugin_description = '服务器管理、远程日志、命令执行与 AI 日志分析'
    plugin_api_prefix = '/admin/api/ops/'
    plugin_menu_path = '/ops/server'
    plugin_dependencies = ('paramiko>=2.0', 'webssh>=1.6.0')
