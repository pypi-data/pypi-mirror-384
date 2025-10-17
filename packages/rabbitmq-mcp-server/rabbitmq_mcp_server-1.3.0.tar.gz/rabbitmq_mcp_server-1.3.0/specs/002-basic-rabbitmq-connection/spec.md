# Feature Specification: Basic RabbitMQ Connection

**Feature Branch**: `002-basic-rabbitmq-connection`  
**Created**: 2025-10-09  
**Status**: Draft  
**Input**: User description: "Basic RabbitMQ Connection"

## Clarifications

### Session 2025-10-09

- Q: Como o sistema deve se comportar nas tentativas de reconexão quando a conexão é perdida? → A: Retry infinito com backoff exponencial - continua tentando indefinidamente, aumentando o intervalo entre tentativas até um máximo
- Q: Quando todas as conexões do pool estão em uso e uma nova operação é solicitada, o que deve acontecer? → A: Bloquear e aguardar - a operação aguarda até que uma conexão seja liberada (com timeout configurável)
- Q: Qual mecanismo o sistema deve usar para detectar que a conexão foi perdida? → A: Híbrido (Heartbeat + Eventos) - combina heartbeat AMQP com monitoramento de eventos de desconexão
- Q: Quais eventos de conexão devem ser obrigatoriamente logados? → A: Eventos críticos - loga conexões estabelecidas, falhas, desconexões e início de reconexão
- Q: Qual tecnologia/protocolo deve ser usado para expor as operações de conexão via descoberta semântica? → A: MCP (Model Context Protocol) com search-ids para permitir consultas semânticas sobre operações disponíveis
- Q: Qual linguagem/plataforma será usada para implementar esta feature? → A: Python (3.9+) com pika ou aio-pika
- Q: A implementação deve usar abordagem síncrona ou assíncrona? → A: Assíncrona (aio-pika) - operações non-blocking com async/await, maior throughput
- Q: Como os parâmetros de conexão (host, porta, credenciais, etc.) devem ser fornecidos ao sistema? → A: Múltiplas fontes - suporta ENV vars + arquivo + argumentos com ordem de precedência
- Q: Qual formato de log estruturado deve ser usado para registrar eventos de conexão? → A: JSON - cada log é um objeto JSON com campos estruturados
- Q: Qual biblioteca de logging Python deve ser usada para emitir logs JSON estruturados? → A: structlog - biblioteca especializada em logging estruturado (padrão para aplicações Python assíncronas modernas)
- Q: Qual formato deve ser usado para o arquivo de configuração? → A: TOML - formato moderno, legível, suporta tipos nativos
- Q: Quais valores devem ser usados para o backoff exponencial na política de retry? → A: Inicial: 1s, Fator: 2x, Máximo: 60s (sequência completa: 1s → 2s → 4s → 8s → 16s → 32s → 60s → 60s → 60s...)
- Q: Qual valor de timeout padrão deve ser usado quando operações aguardam por conexão disponível no pool? → A: 10 segundos (específico para pool) - timeout moderado padrão para operações assíncronas. Diferente do timeout de conexão (30s)
- Q: Qual intervalo de heartbeat AMQP deve ser usado para detectar conexões perdidas? → A: 60 segundos - padrão default do RabbitMQ, balanceado
- Q: Qual convenção de nomenclatura deve ser usada para variáveis de ambiente? → A: AMQP_* para conexão AMQP (AMQP_HOST, AMQP_PORT, AMQP_USER, AMQP_PASSWORD, AMQP_VHOST) e RABBITMQ_* para API de management quando necessário

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Estabelecer Conexão com RabbitMQ (Priority: P1)

Um operador precisa conectar a aplicação ao servidor RabbitMQ usando credenciais válidas para iniciar operações de mensageria.

**Why this priority**: Esta é a funcionalidade base essencial - sem ela, nenhuma outra operação de mensageria é possível. É o primeiro passo crítico para qualquer uso do sistema.

