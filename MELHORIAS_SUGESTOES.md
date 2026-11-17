# Relatório de Apresentação e Validação das Telas Iniciais (Fase de Protótipo e Piloto)

**Projeto:** Sistema de Gestão e Acompanhamento de Demandas da Secretaria Escolar  
**Data:** 17 de Novembro de 2026  
**Público-alvo:** Gestão Escolar, Coordenação e Equipe da Secretaria  

---

## 1. Status dos Itens Apresentados

| Item do Checklist | Rota do Sistema | Status de Desenvolvimento | Resultado da Avaliação Técnica |
| :--- | :--- | :--- | :--- |
| **Apresentar tela de login** | `/login/` | **Concluído e Funcional** | Acesso individual com autenticação segura, bloqueio de contas inativas, visualização de senha e mensagens claras de erro. |
| **Apresentar painel principal** | `/` | **Concluído e Funcional** | Dashboard inicial responsivo com 4 cards de indicadores (abertas, atrasadas, concluídas e tempo médio) e navegação rápida por abas. |
| **Apresentar quadro Kanban** | `/quadro/` | **Concluído e Funcional** | Quadro visual com as 7 etapas do ciclo de vida, cartões com protocolo, solicitante, prioridade, prazo e responsável, adaptado para celular e desktop. |
| **Validar formulário** | `/demandas/nova/` | **Concluído e Funcional** | Validação obrigatória de dados (solicitante, contato, categoria, descrição, prioridade), geração automática de protocolo anual (`SEC-2026-XXXXX`) e auditoria. |
| **Registrar melhorias necessárias** | — | **Documentado Abaixo** | Lista de sugestões e próximas evoluções coletadas para a próxima fase. |

---

## 2. Roteiro de Demonstração para a Gestão

### A. Tela de Login (`/login/`)
- Demonstração do acesso individual por perfil de usuário.
- Credenciais preparadas para demonstração:
  - `admin` (senha `admin123`): Perfil Administrador
  - `gestor` (senha `gestor123`): Perfil Gestor da Secretaria
  - `atendente` (senha `atendente123`): Perfil Atendente/Servidor
- Teste prático do botão de mostrar/ocultar senha e validação de credenciais incorretas.

### B. Painel Principal / Visão Geral (`/`)
- Apresentação dos cards de síntese gerencial:
  - Total de demandas abertas.
  - Alerta em vermelho para demandas atrasadas (prazo expirado).
  - Demandas concluídas e tempo médio de resolução.
- Demonstração da visualização por abas sem recarregar a página (*Abertas*, *Atrasadas* e *Concluídas*).

### C. Quadro Kanban (`/quadro/`)
- Exibição das 7 colunas do fluxo de atendimento:
  1. *Recebida*
  2. *Em triagem*
  3. *Aguardando informações*
  4. *Em andamento*
  5. *Em validação*
  6. *Concluída*
  7. *Cancelada*
- Filtros rápidos por texto livre, categoria, prioridade e responsável diretamente no topo do quadro.

### D. Formulário de Cadastro (`/demandas/nova/`)
- Demonstração de tentativa de submissão em branco e disparo de mensagens de validação obrigatória.
- Cadastro de um pedido real: emissão de protocolo único automático e redirecionamento para a auditoria.

---

## 3. Registro de Melhorias Coletadas e Próximos Passos (Fase 2)

Durante as primeiras validações do protótipo, foram identificadas as seguintes oportunidades de evolução:

1. **Arrastar e Soltar no Kanban (*Drag and Drop*):**
   - *Proposta:* Permitir que os atendentes e gestores arrastem os cartões de uma coluna para outra no Kanban via mouse ou toque no celular, além do botão existente no menu de detalhes.
2. **Notificações e Avisos de Prazos Próximos:**
   - *Proposta:* Destacar em amarelo demandas cujo prazo vença em até 24 ou 48 horas, alertando a equipe antes que fiquem atrasadas.
3. **Upload de Documentos Comprovatórios (Módulo de Anexos):**
   - *Proposta:* Integrar o envio de arquivos PDF/imagens no formulário de atendimento para anexar atestados, certidões ou comprovantes do solicitante.
4. **Portal Externo de Consulta do Aluno:**
   - *Proposta:* Criação de uma página pública simples onde o solicitante digite apenas seu número de protocolo (ex: `SEC-2026-00001`) para acompanhar o status atual sem precisar de login.

