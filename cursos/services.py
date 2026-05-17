import os
from pathlib import Path
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

# 1. BASE PATHS
# O BASE_DIR dentro do container será '/app'
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. CONFIGURAÇÕES DE AMBIENTE E SEGURANÇA
load_dotenv(BASE_DIR / '.env')

# --- APRENDENDO SOBRE SEGURANÇA NO DJANGO ---

# 1. O botão de pânico (DEBUG)
# Em produção/homologação, NUNCA deve ser True. Se for True, o Django mostra uma tela amarela 
# detalhada com suas senhas e variáveis em qualquer erro. O código abaixo lê a string do .env 
# e a converte em um booleano real do Python (True ou False).
DEBUG = os.getenv('DJANGO_DEBUG', 'False').lower() in ('true', '1', 't')

# 2. A Chave Mestra (SECRET_KEY)
# Usada para gerar hashes de senhas, assinar cookies e tokens de recuperação.
# Se alguém descobrir sua SECRET_KEY, poderá falsificar sessões de administrador.
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY and not DEBUG:
    raise ImproperlyConfigured("SECRET_KEY environment variable must be set in production/homologation")

# 3. Barreira contra invasão de domínio (ALLOWED_HOSTS)
# Define quais domínios/IPs podem acessar este app. Evita ataques de "HTTP Host Header Injection", 
# onde um hacker finge que está acessando seu site para redirecionar usuários para links maliciosos.
# Captura a string do .env (ex: "meusite.com,www.meusite.com") e quebra nas vírgulas.
ALLOWED_HOSTS = [host.strip() for host in os.getenv('ALLOWED_HOSTS', '').split(',') if host.strip()]

# 4. Bloco de Segurança Estrita (Apenas quando o DEBUG for False)
if not DEBUG:
    # Comunicação com o Proxy Reverso (Nginx / Traefik / Cloudflare)
    # Como o Django roda dentro do Docker, quem recebe o certificado SSL (HTTPS) é o Proxy.
    # Esta linha avisa ao Django: "Se o Nginx disser que a requisição veio com HTTPS, confie nele".
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    
    # Redirecionamento Forçado para HTTPS
    # Se o usuário digitar "http://meusite.com", o Django joga ele automaticamente para "https://meusite.com".
    SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'True').lower() in ('true', '1', 't')
    
    # Proteção de Cookies de Sessão e CSRF
    # Garante que os cookies do usuário (login e tokens) SÓ trafeguem via HTTPS criptografado.
    # Impede que um hacker em uma rede Wi-Fi pública intercepte o cookie de login (Session Hijacking).
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # Filtro XSS do Navegador
    # Ativa uma proteção nativa nos navegadores antigos/modernos para bloquear páginas 
    # se detectarem um ataque de injeção de script (Cross-Site Scripting).
    SECURE_BROWSER_XSS_FILTER = True
    
    # Proteção contra Sniffing de tipo de conteúdo (MIME Sniffing)
    # Impede que o navegador tente adivinhar o tipo de um arquivo. Se o servidor disser que 
    # um arquivo enviado é um texto, o navegador lerá como texto, impedindo que um hacker 
    # suba um arquivo '.txt' que na verdade esconde um script executável perigoso.
    SECURE_CONTENT_TYPE_NOSNIFF = True

    # HSTS - HTTP Strict Transport Security
    # Uma ordem expressa ao navegador do usuário: "Pelos próximos 365 dias (seconds), você está 
    # PROIBIDO de acessar este site via HTTP. Só aceite HTTPS". O Preload inclui seu site na 
    # lista global de sites 100% seguros mantida pelos navegadores.
    SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '31536000')) # 1 ano
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Confiança de Origem para CSRF
    # O Django moderno bloqueia envios de formulários (POST) se não souber de onde vieram. 
    # Esta linha diz ao Django que os mesmos domínios do ALLOWED_HOSTS usando "https://" são seguros.
    CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS]

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
    'whitenoise.middleware.WhiteNoiseMiddleware', # Perfeito aqui para servir os estáticos no Docker
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

# 4. BANCO DE DADOS (POSTGRES NO DOCKER)
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

# 7. ARQUIVOS ESTÁTICOS E MÍDIA
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# 8. LIMITES DE UPLOAD (5GB)
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