from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    path('', views.index, name='index'),
    path('providers/', views.providers, name='providers'),
    path('playlists/', views.playlists, name='playlists'),
    path('playlists/<int:playlist_id>/editor/', views.channel_editor, name='channel_editor'),
]
