from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/bots/', include('apps.bots.urls')),
    path('api/accounts/', include('apps.accounts.urls')),
    path('api/messages/', include('apps.messages.urls')),
    path('api/chats/', include('apps.chats.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('webhook/', include('apps.bots.webhook_urls')),
    path('', include('apps.core.urls')),  # Main application interface
]

# WebSocket URLs are handled by ASGI in asgi.py

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)