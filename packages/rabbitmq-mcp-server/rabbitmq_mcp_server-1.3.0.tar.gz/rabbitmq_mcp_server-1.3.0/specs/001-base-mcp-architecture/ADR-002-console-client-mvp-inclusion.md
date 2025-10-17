# ADR-002: Console Client & Multilingual Support - MVP Inclusion (Supersedes ADR-001)

**Status**: ACCEPTED (SUPERSEDES ADR-001)  
**Date**: 2025-10-09  
**Decision Makers**: Architecture Team  
**Context**: Constitution compliance mandates console client in MVP

---

## Context

After re-reviewing constitution requirements (§VIII linhas 71, 604-624):
- **OBRIGATÓRIO (NON-NEGOTIABLE)**: "Every MCP server MUST include a built-in console client"
- **OBRIGATÓRIO (NON-NEGOTIABLE)**: Console client deve suportar 20 idiomas mais falados

**ADR-001 Decision (REJECTED)**: Phased delivery (console in Phase 2/3)
- **Why rejected**: Constitution "MUST" is non-negotiable, cannot be deferred
- **Lesson learned**: Constitutional requirements override timeline concerns

---

## Decision

**INCLUDE console client + multilingual support IN MVP** para atingir 100% constitution compliance antes de production release.

### MVP Scope (Updated) - 7-9 semanas
- ✅ Core semantic discovery pattern (3 ferramentas MCP)
- ✅ OpenAPI-driven architecture
- ✅ ChromaDB vector search
- ✅ OpenTelemetry observability
- ✅ **Console client interativo** (NEW - constitutional requirement)
- ✅ **Multilingual support (20 idiomas)** (NEW - constitutional requirement)

---

## Rationale

### 1. **Constitution is Non-Negotiable**
- "MUST" in constitution = mandatory for ANY release
- Cannot interpret as "production-ready only" when it says "Every MCP server MUST"
- Phased delivery violated constitutional authority

### 2. **Risk of "Never Ship" Eliminated**
- Deferring to Phase 2/3 creates risk of incomplete constitution compliance
- Better to ship complete MVP later than incomplete MVP early
- Constitution violations create technical debt that compounds

### 3. **User Experience from Day 1**
- Early adopters get full experience (programmatic + CLI)
- No need for interim solutions or workarounds
- Consistent with "Every MCP server" language in constitution

### 4. **Precedent Alignment**
- While AWS/Terraform launched CLIs later, they're not bound by our constitution
- Our constitution is project-specific and binding
- Following constitution builds trust and quality standards

---

## Implementation Approach

### Console Client Architecture (Simplified)
**Goal**: Lightweight CLI that meets constitutional requirements without over-engineering

**Framework**: Click (simple, widely used, Python-native)
**UI Library**: Rich (for formatting, not full TUI complexity)
**i18n Framework**: gettext (industry standard, simple)

### Simplified Features (MVP-appropriate)
1. **Basic Commands**:
   - `rabbitmq-mcp search "query"` → calls search-ids
   - `rabbitmq-mcp describe <operation-id>` → calls get-id
   - `rabbitmq-mcp execute <operation-id> --params '{"vhost": "/"}'` → calls call-id
   - `rabbitmq-mcp connect --host localhost --user guest` → test connection

2. **i18n Support**:
   - 20 idiomas via gettext .po files
   - Auto-detection via locale.getdefaultlocale()
   - Fallback to English if translation missing
   - Override via `--lang` flag

3. **Basic UI**:
   - Rich tables for search results
   - Syntax highlighting for JSON (pygments)
   - Progress indicators for long operations
   - Color-coded status messages

### What We're NOT Building (to keep MVP scope reasonable)
- ❌ Full interactive TUI (prompt_toolkit)
- ❌ Command history persistence
- ❌ Auto-completion (too complex for MVP)
- ❌ Real-time message monitoring dashboard
- ❌ Advanced configuration management UI

### Translation Strategy (Pragmatic)
**20 idiomas obrigatórios** (constitution linhas 604-624):
1. English (native - written by developers)
2-20. Machine translation via DeepL API/Google Translate (validated by native speakers if available)

**Strings to translate** (~50-100 strings):
- Command descriptions
- Error messages
- Success messages
- Help text
- Status indicators

**Effort**: 2-3 days for translation setup + machine translation + basic validation

---

## Timeline Impact

### Original MVP Timeline (ADR-001)
- **Duration**: 4-5 semanas
- **Tasks**: 61 tasks

### Updated MVP Timeline (ADR-002) - CONSTITUTION COMPLIANT
- **Duration**: 7-9 semanas (+3-4 semanas)
- **Tasks**: 73 tasks (+12 tasks)

