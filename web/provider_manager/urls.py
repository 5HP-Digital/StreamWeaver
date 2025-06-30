from django.urls import path, include

from .views import ProvidersViewSet, ProviderStreamsViewSet
from main.custom_default_router import CustomDefaultRouter

router = CustomDefaultRouter()
router.register(r'providers', ProvidersViewSet, basename='providers')
router.register(r'streams', ProviderStreamsViewSet, basename='streams')

urlpatterns = [
    path('', include(router.urls)),
]
