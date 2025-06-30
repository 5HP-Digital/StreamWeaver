from fileinput import filename

from django.db import transaction
from django.db.models import Max, F, Q
from django.shortcuts import get_object_or_404
from django.http import FileResponse, Http404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from math import ceil
import os
from django.conf import settings

from .models import Playlist, PlaylistChannel
from .serializers import (
    PlaylistSerializer,
    PlaylistCreateSerializer,
    PlaylistUpdateSerializer,
    PlaylistChannelSerializer,
    PlaylistChannelCreateSerializer,
    PlaylistChannelUpdateSerializer,
    ProviderStreamWithDetailsSerializer
)
from job_manager.models import JobState, JobType
from provider_manager.models import ProviderStream


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
                name=serializer.validated_data['name'],
                starting_channel_number=serializer.validated_data.get('starting_channel_number', 1),
                default_lang=serializer.validated_data.get('default_lang', 'en')
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
            if 'name' in serializer.validated_data:
                playlist.name = serializer.validated_data['name']
            if 'starting_channel_number' in serializer.validated_data:
                playlist.starting_channel_number = serializer.validated_data['starting_channel_number']
            if 'default_lang' in serializer.validated_data:
                playlist.default_lang = serializer.validated_data['default_lang']

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

    @action(detail=True, methods=['get', 'post'])
    def channels(self, request, pk=None):
        """
        GET: Get a paginated list of channels for a specific playlist.
        POST: Add a channel to a playlist.

        Query Parameters (GET only):
            page: The page number (default: 1)
            size: The page size (default: 10)
        """
        # Check if playlist exists
        playlist = get_object_or_404(Playlist, pk=pk)

        if request.method == 'GET':
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

            # Get total count of channels for this playlist
            query = PlaylistChannel.objects.filter(playlist=playlist)
            total_items = query.count()

            # Calculate pagination values
            total_pages = ceil(total_items / size) if total_items > 0 else 1
            skip = (page - 1) * size

            # Get the channels for the current page, ordered by order
            channels = query.select_related('provider_stream', 'provider_stream__provider', 'guide').order_by('order')[skip:skip+size]

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
        elif request.method == 'POST':
            serializer = PlaylistChannelCreateSerializer(data=request.data)
            if serializer.is_valid():
                # Get the provider channel
                provider_stream_id = serializer.validated_data['provider_stream_id']

                # Get the maximum order value and add 1, or use 1 if no records exist
                max_order = PlaylistChannel.objects.filter(playlist=playlist).aggregate(Max('order'))['order__max']
                new_order = 1 if max_order is None else max_order + 1

                # Create the playlist channel
                channel = PlaylistChannel.objects.create(
                    title=serializer.validated_data.get('title'),
                    category=serializer.validated_data.get('category'),
                    logo_url=serializer.validated_data.get('logo_url'),
                    playlist=playlist,
                    provider_stream_id=provider_stream_id,
                    order=new_order
                )

                return Response(
                    PlaylistChannelSerializer(channel).data,
                    status=status.HTTP_201_CREATED
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


    @action(detail=True, methods=['get'])
    def categories(self, request, pk=None):
        """
        Retrieves a list of existing playlist channel categories.
        """
        playlist = get_object_or_404(Playlist, pk=pk)

        categories = PlaylistChannel.objects.filter(playlist=playlist, category__isnull=False).order_by('category').values_list('category', flat=True).distinct()
        response_data = {
            'items': categories,
        }
        return Response(response_data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def available_streams(self, request, pk=None):
        """
        Get a paginated list of unassigned streams for a specific playlist.

        Query Parameters:
            page: The page number (default: 1)
            size: The page size (default: 10)
            provider_id: Filter by provider ID (optional)
            is_active: Filter by active status (optional, true/false)
            q: Text search in title, group, and tvg_id (optional)
            sort_by: Field(s) to sort by, comma-separated (optional, default: group,title, options: title,tvg_id,group,is_active)
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

        # Validate sorting parameter
        sort_param = request.query_params.get('sort_by', 'group,title')
        sort_fields = sort_param.split(',')

        # Validate sort fields against the serializer fields
        valid_sort_fields = ['title', 'tvg_id', 'group', 'is_active']
        order_by_fields = []

        for field in sort_fields:
            clean_field = field[1:] if field.startswith('-') else field
            if clean_field in valid_sort_fields:
                order_by_fields.append(field)  # Keep the '-' prefix for descending order
            else:
                return Response(
                    {"error": f"Invalid sort field: {field}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        playlist = get_object_or_404(Playlist, pk=pk)

        # Get all provider streams that are not assigned to any channel in this playlist
        # Start with all streams
        query = ProviderStream.objects.all()

        # Exclude streams that are already assigned to this playlist
        assigned_stream_ids = PlaylistChannel.objects.filter(playlist=playlist).values_list('provider_stream_id', flat=True)
        query = query.exclude(id__in=assigned_stream_ids)

        # Apply filters if provided
        provider_id = request.query_params.get('provider_id')
        if provider_id:
            query = query.filter(provider_id=provider_id)

        is_active = request.query_params.get('is_active')
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            query = query.filter(is_active=is_active_bool)

        q = request.query_params.get('q')
        if q:
            query = query.filter(Q(title__icontains=q) | Q(tvg_id__icontains=q) | Q(group__icontains=q))

        # If no sort fields, use default
        if not order_by_fields:
            order_by_fields = ['group', 'title']

        query = query.select_related('provider').order_by(*order_by_fields)

        # Get total count
        total_items = query.count()

        # Calculate pagination values
        total_pages = ceil(total_items / size) if total_items > 0 else 1
        skip = (page - 1) * size

        # Get the streams for the current page
        streams = query[skip:skip+size]

        # Create response with pagination links
        base_url = request.build_absolute_uri().split('?')[0]
        query_params = request.query_params.copy()

        # Remove page from query params for building links
        if 'page' in query_params:
            del query_params['page']

        # Build query string for links
        query_string = '&'.join([f"{k}={v}" for k, v in query_params.items()])
        query_prefix = '?' + query_string + '&' if query_string else '?'

        response_data = {
            'page': page,
            'total': total_items,
            'items': ProviderStreamWithDetailsSerializer(streams, many=True).data,
            'links': {}
        }

        # Add pagination links
        if page > 1:
            response_data['links']['first'] = f"{base_url}{query_prefix}page=1"
            response_data['links']['previous'] = f"{base_url}{query_prefix}page={page - 1}"

        if page < total_pages:
            response_data['links']['next'] = f"{base_url}{query_prefix}page={page + 1}"
            response_data['links']['last'] = f"{base_url}{query_prefix}page={total_pages}"

        return Response(response_data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def epg_sync(self, request, pk=None):
        """
        Manually trigger a playlist EPG generation job for a specific playlist.

        Returns:
            Response: A response containing the job ID and initial status.
        """
        playlist = get_object_or_404(Playlist, pk=pk)

        # Check if there's already a sync job in progress or queued for this playlist
        active_jobs = playlist.jobs.filter(state__in=[JobState.QUEUED, JobState.IN_PROGRESS])

        if active_jobs.exists():
            job = active_jobs.first()
            return Response({
                "job_id": str(job.job_id),
                "status": job.state,
                "message": job.status_description
            })

        # Create the job
        job = playlist.jobs.create(
            type=JobType.PLAYLIST_EPG_GEN,
            state=JobState.QUEUED,
            max_attempts=1, # when running manual sync, allow one failure only
        )

        return Response({
            "job_id": str(job.job_id),
            "status": "queued",
            "message": "Generation job queued successfully"
        })

    @action(detail=True, methods=['get'], url_path='guide.xml')
    def epg(self, request, pk=None):
        """
        Download the guide.xml file for a specific playlist if it exists.

        Returns:
            FileResponse: The guide.xml file if it exists
            Http404: If the file doesn't exist
        """
        _ = get_object_or_404(Playlist, pk=pk)

        # Construct the file path
        file_path = os.path.join(settings.CONFIG_DIR, f"playlists/{pk}/guide.xml")

        # Check if the file exists
        if not os.path.exists(file_path):
            raise Http404("Guide.xml file not found")

        # Return the file as a response
        return FileResponse(open(file_path, 'rb'), content_type='application/xml', as_attachment=True, filename=f"playlist_{pk}_guide.xml")


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
            if 'category' in serializer.validated_data:
                channel.category = serializer.validated_data['category']
            if 'logo_url' in serializer.validated_data:
                channel.logo_url = serializer.validated_data['logo_url']
            if 'provider_stream_id' in serializer.validated_data:
                channel.provider_stream_id = serializer.validated_data['provider_stream_id']
            if 'order' in serializer.validated_data:
                new_order = serializer.validated_data['order']

                # Validate
                count = channel.playlist.channels.count()
                if count == 1:
                    return Response(
                        { "error": "Cannot reorder the first channel." },
                        status=status.HTTP_400_BAD_REQUEST)
                if new_order > count:
                    return Response(
                        { "error": f"Order must be between 1 and {count}." },
                        status=status.HTTP_400_BAD_REQUEST)

                if new_order > channel.order:
                    first = channel.order + 1
                    last = new_order
                    change = -1
                else:
                    first = new_order
                    last = channel.order - 1
                    change = 1

                # Set a temporary order that won't conflict with any existing orders
                # Use a negative number that's guaranteed to be unique
                channel.order = -channel.pk
                channel.save(update_fields=['order'])

                # Update other channels' orders
                query = channel.playlist.channels.filter(order__gte=first, order__lte=last)
                query = reversed(query) if change > 0 else query
                for ch in query:
                    ch.order += change
                    ch.save()

                # Now set the final order
                channel.order = new_order
            if 'guide_id' in serializer.validated_data:
                channel.guide_id = serializer.validated_data['guide_id']

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
