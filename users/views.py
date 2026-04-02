from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.contrib import messages
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.urls import reverse_lazy
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from datetime import timedelta
from .forms import CustomUserCreationForm, CustomPasswordResetForm
from .models import UserProfile
from .decorators import approved_user_required, admin_required, role_required
from .utils import UserRoleManager


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user:
            if not UserRoleManager.is_approved(user):
                messages.error(request, 'Your account is pending approval. Please contact an administrator.')
                return render(request, 'users/login.html')
            login(request, user)
            return redirect('users:dashboard')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'users/login.html')


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.is_active = True
            user.save()
            messages.success(request, 'Registration successful! Your account is pending approval by an administrator.')
            return redirect('users:login')
    else:
        form = CustomUserCreationForm()

    return render(request, 'users/register.html', {'form': form})


@login_required
def pending_approval_view(request):
    """
    Shown to Google-login users whose account is still pending admin approval.
    If somehow an approved user lands here, redirect them to dashboard.
    """
    if UserRoleManager.is_approved(request.user):
        return redirect('users:dashboard')
    return render(request, 'users/pending_approval.html')


@admin_required
def user_management(request):
    """Admin view to manage user approvals and roles"""
    pending_users = UserProfile.objects.filter(approval_status='pending')
    approved_users = UserProfile.objects.filter(approval_status='approved')

    total_users = User.objects.filter(is_active=True).count()
    admin_users = User.objects.filter(is_superuser=True)

    context = {
        'pending_users': pending_users,
        'approved_users': approved_users,
        'total_users': total_users,
        'admin_users': admin_users,
    }
    context.update(UserRoleManager.get_context_for_user(request.user))
    return render(request, 'users/user_management.html', context)


@admin_required
def approve_user(request, user_id):
    """Approve a user and assign role"""
    if request.method == 'POST':
        try:
            user_profile = get_object_or_404(UserProfile, user_id=user_id)
        except Exception:
            try:
                user = get_object_or_404(User, id=user_id)
                user_profile, created = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={'approval_status': 'pending', 'is_approved': False}
                )
                if created:
                    messages.info(request, f'Created profile for user {user.username}.')
            except Exception:
                messages.error(request, 'User not found or profile could not be created.')
                return redirect('users:user_management')

        role = request.POST.get('role')

        if role not in ['manager', 'staff']:
            messages.error(request, 'Invalid role selected.')
            return redirect('users:user_management')

        user_profile.is_approved = True
        user_profile.approval_status = 'approved'
        user_profile.approved_at = timezone.now()
        user_profile.approved_by = request.user
        user_profile.save()

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
    """Main dashboard view with role-based content and AI notifications"""
    from inventory.notifications import notification_manager
    notification_manager.add_dashboard_notifications(request)

    role = UserRoleManager.get_user_role(request.user)
    context = UserRoleManager.get_context_for_user(request.user)

    from inventory.models import Item
    total_items = Item.objects.count()
    low_stock_items = Item.objects.filter(quantity__lte=10)
    low_stock_count = low_stock_items.count()
    out_of_stock_count = Item.objects.filter(quantity=0).count()

    total_value = sum(item.price * item.quantity for item in Item.objects.all())
    recent_items = Item.objects.order_by('-id')[:5]
    notification_summary = notification_manager.get_notification_summary()

    import json
    from django.db.models import Sum
    from django.db.models.functions import TruncDate
    from inventory.models import Transaction

    today_date = timezone.now().date()
    seven_days_ago = today_date - timedelta(days=6)

    sales_by_day = (
        Transaction.objects.filter(
            transaction_type='SALE',
            payment_status='PAID',
            timestamp__date__gte=seven_days_ago,
        )
        .annotate(day=TruncDate('timestamp'))
        .values('day')
        .annotate(total=Sum('total_amount'))
        .order_by('day')
    )
    day_map = {r['day']: float(r['total']) for r in sales_by_day}
    mini_labels = [(seven_days_ago + timedelta(days=i)).strftime('%a') for i in range(7)]
    mini_data = [day_map.get(seven_days_ago + timedelta(days=i), 0) for i in range(7)]

    recent_sales_total = Transaction.objects.filter(
        transaction_type='SALE', payment_status='PAID'
    ).aggregate(t=Sum('total_amount'))['t'] or 0

    recent_purchases_total = Transaction.objects.filter(
        transaction_type='PURCHASE', payment_status='PAID'
    ).aggregate(t=Sum('total_amount'))['t'] or 0

    context.update({
        'user': request.user,
        'total_items': total_items,
        'low_stock_items': low_stock_count,
        'out_of_stock_items': out_of_stock_count,
        'total_value': total_value,
        'recent_items': recent_items,
        'low_stock_items_list': low_stock_items[:5],
        'notification_summary': notification_summary,
        'mini_labels': json.dumps(mini_labels),
        'mini_data': json.dumps(mini_data),
        'recent_sales_total': recent_sales_total,
        'recent_purchases_total': recent_purchases_total,
    })

    if UserRoleManager.is_admin(request.user):
        context.update({
            'pending_users': UserProfile.objects.filter(approval_status='pending').count(),
            'total_users': UserProfile.objects.filter(approval_status='approved').count(),
        })

    return render(request, 'users/dashboard.html', context)


def logout_view(request):
    """Logout — redirects to landing page"""
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('landing')


class CustomPasswordResetView(PasswordResetView):
    form_class = CustomPasswordResetForm
    template_name = 'users/password_reset.html'
    email_template_name = 'users/password_reset_email.html'
    success_url = reverse_lazy('users:password_reset_done')


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'users/password_reset_confirm.html'
    success_url = reverse_lazy('users:password_reset_complete')


def landing_view(request):
    """Landing page — redirects authenticated users to dashboard"""
    if request.user.is_authenticated:
        return redirect('users:dashboard')
    return render(request, 'landing.html')


@approved_user_required
def profile_view(request):
    """User profile page — read-only, accessible to all approved roles"""
    from inventory.models import Transaction, Item
    from django.db.models import Sum

    user = request.user
    role = UserRoleManager.get_user_role(user)

    try:
        profile = user.userprofile
    except Exception:
        profile = None

    transactions_performed = Transaction.all_objects.filter(performed_by=user).count()
    items_created = Item.all_objects.filter(created_by=user).count()
    sales_total = Transaction.all_objects.filter(
        performed_by=user, transaction_type='SALE', payment_status='PAID'
    ).aggregate(t=Sum('total_amount'))['t'] or 0
    purchases_total = Transaction.all_objects.filter(
        performed_by=user, transaction_type='PURCHASE', payment_status='PAID'
    ).aggregate(t=Sum('total_amount'))['t'] or 0

    context = UserRoleManager.get_context_for_user(user)
    context.update({
        'profile': profile,
        'role': role,
        'transactions_performed': transactions_performed,
        'items_created': items_created,
        'sales_total': sales_total,
        'purchases_total': purchases_total,
    })
    return render(request, 'users/profile.html', context)