from django.db.models import Count, Avg, F, ExpressionWrapper, DurationField
from django.utils import timezone
from .models import Demanda, Categoria


def obter_indicadores_gestao():
    """
    Calcula e consolida os indicadores gerenciais para a secretaria escolar:
    - Total de demandas abertas
    - Demandas por etapa (status)
    - Demandas atrasadas (prazo vencido e ainda abertas)
    - Tempo médio de atendimento (em dias/horas para demandas concluídas)
    - Volume por categoria
    - Distribuição por responsável
    """
    hoje = timezone.now().date()
    status_fechados = ['CONCLUIDA', 'CANCELADA']

    # 1. Total de demandas abertas
    demandas_abertas_qs = Demanda.objects.exclude(status__in=status_fechados)
    total_abertas = demandas_abertas_qs.count()

    # 2. Demandas atrasadas (abertas com prazo anterior a hoje)
    demandas_atrasadas_qs = demandas_abertas_qs.filter(prazo__lt=hoje)
    total_atrasadas = demandas_atrasadas_qs.count()

    # 3. Demandas por etapa (status)
    status_counts_dict = dict(
        Demanda.objects.values('status')
        .annotate(total=Count('id'))
        .values_list('status', 'total')
    )
    demandas_por_etapa = []
    for chave, rotulo in Demanda.STATUS_CHOICES:
        demandas_por_etapa.append({
            'status': chave,
            'nome': rotulo,
            'total': status_counts_dict.get(chave, 0)
        })

    # 4. Tempo médio de atendimento (demandas com data_conclusao)
    demandas_concluidas = Demanda.objects.filter(
        status='CONCLUIDA',
        data_conclusao__isnull=False
    ).annotate(
        tempo_atendimento=ExpressionWrapper(
            F('data_conclusao') - F('data_entrada'),
            output_field=DurationField()
        )
    )
    duracao_media = demandas_concluidas.aggregate(media=Avg('tempo_atendimento'))['media']

    if duracao_media:
        total_segundos = duracao_media.total_seconds()
        dias = int(total_segundos // 86400)
        horas = int((total_segundos % 86400) // 3600)
        tempo_medio_str = f"{dias}d {horas}h" if dias > 0 else f"{horas}h"
        tempo_medio_dias = round(total_segundos / 86400, 1)
    else:
        tempo_medio_str = "Sem dados"
        tempo_medio_dias = 0.0

    # 5. Volume por categoria
    categorias_qs = Categoria.objects.annotate(
        total_demandas=Count('demandas')
    ).order_by('-total_demandas')

    volume_por_categoria = [
        {'categoria': cat.nome, 'total': cat.total_demandas}
        for cat in categorias_qs
    ]

    # 6. Distribuição por responsável (inclui demandas não atribuídas)
    resp_counts = Demanda.objects.exclude(status__in=status_fechados).values(
        'responsavel__id', 'responsavel__username', 'responsavel__first_name', 'responsavel__last_name'
    ).annotate(total=Count('id')).order_by('-total')

    distribuicao_por_responsavel = []
    for r in resp_counts:
        if r['responsavel__id'] is None:
            nome_resp = 'Não atribuído'
        else:
            primeiro = r['responsavel__first_name'] or ''
            ultimo = r['responsavel__last_name'] or ''
            nome_resp = f"{primeiro} {ultimo}".strip() or r['responsavel__username']

        distribuicao_por_responsavel.append({
            'responsavel': nome_resp,
            'total': r['total']
        })

    return {
        'total_abertas': total_abertas,
        'total_atrasadas': total_atrasadas,
        'demandas_por_etapa': demandas_por_etapa,
        'tempo_medio_str': tempo_medio_str,
        'tempo_medio_dias': tempo_medio_dias,
        'volume_por_categoria': volume_por_categoria,
        'distribuicao_por_responsavel': distribuicao_por_responsavel,
    }




def listar_demandas_filtradas(filtros):
    """
    Filtra as demandas de acordo com os critérios informados:
    - status
    - responsavel (id do usuário ou 'sem_responsavel')
    - categoria (id da categoria)
    - prioridade
    - periodo (data_inicio e data_fim na data_entrada)
    - termo de busca (protocolo, solicitante ou contato)
    """
    from django.db.models import Q
    from datetime import datetime

    qs = Demanda.objects.select_related('categoria', 'responsavel').all()

    # Pesquisar protocolo ou solicitante
    busca = filtros.get('busca')
    if busca:
        busca = busca.strip()
        qs = qs.filter(
            Q(protocolo__icontains=busca) |
            Q(solicitante__icontains=busca) |
            Q(contato__icontains=busca) |
            Q(descricao__icontains=busca)
        )

    # Filtrar por status
    status = filtros.get('status')
    if status:
        qs = qs.filter(status=status)

    # Filtrar por responsável
    responsavel = filtros.get('responsavel')
    if responsavel:
        if responsavel == 'sem_responsavel':
            qs = qs.filter(responsavel__isnull=True)
        else:
            try:
                qs = qs.filter(responsavel_id=int(responsavel))
            except (ValueError, TypeError):
                pass

    # Filtrar por categoria
    categoria = filtros.get('categoria')
    if categoria:
        try:
            qs = qs.filter(categoria_id=int(categoria))
        except (ValueError, TypeError):
            pass

    # Filtrar por prioridade
    prioridade = filtros.get('prioridade')
    if prioridade:
        qs = qs.filter(prioridade=prioridade)

    # Filtrar por período (data_inicio e data_fim)
    data_inicio = filtros.get('data_inicio')
    if data_inicio:
        try:
            dt_ini = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            qs = qs.filter(data_entrada__date__gte=dt_ini)
        except (ValueError, TypeError):
            pass

    data_fim = filtros.get('data_fim')
    if data_fim:
        try:
            dt_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
            qs = qs.filter(data_entrada__date__lte=dt_fim)
        except (ValueError, TypeError):
            pass

    return qs.order_by('-data_entrada')



def obter_dados_tela_inicial():
    """
    Retorna os dados consolidados para a tela inicial:
    - Indicadores gerais (abertas, atrasadas, concluídas, tempo médio)
    - Listas recentes de:
        - Demandas abertas
        - Demandas atrasadas
        - Demandas concluídas
    """
    hoje = timezone.now().date()
    status_fechados = ['CONCLUIDA', 'CANCELADA']

    # Totalizadores para a área de indicadores
    demandas_abertas_qs = Demanda.objects.exclude(status__in=status_fechados).select_related('categoria', 'responsavel')
    total_abertas = demandas_abertas_qs.count()

    demandas_atrasadas_qs = demandas_abertas_qs.filter(prazo__lt=hoje)
    total_atrasadas = demandas_atrasadas_qs.count()

    demandas_concluidas_qs = Demanda.objects.filter(status='CONCLUIDA').select_related('categoria', 'responsavel')
    total_concluidas = demandas_concluidas_qs.count()

    total_geral = Demanda.objects.count()

    # Listagens para exibição na tela inicial (limitadas para visualização limpa)
    recentes_abertas = demandas_abertas_qs.order_by('-data_entrada')[:8]
    recentes_atrasadas = demandas_atrasadas_qs.order_by('prazo')[:8]
    recentes_concluidas = demandas_concluidas_qs.order_by('-data_conclusao', '-data_entrada')[:8]

    # Indicadores extras
    indicadores_completos = obter_indicadores_gestao()

    return {
        'total_abertas': total_abertas,
        'total_atrasadas': total_atrasadas,
        'total_concluidas': total_concluidas,
        'total_geral': total_geral,
        'recentes_abertas': recentes_abertas,
        'recentes_atrasadas': recentes_atrasadas,
        'recentes_concluidas': recentes_concluidas,
        'tempo_medio_str': indicadores_completos['tempo_medio_str'],
        'demandas_por_etapa': indicadores_completos['demandas_por_etapa'],
        'volume_por_categoria': indicadores_completos['volume_por_categoria'],
    }



def obter_quadro_kanban(filtros=None):
    """
    Retorna a estrutura de colunas do quadro Kanban com as demandas
    agrupadas por status, contendo todas as informações principais:
    - protocolo
    - tipo de solicitação (categoria)
    - prioridade
    - prazo
    - responsável
    - status
    """
    if filtros:
        demandas_qs = listar_demandas_filtradas(filtros)
    else:
        demandas_qs = Demanda.objects.select_related('categoria', 'responsavel').all().order_by('-data_entrada')

    # Agrupa as demandas em dicionário por status
    demandas_por_status = {chave: [] for chave, _ in Demanda.STATUS_CHOICES}
    for dem in demandas_qs:
        if dem.status in demandas_por_status:
            demandas_por_status[dem.status].append(dem)

    colunas = []
    for chave, rotulo in Demanda.STATUS_CHOICES:
        colunas.append({
            'status': chave,
            'titulo': rotulo,
            'demandas': demandas_por_status[chave],
            'total': len(demandas_por_status[chave]),
        })

    return colunas
