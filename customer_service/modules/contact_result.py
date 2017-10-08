from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist

from django.forms.widgets import Media

from customer_service.models import ContractResult


class ContactResultManager:

    @staticmethod
    def add_display():
        media = Media(js=['common/selector2/js/select2.js', 'js/result.js'],
                      css={'all': ['common/selector2/css/select2.min.css']})
        return {
            'breadcrumb_items': [
                {'href': reverse('result_index'), 'label': u'联系结果列表'},
                {'active': True, 'label': u'新增联系结果'}
            ],
            "panel_heading": u"联系结果登记",
            "media": {
                'js': media.render_js(),
                'css': media.render_css()
            },
            "form": {
                "method": "post",
                "action": reverse('add_result'),
                "fields": [
                    {
                        "type": "text",
                        "label": u"联系结果描述",
                        "help_id": "_result_help",
                        "help_text": u"联系结果的描述信息，如空号，无人接听等",
                        "name": "result",
                        "id": "_result",
                    },
                    {
                        "type": "checkbox",
                        "checkbox_group": [
                            {
                                "label": u"绑定选项",
                                "name": "bind",
                                "id": "_bind",
                                "value": "1",
                                "checked": False
                            }
                        ],
                        "help_id": "_bind_help",
                        "help_text": u'勾选该选项，则客服在选择了该联系结果的时候，玩家将绑定到该客服'
                    },
                    {
                        "type": "submit",
                        "button_type": "submit",
                        "label": u"提交"
                    }
                ]
            }
        }

    @staticmethod
    def edit_display(result_id):
        try:
            result_obj = ContractResult.objects.get(id=result_id)
        except ObjectDoesNotExist:
            return None

        media = Media(js=['common/selector2/js/select2.js', 'js/user.js'],
                      css={'all': ['common/selector2/css/select2.min.css']})

        return {
            'breadcrumb_items': [
                {'href': reverse('result_index'), 'label': u'联系结果列表'},
                {'active': True, 'label': u'修改联系结果信息'}
            ],
            "panel_heading": u"编辑联系结果信息",
            "media": {
                'js': media.render_js(),
                'css': media.render_css()
            },
            "form": {
                "method": "post",
                "action": reverse('edit_result', args=(result_obj.id,)),
                "fields": [
                    {
                        "type": "text",
                        "label": u"联系结果描述",
                        "help_id": "_result_help",
                        "help_text": u"联系结果的描述信息，如空号，无人接听等",
                        "name": "result",
                        "id": "_result",
                        "value": result_obj.result or ''
                    },
                    {
                        "type": "checkbox",
                        "checkbox_group": [
                            {
                                "label": u"绑定选项",
                                "name": "bind",
                                "id": "_bind",
                                "value": "1",
                                "checked": result_obj.bind
                            }
                        ],
                        "help_id": "_bind_help",
                        "help_text": u'勾选该选项，则客服在选择了该联系结果的时候，玩家将绑定到该客服'
                    },
                    {
                        "type": "button",
                        "button_type": "button",
                        "label": u"取消"
                    },
                    {
                        "type": "button",
                        "button_type": "submit",
                        "label": u"提交"
                    }
                ]
            }
        }

    @staticmethod
    def update(result_id, params):
        result = params.get("result")
        bind_text = params.get('bind', 0)
        bind = int(bind_text) == 1

        try:
            ContractResult.objects.get(id=result_id)
        except ObjectDoesNotExist:
            return 0

        ContractResult.objects.filter(id=result_id).update(
            result=result, bind=bind
        )

        return 1

    @staticmethod
    def delete(result_id):
        try:
            result_obj = ContractResult.objects.get(id=result_id)
            result_obj.delete()
        except ObjectDoesNotExist:
            result_obj = None

        return result_obj

    @staticmethod
    def index():
        result_objs = ContractResult.objects.all()
        delete_url = reverse('delete_result')
        media = Media(js=['js/result.js'])
        tbody = [
            {
                'columns': [
                    {'text': result_obj.id, 'style': "display: none"},
                    {'text': result_obj.result},
                    {'text': '<button type="button" class="btn btn-success btn-circle">'
                             '<i class="fa fa-check"></i></button>' if result_obj.bind else
                             '<button type="button" class="btn btn-warning btn-circle">'
                             '<i class="fa fa-times"></i></button>'
                    }
                ],
                'actions': [
                    {
                        'icon': 'fa-edit',
                        'tooltip': u'编辑',
                        'href': reverse('edit_result', args=(result_obj.id,))
                    },
                    {
                        'href': '#',
                        'icon': 'fa-trash-o',
                        'tooltip': u'删除',
                        'func': 'delete_user("{url}", {id}, "{label}")'.format(
                            url=delete_url, id=result_obj.id, label=result_obj.result
                        )
                    }
                ]
            } for result_obj in result_objs
        ]

        context = {
            'breadcrumb_items': [
                {
                    'href': '#',
                    'active': True,
                    'label': u'联系结果'
                }
            ],
            'panel_heading': u'联系结果信息',
            'media': {
                'js': media.render_js()
            },
            'add_url': reverse('add_result'),
            'add_url_label': u'新增联系结果',
            'table': {
                'id': '_result-table',
                'headers': [
                    {'text': u'联系结果'}, {'text': u'绑定项'}, {'text': u'操作'}
                ],
                'tbody': tbody,
            },
            'modal': {
                "id": "_result_delete_modal"
            }
        }

        return context

    @staticmethod
    def save(params):
        result = params.get("result")
        bind_text = params.get('bind', 0)
        bind = int(bind_text) == 1

        result_obj = ContractResult(result=result, bind=bind)

        result_obj.save()

        return result_obj
