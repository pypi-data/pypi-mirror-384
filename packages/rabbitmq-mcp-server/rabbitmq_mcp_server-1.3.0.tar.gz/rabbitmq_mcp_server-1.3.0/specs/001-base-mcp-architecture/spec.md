# Feature Specification: Base MCP Architecture

**Feature Branch**: `001-base-mcp-architecture`  
**Created**: 2025-10-09  
**Status**: Draft  
**Input**: User description: "Base MCP Architecture - Implementation of the fundamental MCP server architecture with the essential 3-tool semantic discovery pattern"

## Clarifications

### Session 2025-10-09

- Q: Como o servidor MCP irá autenticar com o RabbitMQ? → A: Credenciais fixas em variáveis de ambiente (username/password)
- Q: Qual método será usado para implementar a busca semântica? → A: Embeddings com sentence-transformers, modelo all-MiniLM-L6-v2 (384 dimensões, balanceamento ideal entre performance e qualidade para descoberta de operações). Vector database: ChromaDB local file mode recomendado (best Python option per constitution, embedded, portable), sqlite-vec como alternativa (ambos file-based conforme constitution)
- Q: Qual será o timeout máximo para execução de operações RabbitMQ? → A: 30 segundos (operações moderadas, suporta listagens grandes)
- Q: Em que formato os schemas e registro de operações serão armazenados no repositório? → A: SQLite database com extensão sqlite-vec para busca vetorial (estruturado, queryable, suporta embeddings)
- Q: Qual será o nível e formato de logging do servidor MCP? → A: Logging estruturado JSON com níveis configuráveis (production-ready)
- Q: O que acontece quando a especificação OpenAPI é atualizada enquanto o servidor está rodando? → A: A especificação nunca será atualizada em tempo de execução. Quando ocorrer, um novo build e versão serão gerados.
- Q: O que acontece se o usuário tentar executar uma operação sem fornecer parâmetros obrigatórios? → A: Erro de validação imediato antes de tentar executar, listando parâmetros faltantes
- Q: Como o sistema se comporta quando o RabbitMQ retorna dados em formato inesperado? → A: Sistema retorna erro descritivo ao cliente indicando problema de formato/parsing
- Q: O que acontece se múltiplas requisições simultâneas tentam acessar os mesmos recursos de cache? → A: Sistema usa asyncio.Lock (Python async) para garantir acesso thread-safe ao cache, prevenindo race conditions em requisições concorrentes
- Q: Quando a conexão com RabbitMQ falha, qual é a política de reconexão do servidor MCP? → A: Falha imediata; cliente deve tratar e retentar
- Q: Aproximadamente quantas operações distintas existem na especificação OpenAPI do RabbitMQ HTTP API que o sistema precisará gerenciar? → A: Baseado em análise do RabbitMQ HTTP API: v3.13.x (~280 operações), v3.12.x (~260 operações), v3.11.x (~240 operações). Estimativa conservadora: 150-300 operações por versão (API extensa, requer otimização de embeddings)
- Q: Na busca semântica por operações, qual estratégia será usada para ordenar e filtrar resultados por similaridade? → A: Retornar todos os resultados acima de threshold 0.7 (apenas matches muito relevantes)
- Q: Quais métricas operacionais o sistema deve expor para monitoramento e troubleshooting em produção? → A: Instrumentação completa OpenTelemetry com exporter OTLP (obrigatório), Jaeger e Prometheus opcionais; traces distribuídos, métricas (contadores, histogramas), logs correlacionados via trace IDs
- Q: Como o sistema deve lidar com diferentes versões da especificação OpenAPI do RabbitMQ (ex: mudanças entre versões do RabbitMQ)? → A: Suportar versão configurável via variável de ambiente, uma por vez
- Q: O sistema deve implementar proteção contra abuso (rate limiting, throttling) para requisições dos clientes? → A: Rate limiting básico por cliente (100 req/min configurável), identificado via connection ID do protocolo MCP com fallback para IP quando connection ID não disponível

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Descobrir Operações Disponíveis (Priority: P1)

Como desenvolvedor integrando com RabbitMQ, preciso buscar operações relevantes usando linguagem natural, para que eu possa encontrar rapidamente a funcionalidade que preciso sem conhecer todos os endpoints disponíveis.

