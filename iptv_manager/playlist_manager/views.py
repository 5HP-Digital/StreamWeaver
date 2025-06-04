from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from math import ceil

from .models import PlaylistSource, PlaylistSourceChannel
from .serializers import (
    PlaylistSourceSerializer,
    PlaylistSourceCreateSerializer,
    PlaylistSourceUpdateSerializer,
    PlaylistSourceChannelSerializer
)


class SourcesViewSet(viewsets.ViewSet):
    """
    API endpoint for playlist sources.
    Based on IPTV.PlaylistManager/Controllers/SourcesControllers.cs
    """

    def list(self, request):
        """
        Get all playlist sources.
        """
        sources = PlaylistSource.objects.all()
        serializer = PlaylistSourceSerializer(sources, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """
        Get a specific playlist source by ID.
        """
        source = get_object_or_404(PlaylistSource.objects.prefetch_related('invocations'), pk=pk)
        serializer = PlaylistSourceSerializer(source)
        return Response(serializer.data)

    def create(self, request):
        """
        Create a new playlist source.
        """
        serializer = PlaylistSourceCreateSerializer(data=request.data)
        if serializer.is_valid():
            source = serializer.save()
            return Response(
                PlaylistSourceSerializer(source).data, 
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        """
        Update a playlist source.
        """
        source = get_object_or_404(PlaylistSource, pk=pk)
        serializer = PlaylistSourceUpdateSerializer(source, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        """
        Delete a playlist source.
        """
        source = get_object_or_404(PlaylistSource, pk=pk)
        source.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChannelsViewSet(viewsets.ViewSet):
    """
    API endpoint for playlist source channels.
    Based on IPTV.PlaylistManager/Controllers/ChannelsControllers.cs
    """

    def list(self, request, source_id=None):
        """
        Get channels for a specific playlist source with pagination.
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

        # Check if source exists
        source = get_object_or_404(PlaylistSource, pk=source_id)

        # Get total count of channels for this source
        query = PlaylistSourceChannel.objects.filter(source=source)
        total_items = query.count()

        # Calculate pagination values
        total_pages = ceil(total_items / size)
        skip = (page - 1) * size

        # Get the channels for the current page
        channels = query.order_by('tvg_id')[skip:skip+size]

        # Create response with pagination links
        base_url = request.build_absolute_uri().split('?')[0]

        response_data = {
            'page': page,
            'total': total_items,
            'items': PlaylistSourceChannelSerializer(channels, many=True).data,
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
