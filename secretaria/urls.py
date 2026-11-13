from django.urls import path
from . import views

app_name = 'secretaria'

urlpatterns = [
    # Autenticação
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Páginas internas protegidas
    path('', views.index_view, name='index'),
    path('quadro/', views.quadro_kanban, name='quadro_kanban'),
    path('demandas/', views.lista_demandas, name='lista_demandas'),
    path('demandas/nova/', views.criar_demanda, name='criar_demanda'),
    path('demandas/<str:protocolo>/', views.detalhe_demanda, name='detalhe_demanda'),
    path('demandas/<str:protocolo>/editar/', views.editar_demanda, name='editar_demanda'),

    # Painel restrito a Gestores e Administradores
    path('dashboard/', views.dashboard_indicadores, name='dashboard'),
    path('api/indicadores/', views.api_indicadores, name='api_indicadores'),
]