### New Tasks Added (Phase 6.5: Console Client & i18n)
- T057: Implementar CLI framework base (Click)
- T058: Implementar comando search
- T059: Implementar comando describe
- T060: Implementar comando execute
- T061: Implementar comando connect
- T062: Implementar i18n framework (gettext)
- T063: Criar translation templates (.pot files)
- T064: Gerar traduções para 20 idiomas (machine translation)
- T065: Implementar locale detection e fallback
- T066: Implementar Rich formatting para output
- T067: Escrever testes de console CLI
- T068: Escrever testes de i18n coverage

**Parallel Opportunities**: T062-T065 (i18n) podem rodar em paralelo com T057-T061 (CLI commands)

---

## Consequences

### Positive
- ✅ 100% constitution compliance no MVP
- ✅ Zero technical debt relacionado a constitution
- ✅ Early adopters recebem experiência completa
- ✅ Builds trust in constitution adherence

### Negative
- ⚠️ Timeline aumenta 60% (4-5 → 7-9 semanas)
- ⚠️ Escopo MVP maior (mais complexo)
- ⚠️ Risco de atrasar entrega de core value

### Mitigation Strategies
1. **Simplified Console**: Evitar over-engineering, focar no mínimo viable
2. **Machine Translation**: Aceitar traduções automáticas para MVP (melhorar depois)
3. **Parallel Execution**: Maximizar tasks paralelas (CLI + i18n simultaneamente)
4. **Pragmatic Quality**: 80% perfeição OK para console MVP (iterações futuras)

---

## Constitution Compliance Status

### After ADR-001 (REJECTED)
- Constitution Compliance: 🟡 95% (21/22)
- Console Client: ❌ Deferred to Phase 2
- Multilingual: ❌ Deferred to Phase 3

### After ADR-002 (ACCEPTED)
- Constitution Compliance: ✅ **100%** (22/22)
- Console Client: ✅ IN MVP
- Multilingual: ✅ IN MVP (20 idiomas)

---

## Acceptance Criteria (Console Client MVP)

### Console Client - Definition of Done
- ✅ 4 comandos funcionais: search, describe, execute, connect
- ✅ Integration com 3 ferramentas MCP (search-ids, get-id, call-id)
- ✅ Rich formatting para output (tables, JSON highlighting)
- ✅ Help text em todos os comandos
- ✅ Error handling claro
- ✅ Unit tests com coverage >80%

### i18n - Definition of Done
- ✅ 20 idiomas implementados (machine translation OK para MVP)
- ✅ gettext framework configurado
- ✅ Locale auto-detection funcional
- ✅ Fallback para English funcional
- ✅ `--lang` flag para override manual
- ✅ Automated i18n coverage tests (validate all languages present)

---

## Alternatives Considered (Re-evaluated)

### Alternative 1: Phased Delivery (ADR-001) - REJECTED ❌
- **Why rejected**: Violates constitution "MUST include" language
- **Lesson**: Cannot defer constitutional requirements

### Alternative 2: Minimal Console in MVP - REJECTED ❌
- **Why rejected**: "Minimal" too subjective, creates scope creep debates
- **Lesson**: Define clear MVP scope upfront

### Alternative 3: Full-Featured Console in MVP - REJECTED ❌
- **Why rejected**: Over-engineering, timeline explosion
- **Lesson**: Balance constitution compliance with pragmatism

### Alternative 4: Simplified Console + i18n in MVP (ADR-002) - ACCEPTED ✅
- **Why accepted**: Meets constitution, reasonable timeline, pragmatic scope
- **Implementation**: Click + Rich + gettext, 4 commands, machine translation

---

## Review & Approval

### Stakeholders
- [x] Architecture Team: APPROVED (constitution compliance priority)
- [x] Product Management: APPROVED (accepts longer timeline for quality)
- [x] Engineering Team: APPROVED (simplified scope manageable)
- [x] Constitution Review: APPROVED (100% compliance achieved)

### Conditions
1. ✅ Simplified console scope (4 commands only)
2. ✅ Machine translation acceptable for MVP
3. ✅ Parallel execution maximized (CLI + i18n)
4. ✅ Timeline transparency: 7-9 semanas comunicado

---

## Supersedes

**ADR-001**: Console Client & Multilingual Support - Phased Delivery
- **Status**: SUPERSEDED by ADR-002
- **Reason**: Constitution compliance cannot be deferred
- **Date Superseded**: 2025-10-09

---

## References

- Constitution §VIII linha 71: "Every MCP server MUST include a built-in console client"
- Constitution §VIII linhas 604-624: Console Client 20 Languages
- ADR-001: Console Client Phased Delivery (SUPERSEDED)
- Click documentation: https://click.palletsprojects.com/
- Rich documentation: https://rich.readthedocs.io/
- gettext documentation: https://docs.python.org/3/library/gettext.html

---

**Decision**: ACCEPTED (SUPERSEDES ADR-001)  
**Status**: ACTIVE (Updated MVP scope)  
**Timeline**: 7-9 semanas (updated from 4-5)  
**Constitution Compliance**: ✅ 100% (22/22 sections)  
**Next Steps**: Update tasks.md with T057-T068
