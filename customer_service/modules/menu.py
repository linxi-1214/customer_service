from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist

from django.forms.widgets import Media

from customer_service.models import Menu, Role, RoleBindMenu

url_name_dict = {
    'result_index': u'联系结果',
    'user_index': u'用户管理',
    'role_index': u'角色管理',
    'game_index': u'游戏管理',
    'player_index': u'我的玩家',
    'import_player': u'导入玩家',
    'contract_player': u'联系玩家',
    'user_report': u'客服报告',
    'player_contact_detail': u'玩家详情',
    'change_password': u'修改密码',
}


class MenuManager:

    @staticmethod
    def menu_list(excludes=[], selected=[]):
        all_menu = Menu.objects.all()

        all_menu_info = [
            {
                "value": menu.id,
                "label": menu.label or menu.name,
                "selected": menu.id in selected
            } for menu in all_menu if menu.id not in excludes
        ]

        return all_menu_info

    @staticmethod
    def add_display():
        role_objs = Role.objects.all()
        role_options = [
            {
                "value": role.id,
                "label": role.desc or role.name
            } for role in role_objs
        ]

        menu_objs = Menu.objects.all()
        menu_list = [_m.name for _m in menu_objs]

        menu_options = [
            {
                "label": label,
                "value": value
            } for value, label in url_name_dict.items() if value not in menu_list
        ]
        menu_options.insert(0, {"label": "#", "value": "#"})

        media = Media(js=['common/selector2/js/select2.js', 'js/menu.js'],
                      css={'all': ['common/selector2/css/select2.min.css']})
        return {
            'breadcrumb_items': [
                {'href': reverse('menu_index'), 'label': u'菜单列表'},
                {'active': True, 'label': u'添加菜单'}
            ],
            "panel_heading": u"登记菜单",
            "media": {
                'js': media.render_js(),
                'css': media.render_css()
            },
            "form": {
                "method": "post",
                "action": reverse('add_menu'),
                "fields": [
                    {
                        "type": "select",
                        "label": u"菜单连接视图",
                        "help_id": "_menu_help",
                        "help_text": u"点击菜单时，跳转的路径名称，如果是父菜单，填写 # ",
                        "name": "name",
                        "id": "_name",
                        "options": menu_options
                    },
                    {
                        "type": "text",
                        "label": u"菜单标签",
                        "help_id": "_menu_label_help",
                        "help_text": u"菜单展示在页面上的文字",
                        "name": "label",
                        "id": "_label"
                    },
                    {
                        "type": "text",
                        "label": u"菜单图标",
                        "name": "icon",
                        "help_id": "_menu_icon_help",
                        "help_text": u"菜单前方显示的图标",
                        "id": "_icon"
                    },
                    {
                        "type": "select",
                        "label": u'上级菜单',
                        'name': 'parent_menu',
                        'help_id': '_menu_parent_help',
                        'help_text': u'指定该菜单的上级菜单，在菜单栏中，该菜单将显示在上级菜单的下边',
                        'id': '_parent_menu',
                        'options': MenuManager.menu_list()
                    },
                    {
                        "type": "multi_select",
                        "label": u'权限绑定',
                        "help_id": "_menu_role_help",
                        "help_text": u"将该菜单功能分配给某个角色，只有该角色的用户可以看到该菜单，可多选",
                        "name": "role",
                        "id": "_role",
                        "options": role_options
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
    def edit_display(menu_id):
        try:
            menu_obj = Menu.objects.get(id=menu_id)
        except ObjectDoesNotExist:
            return None
        role_objs = Role.objects.all()
        relations = RoleBindMenu.objects.filter(menu_id=menu_id)
        selected_role_ids = [relation.role_id for relation in relations]
        role_options = [
            {
                "value": role.id,
                "label": role.desc or role.name,
                "selected": role.id in selected_role_ids
            } for role in role_objs
        ]

        menu_objs = Menu.objects.all()
        menu_list = [_m.name for _m in menu_objs]
        media = Media(js=['common/selector2/js/select2.js', 'js/menu.js'],
                      css={'all': ['common/selector2/css/select2.min.css']})

        menu_options = [
            {
                "label": label,
                "value": value
            } for value, label in url_name_dict.items() if value not in menu_list
            ]
        menu_options.insert(0, {"label": "#", "value": "#"})

        return {
            'breadcrumb_items': [
                {'href': reverse('menu_index'), 'label': u'菜单列表'},
                {'active': True, 'label': u'修改菜单信息'}
            ],
            "panel_heading": u"编辑",
            "media": {
                'js': media.render_js(),
                'css': media.render_css()
            },
            "form": {
                "method": "post",
                "action": reverse('edit_menu', args=(menu_obj.id,)),
                "fields": [
                    {
                        "type": "text",
                        "label": u"菜单连接视图",
                        "help_id": "_menu_help",
                        "help_text": u"点击菜单时，跳转的路径名称，如果是父菜单，填写 # ",
                        "name": "name",
                        "id": "_name",
                        "value": menu_obj.name or ''
                    },
                    {
                        "type": "text",
                        "label": u"菜单标签",
                        "help_id": "_menu_label_help",
                        "help_text": u"菜单展示在页面上的文字",
                        "name": "label",
                        "id": "_label",
                        "value": menu_obj.label or ''
                    },
                    {
                        "type": "text",
                        "label": u"菜单图标",
                        "name": "icon",
                        "help_id": "_menu_icon_help",
                        "help_text": u"菜单前方显示的图标",
                        "id": "_icon",
                        "value": menu_obj.icon or ''
                    },
                    {
                        "type": "select",
                        "label": u'上级菜单',
                        'name': 'parent_menu',
                        'help_id': '_menu_parent_help',
                        'help_text': u'指定该菜单的上级菜单，在菜单栏中，该菜单将显示在上级菜单的下边',
                        'id': '_parent_menu',
                        'options': MenuManager.menu_list(
                            excludes=[menu_obj.id], selected=[menu_obj.parent]
                        )
                    },
                    {
                        "type": "multi_select",
                        "label": u'权限绑定',
                        "help_id": "_menu_role_help",
                        "help_text": u"将该菜单功能分配给某个角色，只有该角色的用户可以看到该菜单，可多选",
                        "name": "role",
                        "id": "_role",
                        "options": role_options
                    },
                    {
                        "type": "button",
                        "button_type": "button",
                        "extra_class": "btn-info",
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
    def update(menu_id, params):
        menu_name = params.get('name', '')
        menu_label = params.get('label', '')
        menu_icon = params.get('icon', '')
        parent_menu_id = params.get('parent_menu', 0)

        if not menu_label:
            menu_label = url_name_dict.get(menu_name) or " ".join(menu_name.split('_'))

        if parent_menu_id.strip() == '':
            parent_menu_id = 0

        try:
            menu = Menu.objects.get(id=menu_id)
        except ObjectDoesNotExist:
            return 0

        chg_flag = menu_label != menu.label or menu_icon != menu.icon or \
                   menu.name != menu_name or menu.parent != parent_menu_id

        if chg_flag:
            menu.label = menu_label
            menu.icon = menu_icon
            menu.name = menu_name
            menu.parent = parent_menu_id

            menu.save()

        rel_qry_set = RoleBindMenu.objects.filter(menu=menu_id)

        db_role_ids = [rel.role_id for rel in rel_qry_set]

        role_ids = params.getlist('role', [])
        for role_id in role_ids:
            role_id = int(role_id)
            if role_id not in db_role_ids:
                RoleBindMenu.objects.create(role_id=role_id, menu_id=menu_id)
                # 此处还要加上所选菜单的父菜单，因为如果直接给子菜单绑定权限的话呢，还是不能根据父菜单查到
                # modify at 2017-10-24 15:02
                if menu.parent != 0:
                    RoleBindMenu.objects.get_or_create(role_id=role_id, menu_id=menu.parent)
                    try:
                        menu_parent = Menu.objects.get(id=menu.parent)
                    except ObjectDoesNotExist:
                        if menu_parent.parent != 0:
                            RoleBindMenu.objects.get_or_create(role_id=role_id, menu_id=menu_parent.parent)
            else:
                db_role_ids.remove(role_id)

        if db_role_ids:
            RoleBindMenu.objects.filter(role_id__in=db_role_ids, menu=menu_id).delete()

        return 1

    @staticmethod
    def delete(menu_id):
        try:
            menu_obj = Menu.objects.get(id=menu_id)
            menu_obj.delete()
        except ObjectDoesNotExist:
            menu_obj = None

        return menu_obj

    @staticmethod
    def index():
        menu_objs = Menu.objects.all()
        delete_url = reverse('delete_menu')
        media = Media(js=['js/menu.js'])
        tbody = [
            {
                'columns': [
                    {'text': menu_obj.id, 'style': "display: none"},
                    {'text': menu_obj.icon},
                    {'text': menu_obj.label},
                    {'text': menu_obj.name},
                ],
                'actions': [
                    {
                        'icon': 'fa-edit',
                        'tooltip': u'编辑',
                        'theme': ' edit ',
                        'href': reverse('edit_menu', args=(menu_obj.id,))
                    },
                    {
                        'href': '#',
                        'icon': 'fa-trash-o',
                        'tooltip': u'删除',
                        'theme': ' delete ',
                        'func': 'delete_menu("{url}", {id}, "{label}")'.format(
                            url=delete_url, id=menu_obj.id, label=menu_obj.label
                        )
                    }
                ]
            } for menu_obj in menu_objs
        ]

        context = {
            'breadcrumb_items': [
                {
                    'href': '#',
                    'active': True,
                    'label': u'菜单列表'
                }
            ],
            'panel_heading': u'菜单列表',
            'media': {
                'js': media.render_js()
            },
            'add_url': reverse('add_menu'),
            'add_url_label': u'添加新的菜单项目',
            'table': {
                'id': '_menu-table',
                'headers': [
                    {'text': u'菜单图标'}, {'text': u'菜单标签'}, {'text': u'页面名称'}, {'text': u'操作'}
                ],
                'tbody': tbody,
            },
            'modal': {
                "id": "_menu_delete_modal"
            }
        }

        return context

    @staticmethod
    def save(params):
        menu_name = params.get("name")
        menu_icon = params.get('icon', '')
        menu_label = params.get('label', '')
        parent_menu_id = params.get('parent_menu', 0)

        if parent_menu_id.strip() == '':
            parent_menu_id = 0

        if not menu_label:
            menu_label = url_name_dict.get(menu_name) or " ".join(menu_name.split('_'))

        menu_obj = Menu(name=menu_name, label=menu_label, icon=menu_icon, parent=parent_menu_id)
        menu_obj.save()

        role_ids = params.getlist('role', [])
        for role_id in role_ids:
            RoleBindMenu.objects.create(menu_id=menu_obj.id, role_id=role_id)

        return menu_obj

    @staticmethod
    def menu_exists(name):
        if name == '' or name == '#':
            return False
        menu_obj = Menu.objects.filter(name=name)

        return menu_obj.count() > 0