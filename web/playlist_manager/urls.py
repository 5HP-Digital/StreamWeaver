from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import PlaylistsViewSet, ChannelsViewSet

app_name = 'playlist_manager'

router = DefaultRouter()
router.register(r'playlists', PlaylistsViewSet, basename='playlists')
router.register(r'channels', ChannelsViewSet, basename='channels')

urlpatterns = [
    path('', include(router.urls)),
]
