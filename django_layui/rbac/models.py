# -*- coding: utf-8 -*-
"""
django-layui RBAC Models
Optional extension - add 'django_layui.rbac' to INSTALLED_APPS to enable
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class Menu(models.Model):
    """菜单模型"""
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, verbose_name='父级菜单')
    name = models.CharField(max_length=50, verbose_name='菜单名称（中文）')
    name_en = models.CharField(max_length=50, blank=True, default='', verbose_name='菜单名称（英文）')
    name_zh_hans = models.CharField(max_length=50, blank=True, default='', verbose_name='菜单名称（简体中文）')
    icon = models.CharField(max_length=50, default='layui-icon-app', verbose_name='图标')
    path = models.CharField(max_length=200, blank=True, default='', verbose_name='路由地址')
    component = models.CharField(max_length=200, blank=True, default='', verbose_name='组件路径')
    menu_type = models.IntegerField(choices=((1, '目录'), (2, '菜单'), (3, '按钮')), default=2, verbose_name='类型')
    permission = models.CharField(max_length=100, blank=True, default='', verbose_name='权限标识')
    sort = models.IntegerField(default=0, verbose_name='排序')
    visible = models.BooleanField(default=True, verbose_name='是否显示')
    status = models.BooleanField(default=True, verbose_name='状态')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'sys_menu'
        verbose_name = '菜单管理'
        verbose_name_plural = verbose_name
        ordering = ['sort', 'id']

    def __str__(self):
        return self.name
    
    def get_name_by_lang(self, lang_code='zh-hans'):
        """根据语言代码获取对应的菜单名称"""
        lang_map = {
            'zh-hans': self.name_zh_hans or self.name,
            'zh-hant': getattr(self, 'name_zh_hant', None) or self.name_zh_hans or self.name,
            'en': self.name_en or self.name,
        }
        return lang_map.get(lang_code, self.name)


class Role(models.Model):
    """角色模型"""
    name = models.CharField(max_length=50, unique=True, verbose_name='角色名称')
    code = models.CharField(max_length=50, unique=True, verbose_name='角色编码')
    description = models.TextField(blank=True, default='', verbose_name='描述')
    menus = models.ManyToManyField(Menu, blank=True, related_name='roles', verbose_name='关联菜单')
    is_system = models.BooleanField(default=False, verbose_name='系统内置')
    status = models.BooleanField(default=True, verbose_name='状态')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'sys_role'
        verbose_name = '角色管理'
        verbose_name_plural = verbose_name
        ordering = ['id']

    def __str__(self):
        return self.name


class UserProfile(AbstractUser):
    """用户模型 - 扩展Django AbstractUser"""
    phone = models.CharField(max_length=20, blank=True, default='', verbose_name='手机号')
    avatar = models.ImageField(upload_to='avatar/%Y/%m/', blank=True, null=True, verbose_name='头像')
    nickname = models.CharField(max_length=50, blank=True, default='', verbose_name='昵称')
    roles = models.ManyToManyField(Role, blank=True, related_name='users', verbose_name='角色')
    
    # 主题配置 - 深色/浅色双模式
    THEME_CHOICES = [
        ('默认深色', '默认深色'),
        ('默认浅色', '默认浅色'),
    ]
    theme = models.CharField(max_length=20, default='默认深色', choices=THEME_CHOICES, verbose_name='主题')
    language = models.CharField(max_length=10, default='zh-hans', choices=(('zh-hans', '简体中文'), ('en', 'English')), verbose_name='语言')
    is_tester = models.BooleanField(default=False, verbose_name='是否测试人员')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'sys_user'
        verbose_name = '用户管理'
        verbose_name_plural = verbose_name
        ordering = ['id']

    def __str__(self):
        return self.username

    @property
    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return ''

    def has_perm(self, perm, obj=None):
        if self.username == 'admin' or self.is_superuser:
            return True
        # BUG-23 FIX: 直接使用 Menu，不需要 from .models import Menu（同文件内）
        has_custom = Menu.objects.filter(
            roles__users=self,
            permission=perm,
            status=True
        ).exists()
        if has_custom:
            return True
        is_admin_role = self.roles.filter(code='admin', status=True).exists()
        if is_admin_role:
            return True
        return super().has_perm(perm, obj)

    def has_module_perms(self, app_label):
        if self.username == 'admin' or self.is_superuser:
            return True
        is_admin_role = self.roles.filter(code='admin', status=True).exists()
        if is_admin_role:
            return True
        # BUG-24 FIX: 直接使用 Menu，不需要 from .models import Menu（同文件内）
        has_any = Menu.objects.filter(
            roles__users=self,
            permission__startswith=app_label,
            status=True
        ).exists()
        if has_any:
            return True
        return super().has_module_perms(app_label)


class OperationLog(models.Model):
    """操作日志模型"""
    # BUG-27 FIX: 使用 settings.AUTH_USER_MODEL 而非硬编码 UserProfile
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='操作用户')
    module = models.CharField(max_length=50, blank=True, default='', verbose_name='模块')
    action = models.CharField(max_length=200, verbose_name='操作内容')
    ip = models.GenericIPAddressField(blank=True, null=True, verbose_name='IP地址')
    method = models.CharField(max_length=10, blank=True, default='', verbose_name='请求方法')
    url = models.CharField(max_length=500, blank=True, default='', verbose_name='请求URL')
    status = models.IntegerField(default=1, verbose_name='状态(1成功0失败)')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'sys_operation_log'
        verbose_name = '操作日志'
        verbose_name_plural = verbose_name
        ordering = ['-create_time']

    def __str__(self):
        return f'{self.user} - {self.action}' if self.user else self.action


class SystemConfig(models.Model):
    """系统配置模型"""
    key = models.CharField(max_length=100, unique=True, verbose_name='配置键')
    value = models.TextField(blank=True, default='', verbose_name='配置值')
    description = models.CharField(max_length=200, blank=True, default='', verbose_name='描述')
    config_type = models.CharField(max_length=20, default='string', verbose_name='配置类型')
    sort = models.IntegerField(default=0, verbose_name='排序')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'sys_config'
        verbose_name = '系统配置'
        verbose_name_plural = verbose_name
        ordering = ['sort', 'id']

    def __str__(self):
        return self.key
