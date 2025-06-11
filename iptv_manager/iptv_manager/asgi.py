"""
ASGI config for iptv_manager project.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iptv_manager.settings')
django_asgi_app = get_asgi_application()

from django.conf import settings # DO NOT REMOVE THIS LINE!
from channels.security.websocket import AllowedHostsOriginValidator
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from home.consumers import SystemStatsConsumer, ActiveJobsConsumer

application = ProtocolTypeRouter({
    "http": django_asgi_app,
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
