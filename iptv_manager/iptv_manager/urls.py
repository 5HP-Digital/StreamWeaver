"""
URL configuration for iptv_manager project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('home.api.urls')),
    path('', include('home.urls')),
]