from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from math import ceil
import json
from django.conf import settings

from .models import PlaylistSource, PlaylistSourceChannel, Job, JobState
from .rabbitmq import publish_message
from .serializers import (
    PlaylistSourceSerializer,
    PlaylistSourceCreateSerializer,
    PlaylistSourceUpdateSerializer,
    PlaylistSourceChannelSerializer
)
from iptv_manager.utils import ConfigStore

class SourcesViewSet(viewsets.ViewSet):
    """
    API endpoint for playlist sources.
    Based on IPTV.PlaylistManager/Controllers/SourcesControllers.cs
    """

    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """
        Manually trigger a playlist source synchronization.

        Returns:
            Response: A response containing the job ID and initial status.
        """
        source = get_object_or_404(PlaylistSource, pk=pk)

        # Check if source is enabled
        if not source.is_enabled:
            return Response(
                {"error": "Cannot sync disabled playlist source"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if there's already a sync job in progress or pending for this source
        active_jobs = source.jobs.filter(state__in=[JobState.PENDING, JobState.IN_PROGRESS])

        if active_jobs.exists():
            job = active_jobs.first()
            return Response({
                "job_id": str(job.job_id),
                "status": job.state,
                "message": f"Sync already {job.state.lower()} for this source"
            })

        # Retrieve iptv settings
        config_store = ConfigStore()
        settings_data = config_store.get("iptv:settings")

        # Create the job
        job = Job.objects.create(
            state=JobState.PENDING,
            context="{}"  # Temporary, will be updated after job creation
        )

        # Associate the job with the source
        source.jobs.add(job)

        # Create a new Job for the current source with default values
        job_context = {
            "jobId": job.job_id,
            "type": "PlaylistSync",
            "options": {
                "sourceId": source.id,
                "allowChannelAutoDeletion": settings_data.get("allow_channel_auto_deletion", True),
            }
        }

        # Update the job context
        job.context = json.dumps(job_context)
        job.save()

        # Publish the message to RabbitMQ
        publish_success = publish_message(
            settings.RABBITMQ_QUEUE_JOBS,
            job_context
        )

        if not publish_success:
            # If publishing fails, mark the job as failed
            job.state = JobState.FAILED
            job.error = "Failed to publish message to RabbitMQ"
            job.save()

            return Response({
                "job_id": str(job.job_id),
                "status": "failed",
                "message": "Failed to queue sync job"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "job_id": str(job.job_id),
            "status": "queued",
            "message": "Sync job queued successfully"
        })

    @action(detail=True, methods=['get'])
    def sync_status(self, request, pk=None):
        """
        Get the status of a sync job for a playlist source.

        Query Parameters:
            job_id: The UUID of the job to check.

        Returns:
            Response: A response containing the job status.
        """
        job_id = request.query_params.get('job_id')
        if not job_id:
            return Response(
                {"error": "job_id query parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Get the job by UUID
            job = Job.objects.get(job_id=job_id)

            # Check the job state
            if job.state == JobState.PENDING:
                return Response({
                    "job_id": str(job.job_id),
                    "status": "pending",
                    "message": "Sync job is pending"
                })
            elif job.state == JobState.IN_PROGRESS:
                return Response({
                    "job_id": str(job.job_id),
                    "status": "in_progress",
                    "message": "Sync job is in progress"
                })
            elif job.state == JobState.COMPLETED:
                return Response({
                    "job_id": str(job.job_id),
                    "status": "completed",
                    "success": True,
                    "message": "Sync completed successfully"
                })
            elif job.state == JobState.FAILED:
                return Response({
                    "job_id": str(job.job_id),
                    "status": "completed",
                    "success": False,
                    "message": f"Sync failed: {job.error or 'Unknown error'}"
                })
            else:
                return Response({
                    "job_id": str(job.job_id),
                    "status": "unknown",
                    "message": f"Unknown job state: {job.state}"
                })
        except Job.DoesNotExist:
            return Response({
                "job_id": job_id,
                "status": "error",
                "message": "Job not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "job_id": job_id,
                "status": "error",
                "message": f"Error checking job status: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
        source = get_object_or_404(PlaylistSource.objects.prefetch_related('jobs'), pk=pk)
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
