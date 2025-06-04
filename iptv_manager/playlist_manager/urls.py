from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import SourcesViewSet, ChannelsViewSet

router = DefaultRouter()
router.register(r'sources', SourcesViewSet, basename='sources')

urlpatterns = [
    path('', include(router.urls)),
    path('sources/<int:source_id>/channels/', ChannelsViewSet.as_view({'get': 'list'}), name='source-channels'),
]