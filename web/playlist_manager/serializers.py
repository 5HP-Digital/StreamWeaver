from rest_framework import serializers
from .models import Playlist, PlaylistChannel
from provider_manager.models import ProviderChannel
from provider_manager.serializers import ProviderChannelSerializer


class PlaylistSerializer(serializers.ModelSerializer):
    """
    Serializer for Playlist model.
    """
    channel_count = serializers.SerializerMethodField()
    inactive_channel_count = serializers.SerializerMethodField()

    class Meta:
        model = Playlist
        fields = ['id', 'name', 'created_at', 'updated_at', 'channel_count', 'inactive_channel_count']
        read_only_fields = ['id', 'created_at', 'updated_at', 'channel_count', 'inactive_channel_count']

    def get_channel_count(self, obj):
        """
        Get the number of channels associated with this Playlist.
        """
        return obj.channels.count()

    def get_inactive_channel_count(self, obj):
        """
        Get the number of deactivated channels associated with this Playlist.
        """
        return obj.channels.filter(provider_channel__is_active=False).count()


class PlaylistCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a Playlist.
    """
    name = serializers.CharField(required=True)

    class Meta:
        model = Playlist
        fields = ['name']

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Name cannot be empty.")
        return value


class PlaylistUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating a Playlist.
    """
    name = serializers.CharField(required=True)

    class Meta:
        model = Playlist
        fields = ['name']

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Name cannot be empty.")
        return value


class PlaylistReorderSerializer(serializers.Serializer):
    """
    Serializer for reordering playlists.
    """
    playlist_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True
    )

    def validate_playlist_ids(self, value):
        # Check if all IDs are unique
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Playlist IDs must be unique.")

        # Check if all IDs exist and if all existing playlists are included
        existing_ids = set(Playlist.objects.values_list('id', flat=True))
        if set(value) != existing_ids:
            raise serializers.ValidationError("All existing playlist IDs must be included, and no extra IDs.")

        return value


class ProviderWithDetailsSerializer(serializers.ModelSerializer):
    """
    Serializer for Provider model with minimal details.
    """
    class Meta:
        model = ProviderChannel.provider.field.related_model
        fields = ['id', 'name', 'is_enabled']


class ProviderChannelWithDetailsSerializer(serializers.ModelSerializer):
    """
    Serializer for ProviderChannel model with provider details.
    """
    provider = ProviderWithDetailsSerializer(read_only=True)

    class Meta:
        model = ProviderChannel
        fields = ['id', 'title', 'tvg_id', 'media_url', 'logo_url', 'group', 'is_active', 'provider']


class PlaylistChannelSerializer(serializers.ModelSerializer):
    """
    Serializer for PlaylistChannel model.
    """
    provider_channel = ProviderChannelWithDetailsSerializer(read_only=True)

    class Meta:
        model = PlaylistChannel
        fields = ['id', 'title', 'tvg_id', 'category', 'logo_url', 'provider_channel', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class PlaylistChannelCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a PlaylistChannel.
    """
    title = serializers.CharField(required=True)
    provider_channel_id = serializers.IntegerField(required=True)

    class Meta:
        model = PlaylistChannel
        fields = ['title', 'tvg_id', 'category', 'logo_url', 'provider_channel_id']

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        return value

    def validate_tvg_id(self, value):
        if not value.strip():
            raise serializers.ValidationError("TVG ID cannot be empty.")
        return value

    def validate_provider_channel_id(self, value):
        try:
            ProviderChannel.objects.get(pk=value)
        except ProviderChannel.DoesNotExist:
            raise serializers.ValidationError("Provider channel does not exist.")
        return value


class PlaylistChannelUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating a PlaylistChannel.
    """
    title = serializers.CharField(required=False)
    provider_channel_id = serializers.IntegerField(required=False)

    class Meta:
        model = PlaylistChannel
        fields = ['title', 'tvg_id', 'category', 'logo_url', 'provider_channel_id']

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        return value

    def validate_tvg_id(self, value):
        if not value.strip():
            raise serializers.ValidationError("TVG ID cannot be empty.")
        return value

    def validate_provider_channel_id(self, value):
        try:
            ProviderChannel.objects.get(pk=value)
        except ProviderChannel.DoesNotExist:
            raise serializers.ValidationError("Provider channel does not exist.")
        return value