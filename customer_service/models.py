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


class PlayerImport(models.Model):
    filename = models.CharField(null=False, max_length=100, verbose_name=u"文件名称")
    stored_name = models.CharField(null=True, max_length=100, verbose_name=u"保存文件名称")
    path = models.CharField(null=False, max_length=200, verbose_name=u"文件路径")
    import_time = models.DateTimeField(auto_now=True)
    notes = models.TextField(null=True)
    result = models.TextField(null=True)

    class Meta:
        verbose_name = verbose_name_plural = u"文件导入"
        db_table = "player_import"


class PlayerExport(models.Model):
    filename = models.CharField(null=False, max_length=100, verbose_name=u"文件名称")
    path = models.CharField(null=False, max_length=200, verbose_name=u"文件路径")
    export_time = models.DateTimeField(auto_now=True)
    notes = models.TextField(null=True)

    class Meta:
        verbose_name = verbose_name_plural = u"文件导出"
        db_table = "player_export"


class Player(models.Model):
    account = models.CharField(null=False, unique=True, max_length=100, verbose_name=u'账号')
    username = models.CharField(null=True, max_length=100, verbose_name=u'姓名')
    mobile = models.CharField(null=True, max_length=20, verbose_name=u'手机')
    qq = models.CharField(null=True, max_length=20, verbose_name=u'QQ')
    come_from = models.CharField(null=True, max_length=100, verbose_name=u'所属渠道')
    login_count = models.IntegerField(null=True, verbose_name=u'登录次数')

    game_count = models.IntegerField(null=True, verbose_name=u'注册游戏数量')
    register_from_game = models.ForeignKey(Game, null=True, verbose_name=u'账号注册游戏')
    register_from_game_time = models.DateTimeField(null=True, verbose_name=u'账号注册时间')

    charge_count = models.IntegerField(null=True, verbose_name=u'充值次数')
    charge_money_total = models.FloatField(null=True, verbose_name=u'充值总额')

    last_login_info_id = models.IntegerField(null=True, verbose_name=u'最近登录信息ID')
    last_account_log_id = models.IntegerField(null=True, verbose_name=u'最近的充值记录ID')
    last_contact_id = models.IntegerField(null=True, verbose_name=u'最近的联系记录ID')

    imported_from = models.IntegerField(null=True, verbose_name=u'导入自')
    export_to = models.IntegerField(null=True, verbose_name=u'导出到')

    current_contact_user = models.ForeignKey(User, null=True, related_name="contact_user", verbose_name=u'当前查看客服')
    locked = models.BooleanField(default=False, verbose_name=u'是否锁定')
    locked_by_user = models.ForeignKey(User, null=True, verbose_name=u'锁定客服')
    locked_time = models.DateTimeField(null=True, verbose_name=u'锁定时间')

    timestamp = models.DateTimeField(null=True, verbose_name=u'时间戳')
    is_deleted = models.BooleanField(default=False, null=False, verbose_name='是否删除')

    class Meta:
        verbose_name = verbose_name_plural = "玩家"
        db_table = "player"

    def __str__(self):
        return '%s %s' % (self.account, self.username)


class ContractResult(models.Model):
    result = models.CharField(max_length=200, null=False)
    bind = models.BooleanField(default=False, null=False)
    show = models.BooleanField(default=True, null=False)
    process = models.IntegerField(default=-1, null=True)

    class Meta:
        verbose_name = verbose_name_plural = u'联系结果'
        db_table = 'contract_result'


class PlayerBindInfo(models.Model):
    user = models.ForeignKey(User, null=False)
    player = models.ForeignKey(Player, null=False)
    is_bound = models.BooleanField(default=False)                   # 是否绑定
    contract_time = models.DateTimeField(auto_now=True)             # 联系时间
    contract_result = models.ForeignKey(ContractResult, null=True)  # 联系结果
    in_effect = models.BooleanField(default=True, null=False)
    note = models.TextField()                                       # 备注信息

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


class PlayerLoginInfo(models.Model):
    player = models.ForeignKey(Player, null=False)
    game = models.ForeignKey(Game, null=False)
    login_time = models.DateTimeField(null=True)

    class Meta:
        db_table = 'player_login_info'


class AccountLog(models.Model):
    player = models.ForeignKey(Player, null=False)
    game = models.ForeignKey(Game, null=True)
    recorder = models.ForeignKey(User, null=False)      # 充值记录员
    money = models.FloatField(default=0)
    charge_time = models.DateTimeField(null=True)
    timestamp = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = verbose_name_plural = "充值记录"
        db_table = 'account_log'


class Alert(models.Model):
    sender = models.ForeignKey(User, null=False, related_name='alert_sender')
    receiver = models.ForeignKey(User, null=False, related_name='alert_receiver')
    alert_time = models.DateTimeField(null=True)
    timing = models.BooleanField(default=False, null=False, verbose_name=u"是否是定时通知")    # true， 定时， false， 实时
    content = models.TextField()
    href = models.CharField(max_length=200, null=True)
    marked = models.BooleanField(default=False)
    create_time = models.DateTimeField(null=True, auto_now=True)
    update_time = models.DateTimeField(null=True, auto_now=True)

    class Meta:
        verbose_name = verbose_name_plural = "通知信息"
        db_table = "alert"


class Menu(models.Model):
    name = models.CharField(max_length=50, null=False)
    label = models.CharField(max_length=40, null=False)
    icon = models.CharField(max_length=30, null=True)
    order_index = models.IntegerField(null=True)
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


class OperatorLog(models.Model):
    action_time = models.DateTimeField(null=False, auto_now=True)
    object_id = models.IntegerField(null=True)
    object_repr = models.CharField(max_length=200, null=True)
    action_flag = models.SmallIntegerField(null=False)
    change_message = models.TextField(null=False)
    content_type_id = models.IntegerField(null=True)
    user_id = models.IntegerField(null=False)

    class Meta:
        db_table = 'operator_log'



