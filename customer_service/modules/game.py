from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist

from django.forms.widgets import Media

from customer_service.models import Game


class GameManager:

    @staticmethod
    def add_display():
        return {
            'breadcrumb_items': [
                {'href': reverse('game_index'), 'label': u'游戏列表'},
                {'active': True, 'label': u'添加游戏'}
            ],
            "panel_heading": u"登记游戏",
            "form": {
                "method": "post",
                "action": reverse('add_game'),
                "fields": [
                    {
                        "type": "text",
                        "label": u"游戏名称",
                        "help_id": "_game_help",
                        "help_text": u"游戏名称，唯一",
                        "name": "name",
                        "id": "_name"
                    },
                    {
                        "type": "text",
                        "label": u"描述信息",
                        "name": "desc",
                        "id": "_desc"
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
    def edit_display(game_id):
        try:
            game_obj = Game.objects.get(id=game_id)
        except ObjectDoesNotExist:
            return None

        return {
            'breadcrumb_items': [
                {'href': reverse('game_index'), 'label': u'游戏列表'},
                {'active': True, 'label': u'修改游戏信息'}
            ],
            "panel_heading": u"编辑",
            "form": {
                "method": "post",
                "action": reverse('edit_game', args=(game_obj.id,)),
                "fields": [
                    {
                        "type": "text",
                        "label": u"游戏名称",
                        "help_id": "_game_help",
                        "help_text": u"游戏名称，唯一",
                        "name": "name",
                        "value": game_obj.name,
                        "id": "_name"
                    },
                    {
                        "type": "text",
                        "label": u"描述信息",
                        "name": "desc",
                        "value": game_obj.desc or '',
                        "id": "_desc"
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
    def update(game_id, params):
        game_name = params.get('name', '')
        if game_name.strip() == '':
            return None
        game_desc = params.get('desc', '')

        update_rows = Game.objects.filter(id=game_id).update(
            name=game_name, desc=game_desc
        )

        return update_rows


    @staticmethod
    def delete(game_id):
        try:
            game_obj = Game.objects.get(id=game_id)
            game_obj.deleted = True
            game_obj.save()
        except ObjectDoesNotExist:
            game_obj = None

        return game_obj

    @staticmethod
    def index():
        game_objs = Game.objects.filter(deleted=False)
        delete_url = reverse('delete_game')
        tbody = [
            {
                'columns': [
                    {'text': game_obj.id, 'style': "display: none"},
                    {'text': game_obj.name},
                    {'text': game_obj.desc}
                ],
                'actions': [
                    {
                        'icon': 'fa-edit',
                        'tooltip': u'编辑',
                        'href': reverse('edit_game', args=(game_obj.id,))
                    },
                    {
                        'href': '#',
                        'icon': 'fa-trash-o',
                        'tooltip': u'删除',
                        'func': 'delete_game("{url}", {id}, "{name}")'.format(
                            url=delete_url, id=game_obj.id, name=game_obj.name
                        )
                    }
                ]
            } for game_obj in game_objs
        ]

        context = {
            'breadcrumb_items': [
                {
                    'href': '#',
                    'active': True,
                    'label': u'游戏列表'
                }
            ],
            'panel_heading': u'游戏列表',
            'add_url': reverse('add_game'),
            'add_url_label': u'添加新的游戏项目',
            'table': {
                'id': '_game-table',
                'headers': [
                    {'text': u'游戏名称'}, {'text': u'描述信息'}, {'text': u'操作'}
                ],
                'tbody': tbody,
            },
            'modal': {
                "id": "_game_delete_modal"
            }
        }

        return context

    @staticmethod
    def save(params):
        game_name = params.get("name")
        desc = params.get('desc', '')

        game_obj = Game(name=game_name, desc=desc)
        game_obj.save()

        return game_obj

    @staticmethod
    def game_exists(name):
        game_obj = Game.objects.filter(name=name)

        return game_obj.count() > 0