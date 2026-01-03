from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required, user_passes_test

def is_admin(user):
    return user.groups.filter(name='Admin').exists()

def is_manager(user):
    return user.groups.filter(name='Manager').exists()

def is_staff(user):
    return user.groups.filter(name='Staff').exists()

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('users:dashboard')
        else:
            return render(request, 'users/login.html', {'error': 'Invalid credentials'})

    return render(request, 'users/login.html')


def register_view(request):
    if request.method == 'POST':
        from django.contrib.auth.models import User
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(username=username).exists():
            return render(request, 'users/register.html', {'error': 'Username already exists'})

        user = User.objects.create_user(username=username, email=email, password=password)

        staff_group = Group.objects.get(name='Staff')
        user.groups.add(staff_group)

        return redirect('users:login')

    return render(request, 'users/register.html')

@login_required
def dashboard(request):
    role = "Staff"
    if request.user.groups.filter(name="Admin").exists():
        role = "Admin"
    elif request.user.groups.filter(name="Manager").exists():
        role = "Manager"

    return render(request, "users/dashboard.html", {"role": role})


def logout_view(request):
    logout(request)
    return redirect('users:login')
