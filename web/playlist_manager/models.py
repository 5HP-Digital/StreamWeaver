from django.db import models
from django.core.validators import URLValidator
from provider_manager.models import ProviderStream
from guide_manager.models import Guide


class Playlist(models.Model):
    """
    Model representing a playlist.
    """
    name = models.CharField(max_length=255)
    starting_channel_number = models.IntegerField(default=1)
    default_lang = models.CharField(max_length=20, default='en')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class PlaylistChannel(models.Model):
    """
    Model representing a channel within a playlist.
    """
    title = models.CharField(max_length=255, null=True, blank=True)
    logo_url = models.TextField(validators=[URLValidator()], null=True, blank=True)
    category = models.CharField(max_length=255, null=True, blank=True)
    order = models.IntegerField()
    playlist = models.ForeignKey(
        Playlist,
        on_delete=models.CASCADE,
        related_name='channels'
    )
    provider_stream = models.ForeignKey(
        ProviderStream,
        on_delete=models.CASCADE,
        related_name='playlist_channels'
    )
    guide = models.ForeignKey(
        Guide,
        on_delete=models.SET_NULL,
        related_name='playlist_channels',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['playlist', 'order'], name='playlist_channel_order_idx'),
            models.Index(fields=['playlist', 'category'], name='playlist_channel_category_idx')
        ]
        constraints = [
            models.UniqueConstraint(fields=['playlist', 'order'], name='unique_playlist_channel_order'),
            models.UniqueConstraint(fields=['playlist', 'provider_stream'], name='unique_playlist_channel_provider_stream')
        ]

    def __str__(self):
        return self.title or self.provider_stream.title
