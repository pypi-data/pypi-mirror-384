# Contracts: Basic Structured Logging

Este diretório contém os JSON Schemas que definem os contratos de dados do sistema de logging estruturado.

## Schemas Disponíveis

### LogEntry.schema.json
Define a estrutura de uma entrada de log individual, incluindo campos obrigatórios, opcionais e suas regras de validação.

**Uso**: Validar logs gerados pelo sistema ou parsear logs para análise.

**Campos principais**:
- `timestamp` (obrigatório): ISO 8601 UTC com Z
- `level` (obrigatório): ERROR, WARN, INFO, DEBUG
- `category` (obrigatório): Connection, Operation, Error, Security, Performance
- `correlation_id` (obrigatório): UUID v4 ou timestamp-based
- `message` (obrigatório): Descrição do evento (max 100KB)

**Exemplo**:
```json
{
  "timestamp": "2025-10-09T14:32:15.123456Z",
  "level": "INFO",
  "category": "Operation",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "MCP tool executed successfully"
}
```

### LogConfig.schema.json
Define a configuração do sistema de logging, incluindo rotação, retenção e performance.

**Uso**: Validar arquivo de configuração YAML/JSON antes de inicializar sistema de logging.

**Campos principais**:
- `log_level`: Nível mínimo de log
- `rotation_max_bytes`: Tamanho máximo antes de rotação (default 100MB)
- `retention_days`: Dias de retenção (default 30)
- `async_queue_size`: Tamanho do buffer assíncrono

**Exemplo**:
```yaml
log_level: INFO
output_file: ./logs/rabbitmq-mcp-{date}.log
rotation_max_bytes: 104857600
retention_days: 30
```

### SensitiveDataPattern.schema.json
Define padrões regex para redação automática de dados sensíveis.

**Uso**: Configurar padrões customizados de redação além dos built-in.

**Campos principais**:
- `name`: Identificador do padrão
- `pattern`: Regex Python para detectar dados sensíveis
- `replacement`: Texto substituto (ex: "[REDACTED]")

**Exemplo**:
```json
{
  "name": "custom_api_key",
  "pattern": "x-api-key:\\s*([^\\s]+)",
  "replacement": "x-api-key: [REDACTED]",
  "enabled": true
}
```

## Validação de Schemas

### Usando jsonschema (Python)
```python
import json
import jsonschema

# Carregar schema
with open('LogEntry.schema.json') as f:
    schema = json.load(f)

# Validar log entry
log_entry = {
    "timestamp": "2025-10-09T14:32:15.123456Z",
    "level": "INFO",
    "category": "Operation",
    "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "Test message"
}

jsonschema.validate(instance=log_entry, schema=schema)
print("✓ Log entry is valid")
```

### Usando ajv (Node.js)
```javascript
const Ajv = require('ajv');
const fs = require('fs');

const ajv = new Ajv();
const schema = JSON.parse(fs.readFileSync('LogEntry.schema.json', 'utf8'));
const validate = ajv.compile(schema);

const logEntry = {
  timestamp: "2025-10-09T14:32:15.123456Z",
  level: "INFO",
  category: "Operation",
  correlation_id: "550e8400-e29b-41d4-a716-446655440000",
  message: "Test message"
};

if (validate(logEntry)) {
  console.log("✓ Log entry is valid");
} else {
  console.error("✗ Validation errors:", validate.errors);
}
```

## Testes de Contrato

Os schemas devem ser testados em `tests/contract/test_log_schema.py`:

```python
import pytest
import json
from pathlib import Path
from jsonschema import validate, ValidationError

@pytest.fixture
def log_entry_schema():
    schema_path = Path("specs/feature/007-basic-structured-logging/contracts/LogEntry.schema.json")
    return json.loads(schema_path.read_text())

def test_valid_log_entry(log_entry_schema):
    """Valida que log entry completo passa validação"""
    valid_entry = {
        "timestamp": "2025-10-09T14:32:15.123456Z",
        "level": "INFO",
        "category": "Operation",
        "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
        "message": "Test message",
        "tool_name": "call-id",
        "duration_ms": 42.5,
        "result": "success"
    }
    
    # Should not raise ValidationError
    validate(instance=valid_entry, schema=log_entry_schema)

def test_missing_required_fields(log_entry_schema):
    """Valida que campos obrigatórios ausentes causam erro"""
    invalid_entry = {
        "level": "INFO",
        "message": "Missing required fields"
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_entry, schema=log_entry_schema)

def test_invalid_log_level(log_entry_schema):
    """Valida que nível de log inválido causa erro"""
    invalid_entry = {
        "timestamp": "2025-10-09T14:32:15.123456Z",
        "level": "INVALID",  # Not in enum
        "category": "Operation",
        "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
        "message": "Test"
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_entry, schema=log_entry_schema)
```

## Referências

- **JSON Schema Specification**: https://json-schema.org/
- **Python jsonschema**: https://python-jsonschema.readthedocs.io/
- **Pydantic** (geração automática de schemas): https://docs.pydantic.dev/latest/concepts/json_schema/