**Independent Test**: Pode ser testado completamente executando uma operação de conexão com credenciais válidas e verificando que a conexão é estabelecida com sucesso em menos de 5 segundos.

**Acceptance Scenarios**:

1. **Given** o servidor RabbitMQ está disponível e as credenciais são válidas, **When** o operador solicita conexão, **Then** a conexão é estabelecida com sucesso em menos de 5 segundos
2. **Given** o servidor RabbitMQ está disponível mas as credenciais são inválidas, **When** o operador solicita conexão, **Then** o sistema retorna erro claro de autenticação e não estabelece conexão
3. **Given** o servidor RabbitMQ não está acessível, **When** o operador solicita conexão com timeout de 30 segundos, **Then** o sistema retorna erro de timeout após 30 segundos máximo

---

### User Story 2 - Monitorar Saúde da Conexão (Priority: P2)

Um operador precisa verificar se o servidor RabbitMQ está saudável e se a conexão atual está funcionando corretamente.

**Why this priority**: Essencial para operações confiáveis, mas depende de ter uma conexão estabelecida primeiro. Permite diagnóstico rápido de problemas.

**Independent Test**: Pode ser testado executando verificação de saúde após estabelecer conexão e validando que o resultado retorna em menos de 1 segundo com status preciso.

**Acceptance Scenarios**:

1. **Given** uma conexão ativa existe, **When** o operador solicita verificação de saúde, **Then** o sistema retorna status da conexão em menos de 1 segundo
2. **Given** o servidor RabbitMQ está operacional, **When** o operador executa health check, **Then** o sistema confirma disponibilidade do RabbitMQ
3. **Given** a conexão foi perdida, **When** o operador verifica status da conexão, **Then** o sistema detecta e reporta a falha de conexão

---

### User Story 3 - Recuperação Automática de Conexão (Priority: P3)

Quando a conexão com RabbitMQ é perdida inesperadamente, o sistema deve reconectar automaticamente sem intervenção manual.

**Why this priority**: Melhora significativamente a resiliência operacional, mas não é crítico para o funcionamento inicial. Usuários podem reconectar manualmente se necessário.

**Independent Test**: Pode ser testado simulando perda de conexão (desconectar servidor) e verificando que o sistema reconecta automaticamente em menos de 10 segundos quando o servidor volta.

**Acceptance Scenarios**:

1. **Given** uma conexão ativa é perdida, **When** o servidor RabbitMQ volta a ficar disponível, **Then** o sistema reconecta automaticamente em menos de 10 segundos usando política de retry infinito com backoff exponencial (sequência: 1s → 2s → 4s → 8s → 16s → 32s → 60s máximo)
2. **Given** múltiplas tentativas de reconexão falharam consecutivamente, **When** o sistema continua tentando indefinidamente após atingir máximo, **Then** logs de eventos críticos são gerados (conexão perdida, início de reconexão, falhas) e o intervalo permanece fixo em 60s (ex: 60s → 60s → 60s → continua indefinidamente)
3. **Given** a conexão foi recuperada após múltiplas tentativas, **When** operações são solicitadas, **Then** o sistema funciona normalmente com a nova conexão
4. **Given** sistema está em modo de reconexão, **When** operador solicita shutdown ou disconnect manual, **Then** o sistema cancela retry loop e desconecta graciosamente em menos de 2 segundos

---

### User Story 4 - Gerenciar Múltiplas Conexões (Priority: P4)

O sistema deve suportar pool de conexões para permitir múltiplas operações simultâneas de forma eficiente.

**Why this priority**: Otimização de performance que não é crítica para MVP inicial. Pode ser implementada depois para melhorar throughput.

**Independent Test**: Pode ser testado solicitando múltiplas operações simultâneas e verificando que são atendidas usando conexões do pool sem criar nova conexão para cada operação.

**Acceptance Scenarios**:

1. **Given** o pool de conexões está configurado, **When** múltiplas operações são solicitadas simultaneamente, **Then** o sistema utiliza conexões disponíveis do pool
2. **Given** todas as conexões do pool estão em uso, **When** nova operação é solicitada, **Then** o sistema bloqueia e aguarda até que uma conexão seja liberada (timeout padrão: 10 segundos) antes de processar a operação
3. **Given** uma operação é concluída, **When** a conexão é liberada, **Then** a conexão volta ao pool para reutilização e operações aguardando são desbloqueadas

---

### Edge Cases

- **EC-001**: O que acontece quando o servidor RabbitMQ fica indisponível durante operação ativa? → Sistema detecta via heartbeat/eventos, entra em modo reconexão automática (FR-010, FR-011)
- **EC-002**: Como o sistema lida com mudança de senha enquanto conexão está ativa? → Conexão atual permanece válida; próxima tentativa de reconexão falhará com erro de autenticação claro (FR-006)
- **EC-003**: O que acontece quando o virtual host especificado não existe? → Conexão falha com erro específico "VHost não encontrado: /path" (FR-016, FR-020)
- **EC-004**: Como o sistema se comporta quando o limite de conexões do RabbitMQ é atingido? → Falha com erro claro "Connection limit reached", entra em retry automático (FR-006, FR-011)
- **EC-005**: O que acontece se a conexão for fechada pelo servidor RabbitMQ? → Sistema detecta via evento de callback, inicia reconexão automática (FR-010, FR-011)
- **EC-006**: Como o sistema lida com timeout durante health check? → Retorna status unhealthy após timeout de 1s, não bloqueia outras operações (FR-008)
- **EC-007**: O que acontece quando múltiplas tentativas de reconexão consecutivas falham? → Sistema continua retry com backoff exponencial até 60s máximo, logs críticos emitidos: "connection.lost" (detecção inicial), "connection.reconnecting" (início do retry loop), "connection.retry_attempt" (cada tentativa individual com attempt number e next_delay), "connection.retry_failed" (falha de tentativa específica), "connection.reconnected" (sucesso após retries) - todos com structured logging JSON (FR-011, FR-014)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Sistema MUST permitir conexão ao RabbitMQ via protocolo AMQP 0-9-1 usando host, porta, usuário, senha e virtual host específico (suporta múltiplos vhosts conforme necessidade do operador)
- **FR-002**: Sistema MUST carregar parâmetros de conexão de múltiplas fontes (variáveis de ambiente: AMQP_HOST, AMQP_PORT, AMQP_USER, AMQP_PASSWORD, AMQP_VHOST; arquivo TOML; argumentos programáticos) com ordem de precedência: argumentos > ENV vars > arquivo > padrões
- **FR-003**: Sistema MUST validar parâmetros de conexão antes de tentar estabelecer conexão: host não vazio (string com min 1 caractere), porta entre 1-65535 (integer), timeout entre 1-300 segundos (integer), heartbeat entre 0-3600 segundos (integer), usuário e senha não vazios (strings), vhost formato válido (inicia com /)
- **FR-004**: Sistema MUST estabelecer conexão em menos de 5 segundos quando servidor está disponível
- **FR-005**: Sistema MUST aplicar timeout de 30 segundos para tentativas de conexão (após timeout, lança ConnectionTimeoutError e entra em modo de reconexão automática via FR-011)
- **FR-006**: Sistema MUST retornar mensagens de erro claras e específicas para falhas de autenticação
- **FR-007**: Sistema MUST permitir desconexão limpa fechando todos os recursos AMQP apropriadamente
- **FR-008**: Sistema MUST executar verificação de saúde do RabbitMQ retornando resultado em menos de 1 segundo
- **FR-009**: Sistema MUST monitorar estado da conexão em tempo real (conectado, desconectado, reconectando)
- **FR-010**: Sistema MUST detectar perda de conexão automaticamente usando mecanismo híbrido: heartbeat AMQP com intervalo de 60 segundos (protocolo nativo) combinado com eventos de desconexão da biblioteca cliente
- **FR-011**: Sistema MUST tentar reconexão automática quando conexão é perdida (detecção via FR-010) usando política de retry infinito com backoff exponencial: 1s → 2s → 4s → 8s → 16s → 32s → 60s (máximo) → continua indefinidamente em 60s
- **FR-012**: Sistema MUST completar reconexão em menos de 10 segundos quando servidor volta
- **FR-013**: Sistema MUST manter pool de conexões para operações simultâneas (tamanho padrão: 5 conexões, configurável). Quando todas as conexões estão em uso, novas operações MUST bloquear e aguardar até que uma conexão seja liberada (timeout padrão: 10 segundos, configurável)
- **FR-014**: Sistema MUST registrar eventos críticos de conexão em logs estruturados formato JSON com campos: timestamp, level, event_type, message, context (host, port, vhost). Schema completo definido em data-model.md → LogEvent
- **FR-015**: Sistema MUST sanitizar credenciais em logs automaticamente (não exibir senhas em nenhum campo do JSON)
- **FR-017**: Sistema MUST expor operações de conexão através de MCP (Model Context Protocol) usando ChromaDB local mode para semantic search de operações disponíveis
- **FR-018**: Sistema MUST lidar com erros de rede graciosamente sem crash da aplicação
- **FR-019**: Sistema MUST usar valores padrão configuráveis (localhost:5672, vhost="/") quando não especificados
- **FR-020**: Sistema MUST validar existência de virtual host durante tentativa de conexão AMQP (não requer Management API) e retornar erro específico "VHost não encontrado: {vhost}" se não existir (detectado via erro AMQP 530 NOT_ALLOWED)

