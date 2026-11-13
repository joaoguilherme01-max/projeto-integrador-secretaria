from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from .models import Demanda, Categoria
from .services import obter_indicadores_gestao, listar_demandas_filtradas


def lista_demandas(request):
    """
    Exibe a listagem tabular e pesquisável de demandas com filtros por:
    - Status
    - Responsável
    - Categoria
    - Prioridade
    - Período (data_inicio e data_fim)
    - Pesquisa por protocolo, solicitante, contato ou descrição
    """
    filtros = {
        'busca': request.GET.get('busca', ''),
        'status': request.GET.get('status', ''),
        'responsavel': request.GET.get('responsavel', ''),
        'categoria': request.GET.get('categoria', ''),
        'prioridade': request.GET.get('prioridade', ''),
        'data_inicio': request.GET.get('data_inicio', ''),
        'data_fim': request.GET.get('data_fim', ''),
    }

    demandas_qs = listar_demandas_filtradas(filtros)

    paginator = Paginator(demandas_qs, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categorias = Categoria.objects.filter(ativa=True).order_by('nome')
    responsaveis = User.objects.filter(is_active=True).order_by('first_name', 'username')

    context = {
        'page_obj': page_obj,
        'demandas': page_obj.object_list,
        'total_registros': paginator.count,
        'categorias': categorias,
        'responsaveis': responsaveis,
        'status_choices': Demanda.STATUS_CHOICES,
        'prioridade_choices': Demanda.PRIORIDADE_CHOICES,
        'filtros': filtros,
    }
    return render(request, 'secretaria/lista_demandas.html', context)


def detalhe_demanda(request, protocolo):
    """Exibe os detalhes e histórico completo de uma demanda."""
    demanda = get_object_or_404(
        Demanda.objects.select_related('categoria', 'responsavel').prefetch_related('historicos__usuario', 'anexos'),
        protocolo=protocolo
    )
    return render(request, 'secretaria/detalhe_demanda.html', {'demanda': demanda})


def dashboard_indicadores(request):
    """View para exibição do painel gerencial de indicadores."""
    indicadores = obter_indicadores_gestao()
    return render(request, 'secretaria/dashboard.html', {'indicadores': indicadores})


def api_indicadores(request):
    """Endpoint JSON com os indicadores para gráficos ou consumo assíncrono."""
    indicadores = obter_indicadores_gestao()
    return JsonResponse(indicadores)
