from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('bots/', views.bots_view, name='bots'),
    path('chats/', views.chats_view, name='chats'),
    path('chat/<int:chat_id>/', views.chat_view, name='chat'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    
    # User management URLs (admin only)
    path('users/', views.user_management_view, name='user_management'),
    path('users/add/', views.add_user_view, name='add_user'),
    path('users/<int:user_id>/delete/', views.delete_user_view, name='delete_user'),
    
    # Bot management URLs
    path('bots/add/', views.add_bot_view, name='add_bot'),
    path('bots/<int:bot_id>/start/', views.start_bot, name='start_bot'),
    path('bots/<int:bot_id>/stop/', views.stop_bot, name='stop_bot'),
    path('bots/<int:bot_id>/test/', views.test_bot, name='test_bot'),
]