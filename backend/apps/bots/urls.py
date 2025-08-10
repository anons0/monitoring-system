from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import api_views

router = DefaultRouter()
router.register(r'bots', api_views.BotViewSet, basename='bot')

app_name = 'bots'

urlpatterns = [
    path('', include(router.urls)),
    path('add/', views.add_bot, name='add_bot'),
    path('bulk-update/', views.bulk_update, name='bulk_update'),
    path('<int:bot_id>/test/', views.test_bot, name='test_bot'),
    path('<int:bot_id>/settings/', views.bot_settings, name='bot_settings'),
    path('<int:bot_id>/update-basic-info/', views.update_basic_info, name='update_basic_info'),
    path('<int:bot_id>/update-menu-button/', views.update_menu_button, name='update_menu_button'),
    path('<int:bot_id>/update-commands/', views.update_commands, name='update_commands'),
    path('<int:bot_id>/delete/', views.delete_bot, name='delete_bot'),
    path('api/bots/<int:bot_id>/', api_views.get_bot_detail, name='bot_detail'),
    path('api/bots/<int:bot_id>/update-profile/', api_views.update_bot_profile, name='update_bot_profile'),
]