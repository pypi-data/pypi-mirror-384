# Feature Specification: Basic Console Client

**Feature Branch**: `005-basic-console-client`  
**Created**: 2025-10-09  
**Status**: Draft  
**Input**: User description: "Basic Console Client"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Connect and Check Health (Priority: P1)

Um operador de sistema precisa verificar se o servidor RabbitMQ está acessível e funcionando antes de executar operações. Ele abre o console e executa comandos simples para estabelecer conexão e verificar o status.

**Why this priority**: Conexão é a base para todas as outras operações - sem ela, nada funciona. É o primeiro passo em qualquer fluxo de trabalho.

**Independent Test**: Pode ser testado completamente executando o comando de conexão e verificando se retorna status de sucesso ou erro apropriado. Entrega valor imediato: confirmação de que o sistema está operacional.

**Acceptance Scenarios**:

1. **Given** o servidor RabbitMQ está em execução, **When** o usuário executa o comando de conexão com credenciais válidas, **Then** o sistema confirma conexão bem-sucedida e exibe status
2. **Given** o servidor RabbitMQ está inacessível, **When** o usuário tenta conectar, **Then** o sistema exibe mensagem de erro clara indicando que não conseguiu estabelecer conexão
3. **Given** conexão estabelecida, **When** o usuário executa comando de health check, **Then** o sistema retorna status atual do servidor em menos de 100ms

---

### User Story 2 - Manage Queues and Exchanges (Priority: P2)

Um desenvolvedor precisa criar e gerenciar filas e exchanges para configurar a topologia de mensageria. Ele usa comandos para listar recursos existentes, criar novos elementos e remover os que não são mais necessários.

**Why this priority**: Operações de topologia são essenciais para configurar o ambiente de mensageria, mas dependem de uma conexão ativa (P1). Permite preparar a infraestrutura antes de enviar mensagens.

**Independent Test**: Pode ser testado criando uma fila, listando para confirmar sua existência e depois removendo-a. Entrega valor: capacidade de gerenciar a estrutura do sistema de mensageria.

**Acceptance Scenarios**:

1. **Given** conexão estabelecida, **When** usuário lista filas existentes, **Then** sistema exibe todas as filas com suas propriedades básicas
2. **Given** conexão estabelecida, **When** usuário cria nova fila com nome válido, **Then** sistema confirma criação e fila aparece na listagem
3. **Given** fila existente sem mensagens, **When** usuário solicita sua remoção, **Then** sistema remove a fila e confirma operação
4. **Given** conexão estabelecida, **When** usuário cria exchange com tipo válido, **Then** sistema cria exchange e confirma operação
5. **Given** exchange existente, **When** usuário lista exchanges, **Then** sistema exibe o exchange criado com seu tipo

---

### User Story 3 - Publish and Subscribe Messages (Priority: P3)

Um operador precisa enviar mensagens de teste para um exchange e receber mensagens de uma fila para verificar o fluxo de dados. Ele publica mensagens com routing keys específicas e assina filas para monitorar mensagens recebidas.

**Why this priority**: Publicação e consumo de mensagens são operações finais que dependem de conexão (P1) e topologia configurada (P2). Representa o uso efetivo do sistema de mensageria.

**Independent Test**: Pode ser testado publicando uma mensagem em um exchange, assinando a fila vinculada e verificando se a mensagem foi recebida. Entrega valor: capacidade de validar fluxo completo de mensageria.

**Acceptance Scenarios**:

1. **Given** exchange e fila existentes e vinculados, **When** usuário publica mensagem com routing key válida, **Then** sistema confirma envio da mensagem
2. **Given** fila contém mensagens, **When** usuário assina a fila, **Then** sistema entrega mensagens em tempo real conforme chegam
3. **Given** mensagem recebida, **When** usuário processa e reconhece a mensagem, **Then** sistema remove mensagem da fila
4. **Given** mensagem publicada, **When** sistema tem erro de envio, **Then** sistema exibe mensagem de erro clara indicando o problema

---

### User Story 4 - View Status and Metrics (Priority: P4)

Um administrador quer monitorar o estado da conexão e métricas básicas de operação para identificar problemas ou confirmar que o sistema está operando normalmente.

**Why this priority**: Informações de status são úteis mas não essenciais para operações básicas. Podem ser adicionadas após as funcionalidades core estarem funcionando.

**Independent Test**: Pode ser testado executando comando de status e verificando se retorna informações atualizadas sobre conexão e operações. Entrega valor: visibilidade do estado do sistema.

**Acceptance Scenarios**:

