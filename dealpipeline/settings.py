from pathlib import Path
import os
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')


def env_bool(name, default=False):
    return os.environ.get(name, str(default)).lower() in ('true', '1', 'yes')


def env_list(name, default=''):
    raw = os.environ.get(name, default)
    return [v.strip() for v in raw.split(',') if v.strip()]


_INSECURE_SECRET_KEYS = {'', 'change-me', 'django-insecure-change-me-in-production'}
DEBUG = env_bool('DEBUG', False)
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-change-me-in-production')
# JWTs are signed with SECRET_KEY, so a guessable key lets anyone forge a login.
if not DEBUG and SECRET_KEY in _INSECURE_SECRET_KEYS:
    raise ImproperlyConfigured('SECRET_KEY must be set to a unique secret value when DEBUG is false.')
HOST = os.environ.get('HOST', 'http://localhost:8000')
ALLOWED_HOSTS = env_list('ALLOWED_HOSTS', '127.0.0.1,localhost')
TIME_ZONE = os.environ.get('TIME_ZONE', 'UTC')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_spectacular',
    'api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'dealpipeline.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'dealpipeline.wsgi.application'

# --- Database ---
# USE_SQLITE=true forces SQLite regardless of DATABASE_ENGINE.
# DATABASE_ENGINE=postgres switches to Postgres when USE_SQLITE is not set.
_use_sqlite = env_bool('USE_SQLITE', False)
_db_engine = os.environ.get('DATABASE_ENGINE', 'sqlite').lower()

if not _use_sqlite and _db_engine == 'postgres':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('POSTGRES_DB', 'dealpipeline'),
            'USER': os.environ.get('POSTGRES_USER', 'postgres'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'postgres'),
            'HOST': os.environ.get('POSTGRES_HOST', 'db'),
            'PORT': os.environ.get('POSTGRES_PORT', '5432'),
            'OPTIONS': {
                'sslmode': os.environ.get('POSTGRES_SSLMODE', 'prefer'),
            },
            'CONN_MAX_AGE': int(os.environ.get('DB_CONN_MAX_AGE', '60')),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / os.environ.get('SQLITE_NAME', 'db.sqlite3'),
        }
    }

# --- Cache ---
# Redis whenever REDIS_CACHE_URL is set, and by default outside DEBUG. In DEBUG with no Redis
# configured, an in-process cache is used instead: a Redis that isn't there makes every request
# sit through a failed connection. (Don't run that in production: each gunicorn worker would
# keep its own copy and invalidation would not reach the others.)
_cache_url = os.environ.get('REDIS_CACHE_URL')
_cache_location = os.environ.get('CACHE_LOCATION', 'dealpipeline-cache')
_cache_timeout = int(os.environ.get('CACHE_TIMEOUT', '300'))

if _cache_url or not DEBUG:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': _cache_url or 'redis://redis:6379/3',
            'KEY_PREFIX': _cache_location,
            'TIMEOUT': _cache_timeout,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'IGNORE_EXCEPTIONS': True,
            },
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': _cache_location,
            'TIMEOUT': _cache_timeout,
        }
    }

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# --- CORS ---
# Any origin is allowed only in DEBUG. In production list the frontend origin(s) in
# CORS_ALLOWED_ORIGINS (comma separated, with scheme, e.g. https://app.example.com).
CORS_ALLOW_ALL_ORIGINS = env_bool('CORS_ALLOW_ALL_ORIGINS', DEBUG)
CORS_ALLOWED_ORIGINS = env_list('CORS_ALLOWED_ORIGINS', 'http://127.0.0.1:8000,http://localhost:8000')
CSRF_TRUSTED_ORIGINS = env_list('CSRF_TRUSTED_ORIGINS', '')