### Key Entities

- **Connection**: Representa uma conexão AMQP 0-9-1 ativa ao RabbitMQ, gerenciada conforme FR-001, FR-004, FR-005
- **Connection Pool**: Coleção de conexões disponíveis para reutilização em operações simultâneas conforme FR-013 (tamanho padrão: 5, timeout: 10s)
- **Health Status**: Estado de saúde do servidor RabbitMQ e das conexões ativas, verificado conforme FR-008 (resposta <1s)
- **Connection Parameters**: Conjunto de configurações necessárias, carregado conforme FR-002 (precedência: argumentos > ENV > arquivo > padrões) e validado conforme FR-003
- **Retry Policy**: Política de reconexão automática conforme FR-011 (backoff exponencial: inicial 1s, fator 2x, máximo 60s)
- **Connection Monitor**: Componente de detecção de perda de conexão conforme FR-010 (heartbeat AMQP 60s + eventos de callback)
- **MCP Interface**: Interface de descoberta semântica conforme FR-017 (search-ids tool para operações disponíveis)

## Success Criteria *(mandatory)*

### Measurable Outcomes

**Nota de Medição**: Todos os critérios de sucesso são verificados via testes de integração (pytest) com RabbitMQ real. Métricas de latência são coletadas usando `time.time()` antes/depois de operações. Percentis calculados sobre múltiplas execuções (n≥100 para baseline confiável).

