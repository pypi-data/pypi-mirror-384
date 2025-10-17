# Feature Specification: Essential Topology Operations

**Feature Branch**: `003-essential-topology-operations`  
**Created**: 2025-10-09  
**Status**: Draft  
**Input**: User description: "Essential Topology Operations"

## Clarifications

### Session 2025-10-09

- Q: Como o sistema deve validar permissões antes de executar operações destrutivas? → A: Usar as permissões já configuradas no RabbitMQ (usuário da conexão precisa ter permissões adequadas)
- Q: Como o sistema deve se comportar em caso de falha de conexão durante operações? → A: Falhar imediatamente, retornar erro, deixar retry para o usuário
- Q: Qual o mecanismo de confirmação para forçar deleção de fila com mensagens? → A: Flag/parâmetro adicional no comando (ex: --force)
- Q: Quais são as regras de validação para nomes de fila/exchange? → A: Usar as mesmas regras do RabbitMQ (alfanumérico, hífen, underscore, ponto; max 255 chars)
- Q: Qual o comportamento se exchange tiver bindings ativos ao tentar deletá-lo? → A: Bloquear deleção completamente, operador deve deletar bindings primeiro

### Session 2025-10-09 (Round 2)

- Q: Qual é o tipo de interface/aplicação que este sistema deve fornecer? → A: CLI tool (ferramenta de linha de comando com argumentos)

### Session 2025-10-09 (Round 3)

- Q: Qual linguagem/runtime deve ser usada para implementar a CLI? → A: Python
- Q: Qual biblioteca Python deve ser usada para interagir com o RabbitMQ Management API? → A: requests (biblioteca HTTP padrão, máximo controle e amplamente usada)
- Q: Qual framework CLI Python deve ser usado para implementar a interface de linha de comando? → A: click (framework mais popular para CLIs profissionais Python)
- Q: Qual biblioteca Python deve ser usada para structured logging? → A: structlog (padrão da indústria, structured logging nativo, rico em contexto)
- Q: Qual biblioteca Python deve ser usada para formatação de tabelas no output CLI? → A: tabulate (biblioteca mais comum, leve, simples e focada em clareza)

### Session 2025-10-12

- Q: Should the CLI support TLS/SSL connections to the RabbitMQ Management API? → A: TLS with optional certificate verification (verify by default, --insecure flag to skip for self-signed certs)
- Q: Should the CLI support batch operations (creating/deleting multiple resources in a single command)? → A: No batch support - one operation per CLI invocation (simpler, stateless, easier error handling)
- Q: How should the CLI handle HTTP 429 (Too Many Requests) responses from the RabbitMQ Management API? → A: Exponential backoff with maximum 3 retries (1s, 2s, 4s delays - industry standard, resilient)
- Q: How should the CLI manage HTTP connections to the RabbitMQ Management API? → A: Reuse single connection per CLI invocation (efficient for multi-step operations, auto-cleanup on exit)
- Q: What should be the column order for table output when listing queues/exchanges? → A: Name, type/config, stats (identity first, then config, then metrics - natural reading flow)

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
2. **Given** uma fila com mensagens pendentes, **When** tento deletá-la sem flag --force, **Then** recebo um aviso claro de que a fila contém mensagens e a operação é bloqueada
3. **Given** um exchange sem bindings, **When** solicito sua deleção, **Then** o exchange é removido com sucesso
4. **Given** um exchange com bindings ativos, **When** tento deletá-lo, **Then** recebo um erro claro indicando que devo remover os bindings primeiro
5. **Given** um binding existente, **When** solicito sua deleção, **Then** o binding é removido e mensagens param de fluir entre o exchange e a fila
6. **Given** uma operação de deleção válida, **When** executo a deleção, **Then** ela completa em menos de 1 segundo

---

### Edge Cases

