from django.urls import path, include

from .views import GuidesViewSet, CountriesViewSet, CategoriesViewSet, ChannelsViewSet, LanguagesViewSet
from main.custom_default_router import CustomDefaultRouter

router = CustomDefaultRouter()
router.register(r'guides', GuidesViewSet, basename='guides')
router.register(r'countries', CountriesViewSet, basename='countries')
router.register(r'categories', CategoriesViewSet, basename='categories')
router.register(r'channels', ChannelsViewSet, basename='channels')
router.register(r'languages', LanguagesViewSet, basename='languages')

urlpatterns = [
    path('', include(router.urls)),
]
