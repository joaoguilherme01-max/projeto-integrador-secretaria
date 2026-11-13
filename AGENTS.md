# Instruções para Agentes de IA (AGENTS.md)

Este documento orienta os agentes de IA e desenvolvedores que atuam no repositório **projeto-integrador-secretaria** (Sistema de Gestão e Acompanhamento de Demandas da Secretaria Escolar).

---

## 1. Visão Geral do Projeto

O sistema é um painel digital no modelo Kanban e tabular para organizar solicitações da secretaria escolar, acompanhar etapas de atendimento e estabelecer responsabilidades claras.

### Objetivos Principais:
- Centralizar pedidos com emissão de protocolo único (ex.: `SEC-2026-00025`).
- Acompanhar status/etapas em um quadro visual responsivo (desktop, tablet e mobile).
- Definir responsável principal, prioridade e prazo para cada demanda.
- Registrar histórico detalhado de alterações (mudança de status, transferências de responsável, observações).
- Fornecer painel de indicadores gerenciais (demandas abertas, atrasadas, tempo médio, distribuição por responsável e categorias).

---

## 2. Stack Tecnológica

- **Backend:** Python 3.x + Django (app principal: `secretaria`, projeto: `setup`)
- **Banco de Dados:** SQLite (ambiente de desenvolvimento e MVP inicial; arquitetura preparada para migração futura para PostgreSQL via Django ORM)
- **Frontend:** HTML5 semântico, CSS3 responsivo (Bootstrap recomendado) e JavaScript vanilla para interações dinâmicas leves (filtros, confirmações)
- **Autenticação e Permissões:** Sistema nativo do Django (`django.contrib.auth`) com perfis de acesso customizados
- **Ambiente Virtual:** `venv/` (ativar via `venv\Scripts\Activate.ps1` ou `activate.bat`)

---

## 3. Modelo de Dados e Entidades Principais

Baseado no DER e documento norteador do projeto:

1. **`Usuario` (estendendo `auth.User` ou modelo de perfil associado)**
   - `id` (PK)
   - `nome` (String)
   - `login` / `username` (UK)
   - `senha` (Hash protegido)
   - `perfil` (Choices: `ADMINISTRADOR`, `GESTOR`, `ATENDENTE`)
   - `ativo` (Boolean)

2. **`Categoria`**
   - `id` (PK)
   - `nome` (ex.: Declaração, Histórico, Matrícula, Transferência, Atendimento geral)
   - `descricao` (Text)
   - `ativa` (Boolean, default True)

3. **`Demanda`**
   - `id` (PK)
   - `protocolo` (String única gerada automaticamente, ex.: `SEC-AAAA-NNNNN`)
   - `categoria` (FK -> `Categoria`)
   - `responsavel` (FK -> `Usuario`, nullable caso na triagem inicial)
   - `solicitante` (String: nome do aluno/responsável)
   - `contato` (String: telefone ou e-mail estritamente necessário)
   - `descricao` (Text: detalhe do pedido)
   - `prioridade` (Choices: `BAIXA`, `MEDIA`, `ALTA`, `URGENTE`)
   - `status` (Choices: ver fluxo abaixo)
   - `data_entrada` (DateTime, auto_now_add=True)
   - `prazo` (Date)
   - `data_conclusao` (DateTime, nullable)
   - `resultado` (Text: observação de encerramento ou justificativa de cancelamento)

4. **`Historico`**
   - `id` (PK)
   - `demanda` (FK -> `Demanda`, related_name='historicos')
   - `usuario` (FK -> `Usuario`: autor da alteração)
   - `etapa_anterior` (String)
   - `nova_etapa` (String)
   - `responsavel_anterior` (FK -> `Usuario`, nullable)
   - `novo_responsavel` (FK -> `Usuario`, nullable)
   - `observacao` (Text)
   - `data_alteracao` (DateTime, auto_now_add=True)

5. **`Anexo` (Opcional)**
   - `id` (PK)
   - `demanda` (FK -> `Demanda`, related_name='anexos')
   - `nome_arquivo` (String)
   - `arquivo` (FileField com upload_to seguro)
   - `data_envio` (DateTime, auto_now_add=True)

