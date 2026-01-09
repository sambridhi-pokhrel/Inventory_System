from django.shortcuts import redirect
from django.http import HttpResponseForbidden

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden("Admin only")
    return wrapper


def manager_or_admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            if request.user.groups.filter(name="Manager").exists():
                return view_func(request, *args, **kwargs)
        return HttpResponseForbidden("Manager or Admin only")
    return wrapper
