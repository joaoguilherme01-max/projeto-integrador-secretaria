from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from secretaria.models import PerfilUsuario, Categoria, Demanda, Historico
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Cria usuários padrão para testes (Admin, Gestor e Atendente) e dados de demonstração'

    def handle(self, *args, **options):
        # 1. Usuário Administrador
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'first_name': 'Administrador',
                'last_name': 'Geral',
                'email': 'admin@escola.com',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            PerfilUsuario.objects.create(user=admin, perfil='ADMINISTRADOR', ativo=True)
            self.stdout.write(self.style.SUCCESS("Usuário 'admin' criado com senha 'admin123'"))
        else:
            self.stdout.write("Usuário 'admin' já existia.")

        # 2. Usuário Gestor da Secretaria
        gestor, created = User.objects.get_or_create(
            username='gestor',
            defaults={
                'first_name': 'Carlos',
                'last_name': 'Menezes',
                'email': 'gestor@escola.com',
                'is_staff': True,
            }
        )
        if created:
            gestor.set_password('gestor123')
            gestor.save()
            PerfilUsuario.objects.create(user=gestor, perfil='GESTOR', ativo=True)
            self.stdout.write(self.style.SUCCESS("Usuário 'gestor' criado com senha 'gestor123'"))
        else:
            self.stdout.write("Usuário 'gestor' já existia.")

        # 3. Usuário Atendente
        atendente, created = User.objects.get_or_create(
            username='atendente',
            defaults={
                'first_name': 'Mariana',
                'last_name': 'Souza',
                'email': 'atendente@escola.com',
            }
        )
        if created:
            atendente.set_password('atendente123')
            atendente.save()
            PerfilUsuario.objects.create(user=atendente, perfil='ATENDENTE', ativo=True)
            self.stdout.write(self.style.SUCCESS("Usuário 'atendente' criado com senha 'atendente123'"))
        else:
            self.stdout.write("Usuário 'atendente' já existia.")

        # 4. Criar dados de exemplo de demandas se estiver vazio
        if Demanda.objects.count() == 0:
            cat_decl, _ = Categoria.objects.get_or_create(nome='Declaração')
            cat_hist, _ = Categoria.objects.get_or_create(nome='Histórico escolar')
            cat_matr, _ = Categoria.objects.get_or_create(nome='Matrícula')

            hoje = timezone.now().date()
            agora = timezone.now()

            # Demanda aberta no prazo
            d1 = Demanda.objects.create(
                categoria=cat_decl,
                solicitante='João da Silva',
                contato='(11) 98765-4321',
                descricao='Solicitação de declaração de matrícula para comprovação de passe escolar.',
                prioridade='ALTA',
                status='EM_ANDAMENTO',
                responsavel=atendente,
                prazo=hoje + timedelta(days=2)
            )
            Historico.objects.create(
                demanda=d1, usuario=gestor, etapa_anterior='TRIAGEM', nova_etapa='EM_ANDAMENTO',
                observacao='Demanda conferida e atribuída para Mariana.'
            )

            # Demanda atrasada
            d2 = Demanda.objects.create(
                categoria=cat_hist,
                solicitante='Ana Paula Lima',
                contato='ana.paula@email.com',
                descricao='Segunda via de histórico do Ensino Médio de 2024.',
                prioridade='URGENTE',
                status='AGUARDANDO_INFO',
                responsavel=atendente,
                prazo=hoje - timedelta(days=2)
            )

            # Demanda concluída
            d3 = Demanda.objects.create(
                categoria=cat_matr,
                solicitante='Lucas Mendes',
                contato='lucas@email.com',
                descricao='Renovação de matrícula para o ano letivo.',
                prioridade='MEDIA',
                status='CONCLUIDA',
                responsavel=gestor,
                prazo=hoje + timedelta(days=5),
                data_conclusao=agora,
                resultado='Matrícula deferida e documentação arquivada.'
            )
            Historico.objects.create(
                demanda=d3, usuario=gestor, etapa_anterior='EM_VALIDACAO', nova_etapa='CONCLUIDA',
                observacao='Atendimento concluído com sucesso.'
            )

            self.stdout.write(self.style.SUCCESS("Demandas de exemplo criadas com sucesso."))

