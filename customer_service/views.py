import os
import json
from datetime import datetime

from django.template.response import TemplateResponse, HttpResponse
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_http_methods

from webargs import fields
from webargs.djangoparser import use_kwargs, use_args

from customer_service.modules import *
from customer_service.models import Player

from web_service import settings

# Create your views here.


def index(request):
    return HttpResponse()


def new_message(request):
    pass


def message_list(request):
    pass


def user_profile(request):
    pass


def user_settings(request):
    pass


def user_login(request):
    pass


# Menu View Begin   ----------
def menu_index(request):
    context = MenuManager.index()
    menus = Context.menus(request.user)

    context.update(menus=menus)

    return TemplateResponse(request, "change_list.html", context=context)


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


def edit_menu(request, id):
    menus = Context.menus(request.user)
    if request.method == "GET":
        context = MenuManager.edit_display(id)
        context.update(menus=menus)
        return TemplateResponse(request, 'change.html', context=context)
    else:
        update_rows = MenuManager.update(id, request.POST)

        return HttpResponseRedirect(reverse('menu_index'))


@require_http_methods(["POST"])
@csrf_exempt
@use_kwargs({'id': fields.Int(required=True, validate=lambda id: id > 0)})
def delete_menu(request, id):
    menu_obj = MenuManager.delete(id)

    if request.is_ajax():
        content = {'code': 0}
        if menu_obj is None:
            content.update(message=u'游戏删除成功！')
        else:
            content.update(message=u'游戏［ %s ］删除成功！' % menu_obj.name)
        return HttpResponse(content=json.dumps(content), content_type='application/json')

    else:
        menu_index_url = reverse('menu_index')
        return HttpResponseRedirect(menu_index_url)

# Menu View End -------------


# Player View Begin   ----------
def player_index(request):
    context = PlayerManager.index()
    menus = Context.menus(request.user)

    context.update(menus=menus)

    return TemplateResponse(request, "change_list.html", context=context)


def new_player(request):
    menus = Context.menus(request.user)
    if request.method == "GET":
        context = PlayerManager.add_display()
        context.update(menus=menus)

        return TemplateResponse(request, "change.html", context=context)
    else:
        player_obj = PlayerManager.save(request.POST)
        player_index_url = reverse('player_index')
        return HttpResponseRedirect(player_index_url)


def edit_player(request, id):
    menus = Context.menus(request.user)
    if request.method == "GET":
        context = PlayerManager.edit_display(id)
        context.update(menus=menus)
        return TemplateResponse(request, 'change.html', context=context)
    else:
        update_rows = PlayerManager.update(id, request.POST)

        return HttpResponseRedirect(reverse('player_index'))


def export_player(request):
    menus = Context.menus(request.user)
    if request.method == "GET":
        context = PlayerManager.import_display()
        context.update(menus=menus)
        return TemplateResponse(request, 'player_import.html', context=context)
    else:
        PlayerManager.export_player()


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
            PlayerManager.import_player(request.user,
                                        current_time,
                                        settings.FILE_UPLOAD_STORAGE_DIR,
                                        stored_name, file.name)

        return HttpResponse(json.dumps({'msg': 'OK'}))


@require_http_methods(["POST"])
@csrf_exempt
@use_kwargs({'id': fields.Int(required=True, validate=lambda id: id > 0)})
def delete_player(request, id):
    player_obj = PlayerManager.delete(id)

    if request.is_ajax():
        content = {'code': 0}
        if player_obj is None:
            content.update(message=u'游戏删除成功！')
        else:
            content.update(message=u'游戏［ %s ］删除成功！' % player_obj.name)
        return HttpResponse(content=json.dumps(content), content_type='application/json')

    else:
        player_index_url = reverse('player_index')
        return HttpResponseRedirect(player_index_url)


@require_http_methods(["GET", "POST"])
def contract_player(request):
    menus = Context.menus(request.user)

    current_player_id = None
    if request.method == "POST":
        player_id = request.POST.get('player_id')
        PlayerManager.update_contact_result(request.user, player_id, request.POST)
    else:
        player_id = request.GET.get('player', None)
        current_player_id = request.GET.get('current', None)

    context = PlayerManager.contract_display(player_id)
    context.update(menus=menus)

    if current_player_id:
        print(current_player_id)
        Player.objects.filter(id=current_player_id).update(locked=False)

    return TemplateResponse(request, "user_card.html", context=context)

# Player View End -------------


# Result View Begin   ----------
def result_index(request):
    context = ContactResultManager.index()
    menus = Context.menus(request.user)

    context.update(menus=menus)

    return TemplateResponse(request, "change_list.html", context=context)


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


def edit_result(request, id):
    menus = Context.menus(request.user)
    if request.method == "GET":
        context = ContactResultManager.edit_display(id)
        context.update(menus=menus)
        return TemplateResponse(request, 'change.html', context=context)
    else:
        update_rows = ContactResultManager.update(id, request.POST)

        return HttpResponseRedirect(reverse('result_index'))


@require_http_methods(["POST"])
@csrf_exempt
@use_kwargs({'id': fields.Int(required=True, validate=lambda id: id > 0)})
def delete_result(request, id):
    result_obj = ContactResultManager.delete(id)

    if request.is_ajax():
        content = {'code': 0}
        if result_obj is None:
            content.update(message=u'联系结果删除成功！')
        else:
            content.update(message=u'联系结果［ %s ］删除成功！' % result_obj.loginname)
        return HttpResponse(content=json.dumps(content), content_type='application/json')

    else:
        result_index_url = reverse('result_index')
        return HttpResponseRedirect(result_index_url)

# ContactResult View End -------------


# User View Begin   ----------
def user_index(request):
    context = UserManager.index()
    menus = Context.menus(request.user)

    context.update(menus=menus)

    return TemplateResponse(request, "change_list.html", context=context)


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


def edit_user(request, id):
    menus = Context.menus(request.user)
    if request.method == "GET":
        context = UserManager.edit_display(id)
        context.update(menus=menus)
        return TemplateResponse(request, 'change.html', context=context)
    else:
        update_rows = UserManager.update(id, request.POST)

        return HttpResponseRedirect(reverse('user_index'))


@require_http_methods(["POST"])
@csrf_exempt
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
def role_index(request):
    context = RoleManager.index()
    menus = Context.menus(request.user)

    context.update(menus=menus)

    return TemplateResponse(request, "change_list.html", context=context)


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


def edit_role(request, id):
    menus = Context.menus(request.user)
    if request.method == "GET":
        context = RoleManager.edit_display(id)
        context.update(menus=menus)
        return TemplateResponse(request, 'change.html', context=context)
    else:
        update_rows = RoleManager.update(id, request.POST)

        return HttpResponseRedirect(reverse('role_index'))


@require_http_methods(["POST"])
@csrf_exempt
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


# Game View Begin   ----------
def game_index(request):
    context = GameManager.index()
    menus = Context.menus(request.user)

    context.update(menus=menus)

    return TemplateResponse(request, "change_list.html", context=context)


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


def edit_game(request, id):
    menus = Context.menus(request.user)
    if request.method == "GET":
        context = GameManager.edit_display(id)
        context.update(menus=menus)
        return TemplateResponse(request, 'change.html', context=context)
    else:
        update_rows = GameManager.update(id, request.POST)

        return HttpResponseRedirect(reverse('game_index'))


@require_http_methods(["POST"])
@csrf_exempt
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