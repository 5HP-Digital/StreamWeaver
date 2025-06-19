from django.db import models
from django.core.validators import URLValidator
from job_manager.models import JobState
import uuid


class Provider(models.Model):
    """
    Model representing a provider.
    """
    name = models.CharField(max_length=255)
    url = models.TextField(validators=[URLValidator()])
    is_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ProviderStream(models.Model):
    """
    Model representing a stream within a provider.
    """
    provider = models.ForeignKey(
        Provider, 
        on_delete=models.CASCADE, 
        related_name='streams'
    )
    title = models.CharField(max_length=255)
    tvg_id = models.CharField(max_length=255, null=True, blank=True)
    media_url = models.TextField(validators=[URLValidator()])
    logo_url = models.TextField(validators=[URLValidator()], null=True, blank=True)
    group = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['provider', 'is_active'], name='stream_provider_active_idx'),
            models.Index(fields=['group', 'title', 'tvg_id'], name='stream_group_title_tvg_id_idx'),
            models.Index(fields=['is_active'], name='provider_stream_active_idx')
        ]

    def __str__(self):
        return self.title
