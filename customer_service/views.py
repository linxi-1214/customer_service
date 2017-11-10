import os
import re
import json
import logging
from datetime import datetime
from collections import namedtuple

from django.template.response import TemplateResponse, HttpResponse
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ObjectDoesNotExist

from django import http
from django.template import Context, Engine, TemplateDoesNotExist, loader

from webargs import fields
from webargs.djangoparser import use_kwargs, use_args

from customer_service.modules import *
from customer_service.models import Player, Alert
from customer_service.tools.model import updated_fields, set_operator

from web_service import settings
from customer_service.decorator import permission_need, ADMIN, DATA_USER, CUSTOMER_SERVICE

logger = logging.getLogger(__name__)
# Create your views here.


def index(request):
    menus = Context.menus(request.user)
    return TemplateResponse(request, 'index.html', context={'menus': menus})


def new_message(request):
    pass


def message_list(request):
    pass


def user_profile(request):
    pass


def user_settings(request):
    pass


@login_required
@require_http_methods(["POST", "GET"])
def change_password(request):
    if request.method == "GET":
        menus = Context.menus(request.user)
        context = UserManager.change_password_display()
        context.update(menus=menus)

        return TemplateResponse(request, 'change.html', context=context)
    else:
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')

        success, message = UserManager.change_password(request.user, old_password, new_password)

        return HttpResponse(json.dumps({"success": success, "message": message}), content_type="application/json")


@require_http_methods(['POST', 'GET'])
def user_login(request):
    if request.method == "GET":
        next_url = request.GET.get('next', None)
        if next_url:
            context = {'next': next_url}
        else:
            context = {}
        return TemplateResponse(request, 'login.html', context=context)
    else:
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_active:
            login(request, user)
            next_url = request.POST.get('next', None)
            index_url = next_url or reverse('index')

            return HttpResponseRedirect(index_url)
        else:
            return TemplateResponse(request, 'login.html', context={'error': u"认证失败"})


@require_http_methods(["GET"])
def user_logout(request):
    logout(request)
    login_url = reverse('login')

    return HttpResponseRedirect(login_url)


@csrf_exempt
@login_required
@require_http_methods(["POST", "GET"])
def user_report(request):
    menus = Context.menus(request.user)
    if request.method == "GET":
        context = ServiceManager.index_display()
        context.update(menus=menus)

        return TemplateResponse(request, "customer_service.html", context=context)
    else:
        user_id = request.POST.get('account')
        date_range = request.POST.get('time-range')

        date_range = [_d.strip() for _d in date_range.split('~')]
        labels, process_data_list, process_data_dict = ServiceManager.report_display(user_id, date_range)
        json_data = {
            "labels": labels, "line_data": process_data_list, "table_data": process_data_dict
        }

        return HttpResponse(json.dumps(json_data), content_type='application/json')


# Menu View Begin   ----------
@login_required
@permission_need(ADMIN)
def menu_index(request):
    context = MenuManager.index()
    menus = Context.menus(request.user)

    context.update(menus=menus)

    return TemplateResponse(request, "change_list.html", context=context)


@login_required
@permission_need(ADMIN)
def new_menu(request):
    menus = Context.menus(request.user)
    if request.method == "GET":
        context = MenuManager.add_display()
        context.update(menus=menus)

        return TemplateResponse(request, "change.html", context=context)
    else:
        menu_obj = MenuManager.save(request.POST)
        menu_index_url = reverse('menu_index')
        return HttpResponseRedirect(menu_index_url)


@login_required
@permission_need(ADMIN)
def edit_menu(request, id):
    menus = Context.menus(request.user)
    if request.method == "GET":
        context = MenuManager.edit_display(id)
        context.update(menus=menus)
        return TemplateResponse(request, 'change.html', context=context)
    else:
        update_rows = MenuManager.update(id, request.POST)

        return HttpResponseRedirect(reverse('menu_index'))


