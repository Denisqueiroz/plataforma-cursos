from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.urls import reverse_lazy

urlpatterns = [
    path('', RedirectView.as_view(url=reverse_lazy(settings.LOGIN_URL)), name='root-redirect'),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('plataforma/', include('cursos.urls')), 
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)