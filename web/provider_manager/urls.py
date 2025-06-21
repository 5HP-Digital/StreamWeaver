from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ProvidersViewSet, ProviderStreamsViewSet

router = DefaultRouter()
router.register(r'providers', ProvidersViewSet, basename='providers')
router.register(r'streams', ProviderStreamsViewSet, basename='streams')

urlpatterns = [
    path('', include(router.urls)),
]
