from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('users:dashboard')
        else:
            return render(request, 'users/login.html', {'error': 'Invalid credentials'})

    return render(request, 'users/login.html')


def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        if User.objects.filter(username=username).exists():
            return render(request, 'users/register.html', {'error': 'Username already exists'})

        user = User.objects.create_user(username=username, email=email, password=password)

        # Assign default role
        staff_group, _ = Group.objects.get_or_create(name='Staff')
        user.groups.add(staff_group)

        return redirect('users:login')

    return render(request, 'users/register.html')


@login_required
def dashboard(request):
    return render(request, 'users/dashboard.html')
