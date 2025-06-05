from rest_framework import serializers


class ServerTimeSerializer(serializers.Serializer):
    """
    Serializer for server time
    """
    time = serializers.DateTimeField()


class ResourceUtilizationSerializer(serializers.Serializer):
    """
    Serializer for server resource utilization
    """
    cpu_percent = serializers.FloatField()
    memory_percent = serializers.FloatField()
    memory_used = serializers.FloatField()
    memory_total = serializers.FloatField()

class SyncScheduleSerializer(serializers.Serializer):
    """Serializer for individual sync schedule."""
    daysOfWeek = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True
    )
    time = serializers.TimeField()

class SettingsSerializer(serializers.Serializer):
    """Serializer for IPTV settings."""
    sync_enabled = serializers.BooleanField(default=False)
    sync_schedules = serializers.ListField(
        child=SyncScheduleSerializer(),
        default=list
    )
    allow_channel_auto_deletion = serializers.BooleanField(default=True)

    def create(self, validated_data):
        """Not used for this serializer."""
        return validated_data

    def update(self, instance, validated_data):
        """Not used for this serializer."""
        return validated_data
