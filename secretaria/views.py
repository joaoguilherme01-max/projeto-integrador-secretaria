from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .services import obter_indicadores_gestao


def dashboard_indicadores(request):
    """View para exibição do painel gerencial de indicadores."""
    indicadores = obter_indicadores_gestao()
    return render(request, 'secretaria/dashboard.html', {'indicadores': indicadores})


def api_indicadores(request):
    """Endpoint JSON com os indicadores para gráficos ou consumo assíncrono."""
    indicadores = obter_indicadores_gestao()
    return JsonResponse(indicadores)
