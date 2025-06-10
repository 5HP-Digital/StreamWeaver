"""
ASGI config for iptv_manager project.
"""

import os

from channels.security.websocket import AllowedHostsOriginValidator
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from django.urls import path
from home.consumers import SystemStatsConsumer, ActiveJobsConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iptv_manager.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter([
                    path('ws/system-stats/', SystemStatsConsumer.as_asgi()),
                    path('ws/active-jobs/', ActiveJobsConsumer.as_asgi()),
                ]
            )
        )
    ),
})
