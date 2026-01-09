from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

def root_redirect(request):
    if request.user.is_authenticated:
        return redirect('users:dashboard')
    return redirect('users:login')

urlpatterns = [
    path("", root_redirect, name="root"),
    path("admin/", admin.site.urls),
    path("users/", include("users.urls")),
    path("inventory/", include("inventory.urls")),
]
