from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required(login_url="users:login")
def dashboard(request):
    return render(request, "inventory/dashboard.html")