**Why this priority**: Esta é a funcionalidade mais crítica do padrão de descoberta semântica. Sem ela, os usuários não conseguem navegar pelas capacidades do servidor MCP.

**Independent Test**: Pode ser testado enviando consultas em linguagem natural (ex: "listar filas") e verificando se operações relevantes são retornadas com descrições claras.

**Acceptance Scenarios**:

1. **Given** o servidor MCP está rodando, **When** o usuário envia uma busca por "listar filas", **Then** o sistema retorna operações relacionadas a listagem de filas com descrições e IDs
2. **Given** o servidor MCP está rodando, **When** o usuário envia uma busca genérica por "exchanges", **Then** o sistema retorna múltiplas operações relacionadas a exchanges ordenadas por relevância
3. **Given** o servidor MCP está rodando, **When** o usuário envia uma busca por operação inexistente, **Then** o sistema retorna lista vazia ou sugestões alternativas

---

### User Story 2 - Obter Detalhes de Operação (Priority: P1)

Como desenvolvedor, preciso consultar a documentação completa e esquema de parâmetros de uma operação específica, para que eu possa entender exatamente como utilizá-la antes de executá-la.

**Why this priority**: Essencial para o usuário entender os requisitos e formato de cada operação antes de executá-la. Sem isso, seria tentativa e erro.

**Independent Test**: Pode ser testado solicitando detalhes de uma operação conhecida e verificando se o esquema de parâmetros, tipos de dados e documentação são retornados.

**Acceptance Scenarios**:

1. **Given** uma operação válida existe, **When** o usuário solicita detalhes da operação por ID, **Then** o sistema retorna esquema completo de parâmetros, tipos de dados e descrição
2. **Given** uma operação válida existe, **When** o usuário solicita detalhes da operação, **Then** o sistema retorna exemplos de uso quando disponíveis
3. **Given** um ID de operação inválido, **When** o usuário solicita detalhes, **Then** o sistema retorna erro descritivo informando que a operação não existe

---

### User Story 3 - Executar Operações RabbitMQ (Priority: P1)

Como desenvolvedor, preciso executar operações RabbitMQ passando parâmetros validados, para que eu possa gerenciar recursos (filas, exchanges, bindings) de forma programática e confiável.

**Why this priority**: Esta é a funcionalidade principal que entrega valor real. As outras stories permitem descobrir e entender, mas esta efetivamente executa ações.

**Independent Test**: Pode ser testado executando operações conhecidas com parâmetros válidos e verificando se as ações são realizadas no RabbitMQ e resultados corretos são retornados.

**Acceptance Scenarios**:

1. **Given** uma operação válida e parâmetros corretos, **When** o usuário executa a operação, **Then** a ação é realizada no RabbitMQ e resultado de sucesso é retornado
2. **Given** uma operação válida mas parâmetros inválidos, **When** o usuário tenta executar, **Then** o sistema retorna erro de validação antes de tentar executar no RabbitMQ
3. **Given** uma operação válida mas o RabbitMQ está indisponível, **When** o usuário tenta executar, **Then** o sistema retorna falha imediata com erro claro indicando problema de conexão, sem retry automático
4. **Given** uma operação executada com sucesso, **When** a resposta é retornada, **Then** ela inclui dados relevantes da ação realizada

---

### User Story 4 - Receber Feedback Claro de Erros (Priority: P2)

Como desenvolvedor, preciso receber mensagens de erro padronizadas e descritivas quando algo falha, para que eu possa identificar e corrigir problemas rapidamente.

**Why this priority**: Fundamental para boa experiência do desenvolvedor, mas não bloqueia funcionalidade básica.

**Independent Test**: Pode ser testado provocando diferentes tipos de erro (validação, conexão, operação inválida) e verificando se mensagens claras são retornadas.

**Acceptance Scenarios**:

1. **Given** parâmetros inválidos, **When** uma operação é executada, **Then** erro de validação descreve quais parâmetros estão incorretos e o formato esperado
2. **Given** um erro interno do servidor, **When** ocorre durante uma operação, **Then** erro genérico seguro é retornado ao usuário sem expor detalhes internos
3. **Given** qualquer erro, **When** retornado ao usuário, **Then** inclui código de erro padrão MCP para facilitar tratamento programático
4. **Given** RabbitMQ retorna dados em formato inesperado, **When** o servidor processa a resposta, **Then** erro descritivo sobre falha de parsing é retornado ao cliente sem expor stack traces ou detalhes internos