@csrf_exempt
@login_required
@permission_need(ADMIN)
@require_http_methods(["POST"])
@use_kwargs({'id': fields.Int(required=True, validate=lambda id: id > 0)})
def delete_menu(request, id):
    menu_obj = MenuManager.delete(id)

    if request.is_ajax():
        content = {'code': 0}
        if menu_obj is None:
            content.update(message=u'菜单删除成功！')
        else:
            content.update(message=u'菜单［ %s ］删除成功！' % menu_obj.name)
        return HttpResponse(content=json.dumps(content), content_type='application/json')

    else:
        menu_index_url = reverse('menu_index')
        return HttpResponseRedirect(menu_index_url)

# Menu View End -------------


# Player View Begin   ----------
@login_required
@permission_need([ADMIN, DATA_USER, CUSTOMER_SERVICE])
def player_index(request):
    context = PlayerManager.index(request.user)
    menus = Context.menus(request.user)

    context.update(menus=menus)

    return TemplateResponse(request, "change_list.html", context=context)


class Params:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __str__(self):
        repr = []
        for attr in self.__dict__:
            repr.append('%s: %s' % (attr, getattr(self, attr)))
        return "\n".join(repr)


def _structure_namedtuple(request, array_name):
    def structure_dict_pair(obj, key, value):
        m = re.match(r'\[(\w+)\](.*)', key)
        if m:
            if m.group(2) != '':
                _tmp_obj = getattr(obj, m.group(1), None)
                if _tmp_obj is None:
                    _tmp_obj = Params()
                    setattr(obj, m.group(1), _tmp_obj)
                structure_dict_pair(_tmp_obj, m.group(2), value)
            else:
                setattr(obj, m.group(1), value)

    nt = []
    expression = r'^' + array_name + r'\[(\d+)\](.*)'
    reg = re.compile(expression)
    for k, v in request.GET.items():
        m = reg.match(k)
        if m is None:
            continue
        array_index = int(m.group(1))
        try:
            tmp_obj = nt[array_index]
        except IndexError:
            for ind in range(array_index - len(nt) + 1):
                tmp_obj = Params()
                nt.append(tmp_obj)
            tmp_obj = nt[array_index]

        structure_dict_pair(tmp_obj, m.group(2), v)
    return nt


@login_required
@permission_need([ADMIN, DATA_USER, CUSTOMER_SERVICE])
def ajax_player_index(request):
    """
    request.GET: draw ['1']
                columns[0][data] ['']
                columns[0][name] ['']
                columns[0][searchable] ['false']
                columns[0][orderable] ['false']
                columns[0][search][value] ['']
                columns[0][search][regex] ['false']
                columns[1][data] ['id']
                columns[1][name] ['']
                columns[1][searchable] ['true']
                columns[1][orderable] ['true']
                columns[1][search][value] ['']
                columns[1][search][regex] ['false']
                ......
                order[0][column] ['0']
                order[0][dir] ['asc']
                start ['0']
                length ['100']
                search[value] ['']
                search[regex] ['false']
                charge_money_min ['10']
                charge_money_max ['100']
                _ ['1510189926957']
    :param request:
    :return:
    """
    columns = _structure_namedtuple(request, 'columns')
    orders = _structure_namedtuple(request, 'order')
    search_info = _structure_namedtuple(request, 'search')

    draw = request.GET.get('draw')
    start = request.GET.get('start')
    length = request.GET.get('length')
    money_min = request.GET.get('charge_money_min', None)
    money_max = request.GET.get('charge_money_max', None)

    p = Params(columns=columns, orders=orders, search_info=search_info,
               draw=draw, start=start, length=length, money_min=money_min, money_max=money_max)

    player_info = PlayerManager.player_condition_query(request.user, pagination=p)

    return HttpResponse(json.dumps(player_info), content_type='application/json')


@login_required
@permission_need([ADMIN, DATA_USER])
def player_recycle_index(request):
    context = PlayerManager.index(request.user, is_deleted=1)
    menus = Context.menus(request.user)

    context.update(menus=menus)

    return TemplateResponse(request, "change_list.html", context=context)


