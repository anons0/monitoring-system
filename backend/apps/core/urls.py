from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('bots/', views.bots_view, name='bots'),
    path('accounts/', views.accounts_view, name='accounts'),
    path('chat/<int:chat_id>/', views.chat_view, name='chat'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    
    # Bot management URLs
    path('bots/add/', views.add_bot_view, name='add_bot'),
    path('bots/<int:bot_id>/start/', views.start_bot, name='start_bot'),
    path('bots/<int:bot_id>/stop/', views.stop_bot, name='stop_bot'),
    path('bots/<int:bot_id>/test/', views.test_bot, name='test_bot'),
]