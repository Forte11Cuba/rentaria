from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('auth/', include('apps.usuarios.urls')),
    path('dashboard/', include('apps.admin_panel.dueno_urls')),
    path('superadmin/', include('apps.admin_panel.superadmin_urls')),
    path('', include('apps.reservas.urls')),  # flujo cliente — al final por el catch-all <slug>
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
