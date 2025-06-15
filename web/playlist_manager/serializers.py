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
        fields = ['id', 'name', 'starting_channel_number', 'created_at', 'updated_at', 'channel_count', 'inactive_channel_count']
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
    starting_channel_number = serializers.IntegerField(required=False, default=1)

    class Meta:
        model = Playlist
        fields = ['name', 'starting_channel_number']

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
        fields = ['name', 'starting_channel_number']

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
    num = serializers.SerializerMethodField()

    class Meta:
        model = PlaylistChannel
        fields = ['id', 'title', 'tvg_id', 'category', 'logo_url', 'provider_channel', 'created_at', 'updated_at', 'num', 'order']
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
    title = serializers.CharField(required=False)
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
    order = serializers.IntegerField(required=False)

    class Meta:
        model = PlaylistChannel
        fields = ['title', 'tvg_id', 'category', 'logo_url', 'provider_channel_id', 'order']

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

    def validate_order(self, value):
        if value < 1:
            raise serializers.ValidationError("Order must be greater than 0.")

        return value
