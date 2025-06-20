from rest_framework import serializers
from .models import Provider, ProviderStream
from job_manager.models import JobState, JobType


class ProviderSerializer(serializers.ModelSerializer):
    """
    Serializer for Provider model.
    """
    stream_count = serializers.SerializerMethodField()
    last_synced = serializers.SerializerMethodField()
    active_job_id = serializers.SerializerMethodField()

    class Meta:
        model = Provider
        fields = ['id', 'name', 'url', 'is_enabled', 'created_at', 'updated_at', 'stream_count', 'last_synced', 'active_job_id']
        read_only_fields = ['id', 'created_at', 'updated_at', 'stream_count', 'last_synced', 'active_job_id']

    def get_stream_count(self, obj):
        """
        Get the number of streams associated with this Provider.
        """
        return obj.streams.count()

    def get_last_synced(self, obj):
        """
        Get the date of the last successful job.
        """
        last_job = obj.jobs.filter(type=JobType.PROVIDER_SYNC, state=JobState.COMPLETED).order_by('-updated_at').first()
        if last_job:
            return last_job.updated_at
        return None

    def get_active_job_id(self, obj):
        """
        Get whether an active sync job is in progress.
        """
        active_jobs = obj.jobs.filter(type=JobType.PROVIDER_SYNC, state__in=[JobState.QUEUED, JobState.IN_PROGRESS])
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


class ProviderStreamSerializer(serializers.ModelSerializer):
    """
    Serializer for ProviderStream model.
    """
    class Meta:
        model = ProviderStream
        fields = ['id', 'title', 'tvg_id', 'media_url', 'logo_url', 'group', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
