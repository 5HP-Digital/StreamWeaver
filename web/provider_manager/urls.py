from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ProvidersViewSet, ProviderChannelsViewSet

router = DefaultRouter()
router.register(r'providers', ProvidersViewSet, basename='providers')

urlpatterns = [
    path('', include(router.urls)),
    path('providers/<int:provider_id>/channels/', ProviderChannelsViewSet.as_view({'get': 'list'}), name='provider-channels'),
]
