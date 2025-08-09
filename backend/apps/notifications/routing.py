from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/bots/notifications/$', consumers.BotNotificationConsumer.as_asgi()),
    re_path(r'ws/accounts/notifications/$', consumers.AccountNotificationConsumer.as_asgi()),
    re_path(r'ws/notifications/$', consumers.GeneralNotificationConsumer.as_asgi()),
]