---

## 4. Fluxo de Etapas (Status da Demanda)

Toda demanda percorre o seguinte fluxo de ciclo de vida:

1. **`RECEBIDA`** (Recebida): Registrada no sistema, gerou protocolo, aguarda triagem.
2. **`TRIAGEM`** (Em triagem): Equipe verifica informações, categoriza, define prioridade, prazo e responsável.
3. **`AGUARDANDO_INFO`** (Aguardando informações): Bloqueada aguardando documento ou retorno do solicitante/terceiros.
4. **`EM_ANDAMENTO`** (Em andamento): Responsável executando as ações para atendimento.
5. **`EM_VALIDACAO`** (Em validação): Executada, pendente de assinatura, conferência ou validação da gestão.
6. **`CONCLUIDA`** (Concluída): Pedido atendido, com data de conclusão e observação final registradas.
7. **`CANCELADA`** (Cancelada): Solicitação abortada/rejeitada, com motivo obrigatório registrado.

> **Regra Obrigatória:** Toda alteração de status ou atribuição de responsável deve gerar automaticamente um registro em `Historico`.

---

## 5. Perfis e Regras de Negócio (RBAC)

- **Administrador do Sistema:** Gestão completa de usuários, permissões, categorias do sistema e parâmetros gerais.
- **Gestor da Secretaria:** Visualiza todas as demandas, atribui/redistribui responsáveis, ajusta prioridades e prazos, acessa o painel de métricas/indicadores e relatórios.
- **Atendente / Servidor:** Registra novas solicitações, consulta demandas atribuídas ou do setor, movimenta etapas, adiciona observações e conclui pedidos.

---

## 6. Requisitos Funcionais do Sistema

- **RF01:** Autenticação individual (login e senha protegida).
- **RF02:** CRUD completo de demandas com restrição por perfis.
- **RF03:** Geração de protocolo único sequencial/anual (`SEC-YYYY-XXXXX`).
- **RF04:** Visualização em quadro (Kanban) e listagem tabular pesquisável/paginada.
- **RF05:** Definição e alteração de responsável, prioridade e prazo de entrega.
- **RF06:** Auditoria completa e linha do tempo de histórico por demanda.
- **RF07:** Filtros combinados por status, responsável, categoria/tipo, prioridade e data.
- **RF08:** Dashboard gerencial com indicadores (total abertas, fora do prazo, tempo médio, gargalos por etapa).

---

## 7. Diretrizes de Desenvolvimento para Agentes

Ao implementar código neste repositório, o agente deve seguir estritamente:

1. **Padronização Django:**
   - Modelos, views e formulários no app `secretaria`.
   - Utilizar Django Forms (`ModelForm`) com validações nos campos obrigatórios.
   - Manter configurações sensíveis (`SECRET_KEY`, `DEBUG`) compatíveis com variáveis de ambiente.
   - Configurar `LANGUAGE_CODE = 'pt-br'` e `TIME_ZONE = 'America/Sao_Paulo'`.

2. **Segurança e Privacidade (LGPD):**
   - Não expor dados do quadro de demandas sem autenticação (`@login_required`).
   - Coletar apenas dados necessários do solicitante (nome e contato). Evitar dados sensíveis desnecessários.
   - Proteger formulários sempre com `{% csrf_token %}`.
   - Validar permissões nas views (não confiar apenas em botões ocultos no frontend).

3. **Interface e UX:**
   - Layout responsivo adaptado para celular, tablet e desktop.
   - Utilizar cores semânticas para prioridades (ex.: Alta/Urgente em tons de alerta/vermelho).
   - Indicação visual explícita de prazos vencidos/atrasados.
   - Mensagens claras de feedback ao usuário (`django.contrib.messages`).

4. **Comandos Úteis:**
   ```bash
   # Ativação do ambiente virtual (Windows PowerShell)
   .\venv\Scripts\Activate.ps1

   # Migrações
   python manage.py makemigrations secretaria
   python manage.py migrate

   # Execução do servidor
   python manage.py runserver

   # Testes
   python manage.py test secretaria
   ```

