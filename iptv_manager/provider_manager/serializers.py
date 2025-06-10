from rest_framework import serializers
from .models import Provider, ProviderChannel, ProviderSyncJob, JobState


class ProviderSerializer(serializers.ModelSerializer):
    """
    Serializer for Provider model.
    """
    channel_count = serializers.SerializerMethodField()
    last_synced = serializers.SerializerMethodField()
    active_job_id = serializers.SerializerMethodField()

    class Meta:
        model = Provider
        fields = ['id', 'name', 'url', 'is_enabled', 'created_at', 'updated_at', 'channel_count', 'last_synced', 'active_job_id']
        read_only_fields = ['id', 'created_at', 'updated_at', 'channel_count', 'last_synced', 'active_job_id']

    def get_channel_count(self, obj):
        """
        Get the number of channels associated with this Provider.
        """
        return obj.channels.count()

    def get_last_synced(self, obj):
        """
        Get the date of the last successful job.
        """
        last_job = obj.jobs.filter(state=JobState.COMPLETED).order_by('-updated_at').first()
        if last_job:
            return last_job.updated_at
        return None

    def get_active_job_id(self, obj):
        """
        Get whether an active sync job is in progress.
        """
        active_jobs = obj.jobs.filter(state__in=[JobState.QUEUED, JobState.IN_PROGRESS])
        if active_jobs.exists():
            return active_jobs.first().job_id
        return None


class ProviderCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a Provider.
    """
    class Meta:
        model = Provider
        fields = ['name', 'url']


class ProviderUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating a Provider.
    """
    name = serializers.CharField(required=False)
    url = serializers.URLField(required=False)
    is_enabled = serializers.BooleanField(required=False)

    class Meta:
        model = Provider
        fields = ['name', 'url', 'is_enabled']


class ProviderChannelSerializer(serializers.ModelSerializer):
    """
    Serializer for ProviderChannel model.
    """
    class Meta:
        model = ProviderChannel
        fields = ['id', 'title', 'tvg_id', 'media_url', 'logo_url', 'group', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProviderSyncJobSerializer(serializers.ModelSerializer):
    """
    Serializer for ProviderSyncJob model.
    """
    class Meta:
        model = ProviderSyncJob
        fields = ['id', 'job_id', 'state', 'status_description', 'last_attempt_started_at', 
                  'attempt_count', 'max_attempts', 'created_at', 'updated_at']
        read_only_fields = ['id', 'job_id', 'created_at', 'updated_at']
