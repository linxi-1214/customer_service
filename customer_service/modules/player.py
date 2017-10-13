import os
import re
from datetime import datetime
from collections import namedtuple

import xlrd, xlsxwriter

from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from django.forms.widgets import Media
from django.db import connection

from customer_service.models import Menu, Role, RoleBindMenu

from customer_service.models import (
    Game, Player, RegisterInfo, PlayerImport, PlayerExport, AccountLog,
    PlayerLoginInfo, ContractResult, PlayerBindInfo
)


def namedtuplefetchall(cursor):
    """Return all rows from a cursor as a namedtuple"""
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]


class PlayerManager:
    @staticmethod
    def _get_bind_user_info(player_id):
        bind_user_sql = """
                SELECT
                    customer_service_user.loginname,
                    customer_service_user.first_name,
                    customer_service_user.last_name
                FROM player_bind_info
                    INNER JOIN
                    player ON player_bind_info.player_id = player.id
                    INNER JOIN
                    customer_service_user ON player_bind_info.user_id = customer_service_user.id
                WHERE
                    player_bind_info.is_bound=1
                        AND player.id = %s
                ORDER BY player_bind_info.contract_time DESC
                LIMIT 1
            """

        with connection.cursor() as cursor:
            cursor.execute(bind_user_sql, (player_id,))
            qry_set = namedtuplefetchall(cursor)

        bind_user_str = "--"

        if qry_set:
            bind_user = qry_set[0]
            bind_user_str = "%s(%s %s)" % (bind_user.loginname, bind_user.first_name or '', bind_user.last_name or '')

        return bind_user_str

    @staticmethod
    def index(user):
        sql = """
            SELECT
                player.id,
                player.account,
                player.username,
                player.mobile,
                player.qq,
                player.locked,
                player.come_from,
                player.charge_count,
                player.charge_money_total,
                customer_service_user.loginname,
                customer_service_user.first_name,
                customer_service_user.last_name
            FROM player
                LEFT JOIN
                customer_service_user ON customer_service_user.id = player.locked_by_user_id
        """
        if user.role_id != settings.ADMIN_ROLE:
            sql += """
                WHERE player.locked_by_user_id = %s
            """
            params = (user.id,)
        else:
            params = None

        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            player_qry_set = namedtuplefetchall(cursor)

            player_id_list = [player_obj.id for player_obj in player_qry_set]

        place_holder = ", ".join(['%s'] * len(player_id_list))

        register_info_sql = """
            SELECT
                register_info.player_id,
                register_info.register_time,
                game.name AS game_name
            FROM
                register_info
                INNER JOIN game ON register_info.game_id = game.id
            WHERE register_info.id IN (
                SELECT
                   reg_a.id
                FROM register_info AS reg_a WHERE reg_a.id = (
                    SELECT reg_b.id FROM register_info AS reg_b
                    WHERE reg_a.player_id = reg_b.player_id AND reg_b.player_id IN (%s)
                    ORDER BY reg_b.register_time ASC LIMIT 1
                    )
                )
        """ % place_holder

        login_info_sql = """
            SELECT
                login_info.player_id,
                login_info.login_time,
                game.name AS game_name
            FROM
                player_login_info AS login_info
                INNER JOIN game ON login_info.game_id = game.id
            WHERE login_info.id IN (
                SELECT
                    login_a.id
                FROM player_login_info AS login_a WHERE login_a.id = (
                    SELECT login_b.id FROM player_login_info AS login_b
                    WHERE login_a.player_id = login_b.player_id AND login_b.player_id IN (%s)
                    ORDER BY login_b.login_time ASC LIMIT 1
                )
            )
        """ % place_holder

        account_log_sql = """
            SELECT
                account_log.player_id,
                account_log.money AS last_charge_money,
                account_log.charge_time AS last_charge_time,
                game.name AS last_charge_game
            FROM account_log
                INNER JOIN game ON account_log.game_id = game.id
            WHERE account_log.id IN (
                SELECT
                    account_a.id
                FROM account_log AS account_a WHERE account_a.id = (
                    SELECT account_b.id FROM account_log AS account_b
                    WHERE account_a.player_id = account_b.player_id AND account_b.player_id IN (%s)
                    ORDER BY account_b.charge_time DESC LIMIT 1
                )
            )
        """ % place_holder

        bind_info_sql = """
            SELECT
                bind_info.player_id,
                contact.result
            FROM player_bind_info AS bind_info
                INNER JOIN contract_result AS contact ON bind_info.contract_result_id = contact.id
            WHERE bind_info.in_effect = 1
                AND bind_info.id IN (
                    SELECT MAX(id) FROM player_bind_info WHERE player_id IN (%s) GROUP BY player_id
                )
        """ % place_holder

        with connection.cursor() as cursor:
            cursor.execute(register_info_sql, player_id_list)
            register_info_qry_set = namedtuplefetchall(cursor)

            register_info_dict = dict([
                (_reg_info.player_id, _reg_info) for _reg_info in register_info_qry_set
            ])

        with connection.cursor() as cursor:
            cursor.execute(login_info_sql, player_id_list)
            login_info_qry_set = namedtuplefetchall(cursor)

            login_info_dict = dict([
                (_login_info.player_id, _login_info) for _login_info in login_info_qry_set
            ])

        with connection.cursor() as cursor:
            cursor.execute(account_log_sql, player_id_list)
            account_log_qry_set = namedtuplefetchall(cursor)

            account_log_dict = dict([
                (_account_log.player_id, _account_log) for _account_log in account_log_qry_set
            ])

        with connection.cursor() as cursor:
            cursor.execute(bind_info_sql, player_id_list)
            bind_info_qry_set = namedtuplefetchall(cursor)

            bind_info_dict = dict([
                (_bind_info.player_id, _bind_info) for _bind_info in bind_info_qry_set
            ])

        def _attr(dict_info, player_id, attr):
            obj = dict_info.get(player_id)

            if obj is None:
                return '--'
            else:
                val = getattr(obj, attr)
                if isinstance(val, datetime):
                    val = val.strftime('%Y-%m-%d %H:%M:%S')

                if val is None:
                    val = '--'
                return val

        delete_url = reverse('delete_player')
        media = Media(js=['js/player.js'])
        tbody = [
            {
                'columns': [
                    {'text': player_obj.id, 'style': "display: none"},
                    {'text': player_obj.account},
                    {'text': player_obj.username or '--'},
                    {'text': player_obj.mobile or '--'},
                    {'text': player_obj.qq or '--'},
                    {'text': _attr(register_info_dict, player_obj.id, 'game_name')},
                    {'text': _attr(register_info_dict, player_obj.id, 'register_time')},
                    {'text': player_obj.loginname or '--'},
                    {'text': player_obj.come_from or '--'},
                    {'text': _attr(login_info_dict, player_obj.id, 'game_name')},
                    {'text': _attr(login_info_dict, player_obj.id, 'login_time')},
                    {'text': player_obj.charge_count or '--'},
                    {'text': player_obj.charge_money_total or '--'},
                    {'text': _attr(account_log_dict, player_obj.id, 'last_charge_game')},
                    {'text': _attr(account_log_dict, player_obj.id, 'last_charge_money')},
                    {'text': _attr(account_log_dict, player_obj.id, 'last_charge_time')},
                    {'text': _attr(bind_info_dict, player_obj.id, 'result')}
                ],
                'actions': [
                    {
                        'icon': 'fa-edit',
                        'tooltip': u'编辑',
                        'href': reverse('edit_player', args=(player_obj.id,))
                    },
                    {
                        'href': '#',
                        'icon': 'fa-trash-o',
                        'tooltip': u'删除',
                        'func': 'delete_player("{url}", {id}, "{label}")'.format(
                            url=delete_url, id=player_obj.id, label=player_obj.account
                        )
                    }
                ]
            } for player_obj in player_qry_set
            ]

        context = {
            'breadcrumb_items': [
                {
                    'href': '#',
                    'active': True,
                    'label': u'玩家列表'
                }
            ],
            'panel_heading': u'玩家信息列表',
            'media': {
                'js': media.render_js()
            },
            'add_url': reverse('add_player'),
            'add_url_label': u'登记玩家信息',
            'table': {
                'id': '_player-table',
                'headers': [
                    {'text': u'账号'}, {'text': u'姓名'}, {'text': u'手机号'},
                    {'text': u'QQ号码'}, {'text': u'注册游戏'}, {'text': u'注册时间'},
                    {'text': u'所属客服'}, {'text': u'渠道'}, {'text': u'最近登录游戏'}, {'text': u'登录时间'},
                    {'text': u'充值次数'}, {'text': u'充值总额'},
                    {'text': u'最近充值游戏'}, {'text': u'最近充值金额'}, {'text': u'最近充值时间'}, {'text': u'备注'},
                    {'text': u'操作'}
                ],
                'tbody': tbody,
            },
            'modal': {
                "id": "_player_delete_modal"
            }
        }

        return context

    @staticmethod
    def add_display():
        game_objs = Game.objects.all()
        game_options = [
            {
                "value": game_obj.id,
                "label": game_obj.name
            } for game_obj in game_objs
        ]
        media = Media(js=['common/selector2/js/select2.full.js', 'js/player.js'],
                      css={'all': ['common/selector2/css/select2.min.css', 'css/player.css']})
        return {
            'breadcrumb_items': [
                {'href': reverse('player_index'), 'label': u'玩家列表'},
                {'active': True, 'label': u'登记玩家'}
            ],
            "panel_heading": u"登记玩家信息",
            "media": {
                'js': media.render_js(),
                'css': media.render_css()
            },
            "form": {
                "method": "post",
                "action": reverse('add_player'),
                "fields": [
                    {
                        "type": "text",
                        "label": u"玩家账号",
                        "help_id": "player_account_help",
                        "help_text": u"玩家登录账号，由字母和数字组成，唯一",
                        "name": "account",
                        "id": "_account",
                        "placeholder": "account1"
                    },
                    {
                        "type": "text",
                        "label": u"姓名",
                        "name": "username",
                        "id": "_username"
                    },
                    {
                        "type": "text",
                        "label": u"联系方式",
                        "name": "mobile",
                        "id": "_mobile"
                    },
                    {
                        "type": "text",
                        "label": u"QQ号码",
                        "name": "qq",
                        "id": "_qq",
                        "group_css": "previous-border"
                    },
                    {
                        "type": "group",
                        "attrs": {
                            "id": "register_game_info_id"
                        },
                        "group_css": "register-game-none",
                        "group": [
                            {
                                "type": "select",
                                "label": u'注册游戏',
                                'name': 'game_id',
                                'id': '_game_id',
                                'options': game_options,
                                "group_css": "col-lg-4"
                            },
                            {
                                "type": "text",
                                "label": u'注册时间',
                                "name": "game_time",
                                "id": "_game_id",
                                "group_css": "col-lg-4"
                            },
                            {
                                "type": "icon_button",
                                "click": "delete_register_game(this);",
                                "icon": "fa-minus-circle",
                                "extra_class": "btn-danger form-control delete-icon-button",
                                "tooltip": u'删除',
                                "tooltip_position": 'right',
                                "group_css": "col-lg-2"
                            }
                        ]
                    },
                    {
                        "type": "group_button",
                        "attrs": {'id': 'add_game_button_id'},
                        "button_type": "button",
                        "group_css": "bottom-border",
                        "extra_class": "btn-outline btn-sm btn-warning btn-block",
                        "label": u"新&nbsp;增&nbsp;注&nbsp;册&nbsp;游&nbsp;戏",
                        "click": "add_register_game();"
                    },
                    {
                        "type": "submit",
                        "button_type": "submit",
                    }
                ]
            }
        }

    @staticmethod
    def edit_display(player_id):
        try:
            player_obj = Player.objects.get(id=player_id)
        except ObjectDoesNotExist:
            return None

        register_game_sql = """
            SELECT
                game.id,
                game.name,
                register_info.register_time
            FROM
                register_info
                INNER JOIN game ON game.id = register_info.game_id
            WHERE register_info.player_id = %s
            ORDER BY register_info.register_time DESC
        """

        game_objs = Game.objects.all()

        with connection.cursor() as cursor:
            cursor.execute(register_game_sql, (player_id, ))
            qry_set = namedtuplefetchall(cursor)
            selected_register_game_info = [(reg_info.id, reg_info.register_time) for reg_info in qry_set]

        game_options_list = [
            {
                "game_options": [
                    {
                        "value": game_obj.id,
                        "label": game_obj.name,
                        "selected": game_obj.id == reg_game_id
                    } for game_obj in game_objs
                ],
                "reg_time": reg_time
            } for reg_game_id, reg_time in selected_register_game_info
        ]

        if not game_options_list:
            game_options_list = [
                {
                    "game_options": [
                        {
                            "value": game_obj.id,
                            "label": game_obj.name,
                        } for game_obj in game_objs
                    ],
                    "reg_time": ''
                }
            ]

        group_control_list = [
            {
                "type": "group",
                "attrs": {
                    "id": "register_game_info_id"
                },
                "group_css": "register-game-none",
                "group": [
                    {
                        "type": "select",
                        "label": u'注册游戏',
                        'name': 'game_id',
                        'id': '_game_id',
                        'options': game_options['game_options'],
                        "group_css": "col-lg-4"
                    },
                    {
                        "type": "text",
                        "label": u'注册时间',
                        "name": "game_time",
                        "id": "_game_id",
                        "group_css": "col-lg-4",
                        "value": game_options['reg_time'].strftime('%Y-%m-%d %H:%M:%S') if game_options['reg_time'] else ''
                    },
                    {
                        "type": "icon_button",
                        "click": "delete_register_game(this);",
                        "icon": "fa-minus-circle",
                        "extra_class": "btn-danger form-control delete-icon-button",
                        "tooltip": u'删除',
                        "tooltip_position": 'right',
                        "group_css": "col-lg-2"
                    }
                ]
            } for game_options in game_options_list
        ]

        media = Media(js=['common/selector2/js/select2.full.js', 'js/player.js'],
                      css={'all': ['common/selector2/css/select2.min.css', 'css/player.css']})

        context = {
            'breadcrumb_items': [
                {'href': reverse('player_index'), 'label': u'玩家列表'},
                {'active': True, 'label': u'修改玩家信息'}
            ],
            "panel_heading": u"编辑信息列表",
            "media": {
                'js': media.render_js(),
                'css': media.render_css()
            },
            "form": {
                "method": "post",
                "action": reverse('edit_player', args=(player_obj.id, )),
                "fields": [
                    {
                        "type": "text",
                        "label": u"玩家账号",
                        "help_id": "player_account_help",
                        "help_text": u"玩家登录账号，由字母和数字组成，唯一",
                        "name": "account",
                        "id": "_account",
                        "value": player_obj.account
                    },
                    {
                        "type": "text",
                        "label": u"姓名",
                        "name": "username",
                        "id": "_username",
                        "value": player_obj.username
                    },
                    {
                        "type": "text",
                        "label": u"联系方式",
                        "name": "mobile",
                        "id": "_mobile",
                        "value": player_obj.mobile
                    },
                    {
                        "type": "text",
                        "label": u"QQ号码",
                        "name": "qq",
                        "id": "_qq",
                        "group_css": "previous-border",
                        "value": player_obj.qq
                    }
                ]
            }
        }

        context['form']['fields'].extend(group_control_list)
        context['form']['fields'].extend([
            {
                "type": "group_button",
                "attrs": {'id': 'add_game_button_id'},
                "button_type": "button",
                "group_css": "bottom-border",
                "extra_class": "btn-outline btn-sm btn-warning btn-block",
                "label": u"新&nbsp;增&nbsp;注&nbsp;册&nbsp;游&nbsp;戏",
                "click": "add_register_game();"
            },
            {
                "type": "submit",
                "button_type": "submit",
            }
        ])

        return context

    @staticmethod
    def import_display():
        import_records = PlayerImport.objects.all()

        media = Media(
            js=['js/player.js'],
            css={'all': ['common/fileupload/css/fileinput.css', 'css/player.css']}
        )

        header_media = Media(
            js=[
                'common/fileupload/js/plugins/piexif.js',
                'common/fileupload/js/plugins/sortable.js',
                'common/fileupload/js/plugins/purify.js',
                'common/fileupload/js/fileinput.min.js',
                'common/fileupload/js/locales/LANG.js',
                'common/js/jquery.cookie.js',
                # 'js/fileupload.js'
            ]
        )
        tbody = [
            {
                'columns': [
                    {'text': import_record.id, 'style': "display: none"},
                    {'text': import_record.path},
                    {'text': import_record.filename},
                    {'text': import_record.import_time.strftime('%Y-%m-%d %H:%M:%S')},
                    {'text': import_record.notes}
                ],
                'actions': [
                    {
                        'icon': 'fa-list-alt',
                        'tooltip': u'查看导入结果',
                        'label': u'查看',
                        # 'href': reverse('import_detail', args=(import_record.id,))
                        'href': '#'
                    },
                ]
            } for import_record in import_records
            ]

        context = {
            'breadcrumb_items': [
                {
                    'href': '#',
                    'active': True,
                    'label': u'玩家导入'
                }
            ],
            'file_upload': {
                'name': 'filename',
                'type': 'file'
            },
            'panel_heading': u'导入文件列表',
            'media': {
                'js': media.render_js(),
                'css': media.render_css()
            },
            'header_media': {
                'js': header_media.render_js()
            },
            'table': {
                'id': '_player-table',
                'headers': [
                    {'text': u'路径'}, {'text': u'文件名'}, {'text': u'导入时间'},
                    {'text': u'备注'}, {'text': u'操作'}
                ],
                'tbody': tbody,
            }
        }

        return context

    @staticmethod
    def contract_display(player_id, user):
        if player_id is None:
            refresh_player_sql = """
                SELECT
                    player.id,
                    player.account,
                    player.username,
                    player.mobile,
                    player.qq,
                    player.locked,
                    player.come_from,
                    player.charge_count,
                    player.charge_money_total,
                    player.locked_by_user_id
                FROM player
                WHERE player.current_contact_user_id = %s
            """

            player_select_sql = """
                SELECT
                    player.id,
                    player.account,
                    player.username,
                    player.mobile,
                    player.qq,
                    player.locked,
                    player.locked_by_user_id
                FROM player
                    LEFT JOIN
                    (SELECT player_id
                    FROM player_bind_info
                    WHERE player_bind_info.is_bound = 1 AND player_bind_info.in_effect = 1
                    ) AS player_bind_info ON player.id != player_bind_info.player_id
                WHERE player.locked = 0 AND player.locked_by_user_id IS NULL AND player.is_deleted = 0
                    AND current_contact_user_id IS NULL
                ORDER BY player.timestamp, player.id ASC
                LIMIT 1
            """
        else:
            player_select_sql = """
                SELECT
                    player.id,
                    player.account,
                    player.username,
                    player.mobile,
                    player.qq,
                    player.locked,
                    player.locked_by_user_id
                FROM player
                WHERE id = %s
            """

        with connection.cursor() as cursor:
            if player_id is None:
                cursor.execute(refresh_player_sql, (user.id, ))
                player_info = namedtuplefetchall(cursor)
                if len(player_info) == 0:
                    cursor.execute(player_select_sql)
                    player_info = namedtuplefetchall(cursor)
            else:
                cursor.execute(player_select_sql, (player_id, ))
                player_info = namedtuplefetchall(cursor)

            if len(player_info) == 0:
                return {}

            player_info = player_info[0]

        # 查询玩家当前的标记信息
        player_contract_result_sql = """
            SELECT
                r.id, r.result, bind.contract_result_id
            FROM
                contract_result AS r
                    LEFT JOIN
                (SELECT tab_a.contract_result_id
                FROM player_bind_info AS tab_a
                WHERE tab_a.id = (SELECT max(id)
                              FROM player_bind_info AS tab_b
                              WHERE in_effect = 1 AND player_id = %s
                                  AND tab_a.player_id = tab_b.player_id
                              )
                ) AS bind ON bind.contract_result_id = r.id
        """

        with connection.cursor() as cursor:
            cursor.execute(player_contract_result_sql, (player_info.id, ))
            result_info = namedtuplefetchall(cursor)

        # 标记信息查询完毕

        # 查询最近的登录信息
        login_info_sql = """
                    SELECT
                        login_info.player_id,
                        login_info.login_time,
                        game.name AS game_name
                    FROM
                        player_login_info AS login_info
                        INNER JOIN game ON login_info.game_id = game.id
                    WHERE login_info.id = (
                        SELECT
                            login_a.id
                        FROM player_login_info AS login_a WHERE login_a.id = (
                            SELECT login_b.id FROM player_login_info AS login_b
                            WHERE login_a.player_id = login_b.player_id AND login_b.player_id = %s
                            ORDER BY login_b.login_time ASC LIMIT 1
                        )
                    )
                """

        with connection.cursor() as cursor:
            cursor.execute(login_info_sql, (player_info.id, ))
            login_info = namedtuplefetchall(cursor)
            if len(login_info) > 0:
                login_info_obj = login_info[0]
                login_info = {
                    "login_time": login_info_obj.login_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "game_name": login_info_obj.game_name
                }
            else:
                login_info = {"login_time": None, "game_name": None}
        # 查询最近登录的信息完毕

        # 查询玩家的注册游戏信息，最近的充值信息

        account_sql = """
            SELECT
                game.name AS game_name,
                register_info.register_time,
                account.money,
                account.charge_time
            FROM
                register_info
                    LEFT JOIN
                game ON register_info.game_id = game.id
                    LEFT JOIN
                (
                SELECT
                    tab_a.player_id,
                    tab_a.game_id,
                    tab_a.money,
                    tab_a.charge_time
                FROM account_log AS tab_a
                WHERE id = (
                            SELECT max(id)
                            FROM account_log AS tab_b
                            WHERE tab_b.player_id = tab_a.player_id AND tab_b.game_id = tab_a.game_id
                            )
                ) AS account ON account.player_id = register_info.player_id
                                    AND account.game_id = register_info.game_id

            WHERE register_info.player_id = %s
        """

        with connection.cursor() as cursor:
            cursor.execute(account_sql, (player_info.id, ))
            account_info = namedtuplefetchall(cursor)

        status_info = [
            {
                "value": result.id,
                "label": result.result,
                "selected": result.contract_result_id is not None
            } for result in result_info
        ]

        media = Media(
            js=['common/selector2/js/select2.full.js', 'js/player.js'],
            css={'all': ['common/selector2/css/select2.min.css', 'css/player.css']}
        )

        tbody = [
            {
                'columns': [
                    {'text': 1, 'style': 'display: none;'},
                    {'text': account_log.game_name},
                    {'text': account_log.register_time.strftime('%Y-%m-%d %H:%M:%S')\
                        if account_log.register_time else '--'},
                    {'text': account_log.money or 0},
                    {'text': account_log.charge_time.strftime('%Y-%m-%d %H:%M:%S')\
                        if account_log.charge_time else '--'
                     },
                ],

            } for account_log in account_info
            ]

        context = {
            'breadcrumb_items': [
                {
                    'href': '#',
                    'active': True,
                    'label': u'联系游戏玩家'
                }
            ],
            'status': status_info,
            'player': player_info,
            'login_info': login_info,
            'media': {
                'js': media.render_js(),
                'css': media.render_css()
            },
            'table': {
                'id': '_player-table',
                'headers': [
                    {'text': u'游戏'}, {'text': u'注册时间'}, {'text': u'最近充值金额（元）'},
                    {'text': u'充值时间'}
                ],
                'tbody': tbody,
            }
        }

        Player.objects.filter(id=player_info.id).update(current_contact_user=user, timestamp=datetime.now())

        return context

    @staticmethod
    def update_contact_result(user, player_id, params):
        try:
            player_obj = Player.objects.get(id=player_id)
        except ObjectDoesNotExist:
            return None

        username = params.get('username')
        qq = params.get('qq')
        status = params.get('status')
        locked_param = params.get('locked', 0)
        notes = params.get('notes')

        locked = locked_param == '1'

        changed_cols = {}

        if player_obj.username != username.strip():
            changed_cols['username'] = username.strip()

        if player_obj.qq != qq.strip():
            changed_cols['qq'] = qq.strip()

        if player_obj.locked == locked:
            changed_cols['locked'] = locked
            changed_cols['locked_by_user'] = user
            changed_cols['locked_time'] = datetime.now()

        if changed_cols:
            Player.objects.filter(id=player_id).update(**changed_cols)

        if status:
            try:
                status_obj = ContractResult.objects.get(id=status)
            except ObjectDoesNotExist:
                return None

            PlayerBindInfo.objects.create(
                user=user,
                player=player_obj,
                is_bound=status_obj.bind,
                contract_time=datetime.now(),
                contract_result=status_obj,
                in_effect=True,
                notes=notes
            )

        return player_obj

    @staticmethod
    def update(player_id, params):
        try:
            player_obj = Player.objects.get(id=player_id)
        except ObjectDoesNotExist:
            return None

        account = params.get('account')
        player_name = params.get("username")
        player_mobile = params.get('mobile', '')
        player_qq = params.get('qq', '')

        game_field_info = {}
        game_field_reg = re.compile(r'^game_id([0-9]*)')
        for field_name, field_value in params.items():
            m = game_field_reg.match(field_name)
            if m is not None:
                game_id = m.group(1)
                game_time = params.get('game_time%s' % game_id)
                try:
                    game_time = datetime.strptime(game_time, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    try:
                        game_time = datetime.strptime(game_time, '%Y-%m-%d')
                    except ValueError:
                        return {'msg': "时间格式不正确，格式如：2017-09-21 12:00:00"}
                game_field_info[field_value] = game_time

        Player.objects.filter(id=player_id).update(
            account=account,
            username=player_name,
            mobile=player_mobile,
            qq=player_qq
        )

        register_game_objs = RegisterInfo.objects.filter(player_id=player_id)

        registered_game_ids = ['%d' % register_game_obj.game_id for register_game_obj in register_game_objs]

        for game_id, game_time in game_field_info.items():
            if game_id in registered_game_ids:
                # 当前注册，在请求中，更新时间
                RegisterInfo.objects.filter(
                    player_id=player_id,
                    game_id=game_id
                ).update(register_time=game_time)
            else:
                RegisterInfo.objects.create(
                    player_id=player_id,
                    game_id=game_id,
                    register_time=game_time
                )
            registered_game_ids.remove(game_id)

        if registered_game_ids:
            RegisterInfo.objects.filter(
                player_id=player_id, game_id__in=registered_game_ids
            ).delete()

        return player_obj

    @staticmethod
    def delete(player_id):
        try:
            player_obj = Player.objects.get(id=player_id)
            player_obj.delete()
        except ObjectDoesNotExist:
            player_obj = None

        return player_obj

    @staticmethod
    def save(params):
        account = params.get('account')
        player_name = params.get("username")
        player_mobile = params.get('mobile', '')
        player_qq = params.get('qq', '')

        game_field_info = []
        game_field_reg = re.compile(r'^game_id([0-9]*)')
        for field_name, field_value in params.items():
            m = game_field_reg.match(field_name)
            if m is not None:
                game_id = m.group(1)
                game_time = params.get('game_time%s' % game_id)
                try:
                    game_time = datetime.strptime(game_time, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    try:
                        game_time = datetime.strptime(game_time, '%Y-%m-%d')
                    except ValueError:
                        return {'msg': "时间格式不正确，格式如：2017-09-21 12:00:00"}
                game_field_info.append({
                    'game_id': int(field_value),
                    'reg_time': game_time
                })

        player_obj = Player.objects.create(
            account=account,
            username=player_name,
            mobile=player_mobile,
            qq=player_qq
        )

        for game_field in game_field_info:
            RegisterInfo.objects.create(
                player=player_obj,
                game_id=game_field['game_id'],
                register_time=game_field['reg_time']
            )

        return player_obj

    @staticmethod
    def menu_exists(name):
        if name == '' or name == '#':
            return False
        menu_obj = Menu.objects.filter(name=name)

        return menu_obj.count() > 0

    @staticmethod
    def _import_player(user, stored_path, filename, player_import):
        file_name = os.path.join(stored_path, filename)
        workbook = xlrd.open_workbook(file_name)
        sheet = workbook.sheet_by_index(0)

        notes = sheet.cell(0, 0).value

        titles = sheet.row(1)

        title_index = {
            'account': -1,
            'charge_money': -1,
            'charge_time': -1,
            'mobile': -1,
            'come_from': -1,
            'register_name': -1,
            'register_time': -1,
            'last_login_game': -1,
            'last_login_time': -1
        }

        for ind, title in enumerate(titles):
            if title.value == '玩家账号':
                title_index['account'] = ind
            elif title.value == '最近登陆时间':
                title_index['last_login_time'] = ind
            elif title.value == '最近充值金额':
                title_index['charge_money'] = ind
            elif title.value == '最近充值时间':
                title_index['charge_time'] = ind
            elif title.value == '注册时间':
                title_index['register_time'] = ind
            elif title.value == '手机':
                title_index['mobile'] = ind
            elif title.value == '所属渠道':
                title_index['come_from'] = ind
            elif title.value == '注册游戏':
                title_index['register_name'] = ind
            elif title.value == '最近登录游戏':
                title_index['last_login_game'] = ind

        for row_ind in range(2, sheet.nrows):
            player_data = sheet.row(row_ind)
            account_col = player_data[title_index['account']]

            account = '%d' % int(account_col.value) if account_col.ctype == xlrd.XL_CELL_NUMBER else account_col.value
            mobile = player_data[title_index['mobile']].value
            come_from = player_data[title_index['come_from']].value
            charge_money = player_data[title_index['charge_money']].value
            charge_time = player_data[title_index['charge_time']].value
            last_login_game = player_data[title_index['last_login_game']].value
            last_login_time = player_data[title_index['last_login_time']].value
            register_name = player_data[title_index['register_name']].value
            register_time = player_data[title_index['register_time']].value

            try:
                player_obj = Player.objects.get(account=account)
                player_obj.mobile = mobile
                player_obj.come_from = mobile
                player_obj.imported_from = player_import
                player_obj.save()
            except ObjectDoesNotExist:
                player_obj = Player.objects.create(
                    account=account,
                    mobile=mobile,
                    come_from=come_from,
                    import_from=player_import
                )

            if register_name.strip() != '':
                try:
                    game_obj = Game.objects.get(name=register_name)
                except ObjectDoesNotExist:
                    game_obj = Game.objects.create(name=register_name)

                try:
                    register_info_obj = RegisterInfo.objects.get(
                        player=player_obj,
                        game=game_obj
                    )
                    register_info_obj.register_time = register_time
                    register_info_obj.save()
                except ObjectDoesNotExist:
                    RegisterInfo.objects.create(
                        player=player_obj,
                        game=game_obj,
                        register_time=register_time
                    )

                AccountLog.objects.create(
                    player=player_obj,
                    game=game_obj,
                    money=charge_money,
                    charge_time=charge_time,
                    recorder=user
                )

            if last_login_game.strip() != '':
                try:
                    last_login_game_obj = Game.objects.get(name=last_login_game)
                except ObjectDoesNotExist:
                    last_login_game_obj = Game.objects.create(name=last_login_game)

                PlayerLoginInfo.objects.create(
                    player=player_obj,
                    game=last_login_game_obj,
                    login_time=last_login_time
                )

        return notes

    @staticmethod
    def import_player(user, time_obj, stored_path, stored_name, filename):

        player_import_obj = PlayerImport.objects.create(
            filename=filename,
            path=stored_path,
            stored_name=stored_name,
            import_time=time_obj,
        )

        notes = PlayerManager._import_player(user, stored_path, stored_name, player_import_obj)

        player_import_obj.notes = notes
        player_import_obj.save()

    @staticmethod
    def export_player():
        pass