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


from secretaria.services import obter_indicadores_gestao
from django.urls import reverse


class IndicadoresGestaoTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='atendente_ind', password='123', first_name='Joao', last_name='Atendente'
        )
        self.cat_declaracao = Categoria.objects.create(nome='Declaração')
        self.cat_matricula = Categoria.objects.create(nome='Matrícula')

        hoje = timezone.now().date()
        agora = timezone.now()

        # Demanda aberta no prazo
        Demanda.objects.create(
            categoria=self.cat_declaracao,
            solicitante='Aluno 1',
            contato='1111',
            descricao='Teste 1',
            status='EM_ANDAMENTO',
            responsavel=self.user,
            prazo=hoje + timedelta(days=2)
        )

        # Demanda aberta atrasada
        Demanda.objects.create(
            categoria=self.cat_matricula,
            solicitante='Aluno 2',
            contato='2222',
            descricao='Teste 2',
            status='TRIAGEM',
            responsavel=None,
            prazo=hoje - timedelta(days=1)
        )

        # Demanda concluída com tempo medido (durou 2 dias)
        demanda_concluida = Demanda.objects.create(
            categoria=self.cat_declaracao,
            solicitante='Aluno 3',
            contato='3333',
            descricao='Teste 3',
            status='CONCLUIDA',
            responsavel=self.user,
            prazo=hoje + timedelta(days=5),
            data_conclusao=agora
        )
        # Ajusta data_entrada para 2 dias atrás para simular tempo
        Demanda.objects.filter(id=demanda_concluida.id).update(data_entrada=agora - timedelta(days=2))

    def test_calculo_indicadores(self):
        indicadores = obter_indicadores_gestao()

        # Total abertas (2 abertas: EM_ANDAMENTO e TRIAGEM)
        self.assertEqual(indicadores['total_abertas'], 2)

        # Total atrasadas (1 atrasada)
        self.assertEqual(indicadores['total_atrasadas'], 1)

        # Demandas por etapa
        status_map = {item['status']: item['total'] for item in indicadores['demandas_por_etapa']}
        self.assertEqual(status_map.get('EM_ANDAMENTO'), 1)
        self.assertEqual(status_map.get('TRIAGEM'), 1)
        self.assertEqual(status_map.get('CONCLUIDA'), 1)
        self.assertEqual(status_map.get('RECEBIDA'), 0)

        # Volume por categoria
        cat_map = {item['categoria']: item['total'] for item in indicadores['volume_por_categoria']}
        self.assertEqual(cat_map.get('Declaração'), 2)
        self.assertEqual(cat_map.get('Matrícula'), 1)

        # Distribuição por responsável
        resp_map = {item['responsavel']: item['total'] for item in indicadores['distribuicao_por_responsavel']}
        self.assertEqual(resp_map.get('Joao Atendente'), 1)
        self.assertEqual(resp_map.get('Não atribuído'), 1)

        # Tempo médio
        self.assertIn('2d', indicadores['tempo_medio_str'])

    def test_view_dashboard(self):
        response = self.client.get(reverse('secretaria:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Painel de Indicadores Gerenciais')

    def test_api_indicadores(self):
        response = self.client.get(reverse('secretaria:api_indicadores'))
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data['total_abertas'], 2)
        self.assertEqual(json_data['total_atrasadas'], 1)
