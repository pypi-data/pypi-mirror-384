# Feature Specification: Essential Topology Operations

**Feature Branch**: `003-essential-topology-operations`  
**Created**: 2025-10-09  
**Status**: Draft  
**Input**: User description: "Essential Topology Operations"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View and Monitor Message Infrastructure (Priority: P1)

Como operador do sistema, preciso visualizar todas as filas, exchanges e bindings existentes com suas estatísticas básicas para entender o estado atual da infraestrutura de mensagens e identificar problemas.

**Why this priority**: Esta é a funcionalidade mais crítica pois fornece visibilidade essencial da infraestrutura. Sem ela, operadores trabalham às cegas. É também o ponto de partida para todas as outras operações.

**Independent Test**: Pode ser completamente testado conectando a um RabbitMQ com filas/exchanges pré-configuradas e verificando que todas as informações são exibidas corretamente. Entrega valor imediato ao permitir monitoramento sem modificar nada.

**Acceptance Scenarios**:

1. **Given** um sistema com múltiplas filas ativas, **When** solicito a lista de filas, **Then** vejo todas as filas com nome, contagem de mensagens, número de consumidores e uso de memória
2. **Given** um sistema com exchanges de diferentes tipos, **When** solicito a lista de exchanges, **Then** vejo todos os exchanges com nome, tipo (direct/topic/fanout/headers) e contagem de bindings
3. **Given** um sistema com bindings entre filas e exchanges, **When** solicito a lista de bindings, **Then** vejo todos os bindings com exchange de origem, fila de destino e routing key
4. **Given** uma fila com 1000 mensagens, **When** visualizo suas estatísticas, **Then** vejo a contagem exata de mensagens e taxa de processamento
5. **Given** um sistema com 1000 filas, **When** solicito a lista, **Then** recebo todos os resultados em menos de 2 segundos

---

### User Story 2 - Create Message Routing Infrastructure (Priority: P2)

Como operador do sistema, preciso criar filas, exchanges e bindings com configurações apropriadas para estabelecer novos fluxos de mensagens conforme as necessidades da aplicação.

**Why this priority**: Após poder visualizar a infraestrutura (P1), a próxima necessidade crítica é poder criar novos componentes. Isto é essencial para configurar novos serviços e fluxos de mensagens.

**Independent Test**: Pode ser testado criando filas/exchanges/bindings em um RabbitMQ limpo e verificando que são criados corretamente com as opções especificadas. Entrega valor ao permitir configuração de novos fluxos.

**Acceptance Scenarios**:

1. **Given** um virtual host vazio, **When** crio uma nova fila com nome e opções (durável, exclusiva, auto-delete), **Then** a fila é criada com as configurações especificadas e aparece na listagem
2. **Given** um virtual host, **When** crio um exchange especificando nome e tipo (direct/topic/fanout/headers), **Then** o exchange é criado com o tipo correto e fica disponível para bindings
3. **Given** uma fila e um exchange existentes, **When** crio um binding entre eles com routing key, **Then** mensagens enviadas ao exchange com essa routing key são roteadas para a fila
4. **Given** parâmetros de criação válidos, **When** executo a operação de criação, **Then** ela completa em menos de 1 segundo
5. **Given** um nome de fila já existente, **When** tento criar uma fila com o mesmo nome mas configurações diferentes, **Then** recebo uma mensagem clara indicando o conflito

---

### User Story 3 - Remove Obsolete Infrastructure Safely (Priority: P3)

Como operador do sistema, preciso remover filas, exchanges e bindings obsoletos de forma segura, com validações que previnam perda de dados ou interrupção de serviços.

**Why this priority**: Remoção é importante para manutenção e limpeza, mas é menos urgente que visualização e criação. Requer cuidados extras com segurança, por isso vem depois das operações básicas.

**Independent Test**: Pode ser testado criando componentes de teste, verificando as validações de segurança (tentar deletar fila com mensagens), e confirmando remoções bem-sucedidas quando apropriado.

**Acceptance Scenarios**:

1. **Given** uma fila vazia sem consumidores, **When** solicito sua deleção, **Then** a fila é removida e desaparece da listagem
2. **Given** uma fila com mensagens pendentes, **When** tento deletá-la, **Then** recebo um aviso claro de que a fila contém mensagens e a operação é bloqueada
3. **Given** um exchange sem bindings, **When** solicito sua deleção, **Then** o exchange é removido com sucesso
4. **Given** um exchange com bindings ativos, **When** tento deletá-lo, **Then** recebo um aviso claro de que há bindings e a operação é bloqueada
5. **Given** um binding existente, **When** solicito sua deleção, **Then** o binding é removido e mensagens param de fluir entre o exchange e a fila
6. **Given** uma operação de deleção válida, **When** executo a deleção, **Then** ela completa em menos de 1 segundo

---

### Edge Cases

- O que acontece quando tento listar filas/exchanges em um virtual host que não existe?
- Como o sistema responde quando tento criar uma fila com nome inválido (caracteres especiais, muito longo)?
- O que acontece se a conexão com RabbitMQ cai durante uma operação de criação ou deleção?
- Como o sistema lida com tentativa de binding entre fila e exchange que não existem?
- O que acontece quando tento deletar um exchange do sistema (amq.*) que não pode ser removido?
- Como o sistema responde quando há timeout nas operações de listagem com grande volume de entidades?
- O que acontece quando duas operações conflitantes ocorrem simultaneamente (criar e deletar a mesma fila)?

