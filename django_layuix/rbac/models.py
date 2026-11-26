# -*- coding: utf-8 -*-
"""
django-layuix RBAC Models
Required RBAC engine - add 'django_layuix.rbac' to INSTALLED_APPS to enable
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
    catalog_key = models.CharField(
        max_length=200, null=True, blank=True, unique=True,
        editable=False, verbose_name='权限目录唯一键',
    )
    plugin_key = models.CharField(max_length=100, blank=True, default='', verbose_name='所属插件')
    sort = models.IntegerField(default=0, verbose_name='排序')
    visible = models.BooleanField(default=True, verbose_name='是否显示')
    status = models.BooleanField(default=True, verbose_name='状态')
    # 前后端可见性控制
    backend_visible = models.BooleanField(default=True, verbose_name='后台可见')
    frontend_visible = models.BooleanField(default=True, verbose_name='前台可见')
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
            'en': self.name_en or self.name,
        }
        return lang_map.get(lang_code, self.name)

    def save(self, *args, **kwargs):
        if self.plugin_key == 'permission_catalog' and self.permission:
            self.catalog_key = 'permission_catalog:%s' % self.permission
        else:
            self.catalog_key = None
        update_fields = kwargs.get('update_fields')
        if update_fields is not None:
            kwargs['update_fields'] = set(update_fields) | {'catalog_key'}
        super().save(*args, **kwargs)


class Role(models.Model):
    """角色模型"""
    name = models.CharField(max_length=50, unique=True, verbose_name='角色名称')
    code = models.CharField(max_length=50, unique=True, verbose_name='角色编码')
    description = models.TextField(blank=True, default='', verbose_name='描述')
    menus = models.ManyToManyField(Menu, blank=True, related_name='roles', verbose_name='关联菜单')
    # RBAC1: 角色继承（多父节点 DAG，symmetrical=False 表示 A 继承 B 不代表 B 继承 A）
    parent_roles = models.ManyToManyField(
        'self', symmetrical=False, blank=True,
        related_name='child_roles', verbose_name='继承角色'
    )
    # 1.4.1 兼容字段：旧版单父继承契约。新代码优先读取 parent_roles。
    parent = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='children', verbose_name='上级角色（兼容）'
    )
    # 1.4.1 数据权限：默认空白/0，不影响未配置的现有角色。
    scope_node = models.CharField(max_length=100, blank=True, default='', verbose_name='数据作用域节点')
    scope_depth = models.PositiveIntegerField(default=0, verbose_name='作用域向下层数')
    # RBAC2: 角色级人数上限，0/None 表示不限
    max_users = models.PositiveIntegerField(null=True, blank=True, verbose_name='人数上限')
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


class RoleMutex(models.Model):
    """RBAC2 角色互斥组：SSD 在分配时校验，DSD 在激活时校验"""
    KIND_CHOICES = (
        ('ssd', '静态职责分离(SSD)'),
        ('dsd', '动态职责分离(DSD)'),
    )
    name = models.CharField(max_length=50, unique=True, verbose_name='互斥组名称')
    kind = models.CharField(max_length=3, choices=KIND_CHOICES, default='ssd', verbose_name='互斥类型')
    roles = models.ManyToManyField(Role, blank=True, related_name='mutex_groups', verbose_name='互斥角色')
    permissions = models.ManyToManyField(Menu, blank=True, related_name='permission_mutex_groups', verbose_name='互斥权限')
    description = models.TextField(blank=True, default='', verbose_name='说明')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'sys_role_mutex'
        verbose_name = '角色互斥组'
        verbose_name_plural = verbose_name
        indexes = [models.Index(fields=['kind', 'is_active'], name='idx_role_mutex_kind_active')]
        ordering = ['id']

    def __str__(self):
        return self.name


class SoDConstraint(RoleMutex):
    """1.4.1 compatibility proxy for static separation-of-duty constraints."""

    class Meta:
        proxy = True
        verbose_name = 'SSD 互斥约束'
        verbose_name_plural = verbose_name


class RolePrerequisite(models.Model):
    """RBAC2 前置角色：拥有 role 必须先拥有 prerequisite"""
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='required_by', verbose_name='角色')
    prerequisite = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='prerequisite_for', verbose_name='前置角色')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'sys_role_prerequisite'
        verbose_name = '前置角色'
        verbose_name_plural = verbose_name
        unique_together = [('role', 'prerequisite')]
        ordering = ['id']

    def __str__(self):
        return f'{self.role} <- {self.prerequisite}'


class ScopeNode(models.Model):
    """1.4.2 organization node used by the data-scope layer."""
    code = models.CharField(max_length=100, unique=True, verbose_name='节点编码')
    name = models.CharField(max_length=100, verbose_name='节点名称')
    parent = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='child_nodes', verbose_name='上级节点'
    )
    sort = models.IntegerField(default=0, verbose_name='排序')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'sys_scope_node'
        verbose_name = '组织节点'
        verbose_name_plural = verbose_name
        ordering = ['sort', 'id']

    def __str__(self):
        return '%s (%s)' % (self.name, self.code)


class AbacPolicy(models.Model):
    """1.4.2 row/field-level expression policy. Inactive when no policy exists."""
    EFFECT_CHOICES = (('allow', '允许'), ('deny', '拒绝'))
    name = models.CharField(max_length=100, verbose_name='策略名称')
    resource = models.CharField(max_length=150, verbose_name='资源标识')
    action = models.CharField(max_length=50, default='view', verbose_name='动作')
    field = models.CharField(max_length=100, blank=True, default='', verbose_name='字段（空表示行级）')
    effect = models.CharField(max_length=10, choices=EFFECT_CHOICES, default='allow', verbose_name='效果')
    expression = models.TextField(verbose_name='表达式')
    priority = models.IntegerField(default=100, verbose_name='优先级（越小越高）')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'sys_abac_policy'
        verbose_name = 'ABAC 策略'
        verbose_name_plural = verbose_name
        ordering = ['priority', 'id']

    def __str__(self):
        return self.name


class AuthToken(models.Model):
    """Persistent state for signed access tokens."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='auth_tokens', verbose_name='用户',
    )
    jti = models.CharField(max_length=64, unique=True, verbose_name='Token ID')
    token_type = models.CharField(max_length=20, default='access', verbose_name='Token 类型')
    status = models.PositiveSmallIntegerField(default=1, verbose_name='状态')
    issued_at = models.DateTimeField(verbose_name='签发时间')
    expires_at = models.DateTimeField(verbose_name='过期时间')
    revoked_at = models.DateTimeField(null=True, blank=True, verbose_name='撤销时间')
    revoke_reason = models.CharField(max_length=64, blank=True, default='', verbose_name='撤销原因')
    client_ip = models.CharField(max_length=64, blank=True, default='', verbose_name='客户端 IP')
    user_agent = models.CharField(max_length=255, blank=True, default='', verbose_name='User Agent')
    last_used_at = models.DateTimeField(null=True, blank=True, verbose_name='最后使用时间')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'sys_auth_token'
        verbose_name = '访问令牌'
        verbose_name_plural = '访问令牌'
        ordering = ['-issued_at']
        indexes = [
            models.Index(fields=['user', 'status', 'expires_at'], name='idx_auth_token_user_status_exp'),
            models.Index(fields=['expires_at'], name='idx_auth_token_expires_at'),
        ]

    def __str__(self):
        return '%s (%s)' % (self.jti[:12], self.user_id)


