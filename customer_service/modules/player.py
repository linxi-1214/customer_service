import os
import re
import json
import logging
from datetime import datetime
from collections import namedtuple

import xlrd, xlsxwriter

from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from django.forms.widgets import Media
from django.db import connection
from django.conf import settings

from customer_service.models import Menu, Role, RoleBindMenu

from customer_service.models import (
    Game, Player, RegisterInfo, PlayerImport, PlayerExport, AccountLog,
    PlayerLoginInfo, ContractResult, PlayerBindInfo
)

logger = logging.getLogger(__name__)


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
    def _generate_top_form():
        """
        返回玩家列表的查询表单
        :return:
        """

        game_objs = Game.objects.all()
        result_objs = ContractResult.objects.all()

        game_obj_dict = [
            {'label': _game_obj.name, "value": _game_obj.id} for _game_obj in game_objs
        ]

        result_obj_dict = [
            {'label': _result.result, "value": _result.id} for _result in result_objs
        ]

        top_form = {
            "method": "post",
            "action": "#",
            "fields": [
                {
                    "type": "text",
                    "before": "game",
                    "name": "account",
                    "id": "_account",
                    "attrs": {"style": "width: 150px; margin-right: 10px"}
                },
                {
                    "type": "text",
                    "before": "mobile",
                    "name": "mobile",
                    "id": "_mobile",
                    "attrs": {'style': "margin-right: 10px"}
                },
                {
                    "type": "text",
                    "name": "charge_money_min",
                    "id": "_charge_money_min",
                    "before": "money",
                    "attrs": {
                        "style": "width: 120px;"
                    }
                },
                {
                    "type": "text",
                    "label": u"-",
                    "name": "charge_money_max",
                    "id": "_charge_money_max",
                    "before": "money",
                    "attrs": {
                        "style": "width: 120px; margin-right: 10px;",
                    }
                },
                {
                    "type": "select",
                    "name": "game_name",
                    "id": "_game_name",
                    "options": game_obj_dict,
                    "attrs": {'style': "margin-right: 20px; min-width: 120px;"}
                },
                {
                    "type": "select",
                    "name": "result",
                    "id": "_result",
                    "options": result_obj_dict,
                    "attrs": {'style': "margin-right: 20px; min-width: 120px;"}
                },
                {
                    "type": "button",
                    "button_type": "button",
                    "label": u'查&nbsp;&nbsp;询 <i class="fa fa-search"></i>',
                    "click": "player_query(); return false;",
                    "extra_class": "btn-outline btn-primary",
                    "attrs": {'style': 'margin-left: 20px;'}
                },
                {
                    "type": "button",
                    "button_type": "button",
                    "label": u'导出到 EXCEL <i class="fa  fa-sign-out"></i>',
                    "extra_class": "btn-outline btn-warning pull-right",
                    "click": "export_player();"
                }
            ]
        }
        return top_form

    @staticmethod
    def _actions(user, player_obj, is_deleted):
        delete_url = reverse('delete_player')
        recycle_url = reverse('recycle_player')
        if user.role_id == settings.SERVICE_ROLE:
            return [
                {
                    'icon': 'fa-phone-square',
                    'tooltip': u'继续联系',
                    'theme': ' contact ',
                    'href': "%s?player=%d" % (reverse('contract_player'), player_obj.id)
                }
            ]
        else:
            if is_deleted:
                return [
                    {
                        'icon': 'fa-recycle',
                        'tooltip': u'恢复玩家',
                        'theme': ' recycle ',
                        'href': "",
                        'func': 'recycle_player(this, "{url}", {id}, "{label}"); return false;'.format(
                            url=recycle_url, id=player_obj.id, label=player_obj.account
                        )
                    },
                    {
                        'href': '',
                        'icon': 'fa-trash-o',
                        'tooltip': u'删除',
                        'theme': ' delete ',
                        'func': 'delete_player(this, "{url}", {id}, "{label}", true); return false;'.format(
                            url=delete_url, id=player_obj.id, label=player_obj.account
                        )
                    }
                ]
            else:
                return [
                    {
                        'icon': 'fa-edit',
                        'tooltip': u'编辑',
                        'theme': ' edit ',
                        'href': reverse('edit_player', args=(player_obj.id,))
                    },
                    {
                        'href': '',
                        'icon': 'fa-trash-o',
                        'tooltip': u'删除',
                        'theme': ' delete ',
                        'func': 'delete_player(this, "{url}", {id}, "{label}", false); return false;'.format(
                            url=delete_url, id=player_obj.id, label=player_obj.account
                        )
                    }
                ]

    @staticmethod
    def index(user, is_deleted=0):
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
            WHERE player.is_deleted = %s
        """
        params = [is_deleted]
        if user.role_id != settings.ADMIN_ROLE:
            sql += "AND player.locked_by_user_id = %s"
            params.append(user.id)

        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            player_qry_set = namedtuplefetchall(cursor)

            player_id_list = [player_obj.id for player_obj in player_qry_set]

        if len(player_id_list) > 0:
            place_holder = ", ".join(['%s'] * len(player_id_list))
            register_info_sql = """
                SELECT
                    register_info.player_id,
                    register_info.register_time,
                    game.name AS game_name
                FROM
                    register_info
                    INNER JOIN
                    game ON register_info.game_id = game.id
                    INNER JOIN
                    (
                        SELECT
                            player_id, MIN(register_time)
                        FROM register_info
                        WHERE player_id IN (%s)
                        GROUP BY player_id
                    ) AS register_info_b ON register_info.player_id = register_info_b.player_id
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
                    'actions': PlayerManager._actions(user, player_obj, is_deleted)
                } for player_obj in player_qry_set
            ]
        else:
            tbody = []

        media = Media(js=[
            'js/player.js',
            'vendor/datatables/js/dataTables.buttons.min.js',
            'vendor/xlsx/xlsx.full.min.js',
            'vendor/xlsx/Blob.js', 'vendor/xlsx/FileSaver.js',
            'vendor/xlsx/swfobject.js', 'vendor/xlsx/downloadify.min.js', 'vendor/xlsx/base64.min.js',
            'js/export.js', 'js/table.js'
        ])

        table_buttons = [
            {
                'text': u'全 选', 'class': 'btn-sm btn-success',
                'click': "select_all(false, '_player-table');"
            },
            {
                'text': u'反 选', 'class': 'btn-sm btn-success',
                'click': "select_all(true, '_player-table');"
            },
            {
                'text': u'删 除', 'class': 'btn-sm btn-danger',
                'click': "delete_selected('_player-table', '%s', %s);" % (
                    reverse('delete_player_multi'), "true" if is_deleted else "false")
            }
        ]
        if is_deleted:
            table_buttons.append(
                {
                    'text': u'恢 复', 'class': 'btn-sm btn-primary',
                    "click": 'recycle_selected("_player-table", "%s");' % reverse('recycle_player')
                }
            )

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
                'buttons': table_buttons,
                'headers': [
                    {'text': u'账号'}, {'text': u'姓名'}, {'text': u'手机号'},
                    {'text': u'QQ号码'}, {'text': u'注册游戏'}, {'text': u'注册时间'},
                    {'text': u'所属客服'}, {'text': u'渠道'}, {'text': u'最近登录游戏'}, {'text': u'登录时间'},
                    {'text': u'充值次数'}, {'text': u'充值总额'},
                    {'text': u'最近充值游戏'}, {'text': u'最近充值金额'}, {'text': u'最近充值时间'}, {'text': u'备注'},
                    {'text': u'操作'}
                ],
                'tbody': tbody,
                'top_form': PlayerManager._generate_top_form()
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
                "class": "nice-validator n-default n-bootstrap",
                "attrs": "data-validator-option=\"{theme:'bootstrap', timely:2, stopOnError:true}\"",
                "fields": [
                    {
                        "type": "text",
                        "label": u"玩家账号",
                        "help_id": "player_account_help",
                        "help_text": u"玩家登录账号，由字母和数字组成，唯一",
                        "name": "account",
                        "id": "_account",
                        "placeholder": "account1",
                        "attrs": {
                            "data-rule": "玩家账号: required;"
                        }
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
                        'name': 'game_id' + ('%s' % str(ind-1) if ind > 0 else ''),
                        'id': '_game_id' + ('%s' % str(ind-1) if ind > 0 else ''),
                        'options': game_options['game_options'],
                        "group_css": "col-lg-4"
                    },
                    {
                        "type": "text",
                        "label": u'注册时间',
                        "name": "game_time" + ("%s" % str(ind-1) if ind > 0 else ''),
                        "id": "_game_time" + ("%s" % str(ind-1) if ind > 0 else ''),
                        "group_css": "col-lg-4",
                        "value": game_options['reg_time'].strftime('%Y-%m-%d %H:%M:%S') if game_options['reg_time'] else ''
                    },
                    {
                        "type": "icon_button",
                        "click": "delete_register_game(this);",
                        "icon": "fa-minus-circle",
                        "extra_class": "btn-danger delete-icon-button",
                        "tooltip": u'删除',
                        "tooltip_position": 'right',
                        "group_css": "col-lg-2"
                    }
                ]
            } for ind, game_options in enumerate(game_options_list)
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
            js=['common/selector2/js/select2.full.js', 'js/player.js'],
            css={'all': ['common/fileupload/css/fileinput.css',
                         'common/selector2/css/select2.min.css',
                         'css/player.css']}
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
                    {'text': import_record.notes or '--'}
                ],
                'actions': [
                    {
                        'icon': 'fa-play-circle',
                        'tooltip': u'查看导入结果',
                        'label': u'',
                        'theme': ' play ',
                        # 'href': reverse('import_detail', args=(import_record.id,))
                        'href': '#',
                        'func': 'import_result_detail("%s");' % reverse('import_detail', args=(import_record.id, ))
                    },
                    {
                        'icon': 'fa-download',
                        'tooltip': u'下载',
                        'href': '#',
                        'theme': ' download '
                    }
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
                'id': '_player-import-table',
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
        # 查询该客服目前有没有查看过该玩家
        player_bind_info_qry_sql = """
            SELECT
                count(*) AS counter
            FROM player_bind_info
                INNER JOIN
                contract_result ON contract_result.id = player_bind_info.contract_result_id
            WHERE user_id = %s
                AND player_id = %s AND contract_result.process = %s
                AND in_effect = 1 AND {time_func_str} = %s
        """
        if settings.DATABASE_TYPE == "sqlite":
            player_bind_info_qry_sql = player_bind_info_qry_sql.format(
                time_func_str="STRFTIME('%%Y-%%m-%%d', contract_time)"
            )
        elif settings.DATABASE_TYPE == "mysql":
            player_bind_info_qry_sql = player_bind_info_qry_sql.format(
                time_func_str="DATE_FORMAT(contract_time, '%%Y-%%m-%%d')"
            )
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
                FROM
                    player
                        LEFT JOIN
                    (SELECT
                        player_id
                    FROM
                        player_bind_info
                    WHERE
                        is_bound = 1 AND in_effect = 1) AS player_bind_info ON player.id != player_bind_info.player_id
                WHERE
                    player.locked = 0
                        AND player.locked_by_user_id IS NULL
                        AND player.is_deleted = 0
                        AND current_contact_user_id IS NULL
                ORDER BY player.timestamp , player.id ASC
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

            cursor.execute(player_bind_info_qry_sql,
                           (
                               user.id, player_info.id, settings.PROCESS['looked'],
                               datetime.now().strftime('%Y-%m-%d')
                           ))
            bind_info = namedtuplefetchall(cursor)[0]

            if bind_info.counter == 0:
                try:
                    looked_object = ContractResult.objects.filter(process=settings.PROCESS['looked']).first()
                    PlayerBindInfo.objects.create(
                        user=user, player_id=player_info.id,
                        is_bound=False, contract_time=datetime.now(),
                        contract_result=looked_object, in_effect=True
                    )
                except ObjectDoesNotExist:
                    pass

        # 查询玩家当前的标记信息

        contact_result = ContractResult.objects.all()
        last_contact_result_sql = """
            SELECT
                *
            FROM player_bind_info
            WHERE contract_result_id IN (SELECT id FROM contract_result WHERE process > %s) AND player_id=%s
            ORDER BY id DESC LIMIT 1
        """

        with connection.cursor() as cursor:
            cursor.execute(last_contact_result_sql, (settings.PROCESS['looked'], player_info.id))
            bind_result = namedtuplefetchall(cursor)

        if len(bind_result) == 0:
            bind_result = None

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

        # 查询玩家的备注信息
        note_info_set = PlayerBindInfo.objects.filter(player_id=player_info.id).order_by('-contract_time')
        note_info = [
            "% 2d. [时间：%s] 备注：%s" % (
                ind,
                _note.contract_time.strftime('%Y-%m-%d %H:%M:%S'),
                _note.note
            ) for ind, _note in enumerate(note_info_set, start=1) if _note.note is not None and _note.note != ""
        ]

        status_info = [
            {
                "value": result.id,
                "label": result.result,
                "selected": result.process == settings.PROCESS['looked'] if
                bind_result is None else result.id == bind_result[0].contract_result_id
            } for result in contact_result
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
            'note_info': "<br>".join(note_info),
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

        if player_obj.username != username.strip():
            player_obj.username = username.strip()

        if player_obj.qq != qq.strip():
            player_obj.qq = qq.strip()

        if player_obj.locked != locked:
            player_obj.locked = locked
            player_obj.locked_by_user = user if locked else None
            player_obj.locked_time = datetime.now() if locked else None

        if status:
            try:
                status_obj = ContractResult.objects.get(id=status)
            except ObjectDoesNotExist:
                return None

            if status_obj.bind:
                player_obj.locked_by_user = user
                player_obj.locked = True
                player_obj.locked_time = datetime.now()

            PlayerBindInfo.objects.create(
                user=user,
                player=player_obj,
                is_bound=status_obj.bind,
                contract_time=datetime.now(),
                contract_result=status_obj,
                in_effect=True,
                note=notes
            )

        player_obj.save()

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

        registered_game_dict = dict([
            ('%d' % _g.game_id, _g.register_time) for _g in register_game_objs
        ])

        print(game_field_info)
        for game_id, game_time in game_field_info.items():
            if game_id in registered_game_ids:
                # 当前注册，如果在请求中，更新时间
                if game_time != registered_game_dict[game_id]:
                    RegisterInfo.objects.filter(
                        player_id=player_id,
                        game_id=game_id
                    ).update(register_time=game_time)
                registered_game_ids.remove(game_id)
            else:
                RegisterInfo.objects.create(
                    player_id=player_id,
                    game_id=game_id,
                    register_time=game_time
                )

        if registered_game_ids:
            RegisterInfo.objects.filter(
                player_id=player_id, game_id__in=registered_game_ids
            ).delete()

        return player_obj

    @staticmethod
    def delete(player_id, force_delete=False, really_delete=False):
        if isinstance(player_id, (list, tuple)):
            # check player if locked by service while force_delete and really_delete are both False
            if not (force_delete or really_delete):
                player_locked_set = Player.objects.filter(id__in=player_id, locked_by_user__isnull=False)
                if player_locked_set.count() > 0:
                    return False, player_locked_set
            try:
                if not really_delete:
                    Player.objects.filter(id__in=player_id).update(is_deleted=True)
                else:
                    Player.objects.filter(id__in=player_id).delete()
            except:
                return False, None

            return True, None
        else:
            try:
                player_obj = Player.objects.get(id=player_id)
                if not (force_delete or really_delete):
                    if player_obj.locked_by_user is not None:
                        return False, player_obj
                if not really_delete:
                    player_obj.is_deleted = True
                    player_obj.save()
                else:
                    player_obj.delete()
            except ObjectDoesNotExist:
                player_obj = None
            except:
                return False, None

            return True, player_obj

    @staticmethod
    def save(params):
        account = params.get('account')
        player_name = params.get("username")
        player_mobile = params.get('mobile', '')
        player_qq = params.get('qq', '')

        game_field_info = []
        game_field_reg = re.compile(r'^game_id([0-9]+)')
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

        title_index = {}

        for ind, title in enumerate(titles):
            title_index[title.value] = ind

        import_result_error = []
        for row_ind in range(2, sheet.nrows):
            player_data = sheet.row(row_ind)
            if u'玩家账号' not in title_index:
                raise Exception("没有指定玩家账号。")

            account_col = player_data[title_index[u'玩家账号']]
            mobile = player_data[title_index[u'手机']] if u'手机' in title_index else None

            account = '%d' % int(account_col.value) if account_col.ctype == xlrd.XL_CELL_NUMBER else account_col.value
            mobile = '%d' % int(mobile.value) if mobile.ctype == xlrd.XL_CELL_NUMBER else mobile.value
            come_from = player_data[title_index[u'所属渠道']].value if u'所属渠道' in title_index else None
            charge_money = player_data[title_index[u'最近充值金额']].value if u'最近充值金额' in title_index else None
            charge_time = player_data[title_index[u'最近充值时间']].value if u'最近充值时间' in title_index else None
            last_login_game = player_data[title_index[u'最近登录游戏']].value if u'最近登录游戏' in title_index else None
            last_login_time = player_data[title_index[u'最近登陆时间']].value if u'最近登陆时间' in title_index else None
            register_name = player_data[title_index[u'注册游戏']].value if u'注册游戏' in title_index else None
            register_time = player_data[title_index[u'注册时间']].value if u'注册时间' in title_index else None
            game_count = player_data[title_index[u'游戏数量']].value if u'游戏数量' in title_index else None
            charge_money_total = player_data[title_index[u'充值总额']].value if u'充值总额' in title_index else None

            try:
                try:
                    player_obj = Player.objects.get(account=account)
                    player_obj.mobile = mobile
                    player_obj.come_from = come_from
                    player_obj.imported_from = player_import
                    player_obj.charge_money_total = charge_money_total
                    player_obj.game_count = game_count
                    player_obj.save()
                except ObjectDoesNotExist:
                    player_obj = Player.objects.create(
                        account=account,
                        mobile=mobile,
                        come_from=come_from,
                        imported_from=player_import, game_count=game_count, charge_money_total=charge_money_total
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
            except Exception as err:
                logger.exception('import player error:')
                import_result_error.append({
                    'account': account,
                    'error': str(err)
                })

        return notes, import_result_error

    @staticmethod
    def import_player(user, time_obj, stored_path, stored_name, filename):
        player_import_obj = PlayerImport.objects.create(
            filename=filename,
            path=stored_path,
            stored_name=stored_name,
            import_time=time_obj,
        )

        notes, import_result_error = PlayerManager._import_player(user, stored_path, stored_name, player_import_obj)

        player_import_obj.notes = notes
        player_import_obj.result = json.dumps(import_result_error)
        player_import_obj.save()

    @staticmethod
    def import_result_query(import_id):
        try:
            player_import_obj = PlayerImport.objects.get(id=import_id)
        except ObjectDoesNotExist:
            return '[]'

        result_list = player_import_obj.result

        return result_list

    @staticmethod
    def export_player():
        pass

    @staticmethod
    def _query_player(user, player_id=None, time_range=''):
        if user.is_superuser:
            player_set = Player.objects.all()
        else:
            player_sql = """
                SELECT
                    player.id
                    player.account
                FROM player
                    INNER JOIN
                    player_bind_info ON player_bind_info.player_id = player.id
                WHERE player_bind_info.is_bound = 1 AND player_bind_info.user_id = %s
            """
            with connection.cursor() as cursor:
                cursor.execute(player_sql, (user.id,))
                player_set = namedtuplefetchall(cursor)

        media = Media(js=['common/selector2/js/select2.full.js',
                          'vendor/datatables/js/jquery.dataTables.min.js',
                          'vendor/datatables/js/dataTables.bootstrap4.min.js',
                          'common/date/dateRange.js',
                          'js/player.js'],
                      css={'all': [
                          'vendor/bootstrap-social/bootstrap-social.css',
                          'vendor/datatables/css/dataTables.bootstrap4.min.css',
                          'common/selector2/css/select2.min.css',
                          'common/date/dateRange.css'
                      ]})
        options = [
            {
                "label": player.account, "value": player.id, "selected": '%d' % player.id == player_id
            } for player in player_set
        ]

        context = {
            'breadcrumb_items': [
                {
                    'href': '#',
                    'active': True,
                    'label': u'玩家联系记录'
                }
            ],
            'media': {
                'js': media.render_js(),
                "css": media.render_css()
            },
            "form": {
                "method": "post",
                "action": "",
                "fields": [
                    {
                        "type": "group",
                        "attrs": {
                            "id": "register_game_info_id"
                        },
                        "group_css": "register-game-none",
                        "group": [
                            {
                                "type": "select",
                                "label": u"玩家账号",
                                "name": "account",
                                "id": "_account",
                                'options': options,
                                "group_css": "col-lg-4"
                            },
                            {
                                "type": "text",
                                "label": u"时间范围",
                                "name": "time-range",
                                "id": "_time-range",
                                "group_css": "col-lg-4",
                                "value": time_range
                            },
                            {
                                "type": "group_button",
                                "label": u'<i class="fa fa-info-circle"></i>  查&nbsp;&nbsp;看',
                                "extra_class": "btn-outline btn-primary delete-icon-button",
                                "button_type": "submit",
                                "group_css": "col-lg-2"
                            }
                        ]
                    },

                ]
            }
        }

        return context

    @staticmethod
    def _query_player_contact_detail(player_id, date_range):
        try:
            player = Player.objects.get(id=player_id or '0')
        except ObjectDoesNotExist:
            return {}

        bind_info_sql = """
            SELECT
                service.first_name,
                service.last_name,
                service.loginname,
                bind_info.is_bound,
                bind_info.contract_time,
                bind_info.note,
                contact.result,
                contact.process
            FROM
                player_bind_info AS bind_info
                INNER JOIN
                customer_service_user AS service ON service.id = bind_info.user_id
                INNER JOIN
                contract_result AS contact ON contact.id = bind_info.contract_result_id
            WHERE bind_info.player_id = %s {time_range}
            ORDER BY bind_info.contract_time DESC, contact.process ASC
        """

        if date_range is None:
            time_range_condition = ""
            params = (player_id, )
        else:
            time_range_condition = "AND bind_info.contract_time BETWEEN %s AND %s"
            params = (player_id, date_range[0], date_range[1])

        bind_info_sql = bind_info_sql.format(time_range=time_range_condition)

        with connection.cursor() as cursor:
            cursor.execute(bind_info_sql, params)
            bind_info_set = namedtuplefetchall(cursor)

        icon = ["fa-eye", "fa-link", "fa-phone", "fa-lock"]
        icon_class = ["default", "info", "warning", "success"]

        bind_info_list = [
            {
                "user": "%s%s(%s)" % (bind_info.first_name or '', bind_info.last_name or '', bind_info.loginname),
                "is_bound": bind_info.is_bound,
                "contact_time": (bind_info.contract_time.strftime('%Y-%m-%d %H:%M:%S')
                                 if bind_info.contract_time else ''),
                "result": bind_info.result, "process": bind_info.process,
                "note": bind_info.note,
                "arrow_class": "timeline-inverted" if ind % 2 == 0 else "",
                "icon": icon[(bind_info.process - 1) % 4],
                "icon_class": icon_class[(bind_info.process - 1) % 4],
                'player': player.account
            } for ind, bind_info in enumerate(bind_info_set)
            ]

        headers = [
            {'text': u'玩家账号'}, {'text': u'联系玩家'}, {'text': u'联系时间'},
            {'text': u'联系结果'}, {'text': u'备注'}
        ]

        tbody = [
            {
                'columns': [
                    {'text': 1, "style": "display: none"},
                    {'text': bind_info.get('player') or '--'},
                    {'text': bind_info.get('user') or '--'},
                    {'text': bind_info.get('contact_time') or '--'},
                    {'text': bind_info.get('result') or '--'},
                    {'text': bind_info.get('note') or '--'}
                ]
            } for bind_info in bind_info_list
            ]

        table = {
            'id': '_player-contact-table',
            'headers': headers,
            'tbody': tbody,
        }

        return {'contact_record': bind_info_list, "table": table}

    @staticmethod
    def player_contact_detail(user, player_id=None, date_range=None):
        if date_range is not None:
            time_range = '%s ~ %s' % tuple(date_range)
        else:
            time_range = ''
        context = PlayerManager._query_player(user, player_id, time_range)
        contact_info = PlayerManager._query_player_contact_detail(player_id, date_range)

        context.update(contact_info)

        return context
