from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from math import ceil
from django.db.models import Max, F

from .models import Playlist, PlaylistChannel
from .serializers import (
    PlaylistSerializer,
    PlaylistCreateSerializer,
    PlaylistUpdateSerializer,
    PlaylistChannelSerializer,
    PlaylistChannelCreateSerializer,
    PlaylistChannelUpdateSerializer
)


class PlaylistsViewSet(viewsets.ViewSet):
    """
    API endpoint for playlists.
    """

    def list(self, request):
        """
        Get a list of playlists.
        """
        # Get the playlists, ordered by name ascending
        playlists = Playlist.objects.all().order_by('name')
        serializer = PlaylistSerializer(playlists, many=True)

        response_data = {
            'items': serializer.data
        }

        return Response(response_data)

    def retrieve(self, request, pk=None):
        """
        Get a specific playlist by ID.
        """
        playlist = get_object_or_404(Playlist, pk=pk)
        serializer = PlaylistSerializer(playlist)
        return Response(serializer.data)

    def create(self, request):
        """
        Create a new playlist.
        """
        serializer = PlaylistCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Create the playlist with the calculated order
            playlist = Playlist.objects.create(
                name=serializer.validated_data['name']
            )

            return Response(
                PlaylistSerializer(playlist).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        """
        Update a playlist.
        """
        playlist = get_object_or_404(Playlist, pk=pk)
        serializer = PlaylistUpdateSerializer(data=request.data)
        if serializer.is_valid():
            playlist.name = serializer.validated_data['name']
            playlist.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        """
        Delete a playlist.
        """
        playlist = get_object_or_404(Playlist, pk=pk)
        playlist.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def channels(self, request, pk=None):
        """
        Get a paginated list of channels for a specific playlist.

        Query Parameters:
            page: The page number (default: 1)
            size: The page size (default: 10)
        """
        # Validate pagination parameters
        page = int(request.query_params.get('page', 1))
        size = int(request.query_params.get('size', 10))

        if page < 1:
            return Response(
                {"error": "Page number must be greater than or equal to 1"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if size < 1 or size > 100:
            return Response(
                {"error": "Page size must be between 1 and 100"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if playlist exists
        playlist = get_object_or_404(Playlist, pk=pk)

        # Get total count of channels for this playlist
        query = PlaylistChannel.objects.filter(playlist=playlist)
        total_items = query.count()

        # Calculate pagination values
        total_pages = ceil(total_items / size) if total_items > 0 else 1
        skip = (page - 1) * size

        # Get the channels for the current page, ordered by order
        channels = query.order_by('order')[skip:skip+size]

        # Create response with pagination links
        base_url = request.build_absolute_uri().split('?')[0]

        response_data = {
            'page': page,
            'total': total_items,
            'items': PlaylistChannelSerializer(channels, many=True).data,
            'links': {}
        }

        # Add pagination links
        if page > 1:
            response_data['links']['first'] = f"{base_url}?page=1&size={size}"
            response_data['links']['previous'] = f"{base_url}?page={page - 1}&size={size}"

        if page < total_pages:
            response_data['links']['next'] = f"{base_url}?page={page + 1}&size={size}"
            response_data['links']['last'] = f"{base_url}?page={total_pages}&size={size}"

        return Response(response_data)

    @action(detail=True, methods=['post'])
    def add_channel(self, request, pk=None):
        """
        Add a channel to a playlist.
        """
        # Check if playlist exists
        playlist = get_object_or_404(Playlist, pk=pk)

        serializer = PlaylistChannelCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Get the provider channel
            provider_channel_id = serializer.validated_data['provider_channel_id']

            # Get the maximum order value and add 1, or use 1 if no records exist
            max_order = PlaylistChannel.objects.filter(playlist=playlist).aggregate(Max('order'))['order__max']
            new_order = 1 if max_order is None else max_order + 1

            # Create the playlist channel
            channel = PlaylistChannel.objects.create(
                title=serializer.validated_data['title'],
                tvg_id=serializer.validated_data.get('tvg_id'),
                category=serializer.validated_data.get('category'),
                logo_url=serializer.validated_data.get('logo_url'),
                playlist=playlist,
                provider_channel_id=provider_channel_id,
                order=new_order
            )

            return Response(
                PlaylistChannelSerializer(channel).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChannelsViewSet(viewsets.ViewSet):
    """
    API endpoint for playlist channels.
    """
    @transaction.atomic
    def partial_update(self, request, pk=None):
        """
        Update a playlist channel.
        """
        channel = get_object_or_404(PlaylistChannel, pk=pk)
        serializer = PlaylistChannelUpdateSerializer(data=request.data)
        if serializer.is_valid():
            # Update the fields that are present in the request
            if 'title' in serializer.validated_data:
                channel.title = serializer.validated_data['title']
            if 'tvg_id' in serializer.validated_data:
                channel.tvg_id = serializer.validated_data['tvg_id']
            if 'category' in serializer.validated_data:
                channel.category = serializer.validated_data['category']
            if 'logo_url' in serializer.validated_data:
                channel.logo_url = serializer.validated_data['logo_url']
            if 'provider_channel_id' in serializer.validated_data:
                channel.provider_channel_id = serializer.validated_data['provider_channel_id']
            if 'order' in serializer.validated_data:
                new_order = serializer.validated_data['order']
                if new_order > channel.order:
                    first = channel.order + 1
                    last = new_order
                    change = -1
                else:
                    first = new_order
                    last = channel.order - 1
                    change = 1

                channel.playlist.channels.filter(order__gte=first, order__lte=last).update(order=F('order') + change)
                channel.order = new_order

            channel.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @transaction.atomic
    def destroy(self, request, pk=None):
        """
        Delete a playlist channel.
        """
        channel = get_object_or_404(PlaylistChannel, pk=pk)
        removed_order = channel.order
        channel.delete()
        
        # Reorder the remaining channels in the playlist
        channel.playlist.channels.filter(order__gt=removed_order).update(order=F('order') - 1)
        
        return Response(status=status.HTTP_204_NO_CONTENT)
