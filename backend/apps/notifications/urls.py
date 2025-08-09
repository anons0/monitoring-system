from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'notifications', views.NotificationViewSet)

app_name = 'notifications'

urlpatterns = [
    path('', include(router.urls)),
    path('unread-counts/', views.unread_counts, name='unread_counts'),
]