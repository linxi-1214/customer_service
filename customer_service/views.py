import json

from django.template.response import TemplateResponse, HttpResponse
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_http_methods

from webargs import fields
from webargs.djangoparser import use_kwargs, use_args

from customer_service.modules.player import PlayerManager
from customer_service.modules.game import GameManager

# Create your views here.


def index(request):
    pass


def new_player(request):
    if request.method == "GET":
        form = {
            "method": "post",
            "action": ""
        }
        form.update(PlayerManager.add_display())

        context = {
            "panel_heading": u"登记玩家信息",
            "form": form
        }

        return TemplateResponse(request, "change.html", context=context)


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


def game_index(request):
    context = GameManager.index()

    return TemplateResponse(request, "change_list.html", context=context)


def new_game(request):
    if request.method == "GET":
        context = GameManager.add_display()

        return TemplateResponse(request, "change.html", context=context)
    else:
        game_obj = GameManager.save(request.POST)
        game_index_url = reverse('game_index')
        return HttpResponseRedirect(game_index_url)


def edit_game(request, id):
    if request.method == "GET":
        context = GameManager.edit_display(id)

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