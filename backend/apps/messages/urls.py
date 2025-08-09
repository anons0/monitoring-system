from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'messages', views.MessageViewSet, basename='message')

app_name = 'messages'

urlpatterns = [
    path('', include(router.urls)),
    path('send/', views.send_message, name='send_message'),
    path('<int:message_id>/edit/', views.edit_message, name='edit_message'),
    path('<int:message_id>/delete/', views.delete_message, name='delete_message'),
]