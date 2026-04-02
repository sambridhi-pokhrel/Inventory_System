"""
Custom allauth social account adapter.
Redirects Google-login users who are not yet approved to a pending page
instead of the normal dashboard.
"""
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import redirect


class InventorySocialAccountAdapter(DefaultSocialAccountAdapter):

    def get_connect_redirect_url(self, request, socialaccount):
        return self._check_approval(request) or super().get_connect_redirect_url(request, socialaccount)

    def get_login_redirect_url(self, request):
        return self._check_approval(request) or super().get_login_redirect_url(request)

    def _check_approval(self, request):
        """Return pending-approval URL if the session flag is set, else None."""
        if request.session.pop('google_pending_approval', False):
            return '/users/pending-approval/'
        return None