import os
from django.conf import settings
from pathlib import Path
from rest_framework import serializers

from .models import Playlist, PlaylistChannel
from provider_manager.models import ProviderStream
from provider_manager.serializers import ProviderStreamSerializer
from guide_manager.models import Guide
from guide_manager.serializers import GuideSerializer


class PlaylistSerializer(serializers.ModelSerializer):
    """
    Serializer for Playlist model.
    """
    channel_count = serializers.SerializerMethodField()
    inactive_channel_count = serializers.SerializerMethodField()
    has_epg = serializers.SerializerMethodField()

    class Meta:
        model = Playlist
        fields = ['id', 'name', 'starting_channel_number', 'default_lang', 'created_at', 'updated_at', 'channel_count', 'inactive_channel_count', 'has_epg']
        read_only_fields = ['id', 'created_at', 'updated_at', 'channel_count', 'inactive_channel_count', 'has_epg']

    def get_channel_count(self, obj):
        """
        Get the number of channels associated with this Playlist.
        """
        return obj.channels.count()

    def get_inactive_channel_count(self, obj):
        """
        Get the number of deactivated channels associated with this Playlist.
        """
        return obj.channels.filter(provider_stream__is_active=False).count()
    
    def get_has_epg(self, obj):
        """
        Get whether the Playlist has EPG generated for it. 
        """
        guide_path = os.path.join(settings.CONFIG_DIR, f"playlists/{obj.id}/guide.xml")
        return Path(guide_path).exists()


class PlaylistCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a Playlist.
    """
    name = serializers.CharField(required=True)
    starting_channel_number = serializers.IntegerField(required=False, default=1)

    class Meta:
        model = Playlist
        fields = ['name', 'starting_channel_number', 'default_lang']

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Name cannot be empty.")
        return value

    def validate_starting_channel_number(self, value):
        if value < 1:
            raise serializers.ValidationError("Starting channel number must be greater than 0.")
        return value


class PlaylistUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating a Playlist.
    """
    name = serializers.CharField(required=True)
    starting_channel_number = serializers.IntegerField(required=False)

    class Meta:
        model = Playlist
        fields = ['name', 'starting_channel_number', 'default_lang']

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Name cannot be empty.")
        return value

    def validate_starting_channel_number(self, value):
        if value < 1:
            raise serializers.ValidationError("Starting channel number must be greater than 0.")
        return value

class ProviderWithDetailsSerializer(serializers.ModelSerializer):
    """
    Serializer for Provider model with minimal details.
    """
    class Meta:
        model = ProviderStream.provider.field.related_model
        fields = ['id', 'name', 'is_enabled']


class ProviderStreamWithDetailsSerializer(serializers.ModelSerializer):
    """
    Serializer for ProviderStream model with provider details.
    """
    provider = ProviderWithDetailsSerializer(read_only=True)

    class Meta:
        model = ProviderStream
        fields = ['id', 'title', 'tvg_id', 'media_url', 'logo_url', 'group', 'is_active', 'provider']


class PlaylistChannelSerializer(serializers.ModelSerializer):
    """
    Serializer for PlaylistChannel model.
    """
    provider_stream = ProviderStreamWithDetailsSerializer(read_only=True)
    num = serializers.SerializerMethodField()
    guide = GuideSerializer(read_only=True)

    class Meta:
        model = PlaylistChannel
        fields = ['id', 'title', 'category', 'logo_url', 'provider_stream', 'created_at', 'updated_at', 'num', 'order', 'guide']
        read_only_fields = ['id', 'created_at', 'updated_at', 'num']

    def get_num(self, obj):
        """
        Calculate the channel number based on the order and the playlist's starting_channel_number.
        """
        return obj.playlist.starting_channel_number + obj.order - 1


class PlaylistChannelCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a PlaylistChannel.
    """
    title = serializers.CharField(required=False, allow_null=True)
    provider_stream_id = serializers.IntegerField(required=True)
    guide_id = serializers.IntegerField(required=False)

    class Meta:
        model = PlaylistChannel
        fields = ['title', 'category', 'logo_url', 'provider_stream_id', 'guide_id']

    def validate_title(self, value):
        if value and not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        return value

    def validate_provider_stream_id(self, value):
        try:
            ProviderStream.objects.get(pk=value)
        except ProviderStream.DoesNotExist:
            raise serializers.ValidationError("Provider stream does not exist.")
        return value

    def validate_guide_id(self, value):
        if value is not None:
            try:
                Guide.objects.get(pk=value)
            except:
                raise serializers.ValidationError("Guide does not exist.")
        return value


class PlaylistChannelUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating a PlaylistChannel.
    """
    title = serializers.CharField(required=False, allow_null=True)
    provider_stream_id = serializers.IntegerField(required=False)
    guide_id = serializers.IntegerField(required=False)
    order = serializers.IntegerField(required=False)

    class Meta:
        model = PlaylistChannel
        fields = ['title', 'category', 'logo_url', 'provider_stream_id', 'guide_id', 'order']

    def validate_title(self, value):
        if value and not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        return value

    def validate_provider_stream_id(self, value):
        try:
            ProviderStream.objects.get(pk=value)
        except ProviderStream.DoesNotExist:
            raise serializers.ValidationError("Provider stream does not exist.")
        return value

    def validate_order(self, value):
        if value < 1:
            raise serializers.ValidationError("Order must be greater than 0.")

        return value

    def validate_guide_id(self, value):
        if value is not None:
            try:
                Guide.objects.get(pk=value)
            except:
                raise serializers.ValidationError("Guide does not exist.")
        return value
