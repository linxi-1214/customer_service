from django.conf.urls import url

from customer_service import views

urlpatterns = [
    url(r'login/$', views.user_login, name='login'),
    url(r'home/index/$', views.index, name='index'),
    url(r'user-profile', views.user_profile, name='profile'),
    url(r'user-settings', views.user_settings, name='user_settings'),
    url(r'message-add/$', views.new_message, name='add_message'),
    url(r'message-list/$', views.message_list, name='message'),

    # Player View Begin
    url(r'player/index/$', views.player_index, name='player_index'),
    url(r'player/add/$', views.new_player, name='add_player'),
    url(r'player/edit/([0-9]+)/$', views.edit_player, name='edit_player'),
    url(r'player/delete/$', views.delete_player, name='delete_player'),
    url(r'player/import/$', views.import_player, name='import_player'),
    url(r'player/export/$', views.export_player, name='export_player'),
    url(r'player/contract/$', views.contract_player, name='contract_player'),
    # Player View End

    # 游戏 BEGIN
    url(r'game/index/$', views.game_index, name='game_index'),
    url(r'game/add/$', views.new_game, name='add_game'),
    url(r'game/delete/$', views.delete_game, name='delete_game'),
    url(r'game/edit/([0-9]+)/$', views.edit_game, name='edit_game'),
    # Game view end 
    
    # Menu view begin
    url(r'menu/index/$', views.menu_index, name='menu_index'),
    url(r'menu/add/$', views.new_menu, name='add_menu'),
    url(r'menu/delete/$', views.delete_menu, name='delete_menu'),
    url(r'menu/edit/([0-9]+)/$', views.edit_menu, name='edit_menu'),
    # Menu view end
    
    # Role view begin
    url(r'role/index/$', views.role_index, name='role_index'),
    url(r'role/add/$', views.new_role, name='add_role'),
    url(r'role/delete/$', views.delete_role, name='delete_role'),
    url(r'role/edit/([0-9]+)/$', views.edit_role, name='edit_role'),
    # Role view end
    
    # User view begin
    url(r'user/index/$', views.user_index, name='user_index'),
    url(r'user/add/$', views.new_user, name='add_user'),
    url(r'user/delete/$', views.delete_user, name='delete_user'),
    url(r'user/edit/([0-9]+)/$', views.edit_user, name='edit_user'),
    # User view end

    # Result view begin
    url(r'result/index/$', views.result_index, name='result_index'),
    url(r'result/add/$', views.new_result, name='add_result'),
    url(r'result/delete/$', views.delete_result, name='delete_result'),
    url(r'result/edit/([0-9]+)/$', views.edit_result, name='edit_result'),
    # Result view end
]