- **SC-001**: Operadores conseguem estabelecer conexão com RabbitMQ com credenciais válidas: p95 < 5 segundos, p99 < 7 segundos conforme FR-004 (medido via integration tests com 100+ execuções)
- **SC-002**: Verificações de saúde retornam resultado em menos de 1 segundo conforme FR-008 (p95 < 1s, p99 < 1.5s medido via integration tests)
- **SC-003**: Reconexão automática é completada em menos de 10 segundos após servidor voltar conforme FR-012 (p95 < 10s, p99 < 15s medido via integration tests simulando falha de servidor)
- **SC-004**: 100% das falhas de conexão geram mensagens de erro claras e acionáveis
- **SC-005**: Sistema detecta perda de conexão em tempo real dentro de 1 ciclo de heartbeat (máximo 60 segundos, típico <5s via eventos de callback)
- **SC-006**: Zero exposição de credenciais em logs ou mensagens de erro
- **SC-007**: Sistema suporta pelo menos 10 operações simultâneas usando pool de conexões sem degradação de performance
- **SC-008**: Taxa de sucesso de conexão é 100% quando servidor está disponível e credenciais são válidas
- **SC-009**: Desconexões limpas liberam todos os recursos sem vazamentos de memória ou file descriptors
- **SC-010**: Operadores podem diagnosticar problemas de conexão através dos logs estruturados em menos de 2 minutos (tempo médio: <60 segundos, medido via estudo de usabilidade com 5+ operadores simulando cenários de falha comuns: timeout, credenciais inválidas, vhost inexistente)

## Assumptions

- RabbitMQ server versão 3.8 ou superior está disponível
- Protocolo AMQP 0-9-1 será usado para conexões
- Implementação assíncrona em Python 3.9+ usando biblioteca aio-pika (async/await pattern)
- Formato do arquivo de configuração é TOML (formato moderno com suporte a tipos nativos)
- Rede entre aplicação e RabbitMQ possui características típicas de ambiente empresarial (LAN ou datacenter): latência de rede < 10ms (p95), uptime > 99.9%, packet loss < 0.1%. Sistema tolera indisponibilidades temporárias reconectando automaticamente via backoff exponencial
- Logs são emitidos em formato JSON estruturado usando structlog e direcionados para saída configurável (console, arquivo, etc)
- Virtual host "/" (default) existe no servidor RabbitMQ
- Pool de conexões inicia com tamanho configurável (default: 5 conexões)
- Timeout para aguardar conexão disponível no pool é configurável (default: 10 segundos)
- Política de retry usa backoff exponencial com valores: intervalo inicial 1s, fator multiplicador 2x, intervalo máximo 60s
- Heartbeat AMQP é configurado com intervalo de 60 segundos (padrão default do RabbitMQ)
- Biblioteca aio-pika suporta eventos de callback para detecção de desconexão
- Interface MCP é acessível para agentes de IA realizarem descoberta semântica
- Operações assíncronas permitem maior throughput com non-blocking I/O

## Out of Scope

- Operações de criação/gerenciamento de filas, exchanges ou bindings
- Publicação ou consumo de mensagens
- Configurações avançadas de SSL/TLS
- Autenticação via certificados
- Interface gráfica para gerenciamento de conexões
- Métricas detalhadas de performance
- Integração com sistemas de monitoramento externos
- Retry policies customizáveis via API (esta feature implementa policy fixa otimizada: 1s → 2s → 4s → 8s → 16s → 32s → 60s. Customização via arquivo de configuração pode ser considerada em features futuras se houver demanda comprovada)
- Clustering ou high availability

## Future Features (Post-MVP)

### Expansion to Full RabbitMQ Management API (Feature 009)

**Implementação Atual (Esta Feature - 002)**:
- Vector database mínimo usando ChromaDB local mode conforme constituição
- 5 operações de conexão AMQP indexadas com embeddings pré-computados
- Semantic search via sentence-transformers (lightweight model)
- Performance sub-100ms conforme requisito constitucional
- Database file (~2-5MB) commitado no repositório em `data/vectors/connection-ops.db`

**Implementação Futura (Feature 009)**:
- Expansão para centenas de operações do RabbitMQ Management API
- Vector database escalado com todas as operações derivadas de OpenAPI
- Arquitetura two-tier otimizada para datasets grandes
- Suporte a múltiplos vhosts e clusters
- Indexação automática de documentação e troubleshooting scenarios

**Nota**: Esta feature implementa vector database conforme constituição, porém com escopo reduzido (5 operações). Feature 009 expandirá o mesmo sistema para centenas de operações Management API.
