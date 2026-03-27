from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file if python-dotenv is available (optional but recommended)
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / '.env')
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-j*@n4bm0(-g(u5s9g^7+8v7q88$_nii46psh%xs-ef_=0v$djw'

DEBUG = True
ALLOWED_HOSTS = []

# Custom error handlers
handler403 = 'django.views.defaults.permission_denied'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'users',
    'inventory',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'inventory_system.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.csrf',
            ],
        },
    },
]

WSGI_APPLICATION = 'inventory_system.wsgi.application'

# MySQL database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'inventory_system',
        'USER': 'root',
        'PASSWORD': 'dalluBhakunde@11',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files (User uploaded content)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

LOGIN_URL = '/users/login/'
LOGIN_REDIRECT_URL = '/users/dashboard/'
LOGOUT_REDIRECT_URL = '/users/login/'

# ── Email Configuration ───────────────────────────────────────────────────────
# Reads credentials from environment variables or .env file.
# To use Gmail SMTP:
#   1. Enable 2-Step Verification on your Google account
#   2. Generate an App Password at https://myaccount.google.com/apppasswords
#   3. Create a .env file in the project root (same folder as manage.py):
#        EMAIL_HOST_USER=yourgmail@gmail.com
#        EMAIL_HOST_PASSWORD=your_16_char_app_password
#   4. Restart the server

_email_user = os.environ.get('EMAIL_HOST_USER', '')
_email_pass = os.environ.get('EMAIL_HOST_PASSWORD', '')

if _email_user and _email_pass:
    # Real SMTP — sends actual emails
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = _email_user
    EMAIL_HOST_PASSWORD = _email_pass
    DEFAULT_FROM_EMAIL = f'Inventory System <{_email_user}>'
    SERVER_EMAIL = _email_user
else:
    # Fallback — prints emails to the console (safe for development)
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    DEFAULT_FROM_EMAIL = 'Inventory System <noreply@inventorysystem.com>'

# Unsplash API Configuration for automatic product image fetching
# Get your free API key from: https://unsplash.com/developers
# Note: If no API key is configured, system uses Lorem Picsum (free placeholder images)
# Lorem Picsum: https://picsum.photos/ - No API key needed, works automatically
UNSPLASH_ACCESS_KEY = 'PSYRx2PeCWu_Puu_FgIIC-H4KdexJ7gr6jPipGnS-ig'
UNSPLASH_API_URL = 'https://api.unsplash.com/search/photos'

# Payment Gateway Configuration
# ==============================

# Khalti Payment Gateway
# Get your keys from: https://khalti.com/
# Test Mode: Use test keys for development
# Live Mode: Use live keys for production
# IMPORTANT: Replace these with your actual Khalti keys from https://test-admin.khalti.com/
KHALTI_PUBLIC_KEY = None  # Set to None to disable Khalti
KHALTI_SECRET_KEY = None  # Set to None to disable Khalti
KHALTI_VERIFY_URL = 'https://khalti.com/api/v2/payment/verify/'
KHALTI_ENABLED = False  # Set to True when you have valid keys

# eSewa Payment Gateway
# Get your credentials from: https://esewa.com.np/
# Test Mode: Use test merchant ID for development
# Live Mode: Use live merchant ID for production
ESEWA_MERCHANT_ID = 'EPAYTEST'  # Test merchant ID (replace with your merchant ID)
ESEWA_SUCCESS_URL = 'http://127.0.0.1:8000/inventory/payment/esewa/verify/'
ESEWA_FAILURE_URL = 'http://127.0.0.1:8000/inventory/payment/esewa/failure/'
ESEWA_PAYMENT_URL = 'https://uat.esewa.com.np/epay/main'  # Test URL
ESEWA_VERIFY_URL = 'https://uat.esewa.com.np/epay/transrec'  # Test verification URL
ESEWA_ENABLED = False  # Set to True when eSewa test environment is accessible

# For production, use:
# ESEWA_PAYMENT_URL = 'https://esewa.com.np/epay/main'
# ESEWA_VERIFY_URL = 'https://esewa.com.np/epay/transrec'

# Payment Gateway Simulation Mode (for testing when gateways are unavailable)
PAYMENT_SIMULATION_MODE = True  # Set to False in production

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'