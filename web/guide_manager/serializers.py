from rest_framework import serializers
from .models import Country, Category, Channel, Guide


class CountrySerializer(serializers.ModelSerializer):
    """
    Serializer for Country model.
    """
    class Meta:
        model = Country
        fields = ['code', 'name', 'flag']


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for Category model.
    """
    class Meta:
        model = Category
        fields = ['code', 'name']


class ChannelSerializer(serializers.ModelSerializer):
    """
    Serializer for Channel model.
    """
    categories = serializers.SerializerMethodField()

    class Meta:
        model = Channel
        fields = [
            'xmltv_id', 'name', 'network', 'country', 'city', 
            'categories', 'is_nsfw', 'launched_at', 'closed_at', 
            'website_url', 'logo_url'
        ]

    def get_categories(self, obj):
        """
        Convert the comma-separated categories string to an array of strings.
        """
        if obj.categories:
            return [category.strip() for category in obj.categories.split(',')]
        return []


class GuideSerializer(serializers.ModelSerializer):
    """
    Serializer for Guide model.
    """
    channel = ChannelSerializer(read_only=True)

    class Meta:
        model = Guide
        fields = ['id', 'site', 'site_id', 'site_name', 'lang', 'channel']