class PluginRegistry(models.Model):
    """Registered django-layuix plugin metadata (persisted across restarts)."""
    key = models.CharField(max_length=100, unique=True, verbose_name='插件标识')
    name = models.CharField(max_length=100, verbose_name='插件名称')
    version = models.CharField(max_length=30, default='1.0.0', verbose_name='版本')
    description = models.TextField(blank=True, default='', verbose_name='说明')
    api_prefix = models.CharField(max_length=200, blank=True, default='', verbose_name='API 前缀')
    menu_path = models.CharField(max_length=200, blank=True, default='', verbose_name='菜单路径')
    app_label = models.CharField(max_length=100, blank=True, default='', verbose_name='Django App Label')
    dependencies = models.TextField(blank=True, default='', verbose_name='依赖声明')
    source = models.CharField(max_length=20, default='app', verbose_name='来源')
    validation_error = models.TextField(blank=True, default='', verbose_name='校验错误')
    desired_active = models.BooleanField(default=True, verbose_name='用户期望启用')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'sys_plugin_registry'
        verbose_name = '插件注册'
        verbose_name_plural = verbose_name
        ordering = ['key']

    def __str__(self):
        return self.name


class UserProfile(AbstractUser):
    """用户模型 - 扩展Django AbstractUser"""
    phone = models.CharField(max_length=20, blank=True, default='', verbose_name='手机号')
    avatar = models.ImageField(upload_to='avatar/%Y/%m/', blank=True, null=True, verbose_name='头像')
    nickname = models.CharField(max_length=50, blank=True, default='', verbose_name='昵称')
    roles = models.ManyToManyField(Role, blank=True, related_name='users', verbose_name='角色')
    department = models.ForeignKey(
        'Department', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='users', verbose_name='部门',
    )
    position = models.ForeignKey(
        'Position', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='users', verbose_name='主岗',
    )
    positions = models.ManyToManyField(
        'Position', blank=True, related_name='multi_users', verbose_name='兼任岗位',
    )
    
    # 主题配置 - 深色/浅色双模式
    THEME_CHOICES = [
        ('默认浅色', '默认浅色'),
        ('默认深色', '默认深色'),
    ]
    theme = models.CharField(max_length=20, default='默认浅色', choices=THEME_CHOICES, verbose_name='主题')
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
        from .engine import get_effective_permissions, is_full_access
        from .permission_registry import is_registered_permission

        if not perm or not is_registered_permission(perm):
            return False
        if is_full_access(self):
            return True
        if perm in get_effective_permissions(self):
            return True
        return False

    def has_module_perms(self, app_label):
        from .engine import get_effective_permissions, is_full_access
        from .permission_registry import is_registered_permission

        effective = [p for p in get_effective_permissions(self) if is_registered_permission(p)]
        if is_full_access(self):
            return any(is_registered_permission(p) for p in effective) or any(
                p.startswith(str(app_label)) for p in effective
            )
        return any(p.startswith(str(app_label)) for p in effective)


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
    CONFIG_TYPE_CHOICES = [
        ('string', '字符串'),
        ('integer', '整数'),
        ('boolean', '布尔值'),
        ('json', 'JSON'),
        ('image', '图片'),
        ('color', '颜色'),
        ('text', '文本'),
        ('url', 'URL'),
    ]
    
    key = models.CharField(max_length=100, unique=True, verbose_name='配置键')
    value = models.TextField(blank=True, default='', verbose_name='配置值')
    description = models.CharField(max_length=200, blank=True, default='', verbose_name='描述')
    config_type = models.CharField(
        max_length=20, 
        default='string', 
        choices=CONFIG_TYPE_CHOICES,
        verbose_name='配置类型'
    )
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


