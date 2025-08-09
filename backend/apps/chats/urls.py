from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'chats', views.ChatViewSet, basename='chat')

app_name = 'chats'

urlpatterns = [
    path('', include(router.urls)),
    path('bot-chats/', views.bot_chats, name='bot_chats'),
    path('account-chats/', views.account_chats, name='account_chats'),
]