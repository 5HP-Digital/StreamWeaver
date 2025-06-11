from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from math import ceil

from .models import Provider, ProviderChannel, ProviderSyncJob, JobState
from .serializers import (
    ProviderSerializer,
    ProviderCreateSerializer,
    ProviderUpdateSerializer,
    ProviderChannelSerializer,
    ProviderSyncJobSerializer
)
from iptv_manager.utils import ConfigStore

class ProvidersViewSet(viewsets.ViewSet):
    """
    API endpoint for providers.
    Based on IPTV.PlaylistManager/Controllers/SourcesControllers.cs
    """

    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """
        Manually trigger a provider synchronization.

        Returns:
            Response: A response containing the job ID and initial status.
        """
        provider = get_object_or_404(Provider, pk=pk)

        # Check if provider is enabled
        if not provider.is_enabled:
            return Response(
                {"error": "Cannot sync disabled service provider"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if there's already a sync job in progress or queued for this provider
        active_jobs = provider.jobs.filter(state__in=[JobState.QUEUED, JobState.IN_PROGRESS])

        if active_jobs.exists():
            job = active_jobs.first()
            return Response({
                "job_id": str(job.job_id),
                "status": job.state,
                "message": job.status_description
            })

        # Retrieve iptv settings
        config_store = ConfigStore()
        settings_data = config_store.get("iptv:settings")

        # Create the job
        job = provider.jobs.create(
            state=JobState.QUEUED,
            max_attempts=1, # when running manual sync, allow one failure only
            allow_channel_auto_deletion=settings_data.get("allow_channel_auto_deletion")
        )

        job.save()

        return Response({
            "job_id": str(job.job_id),
            "status": "queued",
            "message": "Sync job queued successfully"
        })

    @action(detail=True, methods=['get'])
    def sync_status(self, request, pk=None):
        """
        Get the status of a sync job for a provider.

        Query Parameters:
            job_id: The UUID of the job to check.

        Returns:
            Response: A response containing the job status.
        """

        provider = get_object_or_404(Provider, pk=pk)
        job_id = request.query_params.get('job_id')

        try:
            if job_id:
                # Get the job by UUID
                job = provider.jobs.filter(job_id=job_id).first()
            else:
                if provider.jobs.exists():
                    # Get the most recent job
                    job = provider.jobs.order_by('-created_at').first()
                else:
                    return Response({
                        "error": "Job not found"
                    }, status=status.HTTP_404_NOT_FOUND)

            # Check the job state
            if job.state == JobState.QUEUED:
                return Response({
                    "job_id": str(job.job_id),
                    "status": "queued",
                    "message": job.status_description or "Sync job queued successfully"
                })
            elif job.state == JobState.IN_PROGRESS:
                return Response({
                    "job_id": str(job.job_id),
                    "status": "in_progress",
                    "message": job.status_description
                })
            elif job.state == JobState.COMPLETED:
                return Response({
                    "job_id": str(job.job_id),
                    "status": "completed",
                    "success": True,
                    "message": job.status_description
                })
            elif job.state == JobState.FAILED:
                return Response({
                    "job_id": str(job.job_id),
                    "status": "completed",
                    "success": False,
                    "message": job.status_description
                })
            else:
                return Response({
                    "job_id": str(job.job_id),
                    "status": "unknown",
                    "message": f"Unknown job state: {job.state}"
                })
        except ProviderSyncJob.DoesNotExist:
            return Response({
                "job_id": job_id,
                "status": "error",
                "message": "Job not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "error": f"Error checking job status: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def list(self, request):
        """
        Get all providers.
        """
        providers = Provider.objects.all()
        serializer = ProviderSerializer(providers, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """
        Get a specific provider by ID.
        """
        provider = get_object_or_404(Provider.objects.prefetch_related('jobs'), pk=pk)
        serializer = ProviderSerializer(provider)
        return Response(serializer.data)

    def create(self, request):
        """
        Create a new provider.
        """
        serializer = ProviderCreateSerializer(data=request.data)
        if serializer.is_valid():
            provider = serializer.save()
            return Response(
                ProviderSerializer(provider).data, 
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        """
        Update a provider.
        """
        provider = get_object_or_404(Provider, pk=pk)
        serializer = ProviderUpdateSerializer(provider, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        """
        Delete a provider.
        """
        provider = get_object_or_404(Provider, pk=pk)
        provider.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def jobs(self, request, pk=None):
        """
        Get sync job history for a provider with pagination.

        Active jobs (those in Queued or InProgress state) are returned separately
        from the paginated history list.

        Query Parameters:
            page: The page number (default: 1)
            size: The page size (default: 10)

        Returns:
            Response: A response containing:
                - active_jobs: A list of active sync jobs for the provider
                - page: The current page number
                - total: The total number of non-active jobs
                - items: A paginated list of non-active sync jobs
                - links: Pagination links
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

        # Check if provider exists
        provider = get_object_or_404(Provider, pk=pk)

        # Get active jobs (Queued or InProgress)
        active_jobs = ProviderSyncJob.objects.filter(
            provider=provider,
            state__in=[JobState.QUEUED, JobState.IN_PROGRESS]
        ).order_by('-updated_at')

        # Get non-active jobs (Completed or Failed)
        non_active_jobs = ProviderSyncJob.objects.filter(
            provider=provider,
            state__in=[JobState.COMPLETED, JobState.FAILED]
        )

        # Get total count of non-active jobs
        total_items = non_active_jobs.count()

        # Calculate pagination values
        total_pages = ceil(total_items / size) if total_items > 0 else 1
        skip = (page - 1) * size

        # Get the non-active jobs for the current page, ordered by updated_at descending
        paginated_jobs = non_active_jobs.order_by('-updated_at')[skip:skip+size]

        # Create response with pagination links
        base_url = request.build_absolute_uri().split('?')[0]

        response_data = {
            'page': page,
            'total': total_items,
            'items': ProviderSyncJobSerializer(paginated_jobs, many=True).data,
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


class ProviderChannelsViewSet(viewsets.ViewSet):
    """
    API endpoint for provider channels.
    Based on IPTV.PlaylistManager/Controllers/ChannelsControllers.cs
    """

    def list(self, request, provider_id=None):
        """
        Get channels for a specific provider with pagination.
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

        # Check if provider exists
        provider = get_object_or_404(Provider, pk=provider_id)

        # Get total count of channels for this provider
        query = ProviderChannel.objects.filter(provider=provider)
        total_items = query.count()

        # Calculate pagination values
        total_pages = ceil(total_items / size)
        skip = (page - 1) * size

        # Get the channels for the current page
        channels = query.order_by('group', 'title')[skip:skip+size]

        # Create response with pagination links
        base_url = request.build_absolute_uri().split('?')[0]

        response_data = {
            'page': page,
            'total': total_items,
            'items': ProviderChannelSerializer(channels, many=True).data,
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
