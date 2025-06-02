from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('server-time/', views.ServerTimeView.as_view(), name='server-time'),
    path('resource-utilization/', views.ResourceUtilizationView.as_view(), name='resource-utilization'),
    path('health/', views.HealthCheckView.as_view(), name='health'),
]
