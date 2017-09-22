from django.db import models
from django.utils import timezone
from django.core.mail import send_mail

from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin,\
                                       BaseUserManager

# Create your models here.


class UserManager(BaseUserManager):
    def _create_user(self, loginname, password, is_staff, is_superuser,
                     **extra_fields):

        now = timezone.now()
        if not loginname:
            raise ValueError(_('Users must have an account.'))

        user = self.model(loginname=loginname,
                          is_staff=is_staff,
                          is_active=True,
                          is_superuser=is_superuser,
                          last_login=now,
                          date_joined=now, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, loginname, password=None, **extra_fields):
        return self._create_user(loginname, password, True, False,
                                 **extra_fields)

    def create_superuser(self, loginname, password, **extra_fields):
        user = self._create_user(loginname, password, True, True,
                                 **extra_fields)
        # user.is_active = True
        user.save(using=self._db)
        return user


class Role(models.Model):
    name = models.CharField(null=False, max_length=100, unique=True)
    desc = models.CharField(null=True, max_length=200)

    class Meta:
        verbose_name = "管理员角色"
        verbose_name_plural = "管理员角色"

        db_table = "role"

    def __str__(self):
        return self.name


class User(AbstractBaseUser, PermissionsMixin):
    objects = UserManager()
    loginname = models.CharField(
        _('login name'), null=False, max_length=100, unique=True
    )
    first_name = models.CharField(
        _('姓氏'), max_length=64, blank=True, null=True
    )
    last_name = models.CharField(
        _('名称'), max_length=64, blank=True, null=True
    )
    email = models.EmailField(
        _('邮箱'), unique=True, max_length=255, null=True
    )
    is_staff = models.BooleanField(
        _('staff status'), default=False,
        help_text=_(
            'Designates whether the user can log into this admin site.'
        )
    )
    is_active = models.BooleanField(
        _('active'), default=False,
        help_text=_(
            '标识用户的状态'
        )
    )
    role = models.ForeignKey(Role, related_name='user_role', null=True, default=None)
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    USERNAME_FIELD = 'loginname'

    class Meta:
        verbose_name = _('系统用户')
        verbose_name_plural = _('系统用户')
        default_permissions = ('add', 'change', 'delete', 'view')

    def get_full_name(self):
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        return self.last_name

    def email_user(self, subject, message, from_email=None):
        send_mail(subject, message, from_email, [self.email])


class UserProfile(models.Model):

    class Meta:
        db_table = "user_profile"

    user = models.OneToOneField(User)
    activation_key = models.CharField(max_length=32)
    key_expires = models.DateTimeField()


class Limit(models.Model):
    name = models.CharField(null=False, unique=True, max_length=100)
    desc = models.CharField(null=True, max_length=200)
    role = models.ForeignKey(Role, null=True)

    class Meta:
        verbose_name = "用户权限"
        verbose_name_plural = "用户权限"

        db_table = "limit"


class Game(models.Model):
    name = models.CharField(null=False, unique=True, max_length=100)
    deleted = models.BooleanField(default=False)
    desc = models.CharField(null=True, max_length=200)

    class Meta:
        verbose_name = verbose_name_plural = "游戏"
        db_table = "game"


class Player(models.Model):
    account = models.CharField(null=False, unique=True, max_length=100)
    username = models.CharField(null=True, max_length=100)
    mobile = models.CharField(null=True, max_length=20)
    qq = models.CharField(null=True, max_length=20)
    locked = models.BooleanField(default=False)
    locked_by = models.ForeignKey(User, null=True)

    class Meta:
        verbose_name = verbose_name_plural = "玩家"
        db_table = "player"


class PlayerBindInfo(models.Model):
    user = models.ForeignKey(User, null=False)
    player = models.ForeignKey(Player, null=False)
    is_bound = models.BooleanField(default=False)             # 是否绑定
    contract_time = models.DateTimeField(auto_now=True)       # 联系时间
    note = models.TextField()                                 # 备注信息

    class Meta:
        verbose_name = verbose_name_plural = "玩家联系记录"
        db_table = 'player_bind_info'


class RegisterInfo(models.Model):
    player = models.ForeignKey(Player, null=False)
    game = models.ForeignKey(Game, null=False)
    register_time = models.DateTimeField(null=False)

    class Meta:
        verbose_name = verbose_name_plural = "玩家注册信息"
        db_table = 'register_info'


class AccountLog(models.Model):
    player = models.ForeignKey(Player, null=False)
    game = models.ForeignKey(Game, null=False)
    recorder = models.ForeignKey(User, null=False)      # 充值记录员
    money = models.FloatField(default=0)
    charge_time = models.DateTimeField(null=False)
    timestamp = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = verbose_name_plural = "充值记录"
        db_table = 'account_log'


class Alert(models.Model):
    sender = models.ForeignKey(User, null=False, related_name='alert_sender')
    receiver = models.ForeignKey(User, null=False, related_name='alert_receiver')
    alert_time = models.DateTimeField(null=False)
    content = models.TextField()
    marked = models.BooleanField(default=False)
    create_time = models.DateTimeField(null=True, auto_now=True)
    update_time = models.DateTimeField(null=True, auto_now=True)

    class Meta:
        verbose_name = verbose_name_plural = "通知信息"
        db_table = "alert"


class Menu(models.Model):
    name = models.CharField(max_length=50, unique=True, null=False)
    label = models.CharField(max_length=40, null=False)
    parent = models.IntegerField(null=False, default=0)

    class Meta:
        verbose_name = verbose_name_plural = "菜单"
        db_table = "menu"

    def __str__(self):
        return self.label


class RoleBindMenu(models.Model):
    role = models.ForeignKey(Role, null=False, verbose_name="角色")
    menu = models.ForeignKey(Menu, null=False)

    class Meta:
        verbose_name = verbose_name_plural = "功能权限绑定"
        db_table = "role_bind_menu"

#
# class OperatorLog(models.Model):
#     operator = models.ForeignKey(User, null=False)
#     table_name = models.CharField(null=False, max_length=50)
#     column_name = models.CharField()



