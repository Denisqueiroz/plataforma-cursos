import os
from pathlib import Path
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

# 1. BASE PATHS
# O BASE_DIR dentro do container será '/app'
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. CONFIGURAÇÕES DE AMBIENTE E SEGURANÇA
load_dotenv(BASE_DIR / '.env')

# SEGURANÇA MÁXIMA PARA PRODUÇÃO: DEBUG obrigatoriamente False
DEBUG = False

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ImproperlyConfigured("A variável SECRET_KEY precisa estar configurada no arquivo .env para produção.")

# Captura os domínios e o IP fixo configurados no .env
allowed_hosts_env = os.getenv('ALLOWED_HOSTS', '')
ALLOWED_HOSTS = allowed_hosts_env.split(',') if allowed_hosts_env else []

# Ativação obrigatória de segurança (HTTPS, Cookies e HSTS)
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 ano
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

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

# 4. BANCO DE DADOS (POSTGRESQL NO DOCKER)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'platacursos'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'postgres_db'), # Nome do serviço no docker-compose
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# 5. VALIDAÇÃO DE SENHAS
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# 6. INTERNACIONALIZAÇÃO
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# 7. ARQUIVOS ESTÁTICOS E MÍDIA (CONFIGURAÇÃO PARA O HD EXTERNO)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# O Django salva em /app/media, que o Docker mapeia para o HD
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# 8. LIMITES DE UPLOAD (5GB para vídeos pesados)
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880000
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880000

# 9. AUTENTICAÇÃO E REDIRECIONAMENTOS
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'lista_cursos'
LOGOUT_REDIRECT_URL = 'login'

AUTHENTICATION_BACKENDS = [
    'cursos.backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'