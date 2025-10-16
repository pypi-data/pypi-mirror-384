# Feature Specification: Message Publishing and Consumption

**Feature Branch**: `004-message-publishing-and`  
**Created**: 2025-10-09  
**Status**: Draft  
**Input**: User description: "Message Publishing and Consumption"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Send Messages to Systems (Priority: P1)

Um operador precisa enviar mensagens para outros sistemas através de exchanges. Ele especifica o conteúdo da mensagem, o destino (exchange e routing key) e propriedades opcionais como headers e persistência. O sistema confirma o envio e garante que a mensagem foi entregue ao broker.

**Why this priority**: Este é o cenário mais fundamental - sem a capacidade de publicar mensagens, o sistema não tem propósito. É a base para qualquer comunicação assíncrona.

**Independent Test**: Pode ser testado de forma independente enviando uma mensagem simples para um exchange existente e verificando no broker que a mensagem foi recebida.

**Acceptance Scenarios**:

1. **Given** um exchange configurado existe, **When** operador publica uma mensagem com conteúdo JSON, **Then** mensagem é entregue ao exchange com sucesso em menos de 100ms
2. **Given** operador especifica headers customizados, **When** mensagem é publicada, **Then** headers são preservados na mensagem entregue
3. **Given** operador marca mensagem como persistente, **When** mensagem é publicada, **Then** mensagem sobrevive a reinicializações do broker
4. **Given** operador especifica routing key inválida, **When** tenta publicar, **Then** sistema valida e retorna erro claro antes de enviar

---

### User Story 2 - Receber Mensagens de Filas (Priority: P2)

Um operador deseja consumir mensagens de uma fila específica para processar informações. Ele se inscreve na fila e recebe as mensagens em tempo real conforme elas chegam. Cada mensagem inclui seu conteúdo e metadados relevantes (headers, delivery tag, routing key).

**Why this priority**: Consumir mensagens é essencial para completar o ciclo de comunicação, mas só faz sentido após ter a capacidade de publicar. Este cenário permite receber e visualizar mensagens.

**Independent Test**: Pode ser testado independentemente publicando mensagens em uma fila e verificando que o consumidor recebe todas elas com metadados corretos.

**Acceptance Scenarios**:

1. **Given** uma fila contém mensagens, **When** operador se inscreve na fila, **Then** mensagens são entregues em tempo real com latência inferior a 50ms
2. **Given** múltiplas mensagens estão enfileiradas, **When** operador define limite de prefetch para 10, **Then** sistema recebe no máximo 10 mensagens não confirmadas simultaneamente
3. **Given** operador está consumindo mensagens, **When** nova mensagem chega na fila, **Then** mensagem é entregue imediatamente ao consumidor
4. **Given** fila não existe, **When** operador tenta consumir, **Then** sistema retorna erro claro informando que fila não foi encontrada

---

### User Story 3 - Confirmar Processamento de Mensagens (Priority: P3)

Após processar uma mensagem recebida, o operador precisa informar ao sistema se o processamento foi bem-sucedido ou falhou. Para mensagens processadas com sucesso, ele confirma (ack) para remover da fila. Para falhas, ele pode rejeitar (nack) com opção de recolocar na fila para nova tentativa.

**Why this priority**: A confirmação de mensagens garante confiabilidade e previne perda de dados, mas é uma funcionalidade avançada que depende primeiro da capacidade de publicar e consumir.

**Independent Test**: Pode ser testado consumindo mensagens, confirmando algumas e rejeitando outras, depois verificando que mensagens confirmadas foram removidas e rejeitadas foram reenfileiradas conforme esperado.

**Acceptance Scenarios**:

1. **Given** mensagem foi recebida, **When** operador confirma processamento (ack), **Then** mensagem é removida permanentemente da fila
2. **Given** processamento falhou, **When** operador rejeita com requeue ativado, **Then** mensagem retorna para fila e fica disponível para novo consumidor
3. **Given** processamento falhou criticamente, **When** operador rejeita sem requeue, **Then** mensagem é removida da fila (pode ir para dead letter se configurado)
4. **Given** operador tenta confirmar mensagem já confirmada, **When** envia ack duplicado, **Then** sistema previne erro e ignora graciosamente
5. **Given** operador tenta confirmar com delivery tag inválido, **When** envia ack, **Then** sistema retorna erro claro sobre tag não encontrada

---

### Edge Cases

