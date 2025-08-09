import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(BASE_DIR), '.env'))

def get_env_variable(var_name, default=None, cast_to=str):
    """Get environment variable with optional casting"""
    value = os.environ.get(var_name, default)
    if value is None:
        return None
    if cast_to == bool:
        return value.lower() in ('true', '1', 'yes', 'on')
    elif cast_to == int:
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    return cast_to(value)

SECRET_KEY = get_env_variable('SECRET_KEY', 'dev-secret-key-change-in-production')
DEBUG = get_env_variable('DEBUG', True, bool)

ALLOWED_HOSTS = ['*']

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'corsheaders',
    'channels',
]

LOCAL_APPS = [
    'apps.bots',
    'apps.accounts',
    'apps.messages',
    'apps.chats',
    'apps.notifications',
    'apps.core',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'project.wsgi.application'
ASGI_APPLICATION = 'project.asgi.application'

# Database - Supabase PostgreSQL or SQLite for development
db_name = get_env_variable('DB_NAME')
if db_name:
    # Production/Supabase PostgreSQL
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': db_name,
            'USER': get_env_variable('DB_USER'),
            'PASSWORD': get_env_variable('DB_PASSWORD'),
            'HOST': get_env_variable('DB_HOST'),
            'PORT': get_env_variable('DB_PORT', '5432', int),
            'OPTIONS': {
                'sslmode': 'require',
            },
        }
    }
else:
    # Development SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }

# Redis for Channels
redis_url = get_env_variable('REDIS_URL')
redis_host = get_env_variable('REDIS_HOST', 'localhost')
redis_port = get_env_variable('REDIS_PORT', 6379, int)

# Use Redis for channels (better for production)
if redis_url:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [redis_url],
            },
        },
    }
else:
    # Fallback to Redis with separate host/port
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [(redis_host, redis_port)],
            },
        },
    }

# WebSocket configuration
ASGI_APPLICATION = 'project.asgi.application'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Security settings
FERNET_KEY = get_env_variable('FERNET_KEY', 'temp-key-generate-real-key-for-production')
CORS_ALLOW_ALL_ORIGINS = True

# Webhook configuration
WEBHOOK_BASE_URL = get_env_variable('WEBHOOK_BASE_URL', 'https://your-domain.com')

# Authentication settings
LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/admin/'
LOGOUT_REDIRECT_URL = '/admin/login/'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'bots': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'accounts': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}