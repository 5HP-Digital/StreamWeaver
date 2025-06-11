from django.contrib import admin
from .models import Playlist, PlaylistChannel

admin.site.register(Playlist)
admin.site.register(PlaylistChannel)