- O que acontece quando operador tenta publicar para exchange que não existe?
- Como sistema lida com mensagens maiores que limite do broker?
- O que acontece se conexão cair durante consumo de mensagens?
- Como sistema trata confirmações após reconexão?
- O que acontece se operador tentar confirmar mensagem após timeout?
- Como sistema lida com 100+ consumidores simultâneos na mesma fila?
- O que acontece se mensagem não puder ser deserializada no formato esperado?
- Como sistema trata mensagens com headers malformados?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Sistema DEVE permitir publicar mensagens para exchanges especificando conteúdo, exchange, routing key
- **FR-002**: Sistema DEVE suportar diferentes tipos de payload: JSON, texto simples, binário
- **FR-003**: Sistema DEVE permitir especificar propriedades de mensagem: headers customizados, content-type, correlation ID
- **FR-004**: Sistema DEVE permitir marcar mensagens como persistentes para sobreviver reinicializações
- **FR-005**: Sistema DEVE validar existência do exchange antes de publicar
- **FR-006**: Sistema DEVE completar operações de publicação em menos de 100ms em condições normais
- **FR-007**: Sistema DEVE permitir inscrição em filas específicas para consumo de mensagens
- **FR-008**: Sistema DEVE entregar mensagens ao consumidor em tempo real conforme chegam
- **FR-009**: Sistema DEVE preservar todos os metadados de mensagem: headers, delivery tag, routing key, properties
- **FR-010**: Sistema DEVE permitir configurar limite de prefetch (padrão: 10 mensagens)
- **FR-011**: Sistema DEVE manter latência de consumo abaixo de 50ms por mensagem
- **FR-012**: Sistema DEVE permitir confirmar (ack) mensagens processadas com sucesso
- **FR-013**: Sistema DEVE permitir rejeitar (nack) mensagens com opção de requeue
- **FR-014**: Sistema DEVE rastrear delivery tags para acknowledgment confiável
- **FR-015**: Sistema DEVE prevenir confirmações duplicadas da mesma mensagem
- **FR-016**: Sistema DEVE validar delivery tags antes de processar acknowledgments
- **FR-017**: Sistema DEVE lidar graciosamente com falhas de conexão durante operações
- **FR-018**: Sistema DEVE suportar pelo menos 100 consumidores simultâneos
- **FR-019**: Sistema DEVE alcançar throughput de pelo menos 1000 mensagens por minuto
- **FR-020**: Sistema DEVE validar existência de fila antes de iniciar consumo
- **FR-021**: Sistema DEVE registrar todas as operações de mensagem com correlation IDs para rastreamento
- **FR-022**: Sistema DEVE permitir consumidor escolher entre confirmação automática ou manual

### Key Entities

- **Message**: Representa uma unidade de dados transmitida pelo sistema, contendo payload (conteúdo), headers (metadados customizados), properties (content-type, correlation ID, persistence flag), routing key (chave para roteamento), delivery tag (identificador único para acknowledgment)

- **Publisher**: Representa a capacidade de envio de mensagens, incluindo exchange de destino, routing key pattern, opções de persistência e confirmação de entrega

- **Consumer**: Representa a capacidade de recebimento de mensagens, incluindo fila de origem, prefetch limit, modo de acknowledgment, filtros de mensagem

- **Acknowledgment**: Representa a confirmação de processamento de mensagem, incluindo delivery tag, tipo (ack/nack/reject), opção de requeue, timestamp de processamento

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Operador consegue publicar mensagem simples e confirmar entrega em menos de 100ms
- **SC-002**: Sistema entrega mensagens consumidas com latência máxima de 50ms por mensagem
- **SC-003**: Sistema mantém throughput de pelo menos 1000 mensagens por minuto sob carga normal
- **SC-004**: Sistema suporta 100 consumidores simultâneos sem degradação de performance
- **SC-005**: Zero perda de mensagens durante operações normais (confirmadas corretamente)
- **SC-006**: Operador consegue rastrear ciclo completo de uma mensagem (publicação → consumo → acknowledgment) através dos logs
- **SC-007**: 95% das operações de publicação completam com sucesso na primeira tentativa
- **SC-008**: Sistema se recupera automaticamente de falhas de conexão em menos de 5 segundos
- **SC-009**: Mensagens rejeitadas com requeue retornam para fila em menos de 100ms
- **SC-010**: Operador consegue processar diferentes tipos de payload (JSON, texto, binário) sem configuração adicional
