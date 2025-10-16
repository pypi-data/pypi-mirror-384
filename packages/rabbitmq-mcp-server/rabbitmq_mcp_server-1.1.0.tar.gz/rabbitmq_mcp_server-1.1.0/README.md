# RabbitMQ MCP Connection

Esta feature implementa conexão básica com RabbitMQ exposta via MCP (Model Context Protocol) seguindo o padrão de descoberta semântica (`search-ids`, `get-id`, `call-id`).

## Estrutura

- `src/`
  - `connection/`: componentes núcleo de conexão AMQP
  - `logging/`: configuração de logging estruturado
  - `schemas/`: validações Pydantic
  - `tools/`: MCP tools para operações RabbitMQ
- `tests/`
  - `unit/`, `integration/`, `contract/`: suites de teste
- `config/`: exemplos de configuração (`config.toml.example`, `.env.example`)

Consulte `specs/002-basic-rabbitmq-connection/` para spec, plano e tasks completas.
