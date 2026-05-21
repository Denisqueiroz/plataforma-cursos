from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.urls import reverse_lazy, re_path
from .serve_media import ranged_serve
from cursos.views import CustomLoginView, Setup2FAView, Login2FAView

urlpatterns = [
    path('', RedirectView.as_view(pattern_name=settings.LOGIN_URL), name='root-redirect'),
    path('admin/', admin.site.urls),
    
    # Rotas customizadas de autenticação e 2FA (sobrescrevem apenas o login padrão)
    path('accounts/login/', CustomLoginView.as_view(), name='login'),
    path('accounts/login/2fa/', Login2FAView.as_view(), name='login_2fa'),
    path('accounts/login/2fa/setup/', Setup2FAView.as_view(), name='setup_2fa'),
    
    path('accounts/', include('django.contrib.auth.urls')),
    path('plataforma/', include('cursos.urls')),
    
    # Rota para streaming de media movida para fora do if DEBUG para funcionar em produção (videos)
    re_path(r'^media/(?P<path>.*)$', ranged_serve, {'document_root': settings.MEDIA_ROOT}),
]

# Se quiser adicionar rotas exclusivas de DEBUG no futuro:
if settings.DEBUG:
    pass