@login_required
@permission_need([ADMIN, DATA_USER])
def ajax_player_recycle_index(request):
    player_info = PlayerManager.player_condition_query(request.user, is_deleted=1)

    return HttpResponse(json.dumps({'data': player_info}), content_type='application/json')


@login_required
@permission_need([ADMIN, DATA_USER])
def new_player(request):
    menus = Context.menus(request.user)
    if request.method == "GET":
        context = PlayerManager.add_display()
        context.update(menus=menus)

        return TemplateResponse(request, "change.html", context=context)
    else:
        PlayerManager.save(request.user, request.POST)
        player_index_url = reverse('player_index')
        return HttpResponseRedirect(player_index_url)


@login_required
@permission_need([ADMIN, DATA_USER])
def edit_player(request, id):
    menus = Context.menus(request.user)
    if request.method == "GET":
        context = PlayerManager.edit_display(id)
        context.update(menus=menus)
        return TemplateResponse(request, 'change.html', context=context)
    else:
        PlayerManager.update(request.user, id, request.POST)

        return HttpResponseRedirect(reverse('player_index'))


@login_required
@permission_need([ADMIN, DATA_USER])
def export_player(request):
    menus = Context.menus(request.user)
    if request.method == "GET":
        context = PlayerManager.import_display()
        context.update(menus=menus)
        return TemplateResponse(request, 'player_import.html', context=context)
    else:
        PlayerManager.export_player()


