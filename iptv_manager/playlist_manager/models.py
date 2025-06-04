from django.db import models
from django.core.validators import URLValidator


class PlaylistSource(models.Model):
    """
    Model representing a playlist source.
    Based on IPTV.PlaylistManager/Data/PlaylistSource.cs
    """
    name = models.CharField(max_length=255)
    url = models.TextField(validators=[URLValidator()])
    is_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class PlaylistSourceChannel(models.Model):
    """
    Model representing a channel within a playlist source.
    Based on IPTV.PlaylistManager/Data/PlaylistSourceChannel.cs
    """
    source = models.ForeignKey(
        PlaylistSource, 
        on_delete=models.CASCADE, 
        related_name='channels'
    )
    title = models.CharField(max_length=255)
    tvg_id = models.CharField(max_length=255, null=True, blank=True)
    media_url = models.TextField(validators=[URLValidator()])
    logo_url = models.TextField(validators=[URLValidator()], null=True, blank=True)
    group = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class PlaylistSourceInvocation(models.Model):
    """
    Model representing an invocation of a playlist source.
    Based on IPTV.PlaylistManager/Data/PlaylistSourceInvocation.cs
    """
    source = models.ForeignKey(
        PlaylistSource, 
        on_delete=models.CASCADE, 
        related_name='invocations'
    )
    error = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Invocation for {self.source.name} at {self.created_at}"
