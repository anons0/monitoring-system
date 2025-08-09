from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'accounts', views.AccountViewSet, basename='account')

app_name = 'accounts'

urlpatterns = [
    path('', include(router.urls)),
    path('add/', views.add_account, name='add_account'),
    path('<int:account_id>/login/', views.login_account, name='login_account'),
    path('<int:account_id>/verify/', views.verify_login, name='verify_login'),
    path('<int:account_id>/test/', views.test_account, name='test_account'),
]