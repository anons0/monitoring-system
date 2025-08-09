from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'bots', views.BotViewSet, basename='bot')

app_name = 'bots'

urlpatterns = [
    path('', include(router.urls)),
    path('add/', views.add_bot, name='add_bot'),
    path('<int:bot_id>/test/', views.test_bot, name='test_bot'),
]