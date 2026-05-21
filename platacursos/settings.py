import os
from pathlib import Path
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

# 1. BASE PATHS
BASE_DIR = Path(__file__).resolve().parent.parent

# Carrega o .env localizado na pasta raiz do projeto
load_dotenv(BASE_DIR.parent / '.env')

# 2. CONFIGURAÇÕES DE AMBIENTE E SEGURANÇA
DEBUG = os.getenv('DEBUG', 'False') == 'True'

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY and not DEBUG:
    raise ImproperlyConfigured("SECRET_KEY environment variable must be set in production")

# Correção: Lê do .env de forma dinâmica
raw_hosts = os.getenv('ALLOWED_HOSTS', 'plata-deca.duckdns.org,127.0.0.1,localhost')
ALLOWED_HOSTS = [host.strip() for host in raw_hosts.split(',')]

CSRF_TRUSTED_ORIGINS = [
    'https://plata-deca.duckdns.org',
    'http://172.25.0.29:10443'
]

if not DEBUG:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

# 3. DEFINIÇÃO DA APLICAÇÃO
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

ROOT_URLCONF = 'platacursos.urls'

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

WSGI_APPLICATION = 'platacursos.wsgi.application'

# 4. BANCO DE DADOS
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

# 6. INTERNACIONALIZAÇÃO
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# 7. ARQUIVOS ESTÁTICOS E MÍDIA
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Correção: Aponta para o caminho absoluto no container (/app/media)
# que está mapeado para o seu HD externo.
MEDIA_URL = '/media/'
MEDIA_ROOT = '/app/media'

# 8. LIMITES DE UPLOAD
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880000
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880000

# 9. AUTENTICAÇÃO
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'lista_cursos'
LOGOUT_REDIRECT_URL = 'login'