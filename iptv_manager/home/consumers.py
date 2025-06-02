import json
import asyncio
import datetime
from asyncio import Task

import psutil
from channels.generic.websocket import AsyncWebsocketConsumer


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