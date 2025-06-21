from django.db.models import Count, Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from math import ceil

from .models import Guide, Channel, Country, Category
from .serializers import CountrySerializer, CategorySerializer, ChannelSerializer, GuideSerializer
from job_manager.models import Job, JobState, JobType
from job_manager.serializers import JobSerializer


class CountriesViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for countries.
    """
    queryset = Country.objects.all().order_by('name')
    serializer_class = CountrySerializer


class CategoriesViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for categories.
    """
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer


class ChannelsViewSet(viewsets.ViewSet):
    """
    API endpoint for channels.
    """
    serializer_class = ChannelSerializer

    def list(self, request):
        """
        Get a paginated list of channels with optional filtering.
        """
        # Validate pagination parameters
        page = int(request.query_params.get('page', 1))
        size = int(request.query_params.get('page_size', 20))

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

        queryset = Channel.objects.all().order_by('name')

        # Text search in xmltv_id, name, network
        q = request.query_params.get('q')
        if q:
            queryset = queryset.filter(
                Q(xmltv_id__icontains=q) | 
                Q(name__icontains=q) | 
                Q(network__icontains=q)
            )

        # Filter by countries
        countries = request.query_params.getlist('country')
        if countries:
            queryset = queryset.filter(country__in=countries)

        # Filter by categories
        categories = request.query_params.getlist('category')
        if categories:
            # Since categories is a comma-separated string, we need to filter differently
            category_queries = [Q(categories__icontains=category) for category in categories]
            query = category_queries.pop()
            for categoryQuery in category_queries:
                query |= categoryQuery
            queryset = queryset.filter(query)

        # Filter by launched_at greater than or equal to
        launched_gte = request.query_params.get('launched_gte')
        if launched_gte:
            queryset = queryset.filter(launched_at__gte=launched_gte)

        # Get total count
        total_items = queryset.count()

        # Calculate pagination values
        total_pages = ceil(total_items / size) if total_items > 0 else 1
        skip = (page - 1) * size

        # Get the channels for the current page
        channels = queryset[skip:skip+size]

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
            'items': ChannelSerializer(channels, many=True).data,
            'links': {}
        }

        # Add pagination links
        if page > 1:
            response_data['links']['first'] = f"{base_url}{query_prefix}page=1"
            response_data['links']['previous'] = f"{base_url}{query_prefix}page={page - 1}"

        if page < total_pages:
            response_data['links']['next'] = f"{base_url}{query_prefix}page={page + 1}"
            response_data['links']['last'] = f"{base_url}{query_prefix}page={total_pages}"

        return Response(response_data)


class GuidesViewSet(viewsets.ViewSet):
    """
    API endpoint for guides.
    """

    def list(self, request):
        """
        Get a paginated list of guides with optional filtering.
        """
        # Validate pagination parameters
        page = int(request.query_params.get('page', 1))
        size = int(request.query_params.get('page_size', 20))

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

        queryset = Guide.objects.all().order_by('site_name')

        # Text search in site, site_id, site_name, xmltv_id
        q = request.query_params.get('q')
        if q:
            queryset = queryset.filter(
                Q(site__icontains=q) | 
                Q(site_id__icontains=q) | 
                Q(site_name__icontains=q) |
                Q(xmltv_id__icontains=q)
            )

        # Filter by language
        lang = request.query_params.get('lang')
        if lang:
            queryset = queryset.filter(lang=lang)

        # Filter by channel (xmltv_id)
        channel = request.query_params.get('channel')
        if channel:
            queryset = queryset.filter(xmltv_id=channel)

        # Get total count
        total_items = queryset.count()

        # Calculate pagination values
        total_pages = ceil(total_items / size) if total_items > 0 else 1
        skip = (page - 1) * size

        # Get the guides for the current page
        guides = queryset[skip:skip+size]

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
            'items': GuideSerializer(guides, many=True).data,
            'links': {}
        }

        # Add pagination links
        if page > 1:
            response_data['links']['first'] = f"{base_url}{query_prefix}page=1"
            response_data['links']['previous'] = f"{base_url}{query_prefix}page={page - 1}"

        if page < total_pages:
            response_data['links']['next'] = f"{base_url}{query_prefix}page={page + 1}"
            response_data['links']['last'] = f"{base_url}{query_prefix}page={total_pages}"

        return Response(response_data)

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


class LanguagesViewSet(viewsets.ViewSet):
    """
    API endpoint for languages.
    """

    def list(self, request):
        languages = Guide.objects.values('lang').order_by('lang').values_list('lang', flat=True).distinct()

        response_data = {
            'items': languages,
        }
        return Response(response_data, status=status.HTTP_200_OK)