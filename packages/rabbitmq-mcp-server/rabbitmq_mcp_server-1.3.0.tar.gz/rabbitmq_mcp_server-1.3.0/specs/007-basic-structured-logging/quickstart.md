# Quickstart: Basic Structured Logging

**Feature**: 007-basic-structured-logging  
**Audience**: Desenvolvedores integrando logging estruturado no RabbitMQ MCP Server  
**Time to Complete**: 10 minutos

## Visão Geral

Este guia mostra como usar o sistema de logging estruturado em 3 cenários principais:
1. **Logging básico** - Info, warn, error, debug
2. **Operações com correlation IDs** - Rastreamento de operações MCP
3. **Configuração customizada** - Ajuste de rotação, retenção e performance

---

## Pré-requisitos

```bash
# Instalar dependências usando uvx (preferência do projeto)
uvx pip install structlog pydantic pyyaml
```

---

## 1. Logging Básico

### Inicialização do Logger

```python
from logging import get_logger

# Obter logger configurado (singleton)
logger = get_logger(__name__)

# Log simples
logger.info("Sistema iniciado com sucesso")
logger.warn("Conexão lenta detectada", extra={"latency_ms": 250})
logger.error("Falha ao conectar ao broker", extra={"host": "localhost", "port": 5672})
logger.debug("Detalhes internos da operação", extra={"queue_depth": 1500})
```

### Saída JSON Estruturada

```json
{
  "timestamp": "2025-10-09T14:32:15.123456Z",
  "level": "INFO",
  "category": "Operation",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Sistema iniciado com sucesso"
}
```

### Dados Sensíveis São Automaticamente Redagidos

```python
# ❌ Código INCORRETO (mas seguro graças à redação automática)
logger.info("Conectando ao RabbitMQ", extra={
    "connection_string": "amqp://user:secretpassword@localhost"
})

# ✅ Saída no arquivo de log (senha redagida automaticamente)
{
  "timestamp": "2025-10-09T14:33:20.456789Z",
  "level": "INFO",
  "category": "Connection",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440001",
  "message": "Conectando ao RabbitMQ",
  "connection_string": "amqp://user:[REDACTED]@localhost"
}
```

---

## 2. Operações com Correlation IDs

### Tracking de Operação MCP Completa

```python
from logging.correlation import set_correlation_id, get_correlation_id
import asyncio

async def handle_mcp_tool(tool_name: str, params: dict):
    # Gerar correlation ID no início da operação MCP
    correlation_id = set_correlation_id()
    
    try:
        logger.info(f"Tool {tool_name} iniciada", extra={
            "tool_name": tool_name,
            "params": params
        })
        
        # Executar operação
        result = await execute_tool(tool_name, params)
        
        logger.info(f"Tool {tool_name} concluída com sucesso", extra={
            "tool_name": tool_name,
            "result": result,
            "duration_ms": 42.5
        })
        
        return result
        
    except Exception as e:
        logger.error(f"Tool {tool_name} falhou", extra={
            "tool_name": tool_name,
            "error_type": type(e).__name__,
            "stack_trace": traceback.format_exc()
        })
        raise

# Todos os logs acima terão o mesmo correlation_id
# Permite rastrear toda a operação através dos logs
```

### Buscar Logs por Correlation ID

```bash
# Usando jq para filtrar logs por correlation ID
cat logs/rabbitmq-mcp-2025-10-09.log | jq 'select(.correlation_id == "550e8400-e29b-41d4-a716-446655440000")'

# Ou usando grep
grep "550e8400-e29b-41d4-a716-446655440000" logs/rabbitmq-mcp-2025-10-09.log | jq .
```

---

## 3. Configuração Customizada

### Arquivo de Configuração YAML

```yaml
# config/logging_config.yaml
log_level: INFO                          # ERROR | WARN | INFO | DEBUG

# Destino: Arquivo local (default, mais comum para enterprise message queue apps)
destinations:
  file:
    enabled: true
    path: ./logs/rabbitmq-mcp-{date}.log
    rotation_when: midnight              # Rotação diária
    rotation_interval: 1
    rotation_max_bytes: 104857600        # 100MB
    retention_days: 30                   # Manter logs por 30 dias
    compression: true                    # Comprimir logs rotacionados com gzip
    permissions: "600"                   # Apenas owner read/write (Unix)
  
  # Destino: RabbitMQ AMQP (domain-aligned, dogfooding)
  rabbitmq:
    enabled: true                        # Habilitar publicação de logs em fila
    host: localhost
    port: 5672
    vhost: /
    username: guest
    password: guest
    exchange: logs                       # Exchange dedicada para logs
    exchange_type: topic
    routing_key_pattern: "{level}.{category}"  # ex: INFO.Operation
    durable: true                        # Mensagens persistentes
  
  # Destino: Console (fallback obrigatório)
  console:
    enabled: true                        # Sempre habilitado como fallback
    format: json                         # json ou pretty (para dev)

# Performance
async_queue_size: 10000                  # Buffer para logging assíncrono
async_flush_interval: 0.1                # Flush a cada 100ms
batch_size: 100                          # Batch de 100 logs por write

# Padrões customizados de redação (além dos built-in)
sensitive_patterns:
  - name: custom_secret
    pattern: 'secret_key=([^\s]+)'
    replacement: 'secret_key=[REDACTED]'
    enabled: true
```

