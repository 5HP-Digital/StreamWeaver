import datetime
import psutil
from django.db import connection
from django.db.utils import OperationalError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ServerTimeSerializer, ResourceUtilizationSerializer


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
