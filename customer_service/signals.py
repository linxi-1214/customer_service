import json
from datetime import datetime

from django.core.urlresolvers import reverse
from django.conf import settings
from django.db.models.signals import post_save
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.dispatch import receiver

from customer_service.models import Player, PlayerBindInfo, AccountLog, ContractResult
from customer_service.models import OperatorLog, Alert, User

from customer_service.tools.model import get_operator


@receiver(post_save, sender=Player)
def player_track_handler(sender, **kwargs):
    # 玩家跟踪处理

    player = kwargs.get('instance')
    created = kwargs.get('created')
    update_fields = kwargs.get('update_fields')
    operator = getattr(player, 'operator')
    content_type = ContentType.objects.get(app_label='customer_service', model='player')

    action_flag = ADDITION if created else CHANGE
    change_message = {}

    if created:
        fields = Player._meta.get_fields()
        change_message = dict([
            (field.verbose_name, getattr(player, field.name)) for field in fields if not field.one_to_many
        ])
    else:
        if update_fields:
            if 'mobile' in update_fields:
                # if mobile is updated, notify the admin and service who own the player
                if player.locked_by_user_id is not None:
                    Alert.objects.create(
                        sender_id=operator.id, receiver_id=player.locked_by_user_id,
                        content=u'%s 的手机号已更新为：%s' % (
                            player.account, player.mobile),
                        href=u'%s?player=%d' % (reverse('contract_player'), player.id)
                    )
                admin_users = User.objects.filter(role_id=settings.ADMIN_ROLE)
                for admin_user in admin_users:
                    if admin_user.id == player.locked_by_user_id:
                        continue
                    Alert.objects.create(
                        sender_id=operator.id, receiver_id=admin_user.id, marked=False,
                        content=u'%s 的手机号已更新为：%s' % (
                                player.account, player.mobile),
                        href=u'%s?player=%d' % (reverse('contract_player'), player.id)
                    )
            for update_field in update_fields:
                field = Player._meta.get_field(update_field)
                change_message[field.verbose_name] = getattr(player, update_field)

    if created or (not created and update_fields):
        # 只有创建或有更新字段的时候才记录修改信息
        OperatorLog.objects.create(
            object_id=player.id,
            object_repr=str(player),
            action_flag=action_flag,
            change_message=json.dumps(change_message),
            user_id=operator.id,
            content_type_id=content_type.id,
            action_time=datetime.now()
        )


@receiver(post_save, sender=PlayerBindInfo)
def player_bind_track_handler(sender, **kwargs):
    # 玩家绑定跟踪处理

    bind_info = kwargs.get('instance')
    operator = get_operator(bind_info)
    content_type = ContentType.objects.get(app_label='customer_service', model='player')

    contract_result = ContractResult.objects.get(id=getattr(bind_info, 'contract_result_id'))
    change_message = {u'联系结果': contract_result.result}
    if bind_info.note:
        change_message[u'备注'] = bind_info.note

    OperatorLog.objects.create(
        object_id=bind_info.player_id,
        object_repr=str(bind_info),
        action_flag=ADDITION,
        change_message=json.dumps(change_message),
        user_id=operator.id,
        content_type_id=content_type.id,
        action_time=datetime.now()
    )


