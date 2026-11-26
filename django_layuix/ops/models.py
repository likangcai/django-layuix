# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Date      : 2026-11-26 22:19
# @FileName  : models.py
# -----------------------------
"""
django-layuix Ops Models
Server management for SSH connections
AI model configuration for intelligent log analysis
"""
from django.db import models


class Server(models.Model):
    """服务器模型"""
    name = models.CharField(max_length=100, verbose_name='服务器名称')
    host = models.CharField(max_length=200, verbose_name='主机地址')
    port = models.IntegerField(default=22, verbose_name='SSH端口')
    username = models.CharField(max_length=100, verbose_name='SSH用户名')
    auth_type = models.CharField(max_length=20, choices=(
        ('password', '密码认证'),
        ('key', '密钥认证')
    ), default='password', verbose_name='认证方式')
    password = models.CharField(max_length=500, blank=True, default='', verbose_name='密码')
    private_key = models.TextField(blank=True, default='', verbose_name='私钥')
    description = models.TextField(blank=True, default='', verbose_name='描述')
    is_active = models.BooleanField(default=True, verbose_name='状态')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'ops_server'
        verbose_name = '服务器管理'
        verbose_name_plural = verbose_name
        ordering = ['id']

    def __str__(self):
        return f'{self.name} ({self.host})'

    def get_ssh_client(self):
        """获取 SSH 连接客户端"""
        import paramiko
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            if self.auth_type == 'key' and self.private_key:
                import io
                key_file = io.StringIO(self.private_key)
                # 尝试不同的键类型
                pkey = None
                for key_cls in [paramiko.RSAKey, paramiko.ECDSAKey, paramiko.Ed25519Key]:
                    try:
                        pkey = key_cls.from_private_key(key_file)
                        break
                    except paramiko.SSHException:
                        key_file.seek(0)
                        continue
                if pkey is None:
                    raise ValueError('无法解析私钥，请检查格式（支持 RSA/ECDSA/Ed25519）')
                client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    pkey=pkey,
                    timeout=10,
                    allow_agent=False,
                    look_for_keys=False
                )
            else:
                client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    timeout=10,
                    allow_agent=False,
                    look_for_keys=False
                )
        except Exception as e:
            client.close()
            raise
        return client


class AIModelConfig(models.Model):
    """AI 模型配置 - 用于智能日志分析"""
    PROVIDER_CHOICES = [
        ('openai', 'OpenAI'),
        ('zhipu', '智谱清言'),
        ('qwen', '通义千问'),
        ('deepseek', 'DeepSeek'),
        ('moonshot', '月之暗面 (Kimi)'),
        ('custom', '自定义'),
    ]
    
    name = models.CharField('配置名称', max_length=100)
    provider = models.CharField('服务商', max_length=50, choices=PROVIDER_CHOICES, default='custom')
    api_key = models.CharField('API Key', max_length=500, blank=True, default='', help_text='服务商提供的 API 密钥')
    base_url = models.CharField('Base URL', max_length=500, blank=True, default='', help_text='API 基础地址，留空则使用默认地址')
    model = models.CharField('模型名称', max_length=100, help_text='例如：gpt-4o-mini, qwen-turbo, glm-4')
    is_default = models.BooleanField('默认配置', default=False, help_text='标记为默认使用的配置')
    is_active = models.BooleanField('启用状态', default=True)
    description = models.TextField('描述', blank=True, default='')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'ops_ai_model_config'
        verbose_name = 'AI模型配置'
        verbose_name_plural = verbose_name
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        default_mark = ' [默认]' if self.is_default else ''
        return f'{self.name}{default_mark}'
    
    def save(self, *args, **kwargs):
        """确保只有一个默认配置"""
        if self.is_default:
            # 将其他配置的 is_default 设为 False
            AIModelConfig.objects.filter(is_default=True).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)
    
    @classmethod
    def get_default_config(cls):
        """获取默认配置"""
        config = cls.objects.filter(is_default=True, is_active=True).first()
        if not config:
            # 如果没有默认配置，返回第一个启用的配置
            config = cls.objects.filter(is_active=True).first()
        return config