---

### Edge Cases

- **Especificação OpenAPI runtime**: Nunca é atualizada em tempo de execução; atualizações requerem novo build e deploy de versão
- **Timeout de operações**: Sistema aborta operações que excedem 30 segundos, retornando erro ao cliente indicando timeout. Para operações de listagem grandes (definição: queries que retornam >1000 items OU response >50MB, ex: filas com milhões de mensagens, clusters com centenas de conexões), usar pagination obrigatória com pageSize máximo de 200 itens por página para manter resposta dentro do timeout constitucional de 30s
- **Validação de parâmetros**: Execução sem parâmetros obrigatórios resulta em erro de validação imediato, listando especificamente quais parâmetros estão faltantes, antes de qualquer tentativa de execução
- **Parsing de respostas**: Quando RabbitMQ retorna dados em formato inesperado, sistema retorna erro descritivo ao cliente indicando falha de parsing/formato
- **Concorrência de cache**: Múltiplas requisições simultâneas acessando recursos de cache são gerenciadas com asyncio.Lock para garantir acesso thread-safe
- **Falhas de conexão**: Resultam em falha imediata sem retry automático; cliente é responsável por implementar estratégia de retry apropriada
- **Rate limiting**: Requisições que excedem limite (padrão: 100 req/min por cliente) são rejeitadas com erro HTTP 429 incluindo header Retry-After
- **Streaming AMQP**: amqp.consume retorna stream de mensagens; cliente pode cancelar subscription via nack/disconnect; mensagens não confirmadas retornam para fila após timeout

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Sistema MUST expor exatamente 3 ferramentas públicas: busca semântica, obtenção de detalhes, e execução de operações
- **FR-002**: Sistema MUST derivar todas as operações e esquemas de uma especificação OpenAPI fornecida
- **FR-003**: Sistema MUST validar parâmetros de entrada antes de executar qualquer operação no RabbitMQ, retornando erro imediato que lista especificamente quais parâmetros obrigatórios estão faltantes ou inválidos
- **FR-004**: Sistema MUST retornar códigos de erro padronizados conforme protocolo MCP
- **FR-005**: Sistema MUST organizar operações em categorias (operation categories) baseadas em tags lógicas da OpenAPI
- **FR-006**: Sistema MUST permitir busca por operações usando descrições em linguagem natural, implementada via embeddings com sentence-transformers modelo all-MiniLM-L6-v2 (384 dimensões), retornando apenas resultados com similaridade ≥0.7 ordenados por score de relevância. Threshold 0.7 significa alta relevância semântica. Exemplos testáveis: query "criar fila" retorna "queues.create" score 0.95 (ACEITO), mas rejeita "users.create" score 0.32 (REJEITADO); query "listar exchanges" retorna "exchanges.list" score 0.98 (ACEITO); query "conectar rabbitmq" retorna "connections.create" score 0.85 (ACEITO). Quando busca retorna 0 resultados (nenhum acima 0.7), retornar lista vazia com sugestão: "Try broader search terms"
- **FR-007**: Sistema MUST retornar esquema completo de parâmetros para cada operação quando solicitado
- **FR-008**: Sistema MUST suportar comunicação via JSON-RPC 2.0
- **FR-009**: Sistema MUST validar compliance com especificação do protocolo MCP
- **FR-010**: Sistema MUST executar validação de parâmetros em menos de 10 milissegundos
- **FR-011**: Sistema MUST armazenar esquemas gerados durante build em banco SQLite no repositório para evitar geração em tempo de execução e permitir queries estruturadas (ver estrutura completa de tabelas em `data-model.md`: tables `namespaces`, `operations`, `embeddings`, `metadata`)
- **FR-012**: Sistema MUST suportar operações AMQP (publicar, consumir, confirmar mensagens) que não estão na especificação OpenAPI
- **FR-013**: Sistema MUST autenticar com RabbitMQ usando credenciais (username/password) fornecidas via variáveis de ambiente
- **FR-014**: Sistema MUST abortar operações RabbitMQ que excedam timeout configurável (padrão: 30 segundos, ver Edge Cases para detalhes), retornando erro descritivo ao cliente
- **FR-015**: Sistema MUST implementar logging estruturado em formato JSON com níveis configuráveis (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **FR-016**: Sistema MUST retornar erro descritivo ao cliente quando RabbitMQ retornar dados em formato inesperado, indicando falha de parsing sem expor detalhes internos sensíveis
- **FR-017**: Sistema MUST implementar acesso thread-safe ao cache usando asyncio.Lock (Python async primitives) para prevenir condições de corrida em requisições concorrentes
- **FR-018**: Sistema MUST retornar falha imediata ao cliente quando conexão com RabbitMQ falhar, sem retry automático, permitindo que o cliente implemente sua própria estratégia de retry
- **FR-019**: Sistema MUST implementar instrumentação completa usando OpenTelemetry com exporter OTLP (obrigatório) e Jaeger/Prometheus (opcionais), incluindo traces distribuídos (spans para cada operação com 100% cobertura), métricas (contadores de requisições, histogramas de latência p50/p95/p99, cache hits/misses ratio, concurrent requests gauge) e logs correlacionados com trace IDs. Target: 95% das operações devem gerar traces completos, 100% dos erros devem ser traceable
- **FR-020**: Sistema MUST suportar versão específica da especificação OpenAPI do RabbitMQ configurável via variável de ambiente (RABBITMQ_API_VERSION), carregando o schema correspondente pré-gerado em build time
- **FR-021**: Sistema MUST implementar rate limiting básico por cliente identificado via connection ID do protocolo MCP (padrão: 100 requisições por minuto, configurável via RATE_LIMIT_RPM), rejeitando requisições excedentes com erro HTTP 429 e header Retry-After. Implementação: extrair connection_id de request.context.connection_id (MCP protocol), fallback para request.client.host (IP address), fallback final para "__global__" (debugging). Rate limit key format: "ratelimit:{connection_id}". Fallback hierarchy: (1) connection ID do MCP se disponível, (2) IP do cliente se connection ID ausente, (3) rate limit global compartilhado se ambos indisponíveis (último caso para debugging apenas)

### Key Entities

- **Operação**: Representa uma ação executável no RabbitMQ, identificada por ID único no formato `{category}.{nome}`, contendo esquema de parâmetros, documentação e metadados
- **Esquema**: Define estrutura de parâmetros de entrada e saída para cada operação, incluindo tipos de dados, campos obrigatórios e validações
- **Operation Category**: Agrupamento lógico de operações relacionadas (ex: queues, exchanges, bindings, amqp), derivado das tags da especificação OpenAPI. *Nota técnica: Internamente referenciado como "namespace" no código Python (ex: tabela `namespaces` no SQLite) para seguir PEP 8 e convenções de banco de dados. Em documentação user-facing e contexto MCP, usar sempre "Operation Category".*
- **Operation Registry**: Catálogo central de todas as operações disponíveis, pré-gerado em tempo de build e armazenado em banco SQLite no repositório para acesso eficiente e queries estruturadas

**Glossário MCP**:
- **Ferramenta Pública**: Tool registrada como interface MCP exposta ao cliente (ex: search-ids, get-id, call-id). Apenas 3 ferramentas públicas neste servidor.
- **Operation ID**: Identificador interno de operação RabbitMQ (ex: queues.list, exchanges.create) acessível através da ferramenta call-id, não registrado como tool MCP separada.

**Glossário de Terminologia**:
- **Operation Category** (user-facing): Agrupamento lógico de operações apresentado ao usuário (ex: queues, exchanges, bindings)
- **Namespace** (código interno): Termo técnico usado internamente no código Python e banco SQLite (tabela `namespaces`) seguindo PEP 8
- **Equivalência**: Operation Category ≡ Namespace (mesmo conceito, termos diferentes por contexto)

### AMQP Operations Schemas

Operações de protocolo AMQP (não cobertas pela HTTP API) têm schemas mantidos manualmente:

- **amqp.publish**: Publicar mensagem em exchange
  - Parâmetros: `exchange` (string, required), `routing_key` (string, required), `body` (string/bytes, required), `properties` (object, optional: content_type, content_encoding, delivery_mode, priority, correlation_id, reply_to, expiration, message_id, timestamp, type, user_id, app_id)
  - Retorno: Confirmação de publicação ou erro
  
- **amqp.consume**: Consumir mensagens de fila
  - Parâmetros: `queue` (string, required), `consumer_tag` (string, optional), `auto_ack` (boolean, default: false), `exclusive` (boolean, default: false)
  - Retorno: Stream de mensagens com `delivery_tag`, `routing_key`, `body`, `properties`
  
- **amqp.ack**: Confirmar processamento de mensagem
  - Parâmetros: `delivery_tag` (integer, required), `multiple` (boolean, default: false)
  - Retorno: Confirmação de acknowledgment
  
- **amqp.nack**: Rejeitar mensagem com opção de requeue
  - Parâmetros: `delivery_tag` (integer, required), `multiple` (boolean, default: false), `requeue` (boolean, default: true)
  - Retorno: Confirmação de negative acknowledgment
  
- **amqp.reject**: Rejeitar mensagem (envia para DLQ se configurado)
  - Parâmetros: `delivery_tag` (integer, required), `requeue` (boolean, default: false)
  - Retorno: Confirmação de reject

**Processo de Manutenção de Schemas AMQP**:
Schemas AMQP são mantidos manualmente em `src/mcp_server/schemas/amqp_operations.py` (não auto-gerados). Atualizações necessárias quando:
1. Nova operação AMQP identificada (ex: novas extensões do protocolo)
2. Mudança no protocolo AMQP (ex: novos campos em message properties)
3. Feedback de produção indica campos faltantes ou validações incorretas
4. Atualização de versão do RabbitMQ com mudanças AMQP

**Processo de atualização detalhado**:
1. **Schema Update**: Modificar modelo Pydantic em `src/mcp_server/schemas/amqp_operations.py`
   - Adicionar/remover campos conforme necessário
   - Atualizar validações e tipos de dados
   - Manter backward compatibility quando possível
2. **Registry Update**: Executar `python scripts/update_operation_registry.py` para sincronizar registry (T013c)
3. **Embeddings Regeneration**: Executar `python scripts/generate_embeddings.py` para atualizar índices de busca (T013d)
4. **Test Update**: Atualizar testes em `tests/integration/test_amqp_operations.py` (T013f)
   - Adicionar casos de teste para novos campos
   - Validar schemas com instância RabbitMQ real
5. **Documentation Sync**: Atualizar esta seção em `spec.md` com mudanças
6. **Code Review**: Pull request obrigatório com validação por peer reviewer
7. **Integration Validation**: Testar com RabbitMQ versões suportadas (3.11, 3.12, 3.13)

**Checklist de validação**:
- [ ] Schema Pydantic validado com dados reais do RabbitMQ
- [ ] Testes de integração passando para todas as operações AMQP
- [ ] Embeddings regenerados e busca semântica funcionando
- [ ] Documentação atualizada
- [ ] Backward compatibility mantida (quando aplicável)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Desenvolvedores conseguem descobrir operações relevantes em menos de 5 segundos usando busca por linguagem natural
- **SC-002**: Sistema responde a requisições básicas em menos de 200 milissegundos
- **SC-003**: Validação de parâmetros adiciona menos de 10 milissegundos ao tempo de resposta
- **SC-004**: Sistema mantém uso de memória abaixo de 1GB por instância em operação normal
- **SC-005**: 100% das operações seguem padrão de interface MCP e são validadas por testes de compliance
- **SC-006**: Desenvolvedores executam operações RabbitMQ com sucesso na primeira tentativa após consultar documentação da operação
- **SC-007**: Mensagens de erro permitem que desenvolvedores identifiquem e corrijam problemas sem consultar documentação adicional em 90% dos casos. Método de medição: Survey estruturado com primeiros 30 usuários (early adopters) testando 10 operações comuns cada (300 tentativas totais) nos primeiros 30 dias após MVP release; classificar cada erro como "claro e acionável" ou "necessitou consultar docs". Target: ≥270/300 (90%) classificados como claros. Survey via Google Forms/Typeform. Fallback (se <30 usuários): Análise de tickets de suporte com tags "erro-não-claro" nos primeiros 3 meses (target: <10% dos tickets totais), incluindo listagem específica de parâmetros faltantes ou inválidos. Owner: Product Manager/Tech Lead
- **SC-008**: Operações que excedem 30 segundos são abortadas com mensagem de timeout clara, evitando espera indefinida
- **SC-009**: Logs estruturados em JSON permitem análise automatizada e troubleshooting eficiente em ambientes de produção
- **SC-010**: Sistema mantém integridade de cache sob requisições concorrentes sem condições de corrida ou corrupção de dados
- **SC-011**: Sistema expõe traces, métricas e logs via OpenTelemetry permitindo monitoramento end-to-end e correlação entre requisições, operações e erros em ambientes de produção
- **SC-012**: Sistema protege RabbitMQ de sobrecarga através de rate limiting configurável, rejeitando requisições excedentes em menos de 5 milissegundos com mensagens claras incluindo tempo de espera

## Assumptions *(optional)*

- **Runtime environment**: Servidor executado em ambiente com Python 3.12+ disponível
- **OpenAPI specification**: RabbitMQ HTTP API OpenAPI está disponível e é a fonte confiável de verdade
- **Versioning strategy**: Sistema suporta UMA versão específica da OpenAPI ativa por deploy, selecionável via RABBITMQ_API_VERSION (ex: "3.13", "3.12"). Múltiplas versões (~150-300 operações cada, baseado em análise do RabbitMQ 3.13 HTTP API) podem ser pré-geradas durante build mas apenas uma é carregada em runtime. Versões suportadas inicialmente: RabbitMQ 3.12.x (stable LTS), 3.13.x (latest), 3.11.x (legacy support opcional)
- **Build-time generation**: Schemas, registry e embeddings gerados durante build/deploy e armazenados em SQLite com extensão sqlite-vec, não gerados em runtime. Embeddings regenerados quando: (1) OpenAPI atualizada, (2) modelo ML trocado, (3) descrições modificadas, (4) versão RabbitMQ muda
- **AMQP operations**: Operações AMQP não documentadas na OpenAPI terão schemas Pydantic manuais mantidos separadamente em `schemas/amqp_operations.py`
- **Cache strategy**: Cache de schemas com TTL de 5 minutos para balance entre performance e atualização. Se cache expira durante operação, continuar com schema cached; reload apenas para próxima operação. Implementado com asyncio.Lock para thread-safety
- **Logging defaults**: Nível INFO para produção, configurável via LOG_LEVEL
- **OpenTelemetry defaults**: Exporter OTLP para localhost:4317 (gRPC), sampling rate 100% para traces (produção pode ajustar para 10-20% via OTEL_TRACES_SAMPLER_ARG), métricas exportadas a cada 60s, batch processor com max_queue_size=2048
- **ML model**: Modelo sentence-transformers all-MiniLM-L6-v2 necessário em runtime para gerar embeddings de queries; embeddings de operações são pré-computados

## Dependencies *(optional)*

### Core MCP Server
- MCP Python SDK oficial
- Biblioteca pydantic para modelagem e validação de dados
- Biblioteca jsonschema para validação de schemas em runtime
- Biblioteca pyyaml para parsing da especificação OpenAPI
- Ferramenta datamodel-code-generator para geração de modelos Pydantic a partir de OpenAPI
- Especificação OpenAPI do RabbitMQ HTTP API atualizada
- Biblioteca sentence-transformers para geração de embeddings semânticos
- Modelo ML pré-treinado all-MiniLM-L6-v2 (384 dimensões, balanceamento performance/qualidade)
- ChromaDB local file mode (recomendado - best Python option per constitution) para busca vetorial eficiente com embeddings pré-computados
- Alternativa: SQLite3 com extensão sqlite-vec (ambos file-based, embedded, conforme constitution)
- SQLite3 standalone para armazenamento do registro de operações, schemas e metadata (tabelas: namespaces, operations, metadata)
- Biblioteca structlog ou python-json-logger para logging estruturado em JSON
- OpenTelemetry SDK (opentelemetry-api, opentelemetry-sdk) para instrumentação completa
- OpenTelemetry exporters (OTLP obrigatório, Jaeger e Prometheus opcionais) para traces, métricas e logs
- OpenTelemetry instrumentação automática para Python (opentelemetry-instrumentation)
- Biblioteca slowapi ou similar para implementação de rate limiting por cliente
- Biblioteca pika para cliente AMQP (publish, consume, ack, nack, reject)

### Console Client (Constitution §VIII Mandatory)
- Click framework para CLI commands
- Rich library para formatting (tables, syntax highlighting, progress indicators)
- Pygments para JSON syntax highlighting
- gettext/babel para i18n framework (20 idiomas obrigatórios)
- Machine translation API (DeepL ou Google Translate) para traduções iniciais
