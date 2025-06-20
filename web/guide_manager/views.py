from django.db.models import Count
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Guide, Channel, Country, Category
from job_manager.models import Job, JobState, JobType
from job_manager.serializers import JobSerializer


class GuidesViewSet(viewsets.ViewSet):
    """
    API endpoint for guides.
    """

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get statistics about guides, channels, countries, and categories.
        
        Returns:
            Response: A response containing counts of entities and job information.
        """
        # Get counts of entities
        guides_count = Guide.objects.count()
        channels_count = Channel.objects.count()
        countries_count = Country.objects.count()
        categories_count = Category.objects.count()
        
        # Get the last completed EPG data sync job
        last_completed_job = Job.objects.filter(
            type=JobType.EPG_DATA_SYNC,
            state=JobState.COMPLETED
        ).order_by('-updated_at').first()
        
        # Get the most recent active EPG data sync job
        active_job = Job.objects.filter(
            type=JobType.EPG_DATA_SYNC,
            state__in=[JobState.QUEUED, JobState.IN_PROGRESS]
        ).order_by('-created_at').first()
        
        response_data = {
            'guides': guides_count,
            'channels': channels_count,
            'countries': countries_count,
            'categories': categories_count,
            'last_synced': last_completed_job.updated_at if last_completed_job else None,
            'active_job': JobSerializer(active_job).data if active_job else None
        }
        
        return Response(response_data)
    
    @action(detail=False, methods=['post'])
    def sync(self, request):
        """
        Manually trigger an EPG data synchronization.
        
        Returns:
            Response: A response containing the job ID and initial status.
        """
        # Check if there's already a sync job in progress or queued
        active_jobs = Job.objects.filter(
            type=JobType.EPG_DATA_SYNC,
            state__in=[JobState.QUEUED, JobState.IN_PROGRESS]
        )
        
        if active_jobs.exists():
            job = active_jobs.first()
            return Response({
                "job_id": str(job.job_id),
                "status": job.state,
                "message": job.status_description
            })
        
        # Create the job
        job = Job.objects.create(
            type=JobType.EPG_DATA_SYNC,
            state=JobState.QUEUED,
            max_attempts=1  # when running manual sync, allow one failure only
        )
        
        return Response({
            "job_id": str(job.job_id),
            "status": "queued",
            "message": "EPG data sync job queued successfully"
        })