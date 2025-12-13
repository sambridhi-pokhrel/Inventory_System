# inventory/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
    # render a template if you have one, else simple response
    return render(request, 'inventory/dashboard.html', {})
