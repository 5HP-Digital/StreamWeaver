from django.urls import path, include

from .views import PlaylistsViewSet, ChannelsViewSet
from main.custom_default_router import CustomDefaultRouter

app_name = 'playlist_manager'

router = CustomDefaultRouter()
router.register(r'playlists', PlaylistsViewSet, basename='playlists')
router.register(r'channels', ChannelsViewSet, basename='channels')

urlpatterns = [
    path('', include(router.urls)),
]
