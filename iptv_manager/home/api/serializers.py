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