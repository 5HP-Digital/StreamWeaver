import datetime
import psutil
from django.db import connection
from django.db.utils import OperationalError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ServerTimeSerializer, ResourceUtilizationSerializer, SettingsSerializer
from main.utils import ConfigStore


class ServerTimeView(APIView):
    """
    API view for server time
    """
    def get(self, request):
        now = datetime.datetime.now()
        serializer = ServerTimeSerializer({"time": now})
        return Response(serializer.data)


class ResourceUtilizationView(APIView):
    """
    API view for server resource utilization
    """
    def get(self, request):
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()

        data = {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used": memory.used / (1024 * 1024 * 1024),  # Convert to GB
            "memory_total": memory.total / (1024 * 1024 * 1024)  # Convert to GB
        }

        serializer = ResourceUtilizationSerializer(data)
        return Response(serializer.data)


class HealthCheckView(APIView):
    """
    API view for health check
    Verifies database connection, API and web responsiveness
    """
    def get(self, request):
        # Check database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                db_status = "ok"
        except OperationalError:
            db_status = "error"
            return Response(
                {"status": "error", "detail": "Database connection failed", "db_status": db_status},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        # If we got here, API is responsive
        api_status = "ok"

        # Web server is running if this endpoint is accessible
        web_status = "ok"

        return Response({
            "status": "ok",
            "db_status": db_status,
            "api_status": api_status,
            "web_status": web_status
        })


class SettingsView(APIView):
    """API view for IPTV settings."""

    def get(self, request):
        """Get the current settings."""
        config_store = ConfigStore()
        settings_data = config_store.get("iptv:settings")

        if not settings_data:
            # Default settings
            settings_data = {
                "sync_enabled": False,
                "sync_schedules": [],
                "allow_stream_auto_deletion": True,
                "sync_job_max_attempts": 3
            }
            # Save default settings to config store
            config_store.set("iptv:settings", settings_data)

        serializer = SettingsSerializer(data=settings_data)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.validated_data)

    def put(self, request):
        """Update the settings."""
        serializer = SettingsSerializer(data=request.data)
        if serializer.is_valid():
            config_store = ConfigStore()
            config_store.set("iptv:settings", serializer.validated_data)
            return Response(serializer.validated_data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
