from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist

from django.forms.widgets import Media

from customer_service.models import User, Role


class UserManager:

    @staticmethod
    def add_display():
        role_objs = Role.objects.all()
        role_options = [
            {
                "value": role.id,
                "label": role.desc or role.name,
            } for role in role_objs
            ]

        media = Media(js=['common/selector2/js/select2.full.js', 'js/user.js'],
                      css={'all': ['common/selector2/css/select2.min.css']})
        return {
            'breadcrumb_items': [
                {'href': reverse('user_index'), 'label': u'用户列表'},
                {'active': True, 'label': u'添加用户'}
            ],
            "panel_heading": u"用户信息填写",
            "media": {
                'js': media.render_js(),
                'css': media.render_css()
            },
            "form": {
                "method": "post",
                "action": reverse('add_user'),
                "fields": [
                    {
                        "type": "text",
                        "label": u"登录账号",
                        "help_id": "_loginname_help",
                        "help_text": u"登录系统的账号，只能包含字母，数字，_，必须唯一",
                        "name": "loginname",
                        "id": "_loginname",
                    },
                    {
                        "type": "text",
                        "label": u"姓氏",
                        "name": "first_name",
                        "id": "_first_name",
                    },
                    {
                        "type": "text",
                        "label": u"名字",
                        "name": "last_name",
                        "id": "_last_name",
                    },
                    {
                        "type": "password",
                        "label": u"登录密码",
                        "help_id": "_user_password_help",
                        "help_text": u'不可包含空格，字母区分大小写',
                        "name": "password",
                        "id": "_password",
                    },
                    {
                        "type": "checkbox",
                        "checkbox_group": [
                            {
                                "label": u"激活",
                                "name": "active",
                                "id": "_active",
                                "checked": True
                            }
                        ],
                        "help_id": "_user_active_help",
                        "help_text": u'激活状态的用户才可以登录系统'
                    },
                    {
                        "type": "select",
                        "label": u'角色',
                        'name': 'role_id',
                        'help_id': '_user_role_help',
                        'help_text': u'选择某角色，将具有某角色绑定的功能',
                        'id': '_role_id',
                        'options': role_options
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
    def edit_display(user_id):
        try:
            user_obj = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            return None
        role_objs = Role.objects.all()
        role_options = [
            {
                "value": role.id,
                "label": role.desc or role.name,
                "selected": role.id == user_obj.role_id
            } for role in role_objs
            ]
        media = Media(js=['common/selector2/js/select2.full.js', 'js/user.js'],
                      css={'all': ['common/selector2/css/select2.min.css', 'css/custom-select.css']})

        return {
            'breadcrumb_items': [
                {'href': reverse('user_index'), 'label': u'用户列表'},
                {'active': True, 'label': u'修改用户信息'}
            ],
            "panel_heading": u"编辑用户信息",
            "media": {
                'js': media.render_js(),
                'css': media.render_css()
            },
            "form": {
                "method": "post",
                "action": reverse('edit_user', args=(user_obj.id,)),
                "fields": [
                    {
                        "type": "text",
                        "label": u"登录账号",
                        "help_id": "_loginname_help",
                        "help_text": u"登录系统的账号，只能包含字母，数字，_，必须唯一",
                        "name": "loginname",
                        "id": "_loginname",
                        "value": user_obj.loginname or ''
                    },
                    {
                        "type": "text",
                        "label": u"姓氏",
                        "name": "first_name",
                        "id": "_first_name",
                        "value": user_obj.first_name or ''
                    },
                    {
                        "type": "text",
                        "label": u"名字",
                        "name": "last_name",
                        "id": "_last_name",
                        "value": user_obj.last_name or ''
                    },
                    {
                        "type": "password",
                        "label": u"登录密码",
                        "help_id": "_user_password_help",
                        "help_text": u'如果不打算修改密码，请不要填写任何内容到此文本框',
                        "name": "password",
                        "id": "_password",
                    },
                    {
                        "type": "checkbox",
                        "checkbox_group": [
                            {
                                "label": u"激活",
                                "name": "active",
                                "id": "_active",
                                "checked": user_obj.is_active
                            }
                        ],
                        "help_id": "_user_active_help",
                        "help_text": u'激活状态的用户才可以登录系统'
                    },
                    {
                        "type": "select",
                        "attrs": {
                            "kind": "form-select"
                        },
                        "label": u'角色',
                        'name': 'role_id',
                        'help_id': '_user_role_help',
                        'help_text': u'选择某角色，将具有某角色绑定的功能',
                        'id': '_role_id',
                        'options': role_options
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
    def update(user_id, params):
        loginname = params.get("loginname")
        password = params.get('password')
        first_name = params.get('first_name', '')
        last_name = params.get('last_name', '')
        active_text = params.get('active')
        active = int(active_text) == 1
        role_id = params.get('role_id')

        try:
            user_obj = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            return 0

        if role_id.strip() == '':
            role_id = None

        if role_id is not None and role_id != '':
            user_obj.role_id = int(role_id)

        user_obj.loginname = loginname
        user_obj.first_name = first_name
        user_obj.last_name = last_name
        user_obj.is_active = active
        user_obj.role_id = role_id

        user_obj.set_password(password)
        user_obj.save()

        return 1

    @staticmethod
    def delete(user_id):
        try:
            user_obj = User.objects.get(id=user_id)
            user_obj.delete()
        except ObjectDoesNotExist:
            user_obj = None

        return user_obj

    @staticmethod
    def index():
        user_objs = User.objects.all()
        delete_url = reverse('delete_user')
        media = Media(js=['js/user.js'])
        tbody = [
            {
                'columns': [
                    {'text': user_obj.id, 'style': "display: none"},
                    {'text': user_obj.loginname},
                    {'text': '%s %s' % (user_obj.first_name or '-', user_obj.last_name or '-')},
                    {'text': '<button type="button" class="btn btn-success btn-circle">'
                             '<i class="fa fa-check"></i></button>' if user_obj.is_active else
                             '<button type="button" class="btn btn-warning btn-circle">'
                             '<i class="fa fa-times"></i></button>'
                    },
                    {'text': user_obj.role.desc or user_obj.role.name}
                ],
                'actions': [
                    {
                        'icon': 'fa-edit',
                        'tooltip': u'编辑',
                        'href': reverse('edit_user', args=(user_obj.id,))
                    },
                    {
                        'href': '#',
                        'icon': 'fa-trash-o',
                        'tooltip': u'删除',
                        'func': 'delete_user("{url}", {id}, "{label}")'.format(
                            url=delete_url, id=user_obj.id, label=user_obj.loginname
                        )
                    }
                ]
            } for user_obj in user_objs
        ]

        context = {
            'breadcrumb_items': [
                {
                    'href': '#',
                    'active': True,
                    'label': u'用户列表'
                }
            ],
            'panel_heading': u'用户列表信息',
            'media': {
                'js': media.render_js()
            },
            'add_url': reverse('add_user'),
            'add_url_label': u'添加新用户',
            'table': {
                'id': '_user-table',
                'headers': [
                    {'text': u'登录账号'}, {'text': u'姓名'}, {'text': u'是否激活'}, {'text': u'角色'}, {'text': u'操作'}
                ],
                'tbody': tbody,
            },
            'modal': {
                "id": "_user_delete_modal"
            }
        }

        return context

    @staticmethod
    def save(params):
        loginname = params.get("loginname")
        password = params.get('password')
        first_name = params.get('first_name', '')
        last_name = params.get('last_name', '')
        active_text = params.get('active')
        active = active_text is not None
        role_id = params.get('role_id')

        user_obj = User(loginname=loginname, first_name=first_name, last_name=last_name, is_active=active)

        if role_id is not None and role_id != '':
            user_obj.role_id = int(role_id)

        user_obj.set_password(password)
        user_obj.save()

        return user_obj

    @staticmethod
    def user_exists(loginname):
        user_obj = User.objects.filter(loginname=loginname)

        return user_obj.count() > 0

    @staticmethod
    def change_password(user, old_password, new_password):
        try:
            if user.check_password(old_password):
                user.set_password(new_password)
                user.save()
                return True, "密码修改成功！"
            else:
                return False, "密码验证失败！"
        except Exception as err:
            return False, "修改密码失败！"

    @staticmethod
    def change_password_display():
        media = Media(js=['js/user.js'])
        return {
            'breadcrumb_items': [
                {'active': True, 'label': u'个人设置'},
                {'href': reverse('change_password'), 'label': u'修改密码'}
            ],
            "panel_heading": u"用户密码修改",
            "media": {
                'js': media.render_js(),
            },
            "form": {
                "method": "post",
                "action": reverse('change_password'),
                "attrs": "data-validator-option=\"{theme:'bootstrap', timely:1, stopOnError:true}\"",
                "fields": [
                    {
                        "type": "password",
                        "label": u"原密码",
                        "name": "old_password",
                        "id": "_old_password",
                        'attrs': {
                            'data-rule': '原密码: required;'
                        }
                    },
                    {
                        "type": "password",
                        "label": u"新密码",
                        "help_id": "_new_password_help",
                        "help_text": u'不可包含空格，字母区分大小写',
                        "name": "new_password",
                        "id": "_new_password",
                        "attrs": {
                            'data-rule': "新密码: required; password"
                        }
                    },
                    {
                        "type": "password",
                        "label": u"密码确认",
                        "help_id": "_new_password2_help",
                        "help_text": u'再次输入新密码',
                        "name": "new_password2",
                        "id": "_new_password2",
                        "attrs": {
                            "data-rule": "密码确认: required; match(new_password)"
                        }
                    },
                    {
                        "type": "button",
                        "button_type": "button",
                        "label": u"提 交",
                        "extra_class": "btn-primary btn-block",
                        "click": '"change_password(\'%s\'); return false;"' % reverse('change_password')
                    }
                ]
            }
        }