from django.http import HttpResponseForbidden

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.groups.filter(name="Admin").exists():
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden("Admin access only")
    return wrapper


def manager_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.groups.filter(name__in=["Admin", "Manager"]).exists():
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden("Manager access only")
    return wrapper


def staff_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden("Login required")
    return wrapper
