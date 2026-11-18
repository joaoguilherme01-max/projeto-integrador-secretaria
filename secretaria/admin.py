from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import PerfilUsuario, Categoria, Demanda, Historico, Anexo

# Personalização dos títulos e cabeçalhos do painel administrativo
admin.site.site_header = "Painel Administrativo da Secretaria Escolar"
admin.site.site_title = "Administração da Secretaria"
admin.site.index_title = "Centro de Controle e Gestão de Demandas"


class PerfilUsuarioInline(admin.StackedInline):
    """Permite visualizar e editar o perfil (Administrador/Gestor/Atendente) dentro do cadastro de Usuário."""
    model = PerfilUsuario
    can_delete = False
    verbose_name_plural = 'Perfil de Acesso do Sistema'
    fk_name = 'user'
    extra = 0


# Estende o UserAdmin padrão do Django para integrar o Perfil e melhorar a interface
admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    inlines = [PerfilUsuarioInline]
    list_display = ('username', 'get_full_name_custom', 'email', 'get_perfil_display_custom', 'is_active', 'is_staff')
    list_filter = ('is_active', 'is_staff', 'perfil__perfil')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)

    @admin.display(description='Nome Completo')
    def get_full_name_custom(self, obj):
        return obj.get_full_name() or obj.username

    @admin.display(description='Perfil no Sistema')
    def get_perfil_display_custom(self, obj):
        perfil = getattr(obj, 'perfil', None)
        if not perfil:
            return format_html('<span style="color: #6c757d;">Sem perfil</span>')
        cores = {
            'ADMINISTRADOR': '#b02a37',
            'GESTOR': '#0b5ed7',
            'ATENDENTE': '#198754'
        }
        cor = cores.get(perfil.perfil, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;">{}</span>',
            cor, perfil.get_perfil_display()
        )


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_perfil_badge', 'ativo')
    list_filter = ('perfil', 'ativo')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email')
    list_editable = ('ativo',)

    @admin.display(description='Perfil')
    def get_perfil_badge(self, obj):
        cores = {
            'ADMINISTRADOR': '#b02a37',
            'GESTOR': '#0b5ed7',
            'ATENDENTE': '#198754'
        }
        cor = cores.get(obj.perfil, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;">{}</span>',
            cor, obj.get_perfil_display()
        )


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao_curta', 'total_demandas', 'ativa')
    list_filter = ('ativa',)
    search_fields = ('nome', 'descricao')
    list_editable = ('ativa',)

    @admin.display(description='Descrição')
    def descricao_curta(self, obj):
        return (obj.descricao[:60] + '...') if len(obj.descricao) > 60 else obj.descricao

    @admin.display(description='Total de Demandas')
    def total_demandas(self, obj):
        total = obj.demandas.count()
        return format_html('<strong>{}</strong>', total)


class HistoricoInline(admin.TabularInline):
    model = Historico
    extra = 0
    can_delete = False
    readonly_fields = ('data_alteracao', 'usuario', 'etapa_anterior', 'nova_etapa', 'novo_responsavel', 'observacao')
    ordering = ('-data_alteracao',)


class AnexoInline(admin.TabularInline):
    model = Anexo
    extra = 0
    readonly_fields = ('data_envio',)


@admin.register(Demanda)
class DemandaAdmin(admin.ModelAdmin):
    list_display = (
        'protocolo_tag',
        'solicitante',
        'categoria',
        'responsavel',
        'prioridade_badge',
        'status_badge',
        'prazo_formatado',
        'data_entrada'
    )
    list_filter = ('status', 'prioridade', 'categoria', 'responsavel', 'data_entrada')
    search_fields = ('protocolo', 'solicitante', 'contato', 'descricao')
    readonly_fields = ('protocolo', 'data_entrada', 'data_conclusao')
    date_hierarchy = 'data_entrada'
    list_per_page = 20
    inlines = [HistoricoInline, AnexoInline]

    fieldsets = (
        ('Identificação da Solicitação', {
            'fields': (('protocolo', 'categoria'), ('solicitante', 'contato'))
        }),
        ('Detalhes e Atribuição', {
            'fields': ('descricao', ('prioridade', 'status'), ('responsavel', 'prazo'))
        }),
        ('Conclusão / Desfecho', {
            'classes': ('collapse',),
            'fields': ('data_conclusao', 'resultado')
        }),
        ('Auditoria de Entrada', {
            'classes': ('collapse',),
            'fields': ('data_entrada',)
        }),
    )

    @admin.display(description='Protocolo')
    def protocolo_tag(self, obj):
        return format_html(
            '<strong style="color: #0b5ed7; font-family: monospace; font-size: 13px;">{}</strong>',
            obj.protocolo
        )

    @admin.display(description='Prioridade')
    def prioridade_badge(self, obj):
        cores = {
            'URGENTE': '#b02a37',
            'ALTA': '#fd7e14',
            'MEDIA': '#ffc107',
            'BAIXA': '#6c757d'
        }
        cor = cores.get(obj.prioridade, '#6c757d')
        texto_cor = '#000000' if obj.prioridade == 'MEDIA' else '#ffffff'
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;">{}</span>',
            cor, texto_cor, obj.get_prioridade_display()
        )

    @admin.display(description='Status')
    def status_badge(self, obj):
        cores = {
            'RECEBIDA': '#6c757d',
            'TRIAGEM': '#0dcaf0',
            'AGUARDANDO_INFO': '#ffc107',
            'EM_ANDAMENTO': '#0d6efd',
            'EM_VALIDACAO': '#6f42c1',
            'CONCLUIDA': '#198754',
            'CANCELADA': '#212529'
        }
        cor = cores.get(obj.status, '#6c757d')
        texto_cor = '#000000' if obj.status in ['TRIAGEM', 'AGUARDANDO_INFO'] else '#ffffff'
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;">{}</span>',
            cor, texto_cor, obj.get_status_display()
        )

    @admin.display(description='Prazo')
    def prazo_formatado(self, obj):
        if not obj.prazo:
            return format_html('<span style="color: #6c757d;">-</span>')
        from django.utils import timezone
        if obj.status not in ['CONCLUIDA', 'CANCELADA'] and obj.prazo < timezone.now().date():
            return format_html(
                '<strong style="color: #b02a37;">⚠️ {}</strong>',
                obj.prazo.strftime('%d/%m/%Y')
            )
        return obj.prazo.strftime('%d/%m/%Y')


@admin.register(Historico)
class HistoricoAdmin(admin.ModelAdmin):
    list_display = ('demanda', 'usuario', 'etapa_anterior', 'nova_etapa', 'novo_responsavel', 'data_alteracao')
    list_filter = ('nova_etapa', 'data_alteracao', 'usuario')
    search_fields = ('demanda__protocolo', 'usuario__username', 'observacao')
    readonly_fields = ('demanda', 'usuario', 'etapa_anterior', 'nova_etapa', 'responsavel_anterior', 'novo_responsavel', 'observacao', 'data_alteracao')

    def has_add_permission(self, request):
        return False  # Histórico gerado apenas automaticamente pelo sistema


@admin.register(Anexo)
class AnexoAdmin(admin.ModelAdmin):
    list_display = ('nome_arquivo', 'demanda', 'data_envio')
    search_fields = ('nome_arquivo', 'demanda__protocolo')
    readonly_fields = ('data_envio',)
