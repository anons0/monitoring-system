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
    path('<int:bot_id>/test/', views.test_bot, name='test_bot'),
    path('api/bots/<int:bot_id>/', api_views.get_bot_detail, name='bot_detail'),
    path('api/bots/<int:bot_id>/update-profile/', api_views.update_bot_profile, name='update_bot_profile'),
]