# inventory_system/urls.py
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

# simple dashboard placeholder (replace with real template later)
@login_required
def dashboard(request):
    return HttpResponse(f"Hello {request.user.username}. Role: {getattr(request.user, 'role', 'N/A')}")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),         # users app
    path('', include('inventory.urls')),           # inventory app (root)
    path('dashboard/', dashboard, name='dashboard'),
]