class Dictionary(models.Model):
    """Data dictionary: a named group of reusable option values."""
    code = models.CharField(max_length=64, unique=True, verbose_name='字典编码')
    name = models.CharField(max_length=100, verbose_name='字典名称')
    description = models.CharField(max_length=200, blank=True, default='', verbose_name='描述')
    sort = models.IntegerField(default=0, verbose_name='排序')
    status = models.BooleanField(default=True, verbose_name='状态')
    is_system = models.BooleanField(default=False, verbose_name='系统内置')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'sys_dictionary'
        verbose_name = '数据字典'
        verbose_name_plural = verbose_name
        ordering = ['sort', 'id']

    def __str__(self):
        return '%s (%s)' % (self.name, self.code)


class DictionaryItem(models.Model):
    """A single selectable option inside a data dictionary."""
    dictionary = models.ForeignKey(
        Dictionary, related_name='items', on_delete=models.CASCADE,
        verbose_name='所属字典',
    )
    label = models.CharField(max_length=100, verbose_name='显示名称')
    value = models.CharField(max_length=100, verbose_name='数据值')
    sort = models.IntegerField(default=0, verbose_name='排序')
    status = models.BooleanField(default=True, verbose_name='状态')
    is_default = models.BooleanField(default=False, verbose_name='默认项')
    css_class = models.CharField(max_length=50, blank=True, default='', verbose_name='样式类')
    remark = models.CharField(max_length=200, blank=True, default='', verbose_name='备注')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'sys_dictionary_item'
        verbose_name = '字典项'
        verbose_name_plural = verbose_name
        ordering = ['sort', 'id']
        unique_together = [('dictionary', 'value')]

    def __str__(self):
        return '%s = %s' % (self.label, self.value)


