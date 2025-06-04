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
    return render(request, 'home/iptv.html')
