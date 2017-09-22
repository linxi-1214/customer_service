from django.conf.urls import url

from customer_service import views

urlpatterns = [
    url(r'player/index/', views.new_player, name='index'),
    url(r'login/', views.user_login, name='login'),
    url(r'user-profile', views.user_profile, name='profile'),
    url(r'user-settings', views.user_settings, name='user_settings'),
    url(r'player-add/$', views.new_player, name='add_player'),
    url(r'message-add/$', views.new_message, name='add_message'),
    url(r'message-list/$', views.message_list, name='message'),
    # 游戏 BEGIN
    url(r'game/index/$', views.game_index, name='game_index'),
    url(r'game/add/$', views.new_game, name='add_game'),
    url(r'game/delete/$', views.delete_game, name='delete_game'),
    url(r'game/edit/([0-9]+)/$', views.edit_game, name='edit_game'),
]