1. **Given** conexão ativa, **When** usuário consulta status, **Then** sistema exibe estado da conexão e métricas básicas
2. **Given** sem conexão, **When** usuário consulta status, **Then** sistema indica que não há conexão ativa
3. **Given** operações realizadas, **When** usuário consulta status, **Then** sistema reflete as operações mais recentes

---

### Edge Cases

- O que acontece quando o usuário tenta executar operações sem estar conectado?
- Como o sistema lida com perda de conexão durante operação longa (ex: subscrevendo mensagens)?
- O que acontece quando o usuário fornece nomes inválidos para filas ou exchanges (caracteres especiais, muito longos)?
- Como o sistema responde quando tenta criar recursos que já existem?
- O que acontece quando tenta remover filas que contêm mensagens?
- Como o sistema lida com payloads de mensagens muito grandes?
- O que acontece quando o usuário cancela operação em andamento (Ctrl+C)?
- Como o sistema se comporta com credenciais inválidas ou expiradas?
- O que acontece quando há timeout de rede durante comando?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Sistema DEVE permitir que usuário conecte ao servidor RabbitMQ fornecendo host, porta e credenciais
- **FR-002**: Sistema DEVE exibir confirmação clara de sucesso ou erro após tentativa de conexão
- **FR-003**: Sistema DEVE permitir desconexão explícita do servidor
- **FR-004**: Sistema DEVE verificar saúde da conexão e retornar status do servidor
- **FR-005**: Sistema DEVE listar todas as filas existentes no servidor
- **FR-006**: Sistema DEVE permitir criação de nova fila com nome e opções básicas (durabilidade, auto-delete)
- **FR-007**: Sistema DEVE permitir remoção de fila existente
- **FR-008**: Sistema DEVE listar todos os exchanges existentes no servidor
- **FR-009**: Sistema DEVE permitir criação de novo exchange especificando nome e tipo (direct, topic, fanout, headers)
- **FR-010**: Sistema DEVE permitir remoção de exchange existente
- **FR-011**: Sistema DEVE permitir publicação de mensagem especificando exchange, routing key e payload
- **FR-012**: Sistema DEVE permitir assinatura de fila para receber mensagens em tempo real
- **FR-013**: Sistema DEVE permitir reconhecimento (ack) de mensagens recebidas por delivery tag
- **FR-014**: Sistema DEVE exibir status atual da conexão e métricas básicas de operação
- **FR-015**: Sistema DEVE fornecer ajuda integrada para todos os comandos e opções
- **FR-016**: Sistema DEVE manter histórico de comandos executados entre sessões
- **FR-017**: Sistema DEVE exibir mensagens de erro claras e acionáveis quando operações falham
- **FR-018**: Sistema DEVE validar entrada do usuário antes de executar operações (nomes válidos, parâmetros obrigatórios)
- **FR-019**: Sistema DEVE mostrar indicadores visuais de progresso para operações longas
- **FR-020**: Sistema DEVE usar saída formatada e colorida para melhorar legibilidade

### Key Entities

- **Connection**: Representa conexão ativa com servidor RabbitMQ, incluindo host, porta, credenciais e estado da conexão
- **Queue**: Representa fila de mensagens com atributos como nome, durabilidade, número de mensagens, se é auto-delete
- **Exchange**: Representa exchange com atributos como nome, tipo (direct/topic/fanout/headers), durabilidade
- **Message**: Representa mensagem com payload, routing key, delivery tag, propriedades e metadados
- **Command History**: Histórico de comandos executados pelo usuário, persistido entre sessões

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Usuário consegue conectar ao servidor RabbitMQ e receber confirmação em menos de 2 segundos
- **SC-002**: Comandos simples (listar, criar, deletar) respondem em menos de 100 milissegundos após conexão estabelecida
- **SC-003**: Modo interativo permanece responsivo mesmo após operações prolongadas de subscrição de mensagens
- **SC-004**: 95% dos usuários conseguem executar operações básicas (conectar, criar fila, publicar mensagem) consultando apenas o sistema de ajuda integrado
- **SC-005**: Mensagens de erro permitem que usuário identifique e corrija o problema sem necessitar documentação externa
- **SC-006**: Usuário consegue publicar e receber mensagem de teste em fluxo completo em menos de 1 minuto
- **SC-007**: Histórico de comandos persiste entre sessões e usuário pode reutilizar comandos anteriores
- **SC-008**: Sistema não apresenta vazamentos de memória durante uso prolongado (8+ horas de operação contínua)
- **SC-009**: Interface visual com cores e formatação melhora taxa de conclusão bem-sucedida de tarefas em 30% comparado a output texto simples
- **SC-010**: Todos os comandos são descobertos através do sistema de ajuda sem necessidade de consultar documentação externa