- O que acontece quando tento listar filas/exchanges em um virtual host que não existe? → Retornar erro claro indicando virtual host inexistente
- Como o sistema responde quando tento criar uma fila com nome inválido (caracteres especiais, muito longo)? → Validar antes (alfanuméricos, hífen, underscore, ponto; max 255 chars) e retornar erro específico sobre o problema
- Se a conexão com RabbitMQ cai durante uma operação de criação ou deleção → Falhar imediatamente com erro de conectividade, operador decide se tenta novamente
- Como o sistema lida com tentativa de binding entre fila e exchange que não existem? → Validar existência antes (FR-020) e retornar erro se qualquer um não existir
- O que acontece quando tento deletar um exchange com bindings ativos? → Bloquear deleção (FR-016) e retornar erro indicando que bindings devem ser removidos primeiro
- O que acontece quando tento deletar um exchange do sistema (amq.*) que não pode ser removido? → Prevenir deleção (FR-017) e retornar erro explicando que exchanges de sistema não podem ser removidos
- Como o sistema responde quando há timeout nas operações de listagem com grande volume de entidades? → Retornar erro de timeout, operador pode tentar filtrar por virtual host específico
- O que acontece quando duas operações conflitantes ocorrem simultaneamente (criar e deletar a mesma fila)? → RabbitMQ garante atomicidade; uma operação terá sucesso e a outra falhará com erro apropriado

## Requirements *(mandatory)*

### Functional Requirements

#### Queue Operations
- **FR-001**: Sistema DEVE permitir listar todas as filas de um virtual host específico ou de todos os virtual hosts
- **FR-002**: Sistema DEVE exibir estatísticas básicas de cada fila incluindo **OBRIGATORIAMENTE**: `messages` (total message count), `messages_ready` (ready for delivery), `messages_unacknowledged` (pending ack), `consumers` (active consumer count), `memory` (bytes used). **OPCIONALMENTE** pode exibir estatísticas avançadas: `message_stats.publish`, `message_stats.deliver_get`, `message_stats.ack`, `node` (specific node), `exclusive_consumer_tag`, `policy`, `slave_nodes`, `synchronised_slave_nodes`
  - **Critério de Exibição de Estatísticas Opcionais**: Estatísticas avançadas são exibidas **somente se** o campo correspondente estiver presente na resposta JSON da RabbitMQ Management API. Sistema DEVE validar existência do campo antes de acessar usando o seguinte pattern:
    ```python
    # Check if field exists and is not None before accessing
    if 'message_stats' in response and response['message_stats'] is not None:
        if 'publish' in response['message_stats']:
            display_publish_stats(response['message_stats']['publish'])
    ```
    Isto previne erros de campo ausente quando RabbitMQ não retorna certos campos (ex: filas sem mensagens podem não ter `message_stats`)
  - **Comportamento Default**: CLI exibe apenas estatísticas obrigatórias por padrão. Usar flag `--verbose` para tentar exibir estatísticas opcionais quando disponíveis
- **FR-003**: Sistema DEVE permitir criar novas filas especificando nome e opções básicas (durável, exclusiva, auto-delete)
- **FR-004**: Sistema DEVE validar que o nome da fila é válido antes de criá-la (apenas alfanuméricos, hífen, underscore, ponto; máximo 255 caracteres)
- **FR-005**: Sistema DEVE prevenir criação de fila com nome duplicado no mesmo virtual host
- **FR-006**: Sistema DEVE permitir deletar filas existentes validando ausência de mensagens pendentes e consumidores ativos
- **FR-007**: Sistema DEVE verificar que a fila está vazia (messages=0) e sem consumidores ativos (consumers=0) antes de permitir deleção
- **FR-008**: Sistema DEVE fornecer opção de forçar deleção de fila mesmo com mensagens através de flag CLI --force
  - **Conversão**: Flag CLI `--force` é convertido internamente para query parameter `if-empty=false` no DELETE request à API (ex: DELETE `/api/queues/{vhost}/{queue}?if-empty=false`)
  - **Validação**: Executor HTTP (T006) valida presença da flag e adiciona query parameter antes de executar request

