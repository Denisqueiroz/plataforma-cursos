import os
from pathlib import Path
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

# =====================================================
# BASE PATHS
# =====================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# Carrega variáveis do .env
load_dotenv(BASE_DIR / '.env')

# =====================================================
# SEGURANÇA E AMBIENTE
# =====================================================

# DEBUG
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# SECRET_KEY
SECRET_KEY = os.getenv('SECRET_KEY')

if not SECRET_KEY:
    raise ImproperlyConfigured(
        'SECRET_KEY environment variable must be set'
    )

# =====================================================
# ALLOWED_HOSTS
# =====================================================

raw_hosts = os.getenv(
    'ALLOWED_HOSTS',
    '127.0.0.1,localhost'
)

ALLOWED_HOSTS = [
    host.strip()
    for host in raw_hosts.split(',')
]

# =====================================================
# CSRF TRUSTED ORIGINS
# =====================================================

raw_csrf = os.getenv(
    'CSRF_TRUSTED_ORIGINS',
    'https://plata-deca.duckdns.org'
)

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in raw_csrf.split(',')
]

# =====================================================
# CONFIGURAÇÕES DE PRODUÇÃO
# =====================================================

if not DEBUG:

    # Força HTTPS
    SECURE_SSL_REDIRECT = True

    # Proxy reverso (Nginx/Traefik/Cloudflare)
    SECURE_PROXY_SSL_HEADER = (
        'HTTP_X_FORWARDED_PROTO',
        'https'
    )

    # Cookies seguros
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # Segurança navegador
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

    # HSTS
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # Clickjacking
    X_FRAME_OPTIONS = 'DENY'

    # Referrer Policy
    SECURE_REFERRER_POLICY = 'same-origin'

# =====================================================
# APLICAÇÕES
# =====================================================

AUTH_USER_MODEL = 'cursos.User'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'cursos',
]

# =====================================================
# MIDDLEWARE
# =====================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# =====================================================
# URLS / WSGI
# =====================================================

ROOT_URLCONF = 'platacursos.urls'

WSGI_APPLICATION = 'platacursos.wsgi.application'

# =====================================================
# TEMPLATES
# =====================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        'DIRS': [],

        'APP_DIRS': True,

        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',

                'django.contrib.auth.context_processors.auth',

                'django.contrib.messages.context_processors.messages',

                'django.template.context_processors.media',
            ],
        },
    },
]

# =====================================================
# DATABASE
# =====================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',

        'NAME': os.getenv('DB_NAME', 'platacursos'),

        'USER': os.getenv('DB_USER', 'postgres'),

        'PASSWORD': os.getenv('DB_PASSWORD', ''),

        'HOST': os.getenv('DB_HOST', 'postgres_db'),

        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# =====================================================
# INTERNACIONALIZAÇÃO
# =====================================================

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True

USE_TZ = True

# =====================================================
# STATIC FILES
# =====================================================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

if DEBUG:
    # Em desenvolvimento, permite que o Django encontre estáticos nas pastas dos apps
    STATICFILES_DIRS = [BASE_DIR / 'static']
else:
    # Em produção, usa o WhiteNoise para servir os arquivos coletados
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# =====================================================
# MEDIA FILES
# =====================================================

MEDIA_URL = '/media/'

MEDIA_ROOT = '/app/media'

# =====================================================
# UPLOAD LIMITS
# =====================================================

# 100MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 104857600

FILE_UPLOAD_MAX_MEMORY_SIZE = 104857600

# =====================================================
# LOGIN
# =====================================================

LOGIN_URL = 'login'

LOGIN_REDIRECT_URL = 'lista_cursos'

LOGOUT_REDIRECT_URL = 'login'

# =====================================================
# AUTHENTICATION
# =====================================================

AUTHENTICATION_BACKENDS = [
    'cursos.backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]