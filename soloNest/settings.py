"""
Django settings for soloNest project — production-ready via env vars.
"""

from pathlib import Path
import os as _os

BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

SECRET_KEY = _os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-build-fallback-key-replace-in-production-abc123xyz')

DEBUG = _os.environ.get('DJANGO_DEBUG', 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = _os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'core',
    'support',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]

SITE_ID = 1

AUTH_USER_MODEL = 'core.User'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'soloNest.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.unread_notifications',
            ],
        },
    },
]

WSGI_APPLICATION = 'soloNest.wsgi.application'


# Database — use DATABASE_URL env var in production (Render provides this).
# Falls back to SQLite for local dev.

import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}



# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'   # IST — was UTC, fixed
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# IMPORTANT: Django 4.2+ requires BOTH 'default' (media uploads) and
# 'staticfiles' in STORAGES. Missing 'default' causes InvalidStorageError
# when saving any ImageField / FileField.
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = os.getenv('RAILWAY_VOLUME_MOUNT_PATH', os.path.join(BASE_DIR, 'media'))

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'post_login_redirect'
LOGOUT_REDIRECT_URL = 'home'


# ---- Google login (django-allauth) ----
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_LOGIN_METHODS = {'email', 'username'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
    }
}


# ---- Email (env-based). Defaults to console for dev.
EMAIL_BACKEND = _os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = _os.environ.get('DEFAULT_FROM_EMAIL', 'SoloNest <noreply@solonest.test>')
EMAIL_HOST = _os.environ.get('EMAIL_HOST', '')
EMAIL_PORT = int(_os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = _os.environ.get('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
EMAIL_HOST_USER = _os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = _os.environ.get('EMAIL_HOST_PASSWORD', '')


# ---- CSRF Trusted Origins ----
CSRF_TRUSTED_ORIGINS = ['http://127.0.0.1:8000', 'http://localhost:8000', 'https://*.loca.lt', 'https://*.serveo.net', 'https://*.lhr.life', 'https://*.serveousercontent.com', 'https://*.onrender.com']


# ---- Production HTTPS and Security settings ----
# Automatically enabled in production (when DEBUG is False)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000  # 1 Year HSTS
    SECURE_HSTS_PRELOAD = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
else:
    SECURE_SSL_REDIRECT = _os.environ.get('SECURE_SSL_REDIRECT', 'False').lower() in ('true', '1', 'yes')
    SESSION_COOKIE_SECURE = _os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() in ('true', '1', 'yes')
    CSRF_COOKIE_SECURE = _os.environ.get('CSRF_COOKIE_SECURE', 'False').lower() in ('true', '1', 'yes')
    SECURE_HSTS_SECONDS = int(_os.environ.get('SECURE_HSTS_SECONDS', '0'))



# ---- Default primary key field type ----
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ---- Razorpay (test mode) ----
RAZORPAY_KEY_ID = _os.environ.get('RAZORPAY_KEY_ID', 'rzp_test_placeholder')
RAZORPAY_KEY_SECRET = _os.environ.get('RAZORPAY_KEY_SECRET', 'placeholder_secret')


# ---- OTP ----
OTP_DEV_MODE = _os.environ.get('OTP_DEV_MODE', 'False').lower() in ('true', '1', 'yes')

# ---- Fast2SMS (real phone OTP for India) ----
FAST2SMS_API_KEY = _os.environ.get('FAST2SMS_API_KEY', 'IfjFmPSWvyUcYZKg0dwBXln1phCiDT68Ee9G45brJOQAosk7Ht2FcJKDIOExeiYmnVzLNUWQsB6MRhgP')
