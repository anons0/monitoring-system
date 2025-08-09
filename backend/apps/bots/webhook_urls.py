from django.urls import path
from . import webhook_views

app_name = 'bot_webhooks'

urlpatterns = [
    path('bot/<int:bot_id>/<str:secret>/', webhook_views.bot_webhook, name='bot_webhook'),
]