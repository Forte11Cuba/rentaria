from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('auth/', include('apps.users.urls')),
    path('dashboard/', include('apps.admin_panel.owner_urls')),
    path('superadmin/', include('apps.admin_panel.superadmin_urls')),
    path('', include('apps.bookings.urls')),  # public client flow — last because of <slug> catch-all
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
