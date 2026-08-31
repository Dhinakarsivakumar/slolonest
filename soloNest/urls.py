from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from django.views.static import serve
from django.urls import re_path

from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/google/login/', core_views.google_login_wrapper, name='google_login_wrapper'),
    path('accounts/', include('allauth.urls')),
    path('', include('core.urls')),
    path('support/', include('support.urls')),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]


