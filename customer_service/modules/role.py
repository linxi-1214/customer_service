from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist

from django.forms.widgets import Media

from customer_service.models import Role


class RoleManager:

    @staticmethod
    def add_display():
        return {
            'breadcrumb_items': [
                {'href': reverse('role_index'), 'label': u'角色列表'},
                {'active': True, 'label': u'新建角色'}
            ],
            "panel_heading": u"新建",
            "form": {
                "method": "post",
                "action": reverse('add_role'),
                "fields": [
                    {
                        "type": "text",
                        "label": u"角色名称",
                        "help_id": "_role_help",
                        "help_text": u"角色名称，唯一",
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
    def edit_display(role_id):
        try:
            role_obj = Role.objects.get(id=role_id)
        except ObjectDoesNotExist:
            return None

        return {
            'breadcrumb_items': [
                {'href': reverse('role_index'), 'label': u'角色列表'},
                {'active': True, 'label': u'修改角色信息'}
            ],
            "panel_heading": u"编辑",
            "form": {
                "method": "post",
                "action": reverse('edit_role', args=(role_obj.id,)),
                "fields": [
                    {
                        "type": "text",
                        "label": u"角色名称",
                        "help_id": "_role_help",
                        "help_text": u"角色名称，唯一",
                        "name": "name",
                        "value": role_obj.name,
                        "id": "_name"
                    },
                    {
                        "type": "text",
                        "label": u"描述信息",
                        "name": "desc",
                        "value": role_obj.desc or '',
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
    def update(role_id, params):
        role_name = params.get('name', '')
        if role_name.strip() == '':
            return None
        role_desc = params.get('desc', '')

        update_rows = Role.objects.filter(id=role_id).update(
            name=role_name, desc=role_desc
        )

        return update_rows

    @staticmethod
    def delete(role_id):
        try:
            role_obj = Role.objects.get(id=role_id)
            role_obj.delete()
        except ObjectDoesNotExist:
            role_obj = None

        return role_obj

    @staticmethod
    def index():
        role_objs = Role.objects.all()
        delete_url = reverse('delete_role')
        media = Media(js=['js/role.js'])
        tbody = [
            {
                'columns': [
                    {'text': role_obj.id, 'style': "display: none"},
                    {'text': role_obj.name},
                    {'text': role_obj.desc}
                ],
                'actions': [
                    {
                        'icon': 'fa-edit',
                        'tooltip': u'编辑',
                        'href': reverse('edit_role', args=(role_obj.id,))
                    },
                    {
                        'href': '#',
                        'icon': 'fa-trash-o',
                        'tooltip': u'删除',
                        'func': 'delete_role("{url}", {id}, "{name}")'.format(
                            url=delete_url, id=role_obj.id, name=role_obj.name
                        )
                    }
                ]
            } for role_obj in role_objs
        ]

        context = {
            'breadcrumb_items': [
                {
                    'href': '#',
                    'active': True,
                    'label': u'角色列表'
                }
            ],
            'media': {
                'js': media.render_js()
            },
            'panel_heading': u'角色列表',
            'add_url': reverse('add_role'),
            'add_url_label': u'添加新的角色',
            'table': {
                'id': '_role-table',
                'headers': [
                    {'text': u'角色名称'}, {'text': u'描述信息'}, {'text': u'操作'}
                ],
                'tbody': tbody,
            },
            'modal': {
                "id": "_role_delete_modal"
            }
        }

        return context

    @staticmethod
    def save(params):
        role_name = params.get("name")
        desc = params.get('desc', '')

        role_obj = Role(name=role_name, desc=desc)
        role_obj.save()

        return role_obj

    @staticmethod
    def role_exists(name):
        role_obj = Role.objects.filter(name=name)

        return role_obj.count() > 0