@login_required
@permission_need([ADMIN, DATA_USER])
def import_player(request):
    menus = Context.menus(request.user)
    if request.method == "GET":
        context = PlayerManager.import_display()
        context.update(menus=menus)
        return TemplateResponse(request, 'player_import.html', context=context)
    else:
        files = request.FILES.getlist('player_file')
        for file in files:
            current_time = datetime.now()
            file_suffix = file.name.split('.')
            if len(file_suffix) > 1:
                file_suffix = file_suffix[1]

            stored_name = "%s.%s" % (current_time.strftime('%Y%m%d%H%M%S'), file_suffix)
            with open(os.path.join(settings.FILE_UPLOAD_STORAGE_DIR, stored_name), r'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            try:
                PlayerManager.import_player(request.user,
                                            current_time,
                                            settings.FILE_UPLOAD_STORAGE_DIR,
                                            stored_name, file.name)
            except ValueError as err:
                return HttpResponse(json.dumps({'msg': str(err)}), status=500)

        return HttpResponse(json.dumps({'msg': 'OK'}))


@login_required
@permission_need([ADMIN])
def import_detail(request, import_id):
    import_result = PlayerManager.import_result_query(import_id)

    if import_result is None:
        import_result = '[]'

    return HttpResponse(import_result, content_type='application/json')


@csrf_exempt
@login_required
@permission_need([ADMIN, DATA_USER])
@require_http_methods(["POST"])
@use_kwargs({
    'id': fields.DelimitedList(fields.Int(), required=True)
})
def recycle_player(request, id):
    ret_context = {'code': 0, 'message': u'恢复玩家成功！'}
    try:
        player_set = Player.objects.filter(id__in=id)
        for player in player_set:
            if player.is_deleted == 0:
                continue
            set_operator(player, request.user)
            player.is_deleted = 0
            player.save(update_fields=['is_deleted'])
    except Exception:
        logger.exception("recycle player error: ")
        ret_context.update(code=1, message=u'恢复玩家失败，内部错误！')

    return HttpResponse(content=json.dumps(ret_context), content_type='application/json')


@csrf_exempt
@login_required
@permission_need([ADMIN, DATA_USER])
@require_http_methods(["POST"])
@use_kwargs({
    'id': fields.Int(required=True, validate=lambda id: id > 0),
    'force': fields.Bool(required=False, missing=False),
    'really': fields.Bool(required=False, missing=False)
})
def delete_player(request, id, force=False, really=False):
    PlayerManager.delete(request.user, id, force, really)

    # False, obj: 不可以删除，需要确认
    # False, None: 可以删除，但是删除失败
    # True, None: 可以删除，删除成功
    # True, obj: 可以删除，删除成功

    if request.is_ajax():
        content = {'code': 0}
        return HttpResponse(content=json.dumps(content), content_type='application/json')
    else:
        player_index_url = reverse('player_index')
        return HttpResponseRedirect(player_index_url)


@csrf_exempt
@login_required
@permission_need([ADMIN, DATA_USER])
@require_http_methods(["POST"])
@use_kwargs(
    {
        'id': fields.DelimitedList(fields.Int(), required=True),
        'force': fields.Bool(required=False, missing=False),
        'really': fields.Bool(required=False, missing=False)
    })
def delete_player_multiple(request, id, force=False, really=False):
    print(id)
    delete_success = PlayerManager.delete(request.user, id, force, really)

    return HttpResponse(content=json.dumps({'code': 0}), content_type="application/json")


@login_required
@permission_need([ADMIN, DATA_USER, CUSTOMER_SERVICE])
@require_http_methods(["GET", "POST"])
def contract_player(request):
    menus = Context.menus(request.user)

    if request.method == "POST":
        player_id = request.POST.get('player_id')
        PlayerManager.update_contact_result(request.user, player_id, request.POST)
    else:
        player_id = request.GET.get('player', None)
        current_player_id = request.GET.get('current', None)

        if current_player_id:
            current_player = Player.objects.get(id=current_player_id)
            if current_player.mobile:
                Player.objects.filter(mobile=current_player.mobile).update(current_contact_user=None)
            else:
                Player.objects.filter(id=current_player_id).update(current_contact_user=None)

    context = PlayerManager.contract_display(player_id, request.user)
    context.update(menus=menus)

    return TemplateResponse(request, "user_card.html", context=context)


@login_required
@permission_need([ADMIN, DATA_USER, CUSTOMER_SERVICE])
@require_http_methods(["POST"])
def ajax_contact_player(request):
    player_id = request.POST.get('player_id')
    player_set = PlayerManager.update_contact_result(request.user, player_id, request.POST)

    player_account = [player.account for player in player_set]

    return HttpResponse(json.dumps({'code': 0, 'message': u'玩家 %s 保存成功 !' % ','.join(player_account[:5])}))


@login_required
@permission_need([ADMIN, CUSTOMER_SERVICE])
@require_http_methods(["GET", "POST"])
def player_contact_detail(request):
    menus = Context.menus(request.user)

    time_range = None
    if request.method == "GET":
        player_id = None
    else:
        player_id = request.POST.get('account', None)
        time_range_str = request.POST.get('time-range', None)

        if time_range_str is not None and time_range_str != '':
            time_range = time_range_str.split(' ~ ')
        else:
            time_range = None

    context = PlayerManager.player_contact_detail(request.user, player_id, time_range)
    context.update(menus=menus)

    return TemplateResponse(request, "player_contact_detail.html", context=context)

# Player View End -------------


# Result View Begin   ----------
@login_required
@permission_need(ADMIN)
def result_index(request):
    context = ContactResultManager.index()
    menus = Context.menus(request.user)

    context.update(menus=menus)

    return TemplateResponse(request, "change_list.html", context=context)


@login_required
@permission_need(ADMIN)
def new_result(request):
    menus = Context.menus(request.user)
    if request.method == "GET":
        context = ContactResultManager.add_display()
        context.update(menus=menus)

        return TemplateResponse(request, "change.html", context=context)
    else:
        result_obj = ContactResultManager.save(request.POST)
        result_index_url = reverse('result_index')
        return HttpResponseRedirect(result_index_url)


@login_required
@permission_need(ADMIN)
def edit_result(request, id):
    menus = Context.menus(request.user)
    if request.method == "GET":
        context = ContactResultManager.edit_display(id)
        context.update(menus=menus)
        return TemplateResponse(request, 'change.html', context=context)
    else:
        update_rows = ContactResultManager.update(id, request.POST)

        return HttpResponseRedirect(reverse('result_index'))


@csrf_exempt
@login_required
@permission_need(ADMIN)
@require_http_methods(["POST"])
@use_kwargs({'id': fields.Int(required=True, validate=lambda id: id > 0)})
def delete_result(request, id):
    result_obj = ContactResultManager.delete(id)

    if request.is_ajax():
        content = {'code': 0}
        if result_obj is None:
            content.update(message=u'联系结果删除成功！')
        else:
            content.update(message=u'联系结果［ %s ］删除成功！' % result_obj.result)
        return HttpResponse(content=json.dumps(content), content_type='application/json')

    else:
        result_index_url = reverse('result_index')
        return HttpResponseRedirect(result_index_url)

# ContactResult View End -------------


# User View Begin   ----------
@login_required
@permission_need(ADMIN)
def user_index(request):
    context = UserManager.index()
    menus = Context.menus(request.user)

    context.update(menus=menus)

    return TemplateResponse(request, "change_list.html", context=context)


@login_required
@permission_need(ADMIN)
def new_user(request):
    menus = Context.menus(request.user)
    if request.method == "GET":
        context = UserManager.add_display()
        context.update(menus=menus)

        return TemplateResponse(request, "change.html", context=context)
    else:
        user_obj = UserManager.save(request.POST)
        user_index_url = reverse('user_index')
        return HttpResponseRedirect(user_index_url)


@login_required
@permission_need(ADMIN)
def edit_user(request, id):
    menus = Context.menus(request.user)
    if request.method == "GET":
        context = UserManager.edit_display(id)
        context.update(menus=menus)
        return TemplateResponse(request, 'change.html', context=context)
    else:
        update_rows = UserManager.update(id, request.POST)

        return HttpResponseRedirect(reverse('user_index'))


@csrf_exempt
@login_required
@permission_need(ADMIN)
@require_http_methods(["POST"])
@use_kwargs({'id': fields.Int(required=True, validate=lambda id: id > 0)})
def delete_user(request, id):
    user_obj = UserManager.delete(id)

    if request.is_ajax():
        content = {'code': 0}
        if user_obj is None:
            content.update(message=u'用户删除成功！')
        else:
            content.update(message=u'用户［ %s ］删除成功！' % user_obj.loginname)
        return HttpResponse(content=json.dumps(content), content_type='application/json')

    else:
        user_index_url = reverse('user_index')
        return HttpResponseRedirect(user_index_url)

# User View End -------------


# Role View Begin   ----------
@login_required
@permission_need(ADMIN)
def role_index(request):
    context = RoleManager.index()
    menus = Context.menus(request.user)

    context.update(menus=menus)

    return TemplateResponse(request, "change_list.html", context=context)


@login_required
@permission_need(ADMIN)
def new_role(request):
    menus = Context.menus(request.user)
    if request.method == "GET":
        context = RoleManager.add_display()
        context.update(menus=menus)

        return TemplateResponse(request, "change.html", context=context)
    else:
        role_obj = RoleManager.save(request.POST)
        role_index_url = reverse('role_index')
        return HttpResponseRedirect(role_index_url)


@login_required
@permission_need(ADMIN)
def edit_role(request, id):
    menus = Context.menus(request.user)
    if request.method == "GET":
        context = RoleManager.edit_display(id)
        context.update(menus=menus)
        return TemplateResponse(request, 'change.html', context=context)
    else:
        update_rows = RoleManager.update(id, request.POST)

        return HttpResponseRedirect(reverse('role_index'))


@csrf_exempt
@login_required
@permission_need(ADMIN)
@require_http_methods(["POST"])
@use_kwargs({'id': fields.Int(required=True, validate=lambda id: id > 0)})
def delete_role(request, id):
    role_obj = RoleManager.delete(id)

    if request.is_ajax():
        content = {'code': 0}
        if role_obj is None:
            content.update(message=u'游戏删除成功！')
        else:
            content.update(message=u'游戏［ %s ］删除成功！' % role_obj.name)
        return HttpResponse(content=json.dumps(content), content_type='application/json')

    else:
        role_index_url = reverse('role_index')
        return HttpResponseRedirect(role_index_url)

# Role View End -------------


# Alert View Begin
@login_required
def alert_index(request):
    context = AlertManager.index()
    menus = Context.menus(request.user)

    context.update(menus=menus)

    return TemplateResponse(request, "change_list.html", context=context)


@login_required
def alert_all(request):
    alert_json = AlertManager.all(request.user)

    return HttpResponse(json.dumps(alert_json), content_type='application/json')


@login_required
@csrf_exempt
def ajax_alert_all(request):
    alert_json = AlertManager._ajax_query_all(request.user)

    return HttpResponse(json.dumps(alert_json), content_type='application/json')


@login_required
def red_alert(request, alert_id):
    try:
        alert = Alert.objects.get(id=alert_id)
        if alert.receiver_id == request.user.id:
            alert.marked = True
            alert.save()
    except ObjectDoesNotExist:
        pass

    return HttpResponse('OK')


@login_required
@csrf_exempt
def red_alert_multi(request):
    alert_ids = request.POST.get('id')

    alert_id_list = alert_ids.split(',')
    AlertManager.has_red(alert_id_list)

    return HttpResponse('OK')
# Alert View End


# Game View Begin   ----------
@login_required
@permission_need(ADMIN)
def game_index(request):
    context = GameManager.index()
    menus = Context.menus(request.user)

    context.update(menus=menus)

    return TemplateResponse(request, "change_list.html", context=context)


@login_required
@permission_need(ADMIN)
def new_game(request):
    menus = Context.menus(request.user)
    if request.method == "GET":
        context = GameManager.add_display()
        context.update(menus=menus)

        return TemplateResponse(request, "change.html", context=context)
    else:
        game_obj = GameManager.save(request.POST)
        game_index_url = reverse('game_index')
        return HttpResponseRedirect(game_index_url)


@login_required
@permission_need(ADMIN)
def edit_game(request, id):
    menus = Context.menus(request.user)
    if request.method == "GET":
        context = GameManager.edit_display(id)
        context.update(menus=menus)
        return TemplateResponse(request, 'change.html', context=context)
    else:
        update_rows = GameManager.update(id, request.POST)

        return HttpResponseRedirect(reverse('game_index'))


@csrf_exempt
@login_required
@permission_need(ADMIN)
@require_http_methods(["POST"])
@use_kwargs({'id': fields.Int(required=True, validate=lambda id: id > 0)})
def delete_game(request, id):
    game_obj = GameManager.delete(id)

    if request.is_ajax():
        content = {'code': 0}
        if game_obj is None:
            content.update(message=u'游戏删除成功！')
        else:
            content.update(message=u'游戏［ %s ］删除成功！' % game_obj.name)
        return HttpResponse(content=json.dumps(content), content_type='application/json')

    else:
        game_index_url = reverse('game_index')
        return HttpResponseRedirect(game_index_url)

# Game View End -------------

# Error View Begin


def error_500(request, template_name="errors/500.html"):

    context = {'menus': Context.menus(request.user)}
    template = loader.get_template(template_name)
    return http.HttpResponseServerError(template.render(context, request))


def error_view(request, exception):
    context = {'menus': Context.menus(request.user)}
    exception_name = exception.__class__.__name__

    try:
        print(exception_name)
        if exception_name.lower() == "resolver404":
            template = loader.get_template("errors/404.html")
        elif exception_name.lower() == "permissiondenied":
            template = loader.get_template("errors/403.html")
        elif exception_name.lower() == "suspiciousoperation":
            template = loader.get_template("errors/400.html")
        else:
            template = loader.get_template("errors/400.html")

        body = template.render(context, request)
        content_type = None  # Django will use DEFAULT_CONTENT_TYPE
    except TemplateDoesNotExist:
        template = Engine().from_string(
            '<h1>Not Found</h1>'
            '<p>The requested URL {{ request_path }} was not found on this server.</p>')
        body = template.render(Context(context))
        content_type = 'text/html'
    return http.HttpResponseNotFound(body, content_type=content_type)

# Error View End
