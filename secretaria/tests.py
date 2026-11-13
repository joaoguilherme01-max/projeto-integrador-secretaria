from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from secretaria.models import PerfilUsuario, Categoria, Demanda, Historico, Anexo


class ModelosSecretariaTestCase(TestCase):
    def setUp(self):
        # Usuários e Perfis
        self.user_gestor = User.objects.create_user(
            username='gestor1',
            email='gestor@escola.com',
            password='senha_segura_123',
            first_name='Carlos',
            last_name='Gestor'
        )
        self.perfil_gestor = PerfilUsuario.objects.create(
            user=self.user_gestor,
            perfil='GESTOR'
        )

        self.user_atendente = User.objects.create_user(
            username='atendente1',
            email='atendente@escola.com',
            password='senha_segura_123',
            first_name='Mariana',
            last_name='Atendente'
        )
        self.perfil_atendente = PerfilUsuario.objects.create(
            user=self.user_atendente,
            perfil='ATENDENTE'
        )

        # Categorias
        self.cat_declaracao = Categoria.objects.create(
            nome='Declaração de Matrícula',
            descricao='Emissão de declarações para alunos regulares'
        )
        self.cat_historico = Categoria.objects.create(
            nome='Histórico Escolar',
            descricao='Emissão e 2ª via de histórico escolar'
        )

    def test_criacao_e_relacionamento_perfil_usuario(self):
        """Testa criação e relacionamento 1-para-1 do perfil de usuário."""
        self.assertEqual(self.user_gestor.perfil.perfil, 'GESTOR')
        self.assertTrue(self.user_gestor.perfil.ativo)
        self.assertIn('Carlos Gestor', str(self.user_gestor.perfil))

    def test_geracao_automatica_protocolo_demanda(self):
        """Testa geração de protocolo sequencial anual (ex: SEC-2026-00001)."""
        ano = timezone.now().year
        demanda1 = Demanda.objects.create(
            categoria=self.cat_declaracao,
            solicitante='João da Silva',
            contato='(11) 98765-4321',
            descricao='Solicita declaração de matrícula para passe escolar.',
            prioridade='ALTA',
            prazo=timezone.now().date() + timedelta(days=2)
        )

        demanda2 = Demanda.objects.create(
            categoria=self.cat_historico,
            solicitante='Ana Paula Souza',
            contato='ana@email.com',
            descricao='Solicita 2ª via do histórico do Ensino Médio.',
            prioridade='MEDIA',
            prazo=timezone.now().date() + timedelta(days=5)
        )

        self.assertEqual(demanda1.protocolo, f"SEC-{ano}-00001")
        self.assertEqual(demanda2.protocolo, f"SEC-{ano}-00002")

    def test_relacionamentos_demanda_e_historico(self):
        """Testa relacionamentos entre Demanda, Categoria, Usuários e Histórico."""
        demanda = Demanda.objects.create(
            categoria=self.cat_declaracao,
            solicitante='Lucas Mendes',
            contato='lucas@email.com',
            descricao='Declaração simples de frequência.',
            responsavel=self.user_atendente,
            status='EM_ANDAMENTO'
        )

        # Registro de histórico
        historico = Historico.objects.create(
            demanda=demanda,
            usuario=self.user_gestor,
            etapa_anterior='TRIAGEM',
            nova_etapa='EM_ANDAMENTO',
            responsavel_anterior=None,
            novo_responsavel=self.user_atendente,
            observacao='Demanda direcionada para atendimento prioritário.'
        )

        # Testar relacionamentos reversos
        self.assertEqual(demanda.categoria.demandas.count(), 1)
        self.assertEqual(self.user_atendente.demandas_atribuidas.count(), 1)
        self.assertEqual(demanda.historicos.count(), 1)
        self.assertEqual(demanda.historicos.first().usuario, self.user_gestor)
        self.assertEqual(demanda.historicos.first().novo_responsavel, self.user_atendente)

    def test_anexo_relacionamento(self):
        """Testa inclusão de anexo relacionado à demanda."""
        demanda = Demanda.objects.create(
            categoria=self.cat_historico,
            solicitante='Beatriz Ramos',
            contato='beatriz@email.com',
            descricao='Comprovante de residência anexado.',
        )

        anexo = Anexo.objects.create(
            demanda=demanda,
            nome_arquivo='comprovante.pdf',
            arquivo='anexos/test/comprovante.pdf'
        )

        self.assertEqual(demanda.anexos.count(), 1)
        self.assertEqual(demanda.anexos.first().nome_arquivo, 'comprovante.pdf')
