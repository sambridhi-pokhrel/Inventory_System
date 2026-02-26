from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from users.views import landing_view

urlpatterns = [
    path("", landing_view, name="landing"),
    path("admin/", admin.site.urls),
    path("users/", include("users.urls")),
    path("inventory/", include("inventory.urls")),
]

# Serve static and media files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
