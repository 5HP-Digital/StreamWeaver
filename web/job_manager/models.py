from django.db import models
import uuid


class JobType(models.TextChoices):
    """
    Enum representing the type of job.
    """
    PROVIDER_SYNC = 'ProviderSync'
    EPG_DATA_SYNC = 'EpgDataSync'
    PLAYLIST_EPG_GEN = 'PlaylistEpgGen'

class JobState(models.TextChoices):
    """
    Enum representing the state of a job.
    """
    QUEUED = 'Queued'
    IN_PROGRESS = 'InProgress'
    COMPLETED = 'Completed'
    FAILED = 'Failed'

class Job(models.Model):
    """
    Base model representing a job.
    """
    job_id = models.UUIDField(default=uuid.uuid4, unique=True)
    type = models.CharField(
        max_length=20,
        choices=JobType.choices,
        editable=False
    )
    state = models.CharField(
        max_length=20,
        choices=JobState.choices,
        default=JobState.QUEUED
    )
    status_description = models.TextField(null=True, blank=True)
    last_attempt_started_at = models.DateTimeField(null=True, blank=True)
    attempt_count = models.IntegerField(default=0)
    max_attempts = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ProviderSync
    allow_stream_auto_deletion = models.BooleanField(default=True, null=True, blank=True)
    provider = models.ForeignKey(
        'provider_manager.Provider',
        on_delete=models.CASCADE,
        related_name='jobs',
        null=True,
        blank=True,
    )

    # PlaylistEpgGen
    playlist = models.ForeignKey(
        'playlist_manager.Playlist',
        on_delete=models.CASCADE,
        related_name='jobs',
        null=True,
        blank=True,
    )

    class Meta:
        indexes = [
            models.Index(fields=['state', 'created_at'], name='job_state_created_idx'),
            models.Index(fields=['job_id'], name='job_jobid_idx')
        ]

    def __str__(self):
        return f"{self.type} {self.job_id} - {self.state}"