### Carregar Configuração

```python
from logging.config import load_config_from_file

# Carregar configuração do arquivo YAML
config = load_config_from_file("config/logging_config.yaml")

# Ou configurar programaticamente
from logging.config import LogConfig, LogLevel

config = LogConfig(
    log_level=LogLevel.DEBUG,
    rotation_max_bytes=50 * 1024 * 1024,  # 50MB
    retention_days=90,                     # 90 dias para auditoria
    async_queue_size=20000                 # Buffer maior para alta carga
)

# Aplicar configuração
configure_logging(config)
```

---

## 4. Consumindo Logs do RabbitMQ

### Configurar Consumer de Logs (Opcional)

Se você habilitou o destino RabbitMQ, pode consumir logs em tempo real:

```python
import pika
import json

def process_log_entry(ch, method, properties, body):
    """Consumer callback para processar logs da fila"""
    log_entry = json.loads(body)
    
    # Exemplo: Enviar erros para sistema de alertas
    if log_entry['level'] == 'ERROR':
        send_alert(log_entry)
    
    # Exemplo: Enviar para Elasticsearch
    if should_index_log(log_entry):
        elasticsearch_client.index(index='logs', document=log_entry)
    
    ch.basic_ack(delivery_tag=method.delivery_tag)

# Conectar ao RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Criar fila para consumir logs
channel.queue_declare(queue='log_processor', durable=True)

# Bind fila ao exchange de logs
# Routing key patterns:
# - "ERROR.#"  = Apenas erros
# - "*.Security" = Todos logs de segurança
# - "#" = Todos os logs
channel.queue_bind(
    exchange='logs',
    queue='log_processor',
    routing_key='#'  # Consumir todos os logs
)

# Iniciar consumer
channel.basic_consume(
    queue='log_processor',
    on_message_callback=process_log_entry
)

print('Aguardando logs...')
channel.start_consuming()
```

### Filtrar Logs por Categoria

```python
# Consumer específico para logs de erro
channel.queue_bind(exchange='logs', queue='error_processor', routing_key='ERROR.#')

# Consumer específico para logs de performance
channel.queue_bind(exchange='logs', queue='perf_processor', routing_key='*.Performance')

# Consumer específico para logs de segurança
channel.queue_bind(exchange='logs', queue='security_processor', routing_key='*.Security')
```

### Integração com Agregadores

```python
# Exemplo: Consumer que envia logs para Elasticsearch
def index_to_elasticsearch(ch, method, properties, body):
    log_entry = json.loads(body)
    
    es_client.index(
        index=f"logs-{log_entry['timestamp'][:10]}",  # logs-2025-10-09
        document=log_entry
    )
    
    ch.basic_ack(delivery_tag=method.delivery_tag)

# Exemplo: Consumer que envia logs para Splunk
def send_to_splunk(ch, method, properties, body):
    log_entry = json.loads(body)
    
    splunk_client.send_event(
        sourcetype='rabbitmq_mcp',
        event=log_entry
    )
    
    ch.basic_ack(delivery_tag=method.delivery_tag)
```

---

## 5. Cenários Comuns

### Logging de Performance

```python
import time

async def operation_with_timing():
    start = time.perf_counter()
    
    try:
        result = await some_slow_operation()
        duration_ms = (time.perf_counter() - start) * 1000
        
        logger.info("Operação concluída", extra={
            "category": "PERFORMANCE",
            "operation": "some_slow_operation",
            "duration_ms": duration_ms,
            "result": "success"
        })
        
        return result
    except Exception as e:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.error("Operação falhou", extra={
            "category": "PERFORMANCE",
            "operation": "some_slow_operation",
            "duration_ms": duration_ms,
            "result": "error",
            "error_type": type(e).__name__
        })
        raise
```

### Logging de Segurança

```python
async def authenticate_user(username: str, password: str):
    logger.info("Tentativa de autenticação", extra={
        "category": "Security",
        "username": username,
        # ❌ NÃO incluir password diretamente - será redagida automaticamente se acidentalmente incluída
        "auth_method": "password"
    })
    
    try:
        result = await verify_credentials(username, password)
        
        logger.info("Autenticação bem-sucedida", extra={
            "category": "Security",
            "username": username,
            "result": "success"
        })
        
        return result
        
    except AuthenticationError as e:
        logger.warn("Autenticação falhou", extra={
            "category": "Security",
            "username": username,
            "result": "failure",
            "reason": str(e)
        })
        raise
```

### Logging de Conexões RabbitMQ

