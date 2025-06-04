from rest_framework import serializers
from .models import PlaylistSource, PlaylistSourceChannel, PlaylistSourceInvocation


class PlaylistSourceSerializer(serializers.ModelSerializer):
    """
    Serializer for PlaylistSource model.
    """
    class Meta:
        model = PlaylistSource
        fields = ['id', 'name', 'url', 'is_enabled', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class PlaylistSourceCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a PlaylistSource.
    """
    class Meta:
        model = PlaylistSource
        fields = ['name', 'url']


class PlaylistSourceUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating a PlaylistSource.
    """
    name = serializers.CharField(required=False)
    url = serializers.URLField(required=False)
    is_enabled = serializers.BooleanField(required=False)

    class Meta:
        model = PlaylistSource
        fields = ['name', 'url', 'is_enabled']


class PlaylistSourceChannelSerializer(serializers.ModelSerializer):
    """
    Serializer for PlaylistSourceChannel model.
    """
    class Meta:
        model = PlaylistSourceChannel
        fields = ['id', 'title', 'tvg_id', 'media_url', 'logo_url', 'group', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
