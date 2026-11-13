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

