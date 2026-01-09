"""
Security decorators and utilities for role-based access control
"""
from functools import wraps
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.template.loader import render_to_string


def user_is_approved(user):
    """Check if user is approved to access the system"""
    if not user.is_authenticated:
        return False
    
    # Superusers are always approved
    if user.is_superuser:
        return True
    
    # Check if user has profile and is approved
    if hasattr(user, 'userprofile'):
        return user.userprofile.is_approved
    
    return False


def user_is_admin(user):
    """Check if user is an admin (superuser)"""
    return user.is_authenticated and user.is_superuser


def user_is_manager_or_admin(user):
    """Check if user is manager or admin"""
    if not user.is_authenticated:
        return False
    
    return (user.is_superuser or 
            user.groups.filter(name='Manager').exists())


def user_is_staff_or_above(user):
    """Check if user is staff, manager, or admin"""
    if not user.is_authenticated:
        return False
    
    return (user.is_superuser or 
            user.groups.filter(name__in=['Manager', 'Staff']).exists())


def approved_user_required(view_func):
    """
    Decorator that ensures user is approved before accessing the view
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not user_is_approved(request.user):
            messages.error(request, 'Your account is pending approval. Please contact an administrator.')
            return redirect('users:login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def admin_required(view_func):
    """
    Decorator that requires admin access
    """
    @wraps(view_func)
    @approved_user_required
    @user_passes_test(user_is_admin, login_url='users:login')
    def _wrapped_view(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def manager_or_admin_required(view_func):
    """
    Decorator that requires manager or admin access
    """
    @wraps(view_func)
    @approved_user_required
    @user_passes_test(user_is_manager_or_admin, login_url='users:login')
    def _wrapped_view(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def staff_or_above_required(view_func):
    """
    Decorator that requires staff, manager, or admin access
    """
    @wraps(view_func)
    @approved_user_required
    @user_passes_test(user_is_staff_or_above, login_url='users:login')
    def _wrapped_view(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def role_required(*allowed_roles):
    """
    Flexible decorator that accepts multiple roles
    Usage: @role_required('admin', 'manager')
    """
    def decorator(view_func):
        @wraps(view_func)
        @approved_user_required
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            user_roles = []
            
            if user.is_superuser:
                user_roles.append('admin')
            
            if user.groups.filter(name='Manager').exists():
                user_roles.append('manager')
            
            if user.groups.filter(name='Staff').exists():
                user_roles.append('staff')
            
            if not any(role in user_roles for role in allowed_roles):
                raise PermissionDenied("You don't have permission to access this resource.")
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


class RoleRequiredMixin:
    """
    Mixin for class-based views that require specific roles
    """
    required_roles = []  # List of required roles: ['admin', 'manager', 'staff']
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('users:login')
        
        if not user_is_approved(request.user):
            messages.error(request, 'Your account is pending approval. Please contact an administrator.')
            return redirect('users:login')
        
        user_roles = self.get_user_roles(request.user)
        
        if not any(role in user_roles for role in self.required_roles):
            raise PermissionDenied("You don't have permission to access this resource.")
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_user_roles(self, user):
        """Get list of user's roles"""
        roles = []
        
        if user.is_superuser:
            roles.append('admin')
        
        if user.groups.filter(name='Manager').exists():
            roles.append('manager')
        
        if user.groups.filter(name='Staff').exists():
            roles.append('staff')
        
        return roles


class AdminRequiredMixin(RoleRequiredMixin):
    """Mixin that requires admin access"""
    required_roles = ['admin']


class ManagerOrAdminRequiredMixin(RoleRequiredMixin):
    """Mixin that requires manager or admin access"""
    required_roles = ['admin', 'manager']


class StaffOrAboveRequiredMixin(RoleRequiredMixin):
    """Mixin that requires staff, manager, or admin access"""
    required_roles = ['admin', 'manager', 'staff']