# --- DRF ---
# Endpoints require a valid JWT (obtain one at /api/token). Set API_REQUIRE_AUTH=false only
# as a temporary escape hatch; /api/v1/health stays public either way.
_require_auth = env_bool('API_REQUIRE_AUTH', True)

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated' if _require_auth else 'rest_framework.permissions.AllowAny',
    ],
    # Login attempts are throttled per IP and per target username (see api/auth.py).
    # Behind a reverse proxy set NUM_PROXIES to the number of proxies in front of the app so the
    # client IP is read correctly from X-Forwarded-For.
    'DEFAULT_THROTTLE_RATES': {
        'login': os.environ.get('THROTTLE_LOGIN_PER_IP', '20/min'),
        'login_user': os.environ.get('THROTTLE_LOGIN_PER_USER', '5/min'),
    },
    'NUM_PROXIES': int(os.environ['NUM_PROXIES']) if os.environ.get('NUM_PROXIES') else None,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    # Amounts are stored as exact decimals but keep going out as JSON numbers, as they did
    # when they were floats, so existing frontends keep working.
    'COERCE_DECIMAL_TO_STRING': False,
}

# API documentation (/api/docs/, /api/schema/) follows the same login rule as the API.
SPECTACULAR_SETTINGS = {
    'TITLE': 'Deal Pipeline API',
    'DESCRIPTION': 'Deal tracking, grants and staff development records. '
                   'Responses are wrapped in {"status", "message", "data"}; lists add "pagination".',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'PREPROCESSING_HOOKS': ['api.schema.drop_trailing_slash_duplicates'],
    'SERVE_PERMISSIONS': [
        'rest_framework.permissions.IsAuthenticated' if _require_auth else 'rest_framework.permissions.AllowAny',
    ],
}

# List endpoints are paginated: ?page=1&page_size=100. Without params the first
# API_DEFAULT_PAGE_SIZE rows are returned, with a top-level "pagination" object in the response.
API_DEFAULT_PAGE_SIZE = int(os.environ.get('API_DEFAULT_PAGE_SIZE', '500'))
API_MAX_PAGE_SIZE = int(os.environ.get('API_MAX_PAGE_SIZE', '1000'))

# Uploaded evidence files: allowed extensions and maximum size.
UPLOAD_ALLOWED_EXTENSIONS = env_list(
    'UPLOAD_ALLOWED_EXTENSIONS', 'pdf,doc,docx,xls,xlsx,ppt,pptx,csv,txt,png,jpg,jpeg')
UPLOAD_MAX_MB = int(os.environ.get('UPLOAD_MAX_MB', '10'))
DATA_UPLOAD_MAX_MEMORY_SIZE = UPLOAD_MAX_MB * 1024 * 1024 * 2
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024

# Path of the Django admin site (include the trailing slash). Change it to move the admin.
ADMIN_URL = os.environ.get('ADMIN_URL', 'admin/').lstrip('/')

# --- Password validation ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- i18n ---
LANGUAGE_CODE = 'en-us'
USE_I18N = True
USE_TZ = True

# --- Static / Media ---
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

STORAGES = {
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Email ---
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '465'))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = env_bool('EMAIL_USE_TLS', False)
EMAIL_USE_SSL = env_bool('EMAIL_USE_SSL', True)
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'webmaster@localhost')

# --- Logging ---
_log_level = os.environ.get('LOG_LEVEL', 'INFO')
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {'format': '{levelname} {asctime} {name} {message}', 'style': '{'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'simple'},
    },
    'root': {'handlers': ['console'], 'level': _log_level},
    'loggers': {
        'django': {'handlers': ['console'], 'level': _log_level, 'propagate': False},
        'api': {'handlers': ['console'], 'level': _log_level, 'propagate': False},
    },
}

# --- Security (production only) ---
if not DEBUG:
    # HTTPS is enforced and HSTS is on unless explicitly turned off. The health check path stays
    # reachable over plain HTTP so container/platform probes keep working.
    SECURE_SSL_REDIRECT = env_bool('SECURE_SSL_REDIRECT', True)
    SECURE_REDIRECT_EXEMPT = [r'^api/v1/health/?$']
    SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', '31536000'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', False)
    SECURE_HSTS_PRELOAD = env_bool('SECURE_HSTS_PRELOAD', False)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
