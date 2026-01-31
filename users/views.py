from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.contrib import messages
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.urls import reverse_lazy
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from .forms import CustomUserCreationForm, CustomPasswordResetForm
from .models import UserProfile
from .decorators import (
    approved_user_required, 
    admin_required, 
    role_required
)
from .utils import UserRoleManager


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        print(f"DEBUG: Login attempt - Username: {username}, Password: {'*' * len(password) if password else 'None'}")

        user = authenticate(request, username=username, password=password)
        print(f"DEBUG: Authentication result: {user}")
        
        if user:
            # Check if user is approved
            is_approved = UserRoleManager.is_approved(user)
            print(f"DEBUG: User approval status: {is_approved}")
            
            if not is_approved:
                messages.error(request, 'Your account is pending approval. Please contact an administrator.')
                return render(request, 'users/login.html')
            
            login(request, user)
            print(f"DEBUG: Login successful, redirecting to dashboard")
            return redirect('users:dashboard')
        else:
            print(f"DEBUG: Authentication failed for username: {username}")
            messages.error(request, 'Invalid username or password.')

    return render(request, 'users/login.html')


def simple_login_view(request):
    """Simple debug login view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user:
            # Check if user is approved
            if not UserRoleManager.is_approved(user):
                messages.error(request, 'Your account is pending approval. Please contact an administrator.')
                return render(request, 'users/simple_login.html')
            
            login(request, user)
            messages.success(request, f'Successfully logged in as {user.username}!')
            return redirect('users:dashboard')
        else:
            messages.error(request, f'Invalid credentials for username: {username}')

    return render(request, 'users/simple_login.html')


def basic_login_view(request):
    """Basic login view with minimal styling"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user:
            # Check if user is approved
            if not UserRoleManager.is_approved(user):
                messages.error(request, 'Your account is pending approval. Please contact an administrator.')
                return render(request, 'users/basic_login.html')
            
            login(request, user)
            messages.success(request, f'Successfully logged in as {user.username}!')
            return redirect('users:dashboard')
        else:
            messages.error(request, f'Authentication failed for username: {username}')

    return render(request, 'users/basic_login.html')


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


@admin_required
def user_management(request):
    """Admin view to manage user approvals and roles"""
    pending_users = UserProfile.objects.filter(approval_status='pending')
    approved_users = UserProfile.objects.filter(approval_status='approved')
    
    context = {
        'pending_users': pending_users,
        'approved_users': approved_users,
    }
    context.update(UserRoleManager.get_context_for_user(request.user))
    return render(request, 'users/user_management.html', context)


@admin_required
def approve_user(request, user_id):
    """Approve a user and assign role"""
    if request.method == 'POST':
        user_profile = get_object_or_404(UserProfile, user_id=user_id)
        role = request.POST.get('role')
        
        if role not in ['manager', 'staff']:
            messages.error(request, 'Invalid role selected.')
            return redirect('users:user_management')
        
        # Approve the user
        user_profile.is_approved = True
        user_profile.approval_status = 'approved'
        user_profile.approved_at = timezone.now()
        user_profile.approved_by = request.user
        user_profile.save()
        
        # Assign role using utility function
        UserRoleManager.assign_role(user_profile.user, role)
        
        messages.success(request, f'User {user_profile.user.username} has been approved as {role.title()}.')
    
    return redirect('users:user_management')


@admin_required
def reject_user(request, user_id):
    """Reject a user"""
    user_profile = get_object_or_404(UserProfile, user_id=user_id)
    user_profile.approval_status = 'rejected'
    user_profile.save()
    
    messages.warning(request, f'User {user_profile.user.username} has been rejected.')
    return redirect('users:user_management')


@approved_user_required
def dashboard(request):
    """Main dashboard view with role-based content"""
    # Get user role and context
    role = UserRoleManager.get_user_role(request.user)
    context = UserRoleManager.get_context_for_user(request.user)
    
    # Get inventory statistics
    from inventory.models import Item
    total_items = Item.objects.count()
    low_stock_items = Item.objects.filter(quantity__lte=10)
    low_stock_count = low_stock_items.count()
    out_of_stock_count = Item.objects.filter(quantity=0).count()
    
    # Calculate total value safely
    total_value = 0
    for item in Item.objects.all():
        total_value += item.price * item.quantity
    
    # Get recent items (last 5 added)
    recent_items = Item.objects.order_by('-id')[:5]
    
    # Update context with dashboard data
    context.update({
        "user": request.user,
        "total_items": total_items,
        "low_stock_count": low_stock_count,
        "out_of_stock_count": out_of_stock_count,
        "total_value": total_value,
        "recent_items": recent_items,
        "low_stock_items": low_stock_items[:5],  # Show top 5 low stock items
    })
    
    # Add admin-specific data
    if UserRoleManager.is_admin(request.user):
        pending_users = UserProfile.objects.filter(approval_status='pending').count()
        total_users = UserProfile.objects.filter(approval_status='approved').count()
        context.update({
            "pending_users": pending_users,
            "total_users": total_users,
        })

    return render(request, "users/dashboard.html", context)


def logout_view(request):
    """Simple logout view that works with GET requests"""
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('users:login')


class CustomPasswordResetView(PasswordResetView):
    form_class = CustomPasswordResetForm
    template_name = 'users/password_reset.html'
    email_template_name = 'users/password_reset_email.html'
    success_url = reverse_lazy('users:password_reset_done')


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'users/password_reset_confirm.html'
    success_url = reverse_lazy('users:password_reset_complete')