## Requirements *(mandatory)*

### Functional Requirements

#### Queue Operations
- **FR-001**: Sistema DEVE permitir listar todas as filas de um virtual host específico ou de todos os virtual hosts
- **FR-002**: Sistema DEVE exibir estatísticas básicas de cada fila incluindo: contagem de mensagens, número de consumidores ativos, e uso de memória
- **FR-003**: Sistema DEVE permitir criar novas filas especificando nome e opções básicas (durável, exclusiva, auto-delete)
- **FR-004**: Sistema DEVE validar que o nome da fila é válido antes de criá-la (caracteres permitidos, comprimento)
- **FR-005**: Sistema DEVE prevenir criação de fila com nome duplicado no mesmo virtual host
- **FR-006**: Sistema DEVE permitir deletar filas existentes
- **FR-007**: Sistema DEVE verificar que a fila está vazia antes de permitir deleção
- **FR-008**: Sistema DEVE fornecer opção de forçar deleção de fila mesmo com mensagens (com confirmação explícita)

#### Exchange Operations
- **FR-009**: Sistema DEVE permitir listar todos os exchanges com informações de tipo (direct, topic, fanout, headers)
- **FR-010**: Sistema DEVE exibir estatísticas básicas de cada exchange incluindo contagem de bindings e taxas de mensagens
- **FR-011**: Sistema DEVE permitir criar novos exchanges especificando nome e tipo
- **FR-012**: Sistema DEVE suportar os tipos de exchange padrão: direct, topic, fanout, headers
- **FR-013**: Sistema DEVE validar que o tipo de exchange especificado é válido
- **FR-014**: Sistema DEVE prevenir criação de exchange com nome duplicado
- **FR-015**: Sistema DEVE permitir deletar exchanges existentes
- **FR-016**: Sistema DEVE verificar que o exchange não possui bindings ativos antes de permitir deleção
- **FR-017**: Sistema DEVE prevenir deleção de exchanges do sistema (amq.* e default exchange)

#### Binding Operations
- **FR-018**: Sistema DEVE permitir listar todos os bindings mostrando exchange de origem, fila de destino e routing key
- **FR-019**: Sistema DEVE permitir criar bindings entre exchanges e filas especificando routing key
- **FR-020**: Sistema DEVE validar que tanto exchange quanto fila existem antes de criar binding
- **FR-021**: Sistema DEVE suportar routing keys com padrões de wildcard (* e #) para exchanges tipo topic
- **FR-022**: Sistema DEVE permitir deletar bindings específicos entre exchange e fila
- **FR-023**: Sistema DEVE prevenir criação de bindings duplicados (mesmo exchange, mesma fila, mesma routing key)

#### Safety and Validation
- **FR-024**: Sistema DEVE validar existência de virtual host antes de executar qualquer operação
- **FR-025**: Sistema DEVE fornecer mensagens de erro claras e específicas para cada tipo de falha de validação
- **FR-026**: Sistema DEVE registrar todas as operações de criação e deleção em log para auditoria
- **FR-027**: Sistema DEVE validar permissões antes de executar operações destrutivas

### Key Entities

- **Queue**: Representa uma fila de mensagens com atributos de nome, virtual host, propriedades de durabilidade, estatísticas de mensagens e consumidores
- **Exchange**: Representa um roteador de mensagens com tipo (direct/topic/fanout/headers), nome, virtual host, e estatísticas de throughput
- **Binding**: Representa uma regra de roteamento conectando exchange a fila, incluindo routing key e padrões de matching
- **Virtual Host**: Agrupamento lógico isolando conjuntos de filas, exchanges e bindings

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Operadores conseguem visualizar o estado completo da infraestrutura de mensagens (todas filas, exchanges e bindings) em menos de 2 segundos
- **SC-002**: Operações de criação de fila, exchange ou binding completam em menos de 1 segundo
- **SC-003**: Operações de deleção de fila, exchange ou binding completam em menos de 1 segundo  
- **SC-004**: Sistema previne 100% das tentativas de deleção de filas com mensagens sem confirmação explícita
- **SC-005**: Sistema previne 100% das tentativas de deleção de exchanges com bindings ativos
- **SC-006**: Sistema lida eficientemente com até 1000 filas e 1000 exchanges sem degradação de performance
- **SC-007**: 95% das operações que falham fornecem mensagem de erro clara permitindo ao operador corrigir o problema sem consultar documentação
- **SC-008**: Todas as operações de criação e deleção são registradas em log permitindo auditoria completa
- **SC-009**: Sistema valida 100% dos parâmetros de entrada antes de executar operações, prevenindo estados inconsistentes

## Assumptions

- RabbitMQ Management API está habilitado e acessível
- Operadores têm credenciais apropriadas para acessar a Management API
- Sistema roda em ambiente onde latência de rede até o RabbitMQ é menor que 100ms
- Virtual host padrão é "/" quando não especificado
- Operações de listagem retornam todas as entidades sem paginação para até 1000 itens
- Log de auditoria é persistido usando structured logging com nível INFO para operações bem-sucedidas e WARNING/ERROR para falhas