#### Exchange Operations
- **FR-009**: Sistema DEVE permitir listar todos os exchanges com informações de tipo (direct, topic, fanout, headers)
- **FR-010**: Sistema DEVE exibir estatísticas básicas de cada exchange incluindo **OBRIGATORIAMENTE**: `type` (exchange type), `durable` (durability flag), `auto_delete` (auto-delete flag). **OPCIONALMENTE** pode exibir estatísticas avançadas: `message_stats.publish_in` (incoming message rate), `message_stats.publish_out` (outgoing message rate), `message_stats.confirm`, `message_stats.return_unroutable`, `policy`, `internal`
  - **Critério de Exibição de Estatísticas Opcionais**: Estatísticas avançadas são exibidas **somente se** o campo correspondente estiver presente na resposta JSON da RabbitMQ Management API. Sistema DEVE validar existência do campo antes de acessar usando o seguinte pattern:
    ```python
    # Check if field exists and is not None before accessing
    if 'message_stats' in response and response['message_stats'] is not None:
        if 'publish_in' in response['message_stats']:
            display_publish_in_stats(response['message_stats']['publish_in'])
    ```
    Isto previne erros de campo ausente quando RabbitMQ não retorna certos campos (ex: exchanges sem mensagens podem não ter `message_stats`)
  - **Bindings Count**: `bindings_count` não é fornecido diretamente pela API e requer agregação client-side através de GET `/api/bindings/{vhost}` filtrado por source exchange (implementado em T014)
  - **Comportamento Default**: CLI exibe apenas estatísticas obrigatórias por padrão. Usar flag `--verbose` para tentar exibir estatísticas opcionais quando disponíveis
- **FR-011**: Sistema DEVE permitir criar novos exchanges especificando nome e tipo
- **FR-012**: Sistema DEVE suportar os tipos de exchange padrão: direct, topic, fanout, headers
- **FR-013**: Sistema DEVE validar que o nome do exchange é válido antes de criá-lo (apenas alfanuméricos, hífen, underscore, ponto; máximo 255 caracteres) e que o tipo especificado é válido
- **FR-014**: Sistema DEVE prevenir criação de exchange com nome duplicado
- **FR-015**: Sistema DEVE permitir deletar exchanges existentes
- **FR-016**: Sistema DEVE bloquear deleção de exchange que possui bindings ativos, retornando erro claro indicando que operador deve remover bindings primeiro
- **FR-017**: Sistema DEVE prevenir deleção de exchanges do sistema: exchanges com prefixo "amq.*" e default exchange "" (string vazia)

#### Binding Operations
- **FR-018**: Sistema DEVE permitir listar todos os bindings mostrando exchange de origem, fila de destino e routing key
- **FR-019**: Sistema DEVE permitir criar bindings entre exchanges e filas especificando routing key
- **FR-020**: Sistema DEVE validar que tanto exchange quanto fila existem antes de criar binding
  - **Ordem de Validação**: Validar exchange primeiro (GET `/api/exchanges/{vhost}/{exchange}`), depois queue (GET `/api/queues/{vhost}/{queue}`). **Justificativa**: Exchange ausente é erro mais comum em configurações RabbitMQ (operadores frequentemente esquecem de criar exchange antes de criar bindings), portanto validar primeiro reduz latência de descoberta de erro
  - **Erro Agregado**: Se ambos não existirem, retornar ValidationError listando ambos recursos ausentes para melhor UX
  - **Performance**: Executar validações em paralelo quando possível, mas sempre reportar exchange primeiro em caso de erro
