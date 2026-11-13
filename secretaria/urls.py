from django.urls import path
from . import views

app_name = 'secretaria'

urlpatterns = [
    path('', views.lista_demandas, name='lista_demandas'),
    path('demandas/<str:protocolo>/', views.detalhe_demanda, name='detalhe_demanda'),
    path('dashboard/', views.dashboard_indicadores, name='dashboard'),
    path('api/indicadores/', views.api_indicadores, name='api_indicadores'),
]
