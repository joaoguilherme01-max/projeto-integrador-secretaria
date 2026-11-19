# Instruções para Agentes de IA e Desenvolvedores (AGENTS.md)

Este documento orienta os agentes de IA e desenvolvedores que atuam no repositório **projeto-integrador-secretaria** (Sistema de Gestão e Acompanhamento de Demandas da Secretaria Escolar).

---

## 1. Visão Geral do Projeto

O sistema é um painel digital com visualização em quadro **Kanban**, **listagem tabular pesquisável** e **dashboard gerencial**, projetado para organizar as solicitações da secretaria escolar, rastrear etapas de atendimento, garantir auditoria e estabelecer responsabilidades claras.

### Objetivos Principais:
- Centralizar pedidos com emissão de protocolo único anual sequencial (ex.: `SEC-2026-00001`).
- Acompanhar status/etapas em um quadro Kanban interativo responsivo (computador, tablet e celular).
- Definir responsável principal, prioridade e prazo para cada demanda.
- Registrar histórico detalhado e automático de alterações (mudança de status, transferências de responsável, alterações de prazo/prioridade e observações).
- Fornecer painel de indicadores gerenciais (demandas abertas, atrasadas, tempo médio, distribuição por responsável e categorias).

---

## 2. Stack Tecnológica e Arquitetura

- **Backend:** Python 3.10+ / 3.15 + Django 6.1 (app principal: `secretaria`, projeto: `setup`).
- **Banco de Dados Híbrido:**
  - **Desenvolvimento local:** SQLite (`db.sqlite3`).
  - **Produção (Vercel / Neon / Render / PythonAnywhere):** PostgreSQL configurado automaticamente via `DATABASE_URL` (`dj-database-url` + `psycopg2-binary`).
- **Arquivos Estáticos:** Servidos em produção via `WhiteNoise` (`whitenoise.middleware.WhiteNoiseMiddleware`).
- **Frontend:** HTML5 semântico, Bootstrap 5.3 responsivo, Bootstrap Icons e CSS customizado com acessibilidade WCAG (alto contraste e foco visível).
- **Autenticação e Permissões:** Sistema nativo do Django (`django.contrib.auth`) com decorator customizado `@perfil_necessario` e grupos de permissões por perfil.
- **Ambiente Virtual:** `venv/` (ativar via `.\venv\Scripts\Activate.ps1` no Windows ou `source venv/bin/activate` no Linux).

---

## 3. Modelo de Dados e Entidades Principais

Baseado no DER e implementado em `secretaria/models.py`:

1. **`PerfilUsuario` (vínculo OneToOne com `auth.User`)**
   - `user` (OneToOneField -> User)
   - `perfil` (Choices: `ADMINISTRADOR`, `GESTOR`, `ATENDENTE`)
   - `ativo` (Boolean, default True)

2. **`Categoria`**
   - `id` (PK)
   - `nome` (ex.: *Declaração*, *Histórico escolar*, *Matrícula*, *Transferência*, *Atendimento*)
   - `descricao` (Text)
   - `ativa` (Boolean, default True)

3. **`Demanda`**
   - `id` (PK)
   - `protocolo` (CharField, max_length=20, unique=True, editable=False) - Gerado atomicamente no `save()` no padrão `SEC-YYYY-XXXXX`.
   - `categoria` (FK -> `Categoria`, on_delete=PROTECT)
   - `responsavel` (FK -> `User`, on_delete=SET_NULL, null=True, blank=True)
   - `solicitante` (CharField, max_length=150)
   - `contato` (CharField, max_length=100)
   - `descricao` (TextField)
   - `prioridade` (Choices: `BAIXA`, `MEDIA`, `ALTA`, `URGENTE`)
   - `status` (Choices: 7 etapas - ver abaixo)
   - `data_entrada` (DateTimeField, auto_now_add=True)
   - `prazo` (DateField, null=True, blank=True)
   - `data_conclusao` (DateTimeField, null=True, blank=True)
   - `resultado` (TextField: desfecho ou justificativa de cancelamento)

4. **`Historico`**
   - `id` (PK)
   - `demanda` (FK -> `Demanda`, related_name='historicos')
   - `usuario` (FK -> `User`: autor da alteração)
   - `etapa_anterior` (CharField)
   - `nova_etapa` (CharField)
   - `responsavel_anterior` (FK -> `User`, null=True, blank=True)
   - `novo_responsavel` (FK -> `User`, null=True, blank=True)
   - `observacao` (TextField: notas manuais somadas ao resumo automático de auditoria)
   - `data_alteracao` (DateTimeField, auto_now_add=True)

5. **`Anexo`**
   - `id` (PK)
   - `demanda` (FK -> `Demanda`, related_name='anexos')
   - `nome_arquivo` (CharField)
   - `arquivo` (FileField com upload para `anexos/%Y/%m/`)
   - `data_envio` (DateTimeField, auto_now_add=True)

---

## 4. Fluxo de Etapas (Ciclo de Vida da Demanda)

Toda demanda percorre as seguintes etapas padronizadas (`STATUS_CHOICES`):

1. **`RECEBIDA`** (Recebida): Registrada no sistema, gerou protocolo único, aguarda triagem.
2. **`TRIAGEM`** (Em triagem): Equipe valida documentos, define responsável, prioridade e prazo.
3. **`AGUARDANDO_INFO`** (Aguardando informações): Bloqueada aguardando documento ou retorno do solicitante.
4. **`EM_ANDAMENTO`** (Em andamento): Responsável executando as ações para emissão/atendimento.
5. **`EM_VALIDACAO`** (Em validação): Atividade realizada, aguardando assinatura ou conferência da gestão.
6. **`CONCLUIDA`** (Concluída): Pedido atendido com sucesso; preenche `data_conclusao` automaticamente.
7. **`CANCELADA`** (Cancelada): Solicitação abortada/rejeitada, com motivo registrado no histórico.

