from rest_framework import serializers

from .models import Job


class JobSerializer(serializers.ModelSerializer):
    """
    Serializer for Job model.
    """
    class Meta:
        model = Job
        fields = ['id', 'job_id', 'type', 'state', 'status_description', 'last_attempt_started_at',
                  'attempt_count', 'max_attempts', 'created_at', 'updated_at']
        read_only_fields = ['id', 'job_id', 'type', 'created_at', 'updated_at']