from django.db import models
from django.core.validators import URLValidator
import uuid


class JobState(models.TextChoices):
    """
    Enum representing the state of a job.
    """
    QUEUED = 'Queued'
    IN_PROGRESS = 'InProgress'
    COMPLETED = 'Completed'
    FAILED = 'Failed'


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


class ProviderSyncJob(models.Model):
    """
    Model representing a job.
    """
    job_id = models.UUIDField(default=uuid.uuid4, unique=True)
    state = models.CharField(
        max_length=20,
        choices=JobState.choices,
        default=JobState.QUEUED
    )
    status_description = models.TextField(null=True, blank=True)
    last_attempt_started_at = models.DateTimeField(null=True, blank=True)
    attempt_count = models.IntegerField(default=0)
    max_attempts = models.IntegerField(null=True, blank=True)
    allow_channel_auto_deletion = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name='jobs'
    )

    def __str__(self):
        return f"ProviderSyncJob {self.job_id} - {self.state}"


class ProviderChannel(models.Model):
    """
    Model representing a channel within a provider.
    """
    provider = models.ForeignKey(
        Provider, 
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
