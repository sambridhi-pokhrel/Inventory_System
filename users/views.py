from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group, User
from django.contrib import messages
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.urls import reverse_lazy
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .forms import CustomUserCreationForm, CustomPasswordResetForm
from .models import UserProfile

def is_admin(user):
    return user.is_superuser

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
            # Check if user is approved
            if hasattr(user, 'userprofile') and not user.userprofile.is_approved:
                messages.error(request, 'Your account is pending approval. Please contact an administrator.')
                return render(request, 'users/login.html')
            
            login(request, user)
            return redirect('inventory:item_list')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'users/login.html')

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Don't assign any groups - user needs approval
            user.is_active = True  # Keep user active but not approved
            user.save()
            
            messages.success(request, 'Registration successful! Your account is pending approval by an administrator.')
            return redirect('users:login')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'users/register.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def user_management(request):
    """Admin view to manage user approvals and roles"""
    pending_users = UserProfile.objects.filter(approval_status='pending')
    approved_users = UserProfile.objects.filter(approval_status='approved')
    
    context = {
        'pending_users': pending_users,
        'approved_users': approved_users,
    }
    return render(request, 'users/user_management.html', context)

@login_required
@user_passes_test(is_admin)
def approve_user(request, user_id):
    """Approve a user and assign role"""
    if request.method == 'POST':
        user_profile = get_object_or_404(UserProfile, user_id=user_id)
        role = request.POST.get('role')
        
        # Approve the user
        user_profile.is_approved = True
        user_profile.approval_status = 'approved'
        user_profile.approved_at = timezone.now()
        user_profile.approved_by = request.user
        user_profile.save()
        
        # Assign role
        user = user_profile.user
        if role == 'manager':
            group = Group.objects.get(name='Manager')
            user.groups.add(group)
        elif role == 'staff':
            group = Group.objects.get(name='Staff')
            user.groups.add(group)
        
        messages.success(request, f'User {user.username} has been approved as {role.title()}.')
    
    return redirect('users:user_management')

@login_required
@user_passes_test(is_admin)
def reject_user(request, user_id):
    """Reject a user"""
    user_profile = get_object_or_404(UserProfile, user_id=user_id)
    user_profile.approval_status = 'rejected'
    user_profile.save()
    
    messages.warning(request, f'User {user_profile.user.username} has been rejected.')
    return redirect('users:user_management')

@login_required
def dashboard(request):
    role = "Staff"
    if request.user.is_superuser:
        role = "Admin"
    elif request.user.groups.filter(name="Manager").exists():
        role = "Manager"

    return render(request, "users/dashboard.html", {"role": role})

def logout_view(request):
    logout(request)
    return redirect('users:login')

class CustomPasswordResetView(PasswordResetView):
    form_class = CustomPasswordResetForm
    template_name = 'users/password_reset.html'
    email_template_name = 'users/password_reset_email.html'
    success_url = reverse_lazy('users:password_reset_done')

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'users/password_reset_confirm.html'
    success_url = reverse_lazy('users:password_reset_complete')