> **Regra Obrigatória:** Toda alteração de status, troca de responsável, mudança de prioridade/prazo ou observação gera automaticamente uma entrada no `Historico`.

---

## 5. Perfis e Regras de Negócio (RBAC)

- **Administrador do Sistema (`ADMINISTRADOR`):** Gestão de contas, ativação/desativação de usuários, permissões, categorias do sistema, parâmetros gerais e acesso completo ao Django Admin (`/admin/`).
- **Gestor da Secretaria (`GESTOR`):** Visualiza todas as demandas, atribui e transfere responsáveis, altera prazos e prioridades, acessa o quadro Kanban e tem **acesso exclusivo ao Painel Gerencial de Indicadores** (`/dashboard/`).
- **Atendente / Servidor (`ATENDENTE`):** Registra novas solicitações, consulta a fila de demandas, movimenta etapas no quadro Kanban, insere observações e conclui pedidos (bloqueado de acessar métricas estratégicas).

---

## 6. Mapeamento de Rotas e Telas Implementadas

| Rota / Endpoint | View | Finalidade | Permissão |
| :--- | :--- | :--- | :--- |
| `/login/` | `login_view` | Autenticação com usuário e senha | Pública |
| `/logout/` | `logout_view` | Encerramento seguro de sessão | Autenticado |
| `/` | `index_view` | Tela inicial com totalizadores e abas (Abertas, Atrasadas, Concluídas) | `@login_required` |
| `/quadro/` | `quadro_kanban` | Quadro visual Kanban com 7 colunas e filtros rápidos | `@login_required` |
| `/demandas/` | `lista_demandas` | Listagem tabular pesquisável e paginada com filtros combinados | `@login_required` |
| `/demandas/nova/` | `criar_demanda` | Formulário de registro com geração de protocolo automático | `@login_required` |
| `/demandas/<protocolo>/` | `detalhe_demanda` | Exibição de dados completos, linha do tempo e auditoria | `@login_required` |
| `/demandas/<protocolo>/editar/` | `editar_demanda` | Edição de prazos, prioridade, responsável e observações | `@login_required` |
| `/demandas/<protocolo>/avancar/<status>/` | `avancar_etapa_demanda` | Transição rápida de etapa ("Mover Etapa") | `@login_required` |
| `/dashboard/` | `dashboard_indicadores` | Painel gerencial com gráficos e métricas analíticas | `ADMINISTRADOR`, `GESTOR` |
| `/api/indicadores/` | `api_indicadores` | Endpoint JSON com métricas consolidadas | `ADMINISTRADOR`, `GESTOR` |
| `/admin/` | Django Admin | Interface administrativa com tema customizado e badges | `is_staff` / `ADMINISTRADOR` |

---

## 7. Comandos de Gestão Customizados (`manage.py`)

O app `secretaria` possui os seguintes management commands implementados:

1. **`python manage.py seed_usuarios`**  
   Cria os usuários padrão de teste (`admin`, `gestor`, `atendente`) e demandas de demonstração.
2. **`python manage.py seed_categorias`**  
   Popula as categorias padrão da secretaria escolar (*Declaração, Histórico escolar, Matrícula, Transferência, Atendimento*).
3. **`python manage.py configurar_permissoes`**  
   Cria e configura os grupos de permissões do Django (`ADMINISTRADOR`, `GESTOR`, `ATENDENTE`).
4. **`python manage.py backup_db`**  
   Gera cópia consistente do banco SQLite usando a API nativa de backup em `backups/`.

---

## 8. Diretrizes de Desenvolvimento para Agentes

Ao implementar código neste repositório, o agente deve seguir estritamente:

1. **Padronização Django:**
   - Modelos, views e formulários no app `secretaria`.
   - Utilizar Django Forms (`ModelForm`) com validação nos campos obrigatórios.
   - Manter compatibilidade com `DATABASE_URL` (PostgreSQL em produção e fallback para SQLite local).
   - Manter `LANGUAGE_CODE = 'pt-br'` e `TIME_ZONE = 'America/Sao_Paulo'`.

2. **Segurança e Privacidade (LGPD):**
   - Não expor dados do quadro de demandas sem autenticação (`@login_required`).
   - Coletar apenas dados necessários do solicitante (nome e contato). Evitar dados sensíveis desnecessários.
   - Proteger todos os formulários com `{% csrf_token %}`.
   - Validar permissões nas views com `@perfil_necessario`.

3. **Interface e UX:**
   - Layout responsivo adaptado para computador, tablet e celular (breakpoints móveis no Kanban e menus).
   - Cores semânticas com alto contraste (padrão WCAG AA/AAA).
   - Indicação visual explícita de prazos vencidos (`⚠️` e badge vermelha).
   - Mensagens claras de feedback (`django.contrib.messages`).

4. **Comandos Úteis de Execução e Teste:**
   ```powershell
   # Ativação do ambiente virtual (PowerShell)
   .\venv\Scripts\Activate.ps1

   # Migrações
   python manage.py makemigrations secretaria
   python manage.py migrate

   # Execução do servidor local
   python manage.py runserver

   # Execução acessível na rede local / celular
   python manage.py runserver 0.0.0.0:8000

   # Execução de todos os testes unitários (32+ testes automatizados)
   python manage.py test secretaria
   ```
