"""
URL configuration for iptv_manager project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import RedirectView

urlpatterns = [
    re_path(r'^favicon\.ico$', RedirectView.as_view(url='/static/images/favicon.ico', permanent=True), name='favicon'),
    path('admin/', admin.site.urls),
    path('api/', include('home.api.urls')),
    path('api/', include('provider_manager.urls')),
    path('', include('home.urls')),
]
