"""
SCALE.Core - Django Configuration
Official Master Architecture Implementation
Project Owner: Hemanth Kumar H A
Platform: Supply Chain Analytics & Logistics Engine
"""

import os
import sys
from pathlib import Path
from decimal import Decimal

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / 'apps'))

# Core Security
SECRET_KEY = os.environ.get(
    'SCALE_SECRET_KEY',
    'scale-core-enterprise-insecure-dev-key-change-in-production-9a8b7c6d5e4f'
)
DEBUG = os.environ.get('SCALE_DEBUG', 'True').lower() in ('true', '1', 't')
ALLOWED_HOSTS = os.environ.get('SCALE_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Application definition
INSTALLED_APPS = [
    # Core Django Framework
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-Party Libraries
    'rest_framework',

    # SCALE.Core Modular Enterprise Applications
    'apps.core.apps.CoreConfig',
    'apps.accounts.apps.AccountsConfig',
    'apps.audit.apps.AuditConfig',
    'apps.notifications.apps.NotificationsConfig',
    'apps.inventory.apps.InventoryConfig',
    'apps.sales.apps.SalesConfig',
    'apps.suppliers.apps.SuppliersConfig',
    'apps.procurement.apps.ProcurementConfig',
    'apps.logistics.apps.LogisticsConfig',
    'apps.forecasting.apps.ForecastingConfig',
    'apps.finance.apps.FinanceConfig',
    'apps.intelligence.apps.IntelligenceConfig',
    'apps.automation.apps.AutomationConfig',
    'apps.system_health.apps.SystemHealthConfig',
    'apps.reporting.apps.ReportingConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # SCALE.Core Custom Enterprise Security Middleware
    'apps.accounts.middleware.SessionSecurityMiddleware',
]

ROOT_URLCONF = 'scale_core.urls'

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
                # Enterprise Hybrid Design System Context Processor
                'apps.core.context_processors.enterprise_theme',
            ],
        },
    },
]

WSGI_APPLICATION = 'scale_core.wsgi.application'

# Custom User Model (Mandatory)
AUTH_USER_MODEL = 'accounts.SCALEUser'

# Database Configuration
# Default: SQLite3 for agile local testing; production uses PostgreSQL 16
USE_POSTGRES = os.environ.get('SCALE_USE_POSTGRES', 'False').lower() in ('true', '1')

if USE_POSTGRES:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'scale_core_prod'),
            'USER': os.environ.get('DB_USER', 'scale_user'),
            'PASSWORD': os.environ.get('DB_PASSWORD', 'scale_password'),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
            'CONN_MAX_AGE': 600,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password Validation & Security Policies
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 10}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Authentication URL Routing
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Internationalization & Localization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static & Media Asset Pipeline
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Django REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# Local AI Engine (Ollama + Llama 3.2)
OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://127.0.0.1:11434')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3.2')
OLLAMA_TIMEOUT_SECONDS = int(os.environ.get('OLLAMA_TIMEOUT_SECONDS', '30'))

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Official Identity & Attribution
SCALE_PLATFORM = {
    'NAME': 'SCALE.Core',
    'FULL_NAME': 'Supply Chain Analytics & Logistics Engine',
    'AUTHOR': 'Hemanth Kumar H A',
    'VERSION': '1.0.0-rc1',
    'PHILOSOPHY': 'One human supervises. SCALE.Core operates.',
}
