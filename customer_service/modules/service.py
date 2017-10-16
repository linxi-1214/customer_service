from collections import namedtuple
from datetime import datetime, timedelta

from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist

from django.forms.widgets import Media

from django.conf import settings
from django.db import connection

from customer_service.models import (
    PlayerBindInfo, User
)


def namedtuplefetchall(cursor):
    """Return all rows from a cursor as a namedtuple"""
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]


class ServiceManager:

    @staticmethod
    def index_display():
        user_objs = User.objects.all()
        media = Media(js=['common/selector2/js/select2.full.js',
                          'vendor/jqplot/jquery.jqplot.min.js',
                          'js/customer_service.js'],
                      css={'all': ['common/selector2/css/select2.min.css',
                                   'vendor/jqplot/jquery.jqplot.min.css'
                                   ]})
        options = [
            {
                "label": "%s%s" % (user_obj.first_name or '', user_obj.last_name or '') or user_obj.loginname,
                "value": user_obj.id
            } for user_obj in user_objs
        ]

        context = {
            'breadcrumb_items': [
                {
                    'href': '#',
                    'active': True,
                    'label': u'客服工作报告'
                }
            ],
            'media': {
                'js': media.render_js(),
                "css": media.render_css()
            },
            "form": {
                "method": "post",
                "action": "#",
                "fields": [
                    {
                        "type": "select",
                        "label": u"玩家账号",
                        "name": "account",
                        "id": "_account",
                        'options': options,
                    },
                    {
                        "type": "group",
                        "attrs": {
                            "id": "register_game_info_id"
                        },
                        "group_css": "register-game-none",
                        "group": [
                            {
                                "type": "text",
                                "label": u"时间范围",
                                "name": "time-range",
                                "id": "_time-range",
                                "group_css": "col-lg-4"
                            },
                            {
                                "type": "group_button",
                                "button_type": "button",
                                "click": '"generate_date(\'week\');"',
                                "icon": "fa-minus-circle",
                                "extra_class": "btn-info form-control delete-icon-button",
                                "label": u'近一周',
                                "tooltip_position": 'right',
                                "group_css": "col-lg-1"
                            },
                            {
                                "type": "group_button",
                                "button_type": "button",
                                "click": '"generate_date(\'one month\');"',
                                "extra_class": "btn-info form-control delete-icon-button",
                                "label": u'近一月',
                                "tooltip_position": 'right',
                                "group_css": "col-lg-1"
                            },
                            {
                                "type": "group_button",
                                "button_type": "button",
                                "click": '"generate_date(\'three month\');"',
                                "extra_class": "btn-info form-control delete-icon-button",
                                "label": u'近三月',
                                "tooltip_position": 'right',
                                "group_css": "col-lg-1"
                            }
                        ]
                    },
                    {
                        "type": "button",
                        "label": u'<i class="fa fa-bar-chart-o"></i> 查看报告',
                        "button_type": "button",
                        "click": 'draw_report("%s");' % reverse('user_report')
                    }
                ]
            }
        }

        return context

    @staticmethod
    def report_display(user_id, date_range):
        try:
            User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            return [], [[]]

        if settings.DATABASE_TYPE == "sqlite3":
            query_sql = """
                SELECT
                    count(*) AS counter,
                    strftime('%%Y-%%m-%%d', contract_time) AS contact_date
                FROM player_bind_info
                    INNER JOIN
                    contract_result ON player_bind_info.contract_result_id = contract_result.id
                WHERE contact_date BETWEEN %s AND %s
                    AND user_id = %s
                    AND in_effect = 1
                    AND contract_result.process >= %s
                    {other_condition}
                GROUP BY contact_date
                ORDER BY contact_date ASC
            """
        else:
            query_sql = """"""

        process_order = ['looked', 'contacted', 'connected', 'success']

        ret_data = {}
        start_date, end_date = date_range
        with connection.cursor() as cursor:
            for process in process_order:
                if process == "success":
                    query_sql = query_sql.format(other_condition="AND is_bound=1")
                else:
                    query_sql = query_sql.format(other_condition='')

                print(query_sql)

                cursor.execute(query_sql, (start_date,
                                           end_date,
                                           user_id,
                                           settings.PROCESS[process])
                               )

                query_set = namedtuplefetchall(cursor)

                for contact_info in query_set:
                    if process in ret_data:
                        ret_data[process].update({contact_info.contact_date: contact_info.counter})
                    else:
                        ret_data[process] = {contact_info.contact_date: contact_info.counter}

        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

        ret_data_list = []
        labels = []
        label_collect = False
        for process in process_order:
            current_date = start_date
            print(current_date, end_date)
            while current_date <= end_date:
                if process not in ret_data:
                    ret_data[process] = {}
                time_key = current_date.strftime('%Y-%m-%d')
                if not label_collect:
                    labels.append(time_key)
                if time_key not in ret_data[process]:
                    ret_data[process].update({time_key: 0})

                current_date += timedelta(days=1)
            label_collect = True

            process_data_list = [
                [process_data[0], process_data[1]] for process_data in ret_data[process].items()
            ]
            ret_data_list.append(process_data_list)

        return labels, ret_data_list
