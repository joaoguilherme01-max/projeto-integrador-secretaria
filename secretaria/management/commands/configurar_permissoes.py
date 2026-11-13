from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from secretaria.models import Demanda, Categoria, Historico, Anexo, PerfilUsuario


class Command(BaseCommand):
    help = 'Configura os grupos e permissões nativas do Django para Administrador, Gestor e Atendente'

    def handle(self, *args, **options):
        # ContentTypes dos modelos do sistema
        ct_demanda = ContentType.objects.get_for_model(Demanda)
        ct_categoria = ContentType.objects.get_for_model(Categoria)
        ct_historico = ContentType.objects.get_for_model(Historico)
        ct_anexo = ContentType.objects.get_for_model(Anexo)
        ct_perfil = ContentType.objects.get_for_model(PerfilUsuario)

        # Permissões do sistema
        perms_demanda = Permission.objects.filter(content_type=ct_demanda)
        perms_categoria = Permission.objects.filter(content_type=ct_categoria)
        perms_historico = Permission.objects.filter(content_type=ct_historico)
        perms_anexo = Permission.objects.filter(content_type=ct_anexo)
        perms_perfil = Permission.objects.filter(content_type=ct_perfil)

        # 1. GRUPO: Administrador do Sistema
        # Acesso total: gerenciamento de contas, perfis, categorias, demandas e auditoria
        grupo_admin, _ = Group.objects.get_or_create(name='ADMINISTRADOR')
        grupo_admin.permissions.set(
            list(perms_demanda) +
            list(perms_categoria) +
            list(perms_historico) +
            list(perms_anexo) +
            list(perms_perfil)
        )
        self.stdout.write(self.style.SUCCESS("Grupo 'ADMINISTRADOR' configurado com permissões totais."))

        # 2. GRUPO: Gestor da Secretaria
        # Visualizar, cadastrar e editar todas as demandas, alterar prazos, responsáveis e categorias
        grupo_gestor, _ = Group.objects.get_or_create(name='GESTOR')
        perms_gestor = [
            # Demanda: adicionar, visualizar, alterar
            Permission.objects.get(content_type=ct_demanda, codename='add_demanda'),
            Permission.objects.get(content_type=ct_demanda, codename='view_demanda'),
            Permission.objects.get(content_type=ct_demanda, codename='change_demanda'),
            # Categoria: visualizar e adicionar/alterar categorias de atendimento
            Permission.objects.get(content_type=ct_categoria, codename='view_categoria'),
            Permission.objects.get(content_type=ct_categoria, codename='add_categoria'),
            Permission.objects.get(content_type=ct_categoria, codename='change_categoria'),
            # Histórico: visualizar auditoria
            Permission.objects.get(content_type=ct_historico, codename='view_historico'),
            Permission.objects.get(content_type=ct_historico, codename='add_historico'),
            # Anexos
            Permission.objects.get(content_type=ct_anexo, codename='view_anexo'),
            Permission.objects.get(content_type=ct_anexo, codename='add_anexo'),
        ]
        grupo_gestor.permissions.set(perms_gestor)
        self.stdout.write(self.style.SUCCESS("Grupo 'GESTOR' configurado com permissões gerenciais."))

        # 3. GRUPO: Atendente / Servidor
        # Registrar novas solicitações, consultar demandas, alterar status e registrar observações
        grupo_atendente, _ = Group.objects.get_or_create(name='ATENDENTE')
        perms_atendente = [
            Permission.objects.get(content_type=ct_demanda, codename='add_demanda'),
            Permission.objects.get(content_type=ct_demanda, codename='view_demanda'),
            Permission.objects.get(content_type=ct_demanda, codename='change_demanda'),
            Permission.objects.get(content_type=ct_categoria, codename='view_categoria'),
            Permission.objects.get(content_type=ct_historico, codename='view_historico'),
            Permission.objects.get(content_type=ct_historico, codename='add_historico'),
            Permission.objects.get(content_type=ct_anexo, codename='view_anexo'),
            Permission.objects.get(content_type=ct_anexo, codename='add_anexo'),
        ]
        grupo_atendente.permissions.set(perms_atendente)
        self.stdout.write(self.style.SUCCESS("Grupo 'ATENDENTE' configurado com permissões operacionais."))