class Department(models.Model):
    """Hierarchical department / organization unit."""
    TYPE_CHOICES = [
        (1, '公司'),
        (2, '子公司'),
        (3, '部门'),
        (4, '小组'),
    ]
    name = models.CharField(max_length=150, verbose_name='部门名称')
    code = models.CharField(max_length=64, unique=True, verbose_name='部门编码')
    type = models.IntegerField(choices=TYPE_CHOICES, default=3, verbose_name='部门类型')
    parent = models.ForeignKey(
        'self', null=True, blank=True, related_name='children',
        on_delete=models.CASCADE, verbose_name='上级部门',
    )
    leader = models.CharField(max_length=50, blank=True, default='', verbose_name='负责人')
    phone = models.CharField(max_length=30, blank=True, default='', verbose_name='联系电话')
    email = models.EmailField(blank=True, default='', verbose_name='邮箱')
    sort = models.IntegerField(default=0, verbose_name='排序')
    status = models.BooleanField(default=True, verbose_name='状态')
    note = models.CharField(max_length=255, blank=True, default='', verbose_name='备注')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'sys_department'
        verbose_name = '部门'
        verbose_name_plural = verbose_name
        ordering = ['sort', 'id']

    def __str__(self):
        return '%s (%s)' % (self.name, self.code)


class Position(models.Model):
    """Job position / post."""
    name = models.CharField(max_length=150, verbose_name='岗位名称')
    code = models.CharField(max_length=64, unique=True, verbose_name='岗位编码')
    sort = models.IntegerField(default=0, verbose_name='排序')
    status = models.BooleanField(default=True, verbose_name='状态')
    note = models.CharField(max_length=255, blank=True, default='', verbose_name='备注')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'sys_position'
        verbose_name = '岗位'
        verbose_name_plural = verbose_name
        ordering = ['sort', 'id']

    def __str__(self):
        return '%s (%s)' % (self.name, self.code)


class Region(models.Model):
    """Administrative region tree."""
    LEVEL_CHOICES = [
        (1, '省份'),
        (2, '城市'),
        (3, '县区'),
        (4, '街道'),
    ]
    name = models.CharField(max_length=150, verbose_name='地区名称')
    code = models.CharField(max_length=20, unique=True, verbose_name='行政编码')
    area_code = models.CharField(max_length=20, blank=True, default='', verbose_name='区号')
    zip_code = models.CharField(max_length=20, blank=True, default='', verbose_name='邮编')
    pinyin = models.CharField(max_length=150, blank=True, default='', verbose_name='拼音')
    level = models.IntegerField(choices=LEVEL_CHOICES, default=1, verbose_name='层级')
    parent = models.ForeignKey(
        'self', null=True, blank=True, related_name='children',
        on_delete=models.CASCADE, verbose_name='上级地区',
    )
    sort = models.IntegerField(default=0, verbose_name='排序')
    status = models.BooleanField(default=True, verbose_name='状态')
    note = models.CharField(max_length=255, blank=True, default='', verbose_name='备注')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'sys_region'
        verbose_name = '地区'
        verbose_name_plural = verbose_name
        ordering = ['sort', 'id']

    def __str__(self):
        return '%s (%s)' % (self.name, self.code)


class MemberLevel(models.Model):
    """Member level / customer tier."""
    name = models.CharField(max_length=150, verbose_name='等级名称')
    code = models.CharField(max_length=64, unique=True, verbose_name='等级编码')
    min_points = models.IntegerField(default=0, verbose_name='最低积分')
    discount = models.DecimalField(
        max_digits=5, decimal_places=2, default=100, verbose_name='折扣比例',
    )
    icon = models.CharField(max_length=50, blank=True, default='', verbose_name='图标')
    sort = models.IntegerField(default=0, verbose_name='排序')
    status = models.BooleanField(default=True, verbose_name='状态')
    description = models.CharField(max_length=255, blank=True, default='', verbose_name='说明')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'sys_member_level'
        verbose_name = '会员等级'
        verbose_name_plural = verbose_name
        ordering = ['sort', 'id']

    def __str__(self):
        return '%s (%s)' % (self.name, self.code)
