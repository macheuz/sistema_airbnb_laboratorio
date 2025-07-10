import os
from pathlib import Path

# Diretório base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

# ==========================
# Configurações de Segurança
# ==========================

SECRET_KEY = 'django-insecure-03*a5-pv1ft35br8+ok^(jkm!*)*4+l$$(ki(i+j*!w+*eqj2t'

DEBUG = True  # Certifique-se de alterar para True em ambiente de desenvolvimento

ALLOWED_HOSTS = [
    # URLS para aprovar em producao
    "exemplo.exemplo.com",
    "www.exemplo.exemplo.com",
    "127.0.0.1",
    "localhost",
    "10.10.10.10.10"
]

CSRF_TRUSTED_ORIGINS = [
    "https://exemplo.exemplo.com",
    "https://www.exemplo.exemplo.com",
    "http://exemplo.exemplo.com",
    "https://www.exemplo.exemplo.com:443",
    "http://www.exemplo.exemplo.com:80",
    "https://31.97.249.207",
]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# ==========================
# Aplicações Instaladas
# ==========================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps.core',
    'apps.anuncios',
    'apps.agendamento',
    'apps.avaliacoes',
    'apps.imovel',
    'apps.localizacoes',
]

# ==========================
# Middlewares
# ==========================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ==========================
# Configuração de URLs e WSGI
# ==========================

ROOT_URLCONF = 'planejador_airbnb.urls'

WSGI_APPLICATION = 'planejador_airbnb.wsgi.application'

# ==========================
# Configuração de Templates
# ==========================

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
            ],
        },
    },
]

# ==========================
# Configuração do Banco de Dados
# ==========================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'planb',    # O nome do seu banco de dados no PostgreSQL
        'USER': 'usuario',       # Seu usuário do PostgreSQL
        'PASSWORD': 'senha',   # Sua senha do PostgreSQL
        'HOST': 'localhost',         # Ou o endereço do seu servidor de banco de dados
        'PORT': '5436',              # A porta padrão do PostgreSQL
    }
}

# ==========================
# Validação de Senhas
# ==========================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ==========================
# Internacionalização
# ==========================

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# ==========================
# Configuração de Arquivos Estáticos e Mídia
# ==========================

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'staticfiles'),  # Adicione esta linha
]
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')  # Diretório base para arquivos de mídia
MEDIA_URL = '/media/'

# ==========================
# Configuração de Autenticação
# ==========================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'




# ==========================
# Configuração de Sessões
# ==========================

SESSION_COOKIE_AGE = 30 * 60  # 30 minutos
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_DOMAIN = 'exemplo.exemplo.com'


# ==========================
# Configurações de Segurança Adicionais
# ==========================

CSRF_COOKIE_HTTPONLY = True
CSRF_USE_SESSIONS = True
CSRF_COOKIE_SAMESITE = 'Lax'

SECURE_HSTS_SECONDS = 31536000  # 1 ano
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_REFERRER_POLICY = 'same-origin'
