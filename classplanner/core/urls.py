from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.contrib.auth.views import LogoutView 
from classplanner import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('registration.urls')),
    path('', include('classplanner.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/', include('registration.urls')),
    path('logout/', LogoutView.as_view(), name='logout'),
    re_path(r'^.*/$', views.error_404),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)