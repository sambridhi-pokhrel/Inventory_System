from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    APPROVAL_STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_approved = models.BooleanField(default=False)
    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_users'
    )

    def __str__(self):
        return f"{self.user.username} - {self.approval_status}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a pending UserProfile whenever a new User is created."""
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()


# ---------------------------------------------------------------------------
# Allauth social login signal
# ---------------------------------------------------------------------------
def handle_social_login(request, sociallogin, **kwargs):
    """
    Called by allauth after a successful Google OAuth handshake.

    - If the user is new: their UserProfile is already created as 'pending'
      by the post_save signal above. We mark the session so the adapter
      can redirect them to the pending-approval page.
    - If the user exists but is not approved: same redirect.
    - If the user is approved (or is superuser): let allauth proceed normally.
    """
    user = sociallogin.user

    # Superusers always pass through
    if user.is_superuser:
        return

    # Ensure profile exists (safety net)
    profile, _ = UserProfile.objects.get_or_create(user=user)

    if not profile.is_approved:
        # Store a flag in the session — the adapter checks this
        request.session['google_pending_approval'] = True


# Connect the signal after the function is defined
try:
    from allauth.socialaccount.signals import social_account_added, pre_social_login
    pre_social_login.connect(handle_social_login)
except ImportError:
    pass