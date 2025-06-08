from django.db import models
from django.core.validators import URLValidator
import uuid


class JobState(models.TextChoices):
    """
    Enum representing the state of a job.
    Based on IPTV.JobWorker/Data/JobState.cs
    """
    PENDING = 'Pending'
    IN_PROGRESS = 'InProgress'
    COMPLETED = 'Completed'
    FAILED = 'Failed'


class Job(models.Model):
    """
    Model representing a job.
    Based on IPTV.JobWorker/Data/Job.cs
    """
    job_id = models.UUIDField(default=uuid.uuid4, unique=True)
    state = models.CharField(
        max_length=20,
        choices=JobState.choices,
        default=JobState.PENDING
    )
    attempt_count = models.IntegerField(default=0)
    error = models.TextField(null=True, blank=True)
    context = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Job {self.job_id} - {self.state}"


class PlaylistSource(models.Model):
    """
    Model representing a playlist source.
    Based on IPTV.PlaylistManager/Data/PlaylistSource.cs
    """
    name = models.CharField(max_length=255)
    url = models.TextField(validators=[URLValidator()])
    is_enabled = models.BooleanField(default=False)
    jobs = models.ManyToManyField(
        'Job',
        through='PlaylistSourceJobs',
        related_name='sources'
    )
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


class PlaylistSourceJobs(models.Model):
    """
    Intermediate model for the many-to-many relationship between PlaylistSource and Job.
    """
    source = models.ForeignKey(
        PlaylistSource, 
        on_delete=models.CASCADE,
        related_name='source_jobs'
    )
    job = models.ForeignKey(
        Job, 
        on_delete=models.CASCADE,
        related_name='job_sources'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'playlist_manager_playlistsource_jobs'
        unique_together = ('source', 'job')
