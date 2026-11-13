from django.urls import path
from . import views

app_name = 'secretaria'

urlpatterns = [
    path('dashboard/', views.dashboard_indicadores, name='dashboard'),
    path('api/indicadores/', views.api_indicadores, name='api_indicadores'),
]

