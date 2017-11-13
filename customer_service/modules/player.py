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
from django.db.models import Q

from django.forms.widgets import Media
from django.db import connection
from django.conf import settings

from customer_service.models import Menu, Role, RoleBindMenu
from customer_service.tools.model import updated_fields, set_operator

from customer_service.models import (
    Game, Player, RegisterInfo, PlayerImport, PlayerExport, AccountLog,
    PlayerLoginInfo, ContractResult, PlayerBindInfo, User
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
    def _generate_top_form(user):
        """
        返回玩家列表的查询表单
        :return:
        """

        game_objs = Game.objects.all()
        result_objs = ContractResult.objects.all()

        if user.role_id == settings.ADMIN_ROLE:
            user_objs = User.objects.all()
            user_obj_dict = [
                {'label': _user.loginname, "value": _user.id} for _user in user_objs
            ]
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
                    "placeholder": u'玩家账号',
                    "id": "_account",
                    "attrs": {"style": "width: 150px; margin-right: 10px"}
                },
                {
                    "type": "text",
                    "before": "mobile",
                    "name": "mobile",
                    "placeholder": u'手机号',
                    "id": "_mobile",
                    "attrs": {'style': "margin-right: 10px"}
                },
                {
                    "type": "text",
                    "name": "charge_money_min",
                    "placeholder": u'总额小',
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
                    "placeholder": u'总额大',
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
                    "attrs": {
                        'style': "margin-right: 20px; min-width: 120px;",
                        'data-placeholder': u'游戏'
                    }
                },
                {
                    "type": "select",
                    "name": "result",
                    "id": "_result",
                    "options": result_obj_dict,
                    "attrs": {
                        'style': "margin-right: 20px; min-width: 120px;",
                        'data-placeholder': u'联系结果'
                    }
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
        if user.role_id == settings.ADMIN_ROLE:
            top_form['fields'].insert(2, {
                "type": "select",
                "name": "user",
                "id": "_user",
                "options": user_obj_dict,
                "attrs": {'style': "min-width: 150px;", 'data-placeholder': u'所属客服'}
            })
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
                        'icon': 'fa-phone-square',
                        'tooltip': u'联系该玩家',
                        'theme': ' contact ',
                        'href': "%s?player=%d" % (reverse('contract_player'), player_obj.id)
                    },
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
    def _render_action_html(user, is_deleted):
        delete_url = reverse('delete_player')
        recycle_url = reverse('recycle_player')
        contact_url = reverse('contract_player')
        edit_url = reverse('edit_player', args=(0,))
        edit_url = os.path.dirname(edit_url.rstrip('/'))

        if user.role_id == settings.SERVICE_ROLE:
            function = """function () {
                return '<div class="text-center tooltip-demo">' +
                    '<a class="btn btn-social-icon contact btn-sm" action="contact_player" ' +
                    '    data-toggle="tooltip" data-placement="bottom"' +
                    '    href="#" title="联系该玩家" url="%s">' +
                    '    <i class="fa fa-phone-square"></i>' +
                    '</a>' +
                '</div>';
            }""" % contact_url
        else:
            if is_deleted:
                function = """function() {
                    return '<div class="text-center tooltip-demo">' +
                        '<a class="btn btn-social-icon contact btn-sm" action="recycle_player" ' +
                        ' data-toggle="tooltip" data-placement="bottom" href="#" title="恢复该玩家" url="%s">' +
                        '    <i class="fa fa-recycle"></i>' +
                        '</a>' +
                        '<a class="btn btn-social-icon delete btn-sm" action="delete_player" delete="1" ' +
                        ' data-toggle="tooltip" data-placement="bottom" href="#" title="删除" url="%s">' +
                        '    <i class="fa fa-trash-o"></i>' +
                        '</a>' +
                    '</div>';
                }""" % (recycle_url, delete_url)
            else:
                function = """function () {
                    return '<div class="text-center tooltip-demo">' +
                        '<a class="btn btn-social-icon contact btn-sm" action="contact_player" ' +
                        ' data-toggle="tooltip" data-placement="bottom" href="#" title="联系该玩家" url="%s">' +
                        '    <i class="fa fa-phone-square"></i>' +
                        '</a>' +
                        '<a class="btn btn-social-icon edit btn-sm" data-toggle="tooltip" action="edit_player" ' +
                        ' data-placement="bottom" href="#" title="编辑" url="%s">' +
                        '    <i class="fa fa-edit"></i>' +
                        '</a>' +
                        '<a class="btn btn-social-icon delete btn-sm" action="delete_player" delete="0" ' +
                        ' data-toggle="tooltip" data-placement="bottom" href="#" title="删除" url="%s">' +
                        '    <i class="fa fa-trash-o"></i>' +
                        '</a>' +
                    '</div>'
                }""" % (contact_url, edit_url, delete_url)

        return function

    @staticmethod
    def _structure_pagination(p):
        if p is None:
            return '', '', ''
        order_info_list = p.orders
        columns = p.columns
        order_by = []
        search = []
        for order_info in order_info_list:
            column_index = int(order_info.column)
            column_name = p.columns[column_index].data
            if column_name == '':
                continue
            order_by.append('%s %s' % (column_name, order_info.dir))

        if order_by:
            order_by_sql = "ORDER BY %s" % ", ".join(order_by)
        else:
            order_by_sql = ""

        for column in columns:
            if column.search.value:
                if column.data == 'register_from_game':
                    column_name = 'game.`name`'
                else:
                    column_name = column.data
                if column.search.regex == 'false':
                    search.append("%s = '%s'" % (column_name, column.search.value))
                else:
                    search.append("%s LIKE '%%%%%s%%%%'" % (column_name, column.search.value))

        if p.money_min is not None and p.money_min != '':
            search.append('charge_money_total >= %s' % p.money_min)
        if p.money_max is not None and p.money_max != '':
            search.append('charge_money_total <= %s' % p.money_max)

        if search:
            search_sql = ' AND %s ' % ' AND '.join(search)
        else:
            search_sql = ''

        limit_sql = " LIMIT %s, %s" % (p.start, p.length)

        return search_sql, order_by_sql, limit_sql

    @staticmethod
    def player_condition_query(user, is_deleted=0, pagination=None):
        player_query_sql = """
        SELECT
            player.id, player.account, player.username, player.mobile, player.qq, player.locked,
            player.come_from, player.charge_count, player.charge_money_total,
            game.`name` AS register_from_game, player.register_from_game_time AS register_time,
            customer_service_user.loginname, customer_service_user.first_name, customer_service_user.last_name,

            player_bind_info.result, player_bind_info.contract_time,

            player_login_info.id AS login_game_id, player_login_info.login_game AS last_login_game, player_login_info.login_time AS last_login_time,

            account_log.last_charge_game, account_log.last_charge_time, account_log.last_charge_money
        FROM
            player
                LEFT JOIN
            game ON game.id = player.register_from_game_id
                LEFT JOIN
            customer_service_user ON customer_service_user.id = player.locked_by_user_id
                LEFT JOIN
            (SELECT
                player_bind_info.contract_time,
                    contract_result.result,
                    player_bind_info.id
            FROM
                player_bind_info
            INNER JOIN contract_result ON contract_result.id = player_bind_info.contract_result_id) AS player_bind_info ON player_bind_info.id = player.last_contact_id
                LEFT JOIN
            (SELECT
                player_login_info.id,
                    player_login_info.login_time,
                    game.`name` AS login_game
            FROM
                player_login_info
            INNER JOIN game ON game.id = player_login_info.game_id) AS player_login_info ON player_login_info.id = player.last_login_info_id
                LEFT JOIN
            (SELECT
                account_log.id,
                    account_log.money AS last_charge_money,
                    account_log.charge_time AS last_charge_time,
                    game.`name` AS last_charge_game
            FROM
                account_log
            INNER JOIN game ON game.id = account_log.game_id) AS account_log ON account_log.id = player.last_account_log_id
            WHERE player.is_deleted = %s
        """

        player_count_query = Player.objects.filter(is_deleted=is_deleted)
        params = [is_deleted]
        if user.role_id != settings.ADMIN_ROLE:
            # 非管理员只能查看自己锁定的玩家
            player_query_sql += "AND player.locked_by_user_id = %s"
            params.append(user.id)
            player_count_query = player_count_query.filter(locked_by_user_id=user.id)

        player_count = player_count_query.count()

        search_sql, order_by_sql, limit_sql = PlayerManager._structure_pagination(pagination)

        player_query_sql += search_sql
        player_query_sql += order_by_sql

        with connection.cursor() as cursor:
            count_sql = "SELECT COUNT(id) AS counter FROM ({tmp_table}) AS player_summary".format(
                tmp_table=player_query_sql
            )
            cursor.execute(count_sql, params)
            qry_set = namedtuplefetchall(cursor)
            player_filtered_count = qry_set[0].counter

        player_query_sql += limit_sql

        with connection.cursor() as cursor:
            cursor.execute(player_query_sql, params)
            player_qry_set = namedtuplefetchall(cursor)

        def _strftime(d):
            return d.strftime('%Y-%m-%d %H:%M:%S') if d else '--'

        player_info = [
            {
                'id': _player.id,
                'account': _player.account,
                'username': _player.username or '--',
                'mobile': _player.mobile or '--',
                'charge_count': _player.charge_count or 0, 'charge_money_total': _player.charge_money_total or 0,
                'qq': _player.qq or '--', 'register_from_game': _player.register_from_game or '--',
                'register_time': _strftime(_player.register_time),
                'loginname': _player.loginname, 'come_from': _player.come_from or '--',
                'last_login_game': _player.last_login_game, 'last_login_time': _strftime(_player.last_login_time),
                'last_charge_game': _player.last_charge_game or '--', 'last_charge_money': _player.last_charge_money or 0,
                'last_charge_time': _strftime(_player.last_charge_time),
                'result': _player.result
            } for _player in player_qry_set
        ]
        draw_info = {
            'draw': int(pagination.draw),
            'recordsTotal': player_count,
            'recordsFiltered': player_filtered_count,
            'data': player_info
        }
        return draw_info

    @staticmethod
    def index2(user, is_deleted=0, order_columns=None):
        sql = """
        SELECT
            player.id, player.account, player.username, player.mobile,
            player.qq, player.locked, player.come_from, player.charge_count, player.charge_money_total,
            customer_service_user.loginname, customer_service_user.first_name, customer_service_user.last_name
        FROM player
            LEFT JOIN
            customer_service_user ON customer_service_user.id = player.locked_by_user_id
        WHERE player.is_deleted = %s
        """
        params = [is_deleted]
        if user.role_id != settings.ADMIN_ROLE:
            # 非管理员只能查看自己锁定的玩家
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
            'js/player.js', 'vendor/jqPaginator.min.js',
            'vendor/datatables/js/dataTables.buttons.min.js',
            'vendor/xlsx/xlsx.full.min.js',
            'vendor/xlsx/Blob.js', 'vendor/xlsx/FileSaver.js',
            'vendor/xlsx/swfobject.js', 'vendor/xlsx/downloadify.min.js', 'vendor/xlsx/base64.min.js',
            'js/export.js', 'js/table.js'
        ])

        table_buttons = []
        if user.role_id in (settings.ADMIN_ROLE, settings.DATA_ROLE):
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
                    'text': u'选择当前页', 'class': 'btn-sm btn-info',
                    'click': "select_current_all(false, '_player-table');"
                },
                {
                    'text': u'反选当前页', 'class': 'btn-sm btn-info',
                    'click': "select_current_all(true, '_player-table');"
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
                'extensions': {'select': True},
                'buttons': table_buttons,
                'headers': [
                    {'text': u'账号'}, {'text': u'姓名'}, {'text': u'手机号'},
                    {'text': u'QQ号码'}, {'text': u'注册游戏'}, {'text': u'注册时间'},
                    {'text': u'所属客服'}, {'text': u'渠道'}, {'text': u'最近登录游戏'}, {'text': u'登录时间'},
                    {'text': u'充值<br>次数'}, {'text': u'充值总额'},
                    {'text': u'最近充值游戏'}, {'text': u'最近<br>充值<br>金额'}, {'text': u'最近充值时间'}, {'text': u'联系结果'},
                    {'text': u'操作'}
                ],
                'tbody': tbody,
                'top_form': PlayerManager._generate_top_form(user),
                # 'paginate': {
                #     'current': 1,
                #     'total': 20,
                #     'start': 1, 'end': 10,
                #     'total_pages': 20,
                #
                # }
            },
            'modal': {
                "id": "_player_delete_modal"
            }
        }

        return context

    @staticmethod
    def index(user, is_deleted=0, order_columns=None):
        columns = [
            {'name': 'id', 'serial': 1, 'attrs': {'visible': 'false'}},
            {'name': 'account', 'serial': 2},
            {'name': 'username', 'serial': 3},
            {'name': 'mobile', 'serial': 4},
            {'name': 'qq', 'serial': 5},
            {'name': 'register_from_game', 'serial': 6},
            {'name': 'register_time', 'serial': 7},
            {'name': 'loginname', 'serial': 8},
            {'name': 'come_from', 'serial': 9},
            {'name': 'last_login_game', 'serial': 10},
            {'name': 'last_login_time', 'serial': 11},
            {'name': 'charge_count', 'serial': 12},
            {'name': 'charge_money_total', 'serial': 13},
            {'name': 'last_charge_game', 'serial': 14},
            {'name': 'last_charge_money', 'serial': 15},
            {'name': 'last_charge_time', 'serial': 16},
            {'name': 'result', 'serial': 17},
            {'name': 'action', 'serial': 18,
             'render': PlayerManager._render_action_html(user, is_deleted)
             }
        ]

        media = Media(js=[
            'js/player.js', 'vendor/jqPaginator.min.js',
            'vendor/datatables/js/dataTables.buttons.min.js',
            'vendor/xlsx/xlsx.full.min.js',
            'vendor/xlsx/Blob.js', 'vendor/xlsx/FileSaver.js',
            'vendor/xlsx/swfobject.js', 'vendor/xlsx/downloadify.min.js', 'vendor/xlsx/base64.min.js',
            'js/export.js', 'js/player_table.js'
        ])

        extra_media = Media(js=['js/table.js'])

        table_buttons = []
        if user.role_id in (settings.ADMIN_ROLE, settings.DATA_ROLE):
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
                    'text': u'选择当前页', 'class': 'btn-sm btn-info',
                    'click': "select_current_all(false, '_player-table');"
                },
                {
                    'text': u'反选当前页', 'class': 'btn-sm btn-info',
                    'click': "select_current_all(true, '_player-table');"
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
                'js': media.render_js(),
                'extra_js': extra_media.render_js()
            },
            'add_url': reverse('add_player'),
            'add_url_label': u'登记玩家信息',
            'table': {
                'id': '_player-table',
                'extensions': {'select': True},
                'buttons': table_buttons,
                'headers': [
                    {'text': u'账号'}, {'text': u'姓名'}, {'text': u'手机号'},
                    {'text': u'QQ号码'}, {'text': u'注册游戏'}, {'text': u'注册时间'},
                    {'text': u'所属客服'}, {'text': u'渠道'}, {'text': u'最近登录游戏'}, {'text': u'登录时间'},
                    {'text': u'充值<br>次数'}, {'text': u'充值总额'},
                    {'text': u'最近充值游戏'}, {'text': u'最近<br>充值<br>金额'}, {'text': u'最近充值时间'}, {'text': u'联系结果'},
                    {'text': u'操作'}
                ],
                'render_attributes': {
                    'processing': 'true',
                    'serverSide': 'true'
                },
                'ajax': """$.fn.dataTable.pipeline( {
                    url: '%s',
                    pages: 5
                } )""" % reverse('ajax_player_index') if not is_deleted else reverse('ajax_player_recycle_index'),
                'columns': columns,
                'top_form': PlayerManager._generate_top_form(user),
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
        service_objs = User.objects.all()
        service_options = [
            {
                "value": service.id,
                "label": service.loginname
            } for service in service_objs
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
                        "id": "_qq"
                    },
                    {
                        "type": "group",
                        "attrs": {"id": "game_from_id"},
                        "group_css": "register-game-none",
                        "group": [
                            {
                                "type": "select",
                                "label": u'注册游戏',
                                'name': 'game_from_id',
                                'id': '_game_from_id',
                                'options': game_options,
                                "group_css": "col-lg-6"
                            },
                            {
                                "type": "text",
                                "label": u'注册时间',
                                "name": "game_from_time",
                                "id": "_game_from_time_id",
                                "group_css": "col-lg-6"
                            }
                        ]
                    },
                    {
                        "type": "select",
                        "label": u'所属客服',
                        "name": "service",
                        "id": "_service_id",
                        "options": service_options,
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
                                "label": u'其他游戏',
                                'name': 'game_id',
                                'id': '_game_id',
                                'options': game_options,
                                "group_css": "col-lg-4"
                            },
                            {
                                "type": "text",
                                "label": u'关联时间',
                                "name": "game_time",
                                "id": "_game_id",
                                "group_css": "col-lg-4"
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
                    },
                    {
                        "type": "group_button",
                        "attrs": {'id': 'add_game_button_id'},
                        "button_type": "button",
                        "group_css": "bottom-border",
                        "extra_class": "btn-outline btn-sm btn-warning btn-block",
                        "label": u"新&nbsp;增&nbsp;关&nbsp;联&nbsp;游&nbsp;戏",
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
        service_objs = User.objects.all()

        service_options = [
            {
                "value": service.id,
                "label": service.loginname,
                "selected": service.id == player_obj.locked_by_user_id

            } for service in service_objs
        ]

        register_game_options = [
            {
                "value": _game.id,
                "label": _game.name,
                "selected": _game.id == player_obj.register_from_game_id
            } for _game in game_objs
        ]

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
                        "label": u'其他游戏',
                        'name': 'game_id' + ('%s' % str(ind-1) if ind > 0 else ''),
                        'id': '_game_id' + ('%s' % str(ind-1) if ind > 0 else ''),
                        'options': game_options['game_options'],
                        "group_css": "col-lg-4"
                    },
                    {
                        "type": "text",
                        "label": u'关联时间',
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
                        "value": player_obj.username or ''
                    },
                    {
                        "type": "text",
                        "label": u"联系方式",
                        "name": "mobile",
                        "id": "_mobile",
                        "value": player_obj.mobile or ''
                    },
                    {
                        "type": "text",
                        "label": u"QQ号码",
                        "name": "qq",
                        "id": "_qq",
                        "value": player_obj.qq or ''
                    },
                    {
                        "type": "group",
                        "attrs": {"id": "game_from_id"},
                        "group_css": "register-game-none",
                        "group": [
                            {
                                "type": "select",
                                "label": u'注册游戏',
                                'name': 'game_from_id',
                                'id': '_game_from_id',
                                'options': register_game_options,
                                "group_css": "col-lg-6"
                            },
                            {
                                "type": "text",
                                "label": u'注册时间',
                                "value": player_obj.register_from_game_time.strftime('%Y-%m-%d %H:%M:%S') if player_obj.register_from_game_time else '',
                                "name": "game_from_time",
                                "id": "_game_from_time_id",
                                "group_css": "col-lg-6"
                            }
                        ]
                    },
                    {
                        "type": "select",
                        "label": u'所属客服',
                        "name": "service",
                        "id": "_service_id",
                        "options": service_options,
                        "group_css": "previous-border"
                    },
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
    def _no_contact_player():
        media = Media(
            js=['common/selector2/js/select2.full.js', 'js/form.js', 'js/player.js', 'js/contact.js'],
            css={'all': ['common/selector2/css/select2.min.css', 'css/player.css']}
        )

        context = {
            'media': {
                'js': media.render_js(),
                'css': media.render_css()
            },
            'alert': {'class': 'alert-warning', 'content': u'<i class="fa fa-warning"></i> 暂无可联系客服，请等候管理员添加新的玩家！'}
        }

        return context

    @staticmethod
    def _has_seen_player_today(player_id, user_id):
        """
        判断user 是否查看过当前该玩家（id=player_id)
        :param player_id:
        :param user_id:
        :return:
        """
        player_bind_info_qry_sql = """
            SELECT
                count(player_bind_info.id) AS counter
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

        with connection.cursor() as cursor:
            cursor.execute(player_bind_info_qry_sql, (
                user_id, player_id, settings.PROCESS['looked'], datetime.now().strftime('%Y-%m-%d')
            ))
            bind_info = namedtuplefetchall(cursor)[0]

        return bind_info.counter > 0

    @staticmethod
    def _current_contact_player(player_id, user_id):
        """
        返回 user(id=user_id) 当前的联系玩家
        :param user_id:
        :return:
        """
        if player_id is None:
            player = Player.objects.filter(current_contact_user_id=user_id).first()
            if player:
                player_id = player.id

        player_query_sql = """
        SELECT
            player.id, player.account, player.username, player.mobile, player.qq, player.locked,
            player.come_from, player.charge_count, player.charge_money_total, player.locked_by_user_id,
            game.`name` AS register_from_game, player.register_from_game_time,
            customer_service_user.loginname, customer_service_user.first_name, customer_service_user.last_name,
            player_bind_info.result_id, player_bind_info.result, player_bind_info.contract_time AS contact_time,
            player_login_info.login_game_id, player_login_info.login_game, player_login_info.login_time,
            account_log.last_charge_game, account_log.last_charge_time, account_log.last_charge_money
        FROM
            player
                LEFT JOIN
            game ON game.id = player.register_from_game_id
                LEFT JOIN
            customer_service_user ON customer_service_user.id = player.locked_by_user_id
                LEFT JOIN
            (SELECT
                player_bind_info.contract_time,
                    contract_result.id AS result_id,
                    contract_result.result,
                    player_bind_info.id
            FROM
                player_bind_info
            INNER JOIN contract_result ON contract_result.id = player_bind_info.contract_result_id) AS player_bind_info ON player_bind_info.id = player.last_contact_id
                LEFT JOIN
            (SELECT
                player_login_info.id,
                    player_login_info.login_time,
                    game.id AS login_game_id,
                    game.`name` AS login_game
            FROM
                player_login_info
            INNER JOIN game ON game.id = player_login_info.game_id) AS player_login_info ON player_login_info.id = player.last_login_info_id
                LEFT JOIN
            (SELECT
                account_log.id,
                    account_log.money AS last_charge_money,
                    account_log.charge_time AS last_charge_time,
                    game.`name` AS last_charge_game
            FROM
                account_log
            INNER JOIN game ON game.id = account_log.game_id) AS account_log ON account_log.id = player.last_account_log_id
        """

        query_params = []
        if player_id is not None:
            player_query_sql += """
            WHERE player.id = %s
            """
            query_params.append(player_id)
        else:
            player_query_sql += """
            WHERE
                player.locked = 0
                    AND player.locked_by_user_id IS NULL
                    AND player.is_deleted = 0
                    AND current_contact_user_id IS NULL
            ORDER BY player.timestamp , player.id ASC
            LIMIT 1
            """

        with connection.cursor() as cursor:
            cursor.execute(player_query_sql, query_params)
            player_set = namedtuplefetchall(cursor)
            player = None if len(player_set) == 0 else player_set[0]

        return player

    @staticmethod
    def _register_game_info(player_set, return_type='namedtuple'):
        # 查询玩家的注册游戏信息，最近的充值信息
        player_id_place_holder = ", ".join(['%s'] * len(player_set))

        account_sql = """
            SELECT
                game.name AS game_name, register_info.register_time,
                account.money, account.charge_time,
                player.account
            FROM
                player
                    LEFT JOIN
                register_info ON player.id = register_info.player_id
                    LEFT JOIN
                game ON register_info.game_id = game.id
                    LEFT JOIN
                (
                    SELECT
                        player_id, game_id, money, charge_time
                    FROM account_log
                    WHERE id IN ( SELECT MAX(id) FROM account_log GROUP BY player_id, game_id )
                ) AS account ON account.player_id = register_info.player_id AND account.game_id = register_info.game_id

            WHERE player.id IN ({place_holder})
        """.format(place_holder=player_id_place_holder)

        player_id_list = [_p.id for _p in player_set]

        with connection.cursor() as cursor:
            cursor.execute(account_sql, player_id_list)
            account_info = namedtuplefetchall(cursor)

        if return_type == "namedtuple":
            return account_info
        else:
            account_dict_list = [
                {
                    'game_name': account.game_name,
                    'register_time': account.register_time,
                    'money': account.money,
                    'charge_time': account.charge_time,
                    'account': account.account
                } for account in account_info
            ]
            return account_dict_list

    @staticmethod
    def contract_display(player_id, user):
        player = PlayerManager._current_contact_player(player_id, user.id)

        if player_id is not None and user.role_id != settings.ADMIN_ROLE:
            if player.locked_by_user_id is not None and player.locked_by_user_id != user.id:
                raise PermissionError(u'您没有权限查看该玩家的信息！')

        if not player:
            return PlayerManager._no_contact_player()

        # 如果用户的手机号不为空，那么将相同手机号的所有玩家都绑定
        # modify at 2017-10-30 15:29
        if player.mobile:
            Player.objects.filter(mobile=player.mobile).update(
                current_contact_user=user, timestamp=datetime.now()
            )
            player_set = Player.objects.filter(mobile=player.mobile)
        else:
            Player.objects.filter(id=player.id).update(current_contact_user=user, timestamp=datetime.now())
            player_set = [player]

        has_seen = PlayerManager._has_seen_player_today(player_id, user.id)
        if not has_seen:
            looked_object = ContractResult.objects.filter(process=settings.PROCESS['looked']).first()
            if looked_object:
                for _player in player_set:
                    player_bind_info = PlayerBindInfo(
                        user=user, player_id=_player.id,
                        is_bound=False, contract_time=datetime.now(),
                        contract_result=looked_object, in_effect=True
                    )
                    set_operator(player_bind_info, user)
                    player_bind_info.save()

        # 查询玩家的注册游戏信息，最近的充值信息
        account_info = PlayerManager._register_game_info(player_set)

        # 查询所有游戏
        game_set = Game.objects.all()

        game_options = [
            {
                "label": _game.name, "value": _game.id, "selected": _game.id == player.login_game_id
            } for _game in game_set
        ]

        # 查询玩家的备注信息
        note_info_set = PlayerBindInfo.objects.filter(Q(player_id=player.id),
                                                      Q(note__isnull=False), ~Q(note='')
                                                      ).order_by('-contract_time')
        note_info = [
            "% 2d. [时间：%s] 备注：%s" % (
                ind, _note.contract_time.strftime('%Y-%m-%d %H:%M:%S'), _note.note
            ) for ind, _note in enumerate(note_info_set, start=1)
        ]

        contact_result = ContractResult.objects.filter(~Q(process=settings.PROCESS['looked']))
        status_info = [
            {
                "value": result.id,
                "label": result.result,
                "selected": result.id == player.result_id
            } for result in contact_result
        ]

        media = Media(
            js=['common/selector2/js/select2.full.js', 'js/form.js', 'js/player.js', 'js/contact.js'],
            css={'all': ['common/selector2/css/select2.min.css', 'css/player.css']}
        )

        tbody = [
            {
                'columns': [
                    {'text': 1, 'style': 'display: none;'},
                    {'text': account_log.account},
                    {'text': account_log.game_name or '--'},
                    {'text': account_log.register_time.strftime('%Y-%m-%d %H:%M:%S')
                        if account_log.register_time else '--'},
                    {'text': account_log.money or 0},
                    {'text': account_log.charge_time.strftime('%Y-%m-%d %H:%M:%S')
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
            'player': player,
            'game_options': game_options,
            'note_info': "<br>".join(note_info),
            'media': {
                'js': media.render_js(),
                'css': media.render_css()
            },
            'table': {
                'id': '_player-table',
                'headers': [
                    {'text': u'玩家账号'}, {'text': u'注册游戏'}, {'text': u'注册时间'}, {'text': u'最近充值金额（元）'},
                    {'text': u'充值时间'}
                ],
                'tbody': tbody,
            }
        }

        return context

    @staticmethod
    def update_contact_result(user, player_id, params):
        try:
            player_obj = Player.objects.get(id=player_id)

            if user.role_id != settings.ADMIN_ROLE and\
                    (player_obj.locked_by_user_id is not None and player_obj.locked_by_user_id != user.id):
                raise PermissionError(u'你没有权限修改该玩家！')

            if player_obj.mobile:
                player_set = Player.objects.filter(mobile=player_obj.mobile)
            else:
                player_set = [player_obj]
        except ObjectDoesNotExist:
            return None

        status = params.get('status')
        # locked_param = params.get('locked', 0)
        # locked = locked_param == '1'
        last_login_game = params.get('last_login_game')
        notes = params.get('notes')
        form_changed = params.get('form_changed') == '1'

        update_fields = updated_fields(player_obj, params, ['username', 'qq', 'mobile'])

        current_time = datetime.now()
        status_obj = None
        if status:
            try:
                status_obj = ContractResult.objects.get(id=status)
            except ObjectDoesNotExist:
                pass

        looked_bind_info = ContractResult.objects.filter(process=settings.PROCESS['looked']).first()

        current_bind_info_sql = """
        SELECT * FROM player_bind_info WHERE id = (SELECT MAX(id) FROM player_bind_info WHERE player_id=%s {other_cond})
        """

        if looked_bind_info:
            _cond = "AND contract_result_id != %d" % looked_bind_info.id
            current_bind_info_sql = current_bind_info_sql.format(other_cond=_cond)
        else:
            current_bind_info_sql = current_bind_info_sql.format(other_cond="")

        for player in player_set:
            tmp_update_fields = update_fields
            for changed_field in update_fields:
                setattr(player, changed_field, params.get(changed_field))
            set_operator(player, user)

            if form_changed and not player.locked:
                tmp_update_fields.extend(['locked', 'locked_by_user_id', 'locked_time'])
                player.locked = True
                player.locked_by_user = user
                player.locked_time = current_time.strftime('%Y-%m-%d %H:%M:%S')

            if last_login_game:
                PlayerLoginInfo.objects.create(
                    player_id=player.id, game_id=last_login_game
                )

            if status_obj:
                current_bind_info = None
                if notes.strip() == "":
                    with connection.cursor() as cursor:
                        cursor.execute(current_bind_info_sql, (player.id, ))
                        current_bind_info_set = namedtuplefetchall(cursor)
                        if len(current_bind_info_set) > 0:
                            current_bind_info = current_bind_info_set[0]

                if notes.strip() != "" or \
                        (current_bind_info is None or current_bind_info.contract_result_id != status_obj.id):
                    bind_info = PlayerBindInfo(
                        user=user, player=player, is_bound=status_obj.bind,
                        contract_time=datetime.now(), contract_result=status_obj,
                        in_effect=True, note=notes
                    )
                    set_operator(bind_info, user)
                    bind_info.save()

                    tmp_update_fields.append('last_contact_id')
                    player.last_contact_id = bind_info.id

            player.save(update_fields=tmp_update_fields)

        return player_set

    @staticmethod
    def update(user, player_id, params):
        try:
            player_obj = Player.objects.get(id=player_id)
        except ObjectDoesNotExist:
            return None

        account = params.get('account')
        player_name = params.get("username")
        player_mobile = params.get('mobile', '')
        player_qq = params.get('qq', '')
        service = params.get('service')
        game_from = params.get('game_from_id')
        game_from_time = params.get('game_from_time', None)

        update_fields = updated_fields(
            player_obj, params, ['account', 'username', 'mobile', 'qq'],
            key_map={'register_from_game_id': 'game_from_id', 'register_from_game_time': 'game_from_time',
                     'locked_by_user_id': 'service'}
        )

        game_field_info = {}
        game_field_reg = re.compile(r'^game_id([0-9]*)')
        for field_name, field_value in params.items():
            m = game_field_reg.match(field_name)
            if m is not None:
                if not field_value:
                    continue
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

        player_obj.account = account
        player_obj.username = player_name
        player_obj.mobile = player_mobile
        player_obj.qq = player_qq
        player_obj.register_from_game_id = game_from
        player_obj.register_from_game_time = game_from_time
        player_obj.locked_by_user_id = service
        locked = 0 if service is None else 1
        locked_changed = player_obj.locked != locked
        if locked_changed:
            player_obj.locked = locked
            update_fields.append('locked')
        set_operator(player_obj, user)
        player_obj.save(update_fields=update_fields)

        register_game_objs = RegisterInfo.objects.filter(player_id=player_id)

        registered_game_ids = ['%d' % register_game_obj.game_id for register_game_obj in register_game_objs]

        registered_game_dict = dict([
            ('%d' % _g.game_id, _g.register_time) for _g in register_game_objs
        ])

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
    def delete(user, player_id, force_delete=False, really_delete=False):
        if isinstance(player_id, (list, tuple)):
            if not really_delete:
                Player.objects.filter(id__in=player_id).update(is_deleted=True)
            else:
                Player.objects.filter(id__in=player_id).delete()
            return True
        else:
            try:
                player_obj = Player.objects.get(id=player_id)
                if not really_delete:
                    player_obj.is_deleted = True
                    set_operator(player_obj, user)
                    player_obj.save()
                else:
                    player_obj.delete()
            except ObjectDoesNotExist:
                pass

            return True

    @staticmethod
    def save(user, params):
        account = params.get('account')
        player_name = params.get("username")
        player_mobile = params.get('mobile', '')
        player_qq = params.get('qq', '')
        service = params.get('service')
        game_from = params.get('game_from_id')
        game_from_time = params.get('game_from_time')

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

        player_obj = Player(
            account=account,
            username=player_name,
            mobile=player_mobile,
            qq=player_qq,
            register_from_game_id=game_from,
            register_from_game_time=game_from_time
        )
        if service:
            player_obj.locked = True
            player_obj.locked_by_user_id = service
        # set_operator(player_obj, user)
        player_obj.save()

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
            charge_money = player_data[title_index[u'最近充值金额']].value if u'最近充值金额' in title_index else 0
            charge_time = player_data[title_index[u'最近充值时间']].value if u'最近充值时间' in title_index else None
            last_login_game = player_data[title_index[u'最近登录游戏']].value if u'最近登录游戏' in title_index else None
            last_login_time = player_data[title_index[u'最近登陆时间']].value if u'最近登陆时间' in title_index else None
            register_name = player_data[title_index[u'注册游戏']].value if u'注册游戏' in title_index else None
            register_time = player_data[title_index[u'注册时间']].value if u'注册时间' in title_index else None
            game_count = player_data[title_index[u'游戏数量']].value if u'游戏数量' in title_index else None
            charge_count = player_data[title_index[u'充值次数']].value if u'充值次数' in title_index else None
            charge_money_total = player_data[title_index[u'充值总额']].value if u'充值总额' in title_index else None

            try:
                update_fields = None
                try:
                    player_obj = Player.objects.get(account=account)
                    update_fields = updated_fields(player_obj, {
                        'mobile': mobile, 'come_from': come_from, 'imported_from': player_import.id,
                        'charge_money_total': charge_money_total, 'game_count': game_count,
                        'register_from_game_time': register_time, 'charge_count': charge_count or 0,
                    }, ['mobile', 'come_from', 'charge_money_total', 'game_count', 'imported_from',
                        'register_from_game_time'])
                    player_obj.mobile = mobile
                    player_obj.come_from = come_from
                    player_obj.imported_from = player_import.id
                    player_obj.charge_money_total = charge_money_total
                    player_obj.charge_count = charge_count or 0
                    player_obj.game_count = game_count
                    player_obj.register_from_game_time = register_time
                except ObjectDoesNotExist:
                    player_obj = Player(
                        account=account,
                        mobile=mobile, charge_count=charge_count or 0,
                        come_from=come_from, register_from_game_time=register_time,
                        imported_from=player_import.id, game_count=game_count, charge_money_total=charge_money_total
                    )
                set_operator(player_obj, user)
                player_obj.save(update_fields=update_fields)

                if register_name.strip() != '':
                    try:
                        game_obj = Game.objects.get(name=register_name)
                    except ObjectDoesNotExist:
                        game_obj = Game.objects.create(name=register_name)

                    player_obj.register_from_game_id = game_obj.id

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

                last_login_game_obj = None
                if last_login_game.strip() != '':
                    try:
                        last_login_game_obj = Game.objects.get(name=last_login_game)
                    except ObjectDoesNotExist:
                        last_login_game_obj = Game.objects.create(name=last_login_game)

                    player_login_info = PlayerLoginInfo.objects.create(
                        player=player_obj,
                        game=last_login_game_obj,
                        login_time=last_login_time
                    )
                    player_obj.last_login_info_id = player_login_info.id

                account_log = AccountLog.objects.create(
                    player=player_obj,
                    game=last_login_game_obj,
                    money=charge_money,
                    charge_time=charge_time,
                    recorder=user
                )

                player_obj.last_account_log_id = account_log.id
                player_obj.save()
            except ValueError as err:
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
