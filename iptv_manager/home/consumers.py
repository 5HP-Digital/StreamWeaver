import json
import asyncio
import datetime
from asyncio import Task

import psutil
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from provider_manager.models import ProviderSyncJob, JobState, Provider
from provider_manager.serializers import ProviderSyncJobSerializer, ProviderSerializer

ACTIVE_JOBS_GROUP = 'active_jobs'
JOB_DETAIL_GROUP_PREFIX = 'job_detail_'

class SystemStatsConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for system stats
    """
    send_stats_task: Task

    async def connect(self):
        """
        Called when the WebSocket is handshaking
        """
        await self.accept()
        self.send_stats_task = asyncio.create_task(self.send_stats())

    async def disconnect(self, close_code):
        """
        Called when the WebSocket closes
        """
        self.send_stats_task.cancel()

    async def send_stats(self):
        """
        Send system stats every second
        """
        try:
            while True:
                # Get current time
                now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # Get CPU and memory usage
                cpu_percent = psutil.cpu_percent()
                memory = psutil.virtual_memory()

                # Prepare data
                data = {
                    'time': now,
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_used': round(memory.used / (1024 * 1024 * 1024), 2),  # Convert to GB
                    'memory_total': round(memory.total / (1024 * 1024 * 1024), 2)  # Convert to GB
                }

                # Send data
                await self.send(text_data=json.dumps(data))

                # Wait for 1 second
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            # Task was cancelled, clean up
            pass


class ActiveJobsConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for active jobs
    """
    send_active_jobs_task: Task

    async def connect(self):
        """
        Called when the WebSocket is handshaking
        """
        # Join the active jobs group
        await self.channel_layer.group_add(
            ACTIVE_JOBS_GROUP,
            self.channel_name
        )

        await self.accept()

        # Start sending active jobs updates
        self.send_active_jobs_task = asyncio.create_task(self.send_active_jobs())

    async def disconnect(self, close_code):
        """
        Called when the WebSocket closes
        """
        # Leave the active jobs group
        await self.channel_layer.group_discard(
            ACTIVE_JOBS_GROUP,
            self.channel_name
        )

        # Cancel the task
        self.send_active_jobs_task.cancel()

    @database_sync_to_async
    def get_active_jobs(self):
        """
        Get all active jobs (those in Queued or InProgress state)
        """
        active_jobs = ProviderSyncJob.objects.filter(
            state__in=[JobState.QUEUED, JobState.IN_PROGRESS]
        ).select_related('provider')

        # Create a list of active jobs with their provider IDs
        active_jobs_data = []
        for job in active_jobs:
            job_serializer = ProviderSyncJobSerializer(job)
            active_jobs_data.append({
                'job': job_serializer.data,
                'provider_id': job.provider.id
            })

        return active_jobs_data

    async def send_active_jobs(self):
        """
        Send active jobs updates every 5 seconds
        """
        try:
            while True:
                # Get active jobs
                active_jobs = await self.get_active_jobs()

                # Prepare data
                data = {
                    'type': 'active_jobs_update',
                    'active_jobs': active_jobs
                }

                # Send data to the group
                await self.channel_layer.group_send(
                    ACTIVE_JOBS_GROUP,
                    data
                )

                # Wait for 5 seconds
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            # Task was cancelled, clean up
            pass

    async def active_jobs_update(self, event):
        """
        Handler for active_jobs_update messages
        """
        # Send the active jobs data to the WebSocket
        await self.send(text_data=json.dumps({
            'type': 'active_jobs_update',
            'active_jobs': event['active_jobs']
        }))
