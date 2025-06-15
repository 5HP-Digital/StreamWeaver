from django.db import models
from django.core.validators import URLValidator
from provider_manager.models import ProviderChannel


class Playlist(models.Model):
    """
    Model representing a playlist.
    """
    name = models.CharField(max_length=255)
    starting_channel_number = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class PlaylistChannel(models.Model):
    """
    Model representing a channel within a playlist.
    """
    title = models.CharField(max_length=255, null=True, blank=True)
    tvg_id = models.CharField(max_length=255, null=True, blank=True)
    logo_url = models.TextField(validators=[URLValidator()], null=True, blank=True)
    category = models.CharField(max_length=255, null=True, blank=True)
    order = models.IntegerField()
    playlist = models.ForeignKey(
        Playlist,
        on_delete=models.CASCADE,
        related_name='channels'
    )
    provider_channel = models.ForeignKey(
        ProviderChannel,
        on_delete=models.CASCADE,
        related_name='playlist_channels'
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
            models.UniqueConstraint(fields=['playlist', 'provider_channel'], name='unique_playlist_channel_provider_channel')
        ]

    def __str__(self):
        return self.title or self.provider_channel.title
