from django.shortcuts import render
from django.conf import settings


def index(request):
    """
    View for the homepage
    """
    return render(request, 'home/index.html')


def iptv(request):
    """
    View for the IPTV page
    """
    context = {
        'playlist_manager_url': settings.PLAYLIST_MANAGER_URL
    }
    return render(request, 'home/iptv.html', context)