- **FR-021**: Sistema DEVE suportar routing keys com padrões de wildcard (* e #) para exchanges tipo topic
- **FR-022**: Sistema DEVE permitir deletar bindings específicos entre exchange e fila
- **FR-023**: Sistema DEVE prevenir criação de bindings duplicados (mesmo exchange, mesma fila, mesma routing key)

#### Safety and Validation
- **FR-024**: Sistema DEVE validar existência de virtual host antes de executar qualquer operação
  - **Implementação**: GET `/api/vhosts/{vhost}` antes de cada operação de topology
  - **Cache**: Resultados podem ser cached por até 60 segundos para reduzir overhead
  - **Erro**: Se vhost não existe, retornar ValidationError com code="VHOST_NOT_FOUND", expected="valid vhost", actual="{vhost}", action="Create vhost first or specify existing vhost"
- **FR-024a**: Sistema DEVE implementar retry com exponential backoff para HTTP 429 (Too Many Requests) responses
  - **Retry Strategy**: Máximo de 3 tentativas adicionais (4 total com tentativa inicial) com delays exponenciais: 1s, 2s, 4s
  - **HTTP Status Codes**: Aplicar retry apenas para 429 (rate limiting) e opcionalmente 503 (service unavailable temporário)
  - **Logging**: Log cada retry attempt com nível WARNING incluindo attempt number, delay, e original error
  - **Timeout**: Cada retry respeita o timeout HTTP configurado (30s default per FR-036)
  - **Final Failure**: Após esgotar retries, retornar erro com code="RATE_LIMITED" ou "SERVICE_UNAVAILABLE" incluindo total attempts e suggestion "Wait before retrying or reduce operation frequency"
  - **No Retry On**: Não aplicar retry para outros status codes (4xx client errors, 5xx server errors exceto 503)
- **FR-025**: Sistema DEVE fornecer mensagens de erro claras e específicas para cada tipo de falha de validação seguindo o padrão:
  - **Error Code**: Código categórico (e.g., "INVALID_NAME", "QUEUE_NOT_EMPTY", "UNAUTHORIZED")
  - **Field Context**: Campo/parâmetro afetado (e.g., "queue_name", "vhost", "routing_key")
  - **Expected vs Actual**: Valor esperado vs valor fornecido quando aplicável (e.g., "expected: alphanumeric, got: 'queue@#$'")
  - **Suggested Action**: Ação corretiva clara (e.g., "Remove special characters or use --force flag to delete queue with messages")
  - **Error Message Quality Checklist** (SC-007): 95% dos errors devem incluir todos os 4 elementos acima
- **FR-026**: Sistema DEVE registrar todas as operações de criação e deleção em log estruturado para auditoria (veja também FR-027 para logging de erros de autorização)
  - **Campos Obrigatórios**: timestamp, correlation_id, operation (ex: "queue.create"), vhost, resource_name, user, result (success/failure)
  - **Nível de Log**: INFO para sucesso, ERROR para falhas
  - **Retention**: Logs de auditoria devem ser retidos por 1 ano conforme constitution.md linha 49
- **FR-027**: Sistema DEVE delegar validação de permissões ao RabbitMQ usando as credenciais da conexão estabelecida, propagando erros de autorização com mensagens claras quando operações forem negadas (integrado com FR-026 para auditoria completa de operações autorizadas e não autorizadas)
  - **Formato de erro**: ValidationError com code "UNAUTHORIZED" ou "FORBIDDEN", incluindo operação tentada e permissão requerida
  - **Audit Logging**: Tentativas de operações sem permissão DEVEM ser logadas com nível WARNING incluindo user, operation, e resource (veja FR-026 para formato completo de log de auditoria)

#### CLI Interface Requirements
- **FR-028**: Sistema DEVE fornecer interface de linha de comando com sintaxe clara no formato: `<comando> <subcomando> <opções>`
- **FR-028a**: Sistema DEVE executar uma operação por invocação CLI (stateless execution model)
  - **Single Operation**: Cada comando CLI executa exatamente uma operação (list, create, delete) sobre um recurso
  - **No Batch Operations**: Sistema NÃO suporta múltiplas operações em um único comando (ex: criar 5 filas de uma vez)
  - **Composability**: Operadores podem usar shell loops ou scripts para operações repetitivas (ex: `for queue in q1 q2 q3; do rabbitmq queue create $queue; done`)
  - **Rationale**: Simplifica error handling, mantém CLI stateless, alinha com Unix philosophy, facilita debugging
- **FR-029**: Sistema DEVE aceitar credenciais RabbitMQ via argumentos (--host, --port, --user, --password) ou variáveis de ambiente
- **FR-029a**: Sistema DEVE suportar conexões TLS/SSL ao RabbitMQ Management API com verificação de certificado habilitada por padrão
  - **URL Scheme Detection**: Auto-detectar protocolo baseado em URL scheme (https:// = TLS, http:// = plain HTTP)
  - **Certificate Verification**: Verificar certificados SSL por padrão usando CA bundle do sistema operacional
  - **Insecure Mode**: Fornecer flag CLI `--insecure` para desabilitar verificação de certificado (útil para ambientes dev/test com certificados auto-assinados)
  - **Warning**: Quando `--insecure` é usado, emitir WARNING log indicando que verificação de certificado está desabilitada
  - **Implementation**: Passar `verify=True` (default) ou `verify=False` (quando --insecure) para requests.Session
- **FR-030**: Sistema DEVE exibir mensagens de saída formatadas apropriadamente para consumo humano (tabelas, listas) e opcionalmente em formato estruturado (JSON) via flag --format
- **FR-030a**: Sistema DEVE ordenar colunas de tabelas de output seguindo o padrão: Identity → Configuration → Metrics
  - **Queue List Columns (in order)**: name (identity), durable/exclusive/auto_delete (configuration), messages/messages_ready/messages_unacknowledged/consumers/memory (metrics)
  - **Exchange List Columns (in order)**: name (identity), type/durable/auto_delete (configuration), bindings_count (metrics, computed client-side), opcionalmente message_stats.* com --verbose (metrics)
  - **Binding List Columns (in order)**: source_exchange/destination_queue (identity), routing_key (configuration), vhost (context)
  - **Rationale**: Natural reading flow - operators primeiro identificam o recurso (nome), depois entendem sua configuração, depois avaliam performance/estado
  - **Narrow Terminal Handling**: Quando terminal width < 80 chars, truncar colunas de métricas menos críticas primeiro (preservar name + primary metric sempre visíveis)
- **FR-031**: Sistema DEVE retornar exit codes apropriados: 0 para sucesso, não-zero para erros
- **FR-032**: Sistema DEVE fornecer help text acessível via --help para todos os comandos e subcomandos

#### Pagination Requirements
- **FR-033**: Sistema DEVE implementar paginação obrigatória em todas as operações de listagem (queues.list, exchanges.list, bindings.list)
  - **Implementação**: Client-side pagination (RabbitMQ Management API endpoints `/api/queues`, `/api/exchanges`, `/api/bindings` **NÃO suportam paginação nativa** conforme verificação da documentação oficial em https://www.rabbitmq.com/docs/http-api-reference - API fornece apenas parâmetros `sort`, `columns`, `disable_stats`, mas não `page` ou `page_size`)
  - Sistema busca resultados completos do RabbitMQ Management API via HTTP e aplica slice em memória baseado em page/pageSize
  - **Constitution Compliance**: Esta implementação respeita constitution.md linha 107 "Conditional Pagination" e linha 110 "respect API limitations when pagination is not supported"
  - **Validated**: Confirmado através de consulta à documentação oficial RabbitMQ 4.1 em 2025-10-09
- **FR-034**: Sistema DEVE aceitar parâmetros de paginação: page (número da página, 1-based, default 1) e pageSize (itens por página, default 50, máximo 200)
- **FR-035**: Sistema DEVE retornar metadados de paginação em respostas: page, pageSize, totalItems, totalPages, hasNextPage, hasPreviousPage (todos obrigatórios)
- **FR-036**: Sistema DEVE completar operações de listagem paginadas em menos de 2 segundos por página (classification: **complex operations** per constitution.md linha 571 "Maximum latency of 200ms for basic operations" - listagens com client-side pagination são consideradas complex due to memory processing overhead)
  - **Timeout Configurável**: Timeout HTTP de 30 segundos (padrão mais comum para operações de listagem RabbitMQ com grandes volumes) configurável via Settings.list_timeout (range: 5s-60s). Se operação exceder timeout, retornar erro "OPERATION_TIMEOUT" com suggestion "Reduce page size or filter by specific vhost"
  - **Performance Monitoring**: Operações próximas do limite (>1.5s) DEVEM gerar WARNING log para investigação
  - **Memory Constraint (cross-ref plan.md)**: Client-side pagination DEVE respeitar limite de 1GB de memória por instância (plan.md linha 39). Sistema DEVE processar resultados em streaming quando possível e liberar memória após slice de paginação. Para volumes > 1000 items, considerar page size menor (ex: 25-50 items) para manter footprint baixo. Validação de memory usage incluída em T041 unit tests

### Key Entities

- **Queue**: Representa uma fila de mensagens com atributos de nome, virtual host, propriedades de durabilidade, estatísticas de mensagens e consumidores
- **Exchange**: Representa um roteador de mensagens com tipo (direct/topic/fanout/headers), nome, virtual host, e estatísticas de throughput
- **Binding**: Representa uma regra de roteamento conectando exchange a fila, incluindo routing key e padrões de matching
- **Virtual Host**: Agrupamento lógico isolando conjuntos de filas, exchanges e bindings

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Operadores conseguem visualizar o estado completo da infraestrutura de mensagens (todas filas, exchanges e bindings) em menos de 2 segundos por página paginada
- **SC-002**: Operações de criação de fila, exchange ou binding completam em menos de 1 segundo
- **SC-003**: Operações de deleção de fila, exchange ou binding completam em menos de 1 segundo  
- **SC-004**: Sistema previne 100% das tentativas de deleção de filas com mensagens sem confirmação explícita
- **SC-005**: Sistema bloqueia 100% das tentativas de deleção de exchanges com bindings ativos, exigindo remoção explícita dos bindings primeiro
- **SC-006**: Sistema lida eficientemente com até 1000 filas e 1000 exchanges sem degradação de performance através de paginação
- **SC-007**: 95% das operações que falham fornecem mensagem de erro clara (incluindo código de erro, campo afetado, valor esperado vs atual) permitindo ao operador corrigir o problema sem consultar documentação
  - **Métrica**: Em testes de erro (unit + integration), 95% dos test cases devem validar que mensagem contém: código de erro, contexto específico, e ação sugerida
- **SC-008**: Todas as operações de criação e deleção são registradas em log permitindo auditoria completa
- **SC-009**: Sistema valida 100% dos parâmetros de entrada antes de executar operações, prevenindo estados inconsistentes
- **SC-010**: Operações de listagem retornam metadados de paginação corretos (page, pageSize, totalItems, totalPages, hasNextPage, hasPreviousPage) em 100% das respostas

## Assumptions

- **Sistema é um MCP Server with built-in CLI** implementado em Python seguindo constitution.md linha 71 "Every MCP server MUST include a built-in console client"
  - **Arquitetura**: 3 ferramentas MCP públicas (search-ids, get-id, call-id) expõem operações de topology via semantic discovery pattern
  - **Built-in CLI**: Interface de linha de comando fornece acesso direto às operações mais comuns sem necessidade de cliente MCP externo
  - **Dual Access**: Operadores podem usar built-in CLI para uso interativo OU integrar com clientes MCP (Cursor, VS Code) para workflows programáticos
- **Implementação em Python** permite uso de bibliotecas maduras do ecossistema RabbitMQ e facilita manutenção
- **Framework click** será usado para interface CLI, oferecendo validação robusta de argumentos, help automático e estrutura organizada de comandos
- **Biblioteca requests** será usada para comunicação HTTP com a Management API (escolhida sobre httpx por ser a biblioteca HTTP mais amplamente usada em ambientes empresariais, com suporte estável e debugging tools maduros; async não é necessário para CLI tool). Suporte TLS/SSL nativo com verificação de certificado configurável
  - **Connection Management**: requests.Session será instanciado uma vez por invocação CLI e reutilizado para todas as chamadas API dentro dessa invocação (ex: validate vhost + list queues usa mesma session)
  - **Lifecycle**: Session é criado no início da invocação CLI, usado para todas as operações HTTP, e automaticamente limpo quando processo CLI termina
  - **Benefits**: Reduz overhead de TCP handshake e TLS negotiation entre chamadas sequenciais; suporte nativo a connection pooling interno do requests
  - **No Cross-Invocation Pooling**: Cada invocação CLI cria nova session (alinhado com stateless execution model FR-028a)
- **Biblioteca structlog** será usada para structured logging, permitindo auditoria efetiva com contexto rico em formato JSON
- **Biblioteca tabulate** será usada para formatação de tabelas em output humanizado, garantindo clareza e legibilidade das listagens
- RabbitMQ Management API está habilitado e acessível
- Operadores têm credenciais apropriadas para acessar a Management API
- **Network Latency Assumption**: Sistema roda em ambiente onde latência de rede RTT (Round Trip Time, ida e volta completa) entre CLI e RabbitMQ Management API é menor que 100ms RTT. **Todas referências a latência neste documento usam RTT (Round Trip Time) como métrica padrão**, que representa o tempo total de uma operação HTTP request/response completa (client → server → client). Esta é a latência típica em datacenter ou cloud co-location. Nota: 100ms RTT equivale a aproximadamente 50ms one-way em cada direção.
- Virtual host padrão é "/" quando não especificado
- Log de auditoria é persistido com nível INFO para operações bem-sucedidas e WARNING/ERROR para falhas
- Credenciais de conexão RabbitMQ são fornecidas via argumentos de linha de comando (--user, --password) ou variáveis de ambiente (RABBITMQ_USER, RABBITMQ_PASSWORD)
