from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .models import Demanda, Categoria, Historico
from .forms import DemandaForm
from .services import obter_indicadores_gestao, listar_demandas_filtradas, obter_dados_tela_inicial
from .decorators import perfil_necessario


def login_view(request):
    """View de autenticação individual com usuário e senha."""
    if request.user.is_authenticated:
        return redirect('secretaria:index')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            usuario = form.get_user()
            perfil = getattr(usuario, 'perfil', None)

            # Verifica se o perfil está ativo (superusuários têm bypass)
            if not usuario.is_superuser and perfil and not perfil.ativo:
                messages.error(request, 'Esta conta está inativa. Contate o administrador.')
                return render(request, 'secretaria/login.html', {'form': form})

            login(request, usuario)
            messages.success(request, f'Bem-vindo(a), {usuario.get_full_name() or usuario.username}!')
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('secretaria:index')
        else:
            messages.error(request, 'Usuário ou senha inválidos.')
    else:
        form = AuthenticationForm(request)

    return render(request, 'secretaria/login.html', {'form': form})


def logout_view(request):
    """Encerra a sessão do usuário de forma segura."""
    logout(request)
    messages.info(request, 'Você encerrou sua sessão com segurança.')
    return redirect('secretaria:login')


@login_required
def index_view(request):
    """
    Tela inicial do sistema com:
    - Área de indicadores gerais
    - Abas/Seções para Demandas Abertas, Atrasadas e Concluídas
    """
    dados = obter_dados_tela_inicial()
    context = {
        'dados': dados,
        'perfil_usuario': getattr(request.user, 'perfil', None),
    }
    return render(request, 'secretaria/index.html', context)


@login_required
def criar_demanda(request):
    """
    Formulário para registrar uma nova solicitação da secretaria.
    Gera protocolo sequencial e histórico automático de entrada.
    """
    if request.method == 'POST':
        form = DemandaForm(request.POST)
        if form.is_valid():
            demanda = form.save(commit=False)
            demanda.status = 'RECEBIDA' if not demanda.responsavel else 'EM_ANDAMENTO'
            demanda.save()

            # Criação do primeiro registro de auditoria no histórico
            Historico.objects.create(
                demanda=demanda,
                usuario=request.user,
                etapa_anterior='',
                nova_etapa=demanda.get_status_display(),
                responsavel_anterior=None,
                novo_responsavel=demanda.responsavel,
                observacao=f"Demanda registrada por {request.user.get_full_name() or request.user.username}."
            )

            messages.success(
                request,
                f"Demanda registrada com sucesso! Protocolo gerado: {demanda.protocolo}"
            )
            return redirect('secretaria:detalhe_demanda', protocolo=demanda.protocolo)
        else:
            messages.error(request, 'Por favor, corrija os erros indicados no formulário.')
    else:
        form = DemandaForm()

    return render(request, 'secretaria/form_demanda.html', {'form': form})


@login_required
def lista_demandas(request):
    """
    Exibe a listagem tabular e pesquisável de demandas.
    Protegida: requer autenticação individual.
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
        'perfil_usuario': getattr(request.user, 'perfil', None),
    }
    return render(request, 'secretaria/lista_demandas.html', context)


@login_required
def detalhe_demanda(request, protocolo):
    """
    Exibe os detalhes e histórico completo de uma demanda.
    Protegida: requer autenticação individual.
    """
    demanda = get_object_or_404(
        Demanda.objects.select_related('categoria', 'responsavel').prefetch_related('historicos__usuario', 'anexos'),
        protocolo=protocolo
    )
    return render(request, 'secretaria/detalhe_demanda.html', {'demanda': demanda})


@login_required
@perfil_necessario('ADMINISTRADOR', 'GESTOR')
def dashboard_indicadores(request):
    """
    View de indicadores gerenciais da secretaria.
    Protegida por perfil: Apenas ADMINISTRADOR e GESTOR têm acesso.
    """
    indicadores = obter_indicadores_gestao()
    return render(request, 'secretaria/dashboard.html', {'indicadores': indicadores})


@login_required
@perfil_necessario('ADMINISTRADOR', 'GESTOR')
def api_indicadores(request):
    """
    Endpoint JSON de indicadores.
    Protegida por perfil: Apenas ADMINISTRADOR e GESTOR.
    """
    indicadores = obter_indicadores_gestao()
    return JsonResponse(indicadores)