```python
async def connect_to_rabbitmq(connection_params: dict):
    logger.info("Iniciando conexão RabbitMQ", extra={
        "category": "Connection",
        "host": connection_params["host"],
        "port": connection_params["port"],
        "vhost": connection_params["vhost"]
        # Password será redagida automaticamente se incluída
    })
    
    try:
        connection = await establish_connection(connection_params)
        
        logger.info("Conexão RabbitMQ estabelecida", extra={
            "category": "Connection",
            "host": connection_params["host"],
            "result": "success",
            "connection_id": connection.id
        })
        
        return connection
        
    except ConnectionError as e:
        logger.error("Falha na conexão RabbitMQ", extra={
            "category": "Connection",
            "host": connection_params["host"],
            "result": "error",
            "error_type": "ConnectionError",
            "error_message": str(e)
        })
        raise
```

---

## 6. Análise de Logs

### Filtrar por Nível

```bash
# Apenas erros
cat logs/rabbitmq-mcp-*.log | jq 'select(.level == "ERROR")'

# Warnings e erros
cat logs/rabbitmq-mcp-*.log | jq 'select(.level == "ERROR" or .level == "WARN")'
```

### Filtrar por Categoria

```bash
# Logs de performance
cat logs/rabbitmq-mcp-*.log | jq 'select(.category == "PERFORMANCE")'

# Logs de segurança
cat logs/rabbitmq-mcp-*.log | jq 'select(.category == "Security")'
```

### Análise de Operações Lentas

```bash
# Operações que levaram mais de 100ms
cat logs/rabbitmq-mcp-*.log | jq 'select(.duration_ms > 100) | {timestamp, message, duration_ms, tool_name}'

# Top 10 operações mais lentas
cat logs/rabbitmq-mcp-*.log | jq 'select(.duration_ms) | {duration_ms, tool_name, message}' | jq -s 'sort_by(.duration_ms) | reverse | .[:10]'
```

### Agregação de Erros

```bash
# Contar erros por tipo
cat logs/rabbitmq-mcp-*.log | jq 'select(.error_type) | .error_type' | sort | uniq -c | sort -rn

# Erros mais comuns nas últimas 24h
find logs/ -name "*.log" -mtime -1 | xargs cat | jq 'select(.level == "ERROR") | .message' | sort | uniq -c | sort -rn
```

---

## 7. Troubleshooting

### Logs Não Estão Sendo Escritos

```python
# Verificar se diretório existe
import os
os.makedirs("./logs", exist_ok=True)

# Verificar permissões
import stat
logs_dir = "./logs"
print(f"Permissões: {oct(os.stat(logs_dir).st_mode)[-3:]}")

# Verificar se fallback para console está ativo
# Deve ver logs em stderr se arquivo falhar
```

### Performance Degradada

```python
# Aumentar batch size e queue size
config = LogConfig(
    batch_size=200,          # Mais logs por batch
    async_queue_size=20000,  # Buffer maior
    async_flush_interval=0.2 # Flush menos frequente
)

# Desabilitar compression durante runtime (apenas para rotados)
config.compression_enabled = False
```

### Disco Cheio

```python
# Reduzir retention e tamanho de arquivo
config = LogConfig(
    retention_days=7,              # Apenas 1 semana
    rotation_max_bytes=10485760,   # 10MB ao invés de 100MB
    compression_enabled=True       # SEMPRE comprimir
)

# Verificar espaço em disco
import shutil
stats = shutil.disk_usage("./logs")
free_gb = stats.free / (1024**3)
print(f"Espaço livre: {free_gb:.2f} GB")
```

---

## 8. Testes

### Testar Logging em Testes Unitários

```python
import pytest
from logging import get_logger

def test_logging_with_correlation_id(caplog):
    """Testar que correlation ID é incluído nos logs"""
    from logging.correlation import set_correlation_id
    
    # Given
    logger = get_logger(__name__)
    correlation_id = set_correlation_id()
    
    # When
    logger.info("Test message")
    
    # Then
    assert correlation_id in caplog.text
    assert "Test message" in caplog.text

def test_sensitive_data_redaction():
    """Testar que dados sensíveis são redagidos"""
    from logging.redaction import apply_redaction
    
    # Given
    log_entry = {
        "message": "Connecting",
        "connection_string": "amqp://user:secret@localhost"
    }
    
    # When
    redacted = apply_redaction(log_entry)
    
    # Then
    assert "secret" not in str(redacted)
    assert "[REDACTED]" in redacted["connection_string"]
```

---

## Próximos Passos

1. ✅ **Logging básico funcionando** - Pronto para desenvolvimento
2. 🔄 **Integrar com MCP tools** - Adicionar logging em todas as tools
3. 🔄 **Configurar rotação** - Ajustar para ambiente de produção
4. 🔄 **Integrar com agregadores** - Future: ELK, Splunk, CloudWatch (fora de escopo MVP)

## Referências

- [Constitution - Seção V: Observability](../../../.specify/memory/constitution.md#v-observability--error-handling)
- [Data Model](./data-model.md) - Entidades e schemas detalhados
- [Contracts](./contracts/) - JSON schemas para validação
- [structlog Documentation](https://www.structlog.org/) - Biblioteca de logging estruturado
