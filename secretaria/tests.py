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


from secretaria.services import obter_indicadores_gestao, listar_demandas_filtradas
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
        # Usuário autenticado como gestor
        PerfilUsuario.objects.create(user=self.user, perfil='GESTOR')
        self.client.force_login(self.user)
        response = self.client.get(reverse('secretaria:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Painel Gerencial de Indicadores')

    def test_api_indicadores(self):
        PerfilUsuario.objects.get_or_create(user=self.user, defaults={'perfil': 'GESTOR'})
        self.client.force_login(self.user)
        response = self.client.get(reverse('secretaria:api_indicadores'))
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data['total_abertas'], 2)
        self.assertEqual(json_data['total_atrasadas'], 1)



class FiltrosLocalizacaoTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='mariana', first_name='Mariana', password='123')
        self.user2 = User.objects.create_user(username='roberto', first_name='Roberto', password='123')

        self.cat1 = Categoria.objects.create(nome='Declaração')
        self.cat2 = Categoria.objects.create(nome='Histórico')

        hoje = timezone.now().date()
        agora = timezone.now()

        # Demanda 1
        d1 = Demanda.objects.create(
            categoria=self.cat1,
            solicitante='Fernanda Lima',
            contato='1199999999',
            descricao='Declaração de conclusão',
            status='RECEBIDA',
            prioridade='URGENTE',
            responsavel=self.user1,
            prazo=hoje + timedelta(days=1)
        )
        Demanda.objects.filter(id=d1.id).update(data_entrada=agora - timedelta(days=10))

        # Demanda 2
        d2 = Demanda.objects.create(
            categoria=self.cat2,
            solicitante='Gabriel Ramos',
            contato='gabriel@escola.com',
            descricao='Segunda via histórico escolar',
            status='EM_ANDAMENTO',
            prioridade='BAIXA',
            responsavel=self.user2,
            prazo=hoje + timedelta(days=15)
        )
        Demanda.objects.filter(id=d2.id).update(data_entrada=agora - timedelta(days=2))

        # Demanda 3 (sem responsável)
        d3 = Demanda.objects.create(
            categoria=self.cat1,
            solicitante='Lucas Ferreira',
            contato='lucas@escola.com',
            descricao='Atendimento geral de dúvidas',
            status='TRIAGEM',
            prioridade='MEDIA',
            responsavel=None,
            prazo=hoje + timedelta(days=3)
        )
        Demanda.objects.filter(id=d3.id).update(data_entrada=agora)

        self.d1 = Demanda.objects.get(id=d1.id)
        self.d2 = Demanda.objects.get(id=d2.id)
        self.d3 = Demanda.objects.get(id=d3.id)

    def test_pesquisar_protocolo(self):
        res = listar_demandas_filtradas({'busca': self.d1.protocolo})
        self.assertEqual(res.count(), 1)
        self.assertEqual(res.first().protocolo, self.d1.protocolo)

    def test_filtrar_por_status(self):
        res = listar_demandas_filtradas({'status': 'EM_ANDAMENTO'})
        self.assertEqual(res.count(), 1)
        self.assertEqual(res.first().protocolo, self.d2.protocolo)

    def test_filtrar_por_responsavel(self):
        res = listar_demandas_filtradas({'responsavel': str(self.user1.id)})
        self.assertEqual(res.count(), 1)
        self.assertEqual(res.first().protocolo, self.d1.protocolo)

        res_sem_resp = listar_demandas_filtradas({'responsavel': 'sem_responsavel'})
        self.assertEqual(res_sem_resp.count(), 1)
        self.assertEqual(res_sem_resp.first().protocolo, self.d3.protocolo)

    def test_filtrar_por_categoria(self):
        res = listar_demandas_filtradas({'categoria': str(self.cat2.id)})
        self.assertEqual(res.count(), 1)
        self.assertEqual(res.first().protocolo, self.d2.protocolo)

    def test_filtrar_por_prioridade(self):
        res = listar_demandas_filtradas({'prioridade': 'URGENTE'})
        self.assertEqual(res.count(), 1)
        self.assertEqual(res.first().protocolo, self.d1.protocolo)

    def test_filtrar_por_periodo(self):
        hoje = timezone.now().date()
        dt_ini = (hoje - timedelta(days=3)).strftime('%Y-%m-%d')
        dt_fim = hoje.strftime('%Y-%m-%d')

        res = listar_demandas_filtradas({'data_inicio': dt_ini, 'data_fim': dt_fim})
        # d2 (2 dias atras) e d3 (hoje) devem estar presentes; d1 (10 dias atrás) não deve
        self.assertEqual(res.count(), 2)
        protocolos = list(res.values_list('protocolo', flat=True))
        self.assertIn(self.d2.protocolo, protocolos)
        self.assertIn(self.d3.protocolo, protocolos)
        self.assertNotIn(self.d1.protocolo, protocolos)

    def test_view_lista_demandas(self):
        self.client.force_login(self.user1)
        url = reverse('secretaria:lista_demandas')
        response = self.client.get(url, {'busca': 'Fernanda'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.d1.protocolo)
        self.assertNotContains(response, self.d2.protocolo)



class AutenticacaoControleAcessoTestCase(TestCase):
    def setUp(self):
        # Usuário Administrador
        self.user_admin = User.objects.create_user(
            username='admin_user', password='password123', first_name='Admin'
        )
        PerfilUsuario.objects.create(user=self.user_admin, perfil='ADMINISTRADOR', ativo=True)

        # Usuário Gestor
        self.user_gestor = User.objects.create_user(
            username='gestor_user', password='password123', first_name='Gestor'
        )
        PerfilUsuario.objects.create(user=self.user_gestor, perfil='GESTOR', ativo=True)

        # Usuário Atendente
        self.user_atendente = User.objects.create_user(
            username='atendente_user', password='password123', first_name='Atendente'
        )
        PerfilUsuario.objects.create(user=self.user_atendente, perfil='ATENDENTE', ativo=True)

        # Usuário Inativo
        self.user_inativo = User.objects.create_user(
            username='inativo_user', password='password123', first_name='Inativo'
        )
        PerfilUsuario.objects.create(user=self.user_inativo, perfil='ATENDENTE', ativo=False)

    def test_login_sucesso_e_logout(self):
        """Testa login com credenciais válidas e posterior logout."""
        # Login (redireciona para a tela inicial / index)
        response = self.client.post(reverse('secretaria:login'), {
            'username': 'atendente_user',
            'password': 'password123'
        })
        self.assertRedirects(response, reverse('secretaria:index'))

        # Logout
        response_logout = self.client.get(reverse('secretaria:logout'))
        self.assertRedirects(response_logout, reverse('secretaria:login'))

    def test_login_usuario_inativo_bloqueado(self):
        """Testa se usuário com perfil inativo é impedido de acessar."""
        response = self.client.post(reverse('secretaria:login'), {
            'username': 'inativo_user',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Esta conta está inativa')

    def test_protecao_paginas_internas_anonimo(self):
        """Garante que usuários não autenticados são redirecionados para a tela de login."""
        response_demandas = self.client.get(reverse('secretaria:lista_demandas'))
        self.assertEqual(response_demandas.status_code, 302)
        self.assertIn('/login/', response_demandas.url)

        response_dashboard = self.client.get(reverse('secretaria:dashboard'))
        self.assertEqual(response_dashboard.status_code, 302)
        self.assertIn('/login/', response_dashboard.url)

    def test_controle_acesso_dashboard_por_perfil(self):
        """
        GESTOR e ADMINISTRADOR podem acessar o dashboard.
        ATENDENTE é redirecionado com aviso de falta de permissão.
        """
        # Teste com Atendente (deve ser bloqueado do dashboard)
        self.client.login(username='atendente_user', password='password123')
        response_atendente = self.client.get(reverse('secretaria:dashboard'), follow=True)
        self.assertRedirects(response_atendente, reverse('secretaria:lista_demandas'))
        self.assertContains(response_atendente, 'Acesso não autorizado')
        self.client.logout()

        # Teste com Gestor (acesso permitido)
        self.client.login(username='gestor_user', password='password123')
        response_gestor = self.client.get(reverse('secretaria:dashboard'))
        self.assertEqual(response_gestor.status_code, 200)
        self.assertContains(response_gestor, 'Painel Gerencial de Indicadores')
        self.client.logout()

        # Teste com Administrador (acesso permitido)
        self.client.login(username='admin_user', password='password123')
        response_admin = self.client.get(reverse('secretaria:dashboard'))
        self.assertEqual(response_admin.status_code, 200)
        self.client.logout()



class TelaInicialTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user_home', password='123')
        PerfilUsuario.objects.create(user=self.user, perfil='ATENDENTE')

        cat = Categoria.objects.create(nome='Matrícula')
        hoje = timezone.now().date()
        agora = timezone.now()

        # Demanda aberta no prazo
        self.dem_aberta = Demanda.objects.create(
            categoria=cat, solicitante='Ana Clara', contato='123',
            descricao='Matrícula nova', status='EM_ANDAMENTO',
            prazo=hoje + timedelta(days=2), responsavel=self.user
        )

        # Demanda atrasada
        self.dem_atrasada = Demanda.objects.create(
            categoria=cat, solicitante='Bernardo Lima', contato='456',
            descricao='Documento pendente', status='TRIAGEM',
            prazo=hoje - timedelta(days=3), responsavel=self.user
        )

        # Demanda concluída
        self.dem_concluida = Demanda.objects.create(
            categoria=cat, solicitante='Carlos Eduardo', contato='789',
            descricao='Finalizado', status='CONCLUIDA',
            data_conclusao=agora, responsavel=self.user
        )

    def test_tela_inicial_carregamento_e_indicadores(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('secretaria:index'))
        self.assertEqual(response.status_code, 200)

        # Verifica presença dos totalizadores e demandas
        self.assertContains(response, 'Visão Geral das Demandas')
        self.assertContains(response, 'Demandas Abertas')
        self.assertContains(response, 'Demandas Atrasadas')
        self.assertContains(response, 'Demandas Concluídas')

        # Verifica se os protocolos aparecem nas seções
        self.assertContains(response, self.dem_aberta.protocolo)
        self.assertContains(response, self.dem_atrasada.protocolo)
        self.assertContains(response, self.dem_concluida.protocolo)



class CriacaoDemandaTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='atendente_form', password='123')
        PerfilUsuario.objects.create(user=self.user, perfil='ATENDENTE')
        self.categoria = Categoria.objects.create(nome='Declaração de Matrícula')

    def test_get_formulario_criar_demanda(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('secretaria:criar_demanda'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Registrar Nova Solicitação')
        self.assertContains(response, 'Solicitante (Aluno/Responsável)')
        self.assertContains(response, 'Tipo de Solicitação')

    def test_post_criar_demanda_com_sucesso(self):
        self.client.force_login(self.user)
        dados = {
            'solicitante': 'Mariana Rios',
            'contato': '(11) 97777-8888',
            'categoria': str(self.categoria.id),
            'descricao': 'Precisa de declaração urgente para estágio.',
            'prioridade': 'URGENTE',
            'prazo': (timezone.now().date() + timedelta(days=1)).strftime('%Y-%m-%d'),
            'responsavel': str(self.user.id),
        }
        response = self.client.post(reverse('secretaria:criar_demanda'), dados)
        self.assertEqual(response.status_code, 302)

        # Verifica se foi salva no banco
        demanda = Demanda.objects.filter(solicitante='Mariana Rios').first()
        self.assertIsNotNone(demanda)
        self.assertTrue(demanda.protocolo.startswith('SEC-'))
        self.assertEqual(demanda.prioridade, 'URGENTE')
        self.assertEqual(demanda.responsavel, self.user)
        self.assertEqual(demanda.historicos.count(), 1)



class QuadroKanbanTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='kanban_user', password='123', first_name='Lucas')
        PerfilUsuario.objects.create(user=self.user, perfil='ATENDENTE')
        self.cat = Categoria.objects.create(nome='Declaração de Passe')

        self.demanda = Demanda.objects.create(
            categoria=self.cat,
            solicitante='Carolina Castro',
            contato='11988887777',
            descricao='Passe estudantil urgente',
            prioridade='ALTA',
            status='EM_ANDAMENTO',
            responsavel=self.user,
            prazo=timezone.now().date() + timedelta(days=2)
        )

    def test_quadro_kanban_view_e_campos_do_cartao(self):
        """Testa o carregamento do quadro e a presença dos campos obrigatórios no cartão."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('secretaria:quadro_kanban'))
        self.assertEqual(response.status_code, 200)

        # 1. Protocolo
        self.assertContains(response, self.demanda.protocolo)
        # 2. Tipo de solicitação (categoria)
        self.assertContains(response, 'Declaração de Passe')
        # 3. Prioridade
        self.assertContains(response, 'Alta')
        # 4. Prazo
        self.assertContains(response, self.demanda.prazo.strftime('%d/%m'))
        # 5. Responsável
        self.assertContains(response, 'Lucas')
        # 6. Status (título da coluna do Kanban)
        self.assertContains(response, 'Em Andamento')



class DetalheEdicaoDemandaTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='servidor_detalhe', password='123', first_name='Joao')
        PerfilUsuario.objects.create(user=self.user, perfil='ATENDENTE')

        self.outro_user = User.objects.create_user(username='outro_resp', password='123', first_name='Renata')
        PerfilUsuario.objects.create(user=self.outro_user, perfil='ATENDENTE')

        self.cat = Categoria.objects.create(nome='Transferência Escolar')
        self.demanda = Demanda.objects.create(
            categoria=self.cat,
            solicitante='Pedro Henrique',
            contato='(11) 91234-5678',
            descricao='Solicita transferência para outra escola.',
            prioridade='MEDIA',
            status='TRIAGEM',
            responsavel=self.user,
            prazo=timezone.now().date() + timedelta(days=5)
        )

        Historico.objects.create(
            demanda=self.demanda,
            usuario=self.user,
            etapa_anterior='RECEBIDA',
            nova_etapa='TRIAGEM',
            observacao='Entrada e triagem inicial de documentação.'
        )

    def test_exibir_dados_completos_e_historico(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('secretaria:detalhe_demanda', args=[self.demanda.protocolo]))
        self.assertEqual(response.status_code, 200)

        # Dados completos
        self.assertContains(response, self.demanda.protocolo)
        self.assertContains(response, 'Pedro Henrique')
        self.assertContains(response, '(11) 91234-5678')
        self.assertContains(response, 'Transferência Escolar')
        self.assertContains(response, 'Solicita transferência para outra escola.')

        # Histórico e observações
        self.assertContains(response, 'Entrada e triagem inicial de documentação.')
        self.assertContains(response, 'Histórico de Alterações e Auditoria')

        # Botão de edição
        self.assertContains(response, reverse('secretaria:editar_demanda', args=[self.demanda.protocolo]))

    def test_editar_demanda_e_gerar_historico(self):
        self.client.force_login(self.user)
        dados = {
            'solicitante': 'Pedro Henrique Atualizado',
            'contato': '(11) 91234-5678',
            'categoria': str(self.cat.id),
            'descricao': 'Solicita transferência com urgência.',
            'prioridade': 'ALTA',
            'status': 'EM_ANDAMENTO',
            'responsavel': str(self.outro_user.id),
            'prazo': (timezone.now().date() + timedelta(days=3)).strftime('%Y-%m-%d'),
            'observacao_alteracao': 'Demanda assumida por Renata para confecção dos documentos.',
            'resultado': '',
        }
        response = self.client.post(reverse('secretaria:editar_demanda', args=[self.demanda.protocolo]), dados)
        self.assertEqual(response.status_code, 302)

        self.demanda.refresh_from_db()
        self.assertEqual(self.demanda.status, 'EM_ANDAMENTO')
        self.assertEqual(self.demanda.prioridade, 'ALTA')
        self.assertEqual(self.demanda.responsavel, self.outro_user)

        # Verifica se o novo histórico foi gravado
        ultimo_hist = self.demanda.historicos.first()
        self.assertEqual(ultimo_hist.nova_etapa, 'Em Andamento')
        self.assertEqual(ultimo_hist.usuario, self.user)
        self.assertIn('Demanda assumida por Renata', ultimo_hist.observacao)



class ProtocoloUnicoTestCase(TestCase):
    def setUp(self):
        self.cat = Categoria.objects.create(nome='Matrícula e Rematrícula')

    def test_padrao_formato_protocolo(self):
        """Verifica se o protocolo segue estritamente o padrão 'SEC-YYYY-NNNNN'."""
        demanda = Demanda.objects.create(
            categoria=self.cat,
            solicitante='Aluno Teste Padrão',
            contato='1199999999',
            descricao='Teste de formato'
        )
        ano = timezone.now().year
        padrao = rf"^SEC-{ano}-\d{{5}}$"
        import re
        self.assertTrue(re.match(padrao, demanda.protocolo))

    def test_geracao_sequencial_protocolo(self):
        """Garante que a numeração seja rigorosamente sequencial."""
        ano = timezone.now().year
        d1 = Demanda.objects.create(categoria=self.cat, solicitante='A1', contato='1', descricao='D1')
        d2 = Demanda.objects.create(categoria=self.cat, solicitante='A2', contato='2', descricao='D2')
        d3 = Demanda.objects.create(categoria=self.cat, solicitante='A3', contato='3', descricao='D3')

        seq1 = int(d1.protocolo.split('-')[-1])
        seq2 = int(d2.protocolo.split('-')[-1])
        seq3 = int(d3.protocolo.split('-')[-1])

        self.assertEqual(seq2, seq1 + 1)
        self.assertEqual(seq3, seq2 + 1)

    def test_impedir_protocolos_duplicados(self):
        """Garante unicidade estrita: erro de integridade ao tentar duplicar protocolo."""
        from django.db import IntegrityError
        demanda = Demanda.objects.create(
            categoria=self.cat,
            solicitante='Aluno Original',
            contato='1199999999',
            descricao='Original'
        )

        demanda_duplicada = Demanda(
            categoria=self.cat,
            solicitante='Tentativa Duplicada',
            contato='1188888888',
            descricao='Duplicada'
        )
        # Força o mesmo protocolo manualmente para testar a restrição UNIQUE do banco
        demanda_duplicada.protocolo = demanda.protocolo

        with self.assertRaises(IntegrityError):
            demanda_duplicada.save()



class EdicaoCompletaDemandaTestCase(TestCase):
    def setUp(self):
        self.user_editor = User.objects.create_user(username='editor_user', password='123', first_name='Gabriel')
        PerfilUsuario.objects.create(user=self.user_editor, perfil='GESTOR')

        self.user_novo_resp = User.objects.create_user(username='resp_novo', password='123', first_name='Camila')
        PerfilUsuario.objects.create(user=self.user_novo_resp, perfil='ATENDENTE')

        self.cat = Categoria.objects.create(nome='Declaração de Conclusão')
        hoje = timezone.now().date()
        self.demanda = Demanda.objects.create(
            categoria=self.cat,
            solicitante='Matheus Oliveira',
            contato='11988889999',
            descricao='Descrição inicial da demanda.',
            prioridade='BAIXA',
            status='RECEBIDA',
            responsavel=None,
            prazo=hoje + timedelta(days=10)
        )

    def test_editar_descricao_responsavel_prioridade_prazo(self):
        """
        Testa edição de descrição, responsável, prioridade e prazo com
        geração detalhada no histórico de auditoria.
        """
        self.client.force_login(self.user_editor)
        novo_prazo = (timezone.now().date() + timedelta(days=2)).strftime('%Y-%m-%d')

        dados = {
            'solicitante': 'Matheus Oliveira',
            'contato': '11988889999',
            'categoria': str(self.cat.id),
            'descricao': 'Descrição atualizada com detalhes adicionais do requerimento.',
            'prioridade': 'URGENTE',
            'status': 'EM_ANDAMENTO',
            'responsavel': str(self.user_novo_resp.id),
            'prazo': novo_prazo,
            'observacao_alteracao': 'Demanda priorizada a pedido da coordenação.',
            'resultado': '',
        }

        url = reverse('secretaria:editar_demanda', args=[self.demanda.protocolo])
        response = self.client.post(url, dados)
        self.assertEqual(response.status_code, 302)

        self.demanda.refresh_from_db()

        # 1. Editar descrição
        self.assertEqual(self.demanda.descricao, 'Descrição atualizada com detalhes adicionais do requerimento.')

        # 2. Alterar responsável
        self.assertEqual(self.demanda.responsavel, self.user_novo_resp)

        # 3. Atualizar prioridade
        self.assertEqual(self.demanda.prioridade, 'URGENTE')

        # 4. Atualizar prazo
        self.assertEqual(self.demanda.prazo.strftime('%Y-%m-%d'), novo_prazo)

        # Verificar se o histórico de auditoria registrou todas as alterações
        historico = self.demanda.historicos.first()
        self.assertIsNotNone(historico)
        self.assertEqual(historico.usuario, self.user_editor)
        self.assertIn('Prioridade:', historico.observacao)
        self.assertIn('Responsável:', historico.observacao)
        self.assertIn('Prazo:', historico.observacao)
        self.assertIn('Descrição da demanda atualizada', historico.observacao)
        self.assertIn('Demanda priorizada a pedido da coordenação', historico.observacao)



class AuditoriaMudancasTestCase(TestCase):
    def setUp(self):
        self.servidor = User.objects.create_user(
            username='auditor_teste', password='123', first_name='Patrícia', last_name='Alves'
        )
        PerfilUsuario.objects.create(user=self.servidor, perfil='ATENDENTE')
        self.cat = Categoria.objects.create(nome='Certidão Escolar')

        self.demanda = Demanda.objects.create(
            categoria=self.cat,
            solicitante='Vinícius Santos',
            contato='11955554444',
            descricao='Emissão de certidão de conclusão.',
            status='RECEBIDA',
            prioridade='MEDIA',
            responsavel=self.servidor,
            prazo=timezone.now().date() + timedelta(days=4)
        )

    def test_auditoria_completa_mudanca_status(self):
        """
        Garante que todos os 5 itens do checklist de auditoria sejam gravados:
        1. Usuário responsável pela alteração
        2. Data e horário (DateTimeField com auto_now_add)
        3. Status anterior
        4. Novo status
        5. Observações
        """
        self.client.force_login(self.servidor)
        url = reverse('secretaria:editar_demanda', args=[self.demanda.protocolo])

        tempo_antes = timezone.now() - timedelta(seconds=2)

        dados = {
            'solicitante': 'Vinícius Santos',
            'contato': '11955554444',
            'categoria': str(self.cat.id),
            'descricao': 'Emissão de certidão de conclusão.',
            'prioridade': 'ALTA',
            'status': 'EM_ANDAMENTO',
            'responsavel': str(self.servidor.id),
            'prazo': self.demanda.prazo.strftime('%Y-%m-%d'),
            'observacao_alteracao': 'Documentação conferida no arquivo geral; processo iniciado.',
            'resultado': '',
        }

        response = self.client.post(url, dados)
        self.assertEqual(response.status_code, 302)

        self.demanda.refresh_from_db()
        self.assertEqual(self.demanda.status, 'EM_ANDAMENTO')

        # Recupera o registro gerado no histórico
        historico = self.demanda.historicos.first()
        self.assertIsNotNone(historico)

        # 1. Usuário responsável pela alteração
        self.assertEqual(historico.usuario, self.servidor)
        self.assertEqual(historico.usuario.get_full_name(), 'Patrícia Alves')

        # 2. Data e horário registrados
        self.assertGreaterEqual(historico.data_alteracao, tempo_antes)
        self.assertLessEqual(historico.data_alteracao, timezone.now() + timedelta(seconds=2))

        # 3. Status anterior
        self.assertEqual(historico.etapa_anterior, 'Recebida')

        # 4. Novo status
        self.assertEqual(historico.nova_etapa, 'Em Andamento')

        # 5. Salvar observações
        self.assertIn('Documentação conferida no arquivo geral; processo iniciado.', historico.observacao)



class RegistroNovasSolicitacoesChecklistTestCase(TestCase):
    def setUp(self):
        self.atendente = User.objects.create_user(
            username='atendente_registro', password='123', first_name='Camila', last_name='Atendente'
        )
        PerfilUsuario.objects.create(user=self.atendente, perfil='ATENDENTE')
        self.categoria = Categoria.objects.create(nome='Declaração de Frequência')

    def test_checklist_validar_informacoes_obrigatorias(self):
        """Item do Checklist: Validar informações obrigatórias (rejeitar submissão com campos vazios)."""
        self.client.force_login(self.atendente)
        url = reverse('secretaria:criar_demanda')

        # Envia formulário sem preencher os campos obrigatórios
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 200)

        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('solicitante', form.errors)
        self.assertIn('contato', form.errors)
        self.assertIn('categoria', form.errors)
        self.assertIn('descricao', form.errors)
        self.assertIn('prioridade', form.errors)

    def test_checklist_receber_salvar_e_retornar_confirmacao(self):
        """
        Itens do Checklist:
        1. Receber dados do formulário
        2. Salvar a demanda no banco
        3. Retornar confirmação de cadastro
        """
        self.client.force_login(self.atendente)
        url = reverse('secretaria:criar_demanda')

        dados_formulario = {
            'solicitante': 'Lucas Silveira',
            'contato': '(11) 98888-7777',
            'categoria': str(self.categoria.id),
            'descricao': 'Precisa de declaração de frequência para estágio curricular.',
            'prioridade': 'ALTA',
            'prazo': (timezone.now().date() + timedelta(days=2)).strftime('%Y-%m-%d'),
            'responsavel': str(self.atendente.id),
        }

        # 1. Receber dados do formulário (POST)
        response = self.client.post(url, dados_formulario, follow=True)

        # 2. Salvar a demanda
        demanda = Demanda.objects.filter(solicitante='Lucas Silveira').first()
        self.assertIsNotNone(demanda)
        self.assertEqual(demanda.categoria, self.categoria)
        self.assertEqual(demanda.prioridade, 'ALTA')
        self.assertEqual(demanda.responsavel, self.atendente)

        # 3. Retornar confirmação de cadastro (Redirecionamento com mensagem de sucesso e protocolo)
        self.assertRedirects(response, reverse('secretaria:detalhe_demanda', args=[demanda.protocolo]))
        self.assertContains(response, 'Demanda registrada com sucesso!')
        self.assertContains(response, demanda.protocolo)



class TransicaoEtapasChecklistTestCase(TestCase):
    def setUp(self):
        self.servidor = User.objects.create_user(username='transicao_user', password='123')
        PerfilUsuario.objects.create(user=self.servidor, perfil='ATENDENTE')
        self.cat = Categoria.objects.create(nome='Matrícula')

        self.demanda = Demanda.objects.create(
            categoria=self.cat,
            solicitante='Aluno Fluxo Completo',
            contato='11911112222',
            descricao='Teste de transição das 7 etapas',
            status='RECEBIDA'
        )

    def test_ciclo_completo_todas_as_etapas(self):
        """
        Testa o avanço pelas 7 etapas do checklist:
        1. RECEBIDA
        2. TRIAGEM (Em triagem)
        3. AGUARDANDO_INFO (Aguardando informações)
        4. EM_ANDAMENTO (Em andamento)
        5. EM_VALIDACAO (Em validação)
        6. CONCLUIDA (Concluída)
        7. CANCELADA (Cancelada)
        """
        self.client.force_login(self.servidor)
        etapas = [
            'TRIAGEM',
            'AGUARDANDO_INFO',
            'EM_ANDAMENTO',
            'EM_VALIDACAO',
            'CONCLUIDA',
            'CANCELADA',
            'RECEBIDA',
        ]

        for etapa in etapas:
            url = reverse('secretaria:avancar_etapa', args=[self.demanda.protocolo, etapa])
            response = self.client.get(url, follow=True)
            self.assertEqual(response.status_code, 200)

            self.demanda.refresh_from_db()
            self.assertEqual(self.demanda.status, etapa)

            # Verifica se gerou o histórico correspondente à transição
            ultimo_hist = self.demanda.historicos.first()
            self.assertIsNotNone(ultimo_hist)
            self.assertEqual(ultimo_hist.nova_etapa, self.demanda.get_status_display())
            self.assertEqual(ultimo_hist.usuario, self.servidor)

        # Na etapa CONCLUIDA, verifica se preencheu data de conclusão
        # Re-testa conclusão explicitamente
        url_concluir = reverse('secretaria:avancar_etapa', args=[self.demanda.protocolo, 'CONCLUIDA'])
        self.client.get(url_concluir)
        self.demanda.refresh_from_db()
        self.assertEqual(self.demanda.status, 'CONCLUIDA')
        self.assertIsNotNone(self.demanda.data_conclusao)
