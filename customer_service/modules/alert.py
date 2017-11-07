import os

from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist

from django.forms.widgets import Media

from customer_service.models import Alert


class AlertManager:

    @staticmethod
    def all(user):
        alerts = Alert.objects.filter(receiver_id=user.id, marked=False).order_by('update_time')
        alert_json = [
            {
                'id': alert.id,
                'href': alert.href,
                'content': alert.content,
                'time': alert.update_time.strftime('%Y-%m-%d %H:%M:%S') if alert.update_time else ''
            } for alert in alerts
        ]

        return alert_json

    @staticmethod
    def has_red(alert_id):
        if not isinstance(alert_id, (list, tuple)):
            alert_id = [alert_id]
        Alert.objects.filter(id__in=alert_id).update(marked=True)
        return True

    @staticmethod
    def _ajax_query_all(user):
        alerts = Alert.objects.filter(receiver_id=user.id).order_by('marked', '-update_time')

        alert_json = [
            {
                "DT_RowId": "row_%d" % _alert.id,
                "id": _alert.id,
                "content": _alert.content,
                "sender": _alert.sender.loginname,
                "marked": _alert.marked,
                "href": _alert.href,
                "update_time": _alert.update_time.strftime('%Y-%m-%d %H:%M:%S') if _alert.update_time else ''
            } for _alert in alerts
        ]

        return {'data': alert_json}

    @staticmethod
    def index():
        media = Media(js=[
            'js/player.js', 'js/table.js', 'js/alert_table.js'
        ])

        table_buttons = [
            {
                'text': u'全 选', 'class': 'btn-sm btn-success',
                'click': "select_all(false, '_alert-table');"
            },
            {
                'text': u'反 选', 'class': 'btn-sm btn-success',
                'click': "select_all(true, '_alert-table');"
            },
            {
                'text': u'选择当前页', 'class': 'btn-sm btn-info',
                'click': "select_current_all(false, '_alert-table');"
            },
            {
                'text': u'反选当前页', 'class': 'btn-sm btn-info',
                'click': "select_current_all(true, '_alert-table');"
            },
            {
                'text': u'标为已读', 'class': 'btn-sm btn-primary',
                'click': "marked_alert_selected('%s');" % (reverse('red_alert_multi'))
            }
        ]

        columns = [
            {'name': 'id', 'serial': 1, 'attrs': {'visible': 'false'}},
            {'name': 'content', 'serial': 2},
            {'name': 'sender', 'serial': 3},
            {'name': 'update_time', 'serial': 4},
            {'name': 'marked', 'serial': 5,
             'render': """function (data, type, row, meta) {
                var marked_html = '<i class="fa fa-star-o" style="font-size: 18px;"></i>';
                if (data)
                   marked_html = '<i class="fa fa-star" style="font-size: 18px; color: #337ab7;"></i>';

                return marked_html;
                }"""
             },
            {'name': 'href', 'serial': 6,
             'render': """function(data, type, row, meta) {
                   var action_html = '<div class="tooltip-demo">' +
                       ' <a class="btn btn-social-icon contact btn-sm"' +
                       ' data-toggle="tooltip" data-placement="bottom"' +
                       ' href="#" url="' + data + '" title="查看" action="alert_seen">' +
                       '<i class="fa fa-leaf"></i>' +
                       '</a>' +
                       '<button type="button" action="alert_marked_btn" data-toggle="tooltip" data-placement="bottom"' +
                       ' class="btn btn-primary btn-circle btn-outline" title="标为已读"><i class="fa fa-bookmark"></i>' +
                       ' </button>' +
                       '</div>';
                   return action_html;
               }"""
             }
        ]

        on_init = """
        $("button[action=alert_marked_btn]").click(function () {
            var btn_obj = $(this);
            btn_obj.tooltip('hide');
            var tr = $(this).closest('tr');
            var row = $("#_alert-table")
                .DataTable()
                .row(tr);
            var seen_url = "%s/" + row.data().id + "/";
            $.get(seen_url, function (data, status) {
              if (status == "success") {
                  var tmp_data = row.data();
                  tmp_data.marked = true;
                  row.data(tmp_data).draw();
              }
              $('.tooltip-demo').tooltip({
                selector: "[data-toggle=tooltip]",
                container: "body"
            });
            });

            // return false;
        });
        $("a[action=alert_seen]").click(function () {
            var btn_obj = $(this);
            btn_obj.tooltip('hide');
            var tr = $(this).closest('tr');
            var url = $(this).attr('url');
            var row = $("#_alert-table")
                .DataTable()
                .row(tr);
            var seen_url = "%s/" + row.data().id + "/";
            $.get(seen_url, function (data, status) {
              if (status == "success") {
                  var tmp_data = row.data();
                  tmp_data.marked = true;
                  row.data(tmp_data).draw();
              }
              $('.tooltip-demo').tooltip({
                selector: "[data-toggle=tooltip]",
                container: "body"
            });
            });

            location.href = url;
            return false;
        });
        """ % (os.path.dirname(reverse('red_alert', args=(0,)).rstrip('/')),
               os.path.dirname(reverse('red_alert', args=(0,)).rstrip('/')))

        context = {
            'breadcrumb_items': [
                {
                    'href': '#',
                    'active': True,
                    'label': u'通知信息列表'
                }
            ],
            'panel_heading': u'通知信息列表',
            'media': {
                'js': media.render_js()
            },
            'table': {
                'id': '_alert-table',
                'extensions': {'select': True},
                'buttons': table_buttons,
                'headers': [
                    {'text': u'通知信息'}, {'text': u'通知发送人'}, {'text': u'通知时间'},
                    {'text': u'已读'}, {'text': u'操作'}
                ],
                'ajax': "../ajax-all/",
                'on_init': [on_init],
                "columns": columns
            }
        }

        return context
