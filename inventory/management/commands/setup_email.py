"""
Management command: setup_email
Usage:
  python manage.py setup_email --test-email you@gmail.com
  python manage.py setup_email --update-users admin=admin@example.com manager=mgr@example.com
"""

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Test email configuration and optionally update user email addresses'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-email',
            type=str,
            help='Send a test email to this address to verify SMTP is working',
        )
        parser.add_argument(
            '--update-users',
            nargs='+',
            type=str,
            help='Update user emails in format: username=email (e.g. admin=admin@gmail.com)',
        )
        parser.add_argument(
            '--list-users',
            action='store_true',
            help='List all users and their current email addresses',
        )

    def handle(self, *args, **options):
        if options['list_users']:
            self._list_users()

        if options['update_users']:
            self._update_users(options['update_users'])

        if options['test_email']:
            self._send_test_email(options['test_email'])

        if not any([options['list_users'], options['update_users'], options['test_email']]):
            self.stdout.write(self.style.WARNING(
                'No action specified. Use --help to see available options.\n'
                'Examples:\n'
                '  python manage.py setup_email --list-users\n'
                '  python manage.py setup_email --test-email you@gmail.com\n'
                '  python manage.py setup_email --update-users admin=admin@gmail.com\n'
            ))

    def _list_users(self):
        self.stdout.write(self.style.HTTP_INFO('\n── Current Users ──────────────────────'))
        users = User.objects.all().order_by('username')
        for user in users:
            role = 'superuser' if user.is_superuser else (
                'manager' if user.groups.filter(name='Manager').exists() else 'staff'
            )
            email_status = '✓' if user.email else '✗ (no email)'
            self.stdout.write(
                f"  {user.username:<20} {role:<12} {email_status} {user.email}"
            )
        self.stdout.write('')

    def _update_users(self, user_args):
        self.stdout.write(self.style.HTTP_INFO('\n── Updating User Emails ────────────────'))
        for arg in user_args:
            if '=' not in arg:
                self.stdout.write(self.style.ERROR(f'  Invalid format: {arg} (use username=email)'))
                continue
            username, email = arg.split('=', 1)
            try:
                user = User.objects.get(username=username.strip())
                old_email = user.email or '(none)'
                user.email = email.strip()
                user.save()
                self.stdout.write(self.style.SUCCESS(
                    f'  ✓ {username}: {old_email} → {email.strip()}'
                ))
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'  ✗ User not found: {username}'))
        self.stdout.write('')

    def _send_test_email(self, recipient):
        self.stdout.write(self.style.HTTP_INFO(f'\n── Sending Test Email to {recipient} ──'))
        backend = settings.EMAIL_BACKEND
        self.stdout.write(f'  Backend: {backend}')

        if 'console' in backend:
            self.stdout.write(self.style.WARNING(
                '  ⚠ Console backend active — email will print below, not actually send.\n'
                '  To enable real email, create a .env file with EMAIL_HOST_USER and EMAIL_HOST_PASSWORD.\n'
                '  See .env.example for instructions.\n'
            ))

        try:
            send_mail(
                subject='✅ Inventory System — Email Test',
                message=(
                    'This is a test email from your Inventory Management System.\n\n'
                    'If you received this, your email configuration is working correctly!\n\n'
                    'You can now use password reset and email notifications.\n\n'
                    '— Inventory System'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f'  ✓ Test email sent successfully to {recipient}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Failed to send email: {e}'))
            self.stdout.write(self.style.WARNING(
                '\n  Troubleshooting:\n'
                '  1. Check EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in your .env file\n'
                '  2. Make sure you are using a Gmail App Password, not your real password\n'
                '  3. Enable 2-Step Verification on your Google account first\n'
                '  4. Generate App Password at: https://myaccount.google.com/apppasswords\n'
            ))
        self.stdout.write('')
