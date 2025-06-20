from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import GuidesViewSet

router = DefaultRouter()
router.register(r'guides', GuidesViewSet, basename='guides')

urlpatterns = [
    path('', include(router.urls)),
]