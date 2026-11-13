from django.contrib import admin
from .models import PerfilUsuario, Categoria, Demanda, Historico, Anexo


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'perfil', 'ativo')
    list_filter = ('perfil', 'ativo')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email')


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ativa')
    list_filter = ('ativa',)
    search_fields = ('nome', 'descricao')


class HistoricoInline(admin.TabularInline):
    model = Historico
    extra = 0
    readonly_fields = ('data_alteracao',)


class AnexoInline(admin.TabularInline):
    model = Anexo
    extra = 0
    readonly_fields = ('data_envio',)


@admin.register(Demanda)
class DemandaAdmin(admin.ModelAdmin):
    list_display = ('protocolo', 'solicitante', 'categoria', 'responsavel', 'prioridade', 'status', 'prazo', 'data_entrada')
    list_filter = ('status', 'prioridade', 'categoria', 'responsavel')
    search_fields = ('protocolo', 'solicitante', 'contato', 'descricao')
    readonly_fields = ('protocolo', 'data_entrada', 'data_conclusao')
    inlines = [HistoricoInline, AnexoInline]


@admin.register(Historico)
class HistoricoAdmin(admin.ModelAdmin):
    list_display = ('demanda', 'usuario', 'etapa_anterior', 'nova_etapa', 'data_alteracao')
    list_filter = ('nova_etapa', 'data_alteracao')
    search_fields = ('demanda__protocolo', 'usuario__username', 'observacao')


@admin.register(Anexo)
class AnexoAdmin(admin.ModelAdmin):
    list_display = ('nome_arquivo', 'demanda', 'data_envio')
    search_fields = ('nome_arquivo', 'demanda__protocolo')
