from django.shortcuts import render


def index(request):
    """
    View for the homepage
    """
    return render(request, 'home/index.html')


def providers(request):
    """
    View for the Providers page
    """
    return render(request, 'home/providers.html')
