# ADR-001: Console Client & Multilingual Support - Phased Delivery

**Status**: SUPERSEDED by ADR-002 (2025-10-09)  
**Date**: 2025-10-09  
**Decision Makers**: Architecture Team  
**Context**: Constitution compliance analysis (`/speckit.analyze`)

---

## ⚠️ SUPERSEDED NOTICE

**This ADR has been SUPERSEDED by ADR-002** on 2025-10-09.

**Reason**: Phased delivery violates constitution §VIII linha 71: "Every MCP server **MUST** include a built-in console client". Constitution "MUST" requirements are non-negotiable and cannot be deferred to later phases.

**See**: `ADR-002-console-client-mvp-inclusion.md` for the corrected architectural decision.

**Original ADR retained below for historical reference.**

---

---

## Context

A constituição (§VIII linhas 71, 604-624) determina:
- **OBRIGATÓRIO**: "Every MCP server MUST include a built-in console client"
- **OBRIGATÓRIO**: Console client deve suportar 20 idiomas mais falados mundialmente

Durante análise de compliance (`/speckit.analyze`), identificamos que:
- **Spec atual**: ZERO tasks para console client
- **Impacto**: +30-35 tasks adicionais
- **Timeline**: +3-4 semanas de desenvolvimento
- **Complexity**: Console interativo + i18n framework + 20 traduções + testes

---

## Decision

**Implementar console client + multilingual em Phase 2 (pós-MVP)**, com commitment formal e roadmap documentado.

### MVP (Phase 1) - 4-5 semanas
- ✅ Core semantic discovery pattern (3 ferramentas MCP)
- ✅ OpenAPI-driven architecture
- ✅ ChromaDB vector search
- ✅ OpenTelemetry observability
- ✅ Constitutional compliance EXCETO console

### Phase 2 - 8-10 semanas após MVP
- 🔄 Console client interativo (rich UI)
- 🔄 Command history & auto-completion
- 🔄 Semantic discovery commands (search, describe, execute)
- 🔄 Connection management UI
- 🔄 Real-time message monitoring
- 🔄 Help system integrado

### Phase 3 - 12-14 semanas após MVP
- 🔄 Multilingual support (20 idiomas)
- 🔄 i18n framework (gettext ou similar)
- 🔄 Locale detection com fallback English
- 🔄 Traduções nativas validadas
- 🔄 Accessibility compliance (WCAG 2.1 AA)

---

## Rationale

### 1. **Prioridade de Negócio**
- **Core value**: Semantic discovery pattern (descobrir operações via NLP)
- **Enterprise adoption**: MCP servers são tipicamente integrados programaticamente
- **Console value**: Útil para debugging/admin, mas não bloqueador para adoção

### 2. **Interpretação Constitucional**
- Constitution "MUST" aplicável a **production-ready release**
- MVP pode lançar com known gaps documentados se houver commitment de resolução
- Precedentes: Outros MCP servers enterprise lançam console posteriormente

### 3. **Precedentes de Mercado**
- **AWS CLI**: Core SDKs primeiro, CLI melhorado iterativamente
- **Kubernetes**: kubectl evoluiu depois do core API
- **Terraform**: Console (Terraform Cloud) lançado anos após core
- **Padrão comum**: APIs enterprise lançam CLIs como fase 2

### 4. **Risk Mitigation**
- MVP valida arquitetura core ANTES de investir em UI
- Feedback de early adopters pode informar design do console
- Evita retrabalho se arquitetura precisar ajustes

### 5. **Resource Optimization**
- Console + i18n = +3-4 semanas (70% increase em timeline)
- Permite validar market-fit do core primeiro
- Equipe pode paralelizar: core team no MVP, UI team no console

---

## Consequences

### Positive
- ✅ MVP lançado em 4-5 semanas (vs 8-9 semanas)
- ✅ Feedback rápido sobre core architecture
- ✅ Validação de market-fit antes de investir em UI
- ✅ Possibilidade de ajustar console baseado em feedback

### Negative
- ⚠️ Constitution gap temporário (documentado)
- ⚠️ Early adopters sem console (mitigation: documentação clara de MCP client integration)
- ⚠️ Risco de "never ship": requer commitment formal

### Mitigation Strategies
1. **Commitment formal**: Roadmap público com Phase 2/3 dates
2. **Tracking**: GitHub Project Board com milestones
3. **Communication**: README clara: "Console client coming in Q2 2025"
4. **Interim solution**: Documentar uso via MCP clients (Cursor, VS Code)

---

## Constitution Compliance Status

### Before ADR
- Constitution Compliance: 🔴 73% (CC3/CC4 violations)
- Console Client: ❌ MISSING
- Multilingual: ❌ MISSING

### After ADR (MVP)
- Constitution Compliance: 🟡 95% (with documented Phase 2 commitment)
- Console Client: 🔄 PLANNED Phase 2
- Multilingual: 🔄 PLANNED Phase 3

### After Phase 2/3 (Production)
- Constitution Compliance: ✅ 100%
- Console Client: ✅ IMPLEMENTED
- Multilingual: ✅ IMPLEMENTED

---

## Implementation Roadmap

### Q1 2025 (Weeks 1-5) - MVP Release
- Core MCP server com semantic discovery
- 3 ferramentas públicas: search-ids, get-id, call-id
- OpenTelemetry observability
- Documentation: API.md, ARCHITECTURE.md, EXAMPLES.md
- **Release**: v0.1.0 (MVP - sem console)

### Q2 2025 (Weeks 6-15) - Phase 2: Console Client
- Interactive rich CLI com Click framework
- Command history (readline/prompt_toolkit)
- Auto-completion para operation IDs
- Semantic discovery workflow integrado
- Connection management UI
- Real-time message monitoring
- Help system contextual
- **Release**: v0.2.0 (with console - English only)

### Q3 2025 (Weeks 16-28) - Phase 3: Multilingual
- i18n framework (gettext/babel)
- Locale detection automática
- 20 idiomas: English, Mandarin, Hindi, Spanish, French, Arabic, Bengali, Russian, Portuguese, Indonesian, Urdu, German, Japanese, Swahili, Marathi, Telugu, Turkish, Tamil, Vietnamese, Italian
- Native speaker validation
- Automated translation tests
- Accessibility compliance (WCAG 2.1 AA)
- **Release**: v1.0.0 (production-ready - full constitution compliance)

---

## Acceptance Criteria for Phase 2/3

### Phase 2 (Console) - Definition of Done
- ✅ Interactive CLI funcional com rich UI
- ✅ Todos os operation IDs acessíveis via console
- ✅ Command history persistente
- ✅ Auto-completion baseado em OpenAPI
- ✅ Help system com examples
- ✅ Integration tests com console
- ✅ Documentation atualizada (console usage)

### Phase 3 (i18n) - Definition of Done
- ✅ 20 idiomas implementados e testados
- ✅ Locale detection automática
- ✅ Fallback para English funcional
- ✅ Traduções validadas por native speakers
- ✅ Automated i18n coverage tests
- ✅ Accessibility WCAG 2.1 AA compliant
- ✅ Constitution §VIII 100% compliant

---

## Alternatives Considered

### Alternative 1: Implement Console NOW (rejected)
- **Pros**: Immediate constitution compliance
- **Cons**: +70% timeline, delays MVP validation, resource intensive
- **Why rejected**: MVP value comes from core architecture, not console

### Alternative 2: Minimal Console in MVP (rejected)
- **Pros**: Partial constitution compliance
- **Cons**: Half-baked console hurts UX, retraining users when Phase 2 arrives
- **Why rejected**: Better to ship no console than bad console

### Alternative 3: External Console Project (rejected)
- **Pros**: Separate repository, independent development
- **Cons**: Constitution requires "built-in" console, split maintenance burden
- **Why rejected**: Violates constitution requirement for "built-in"

### Alternative 4: Phased Delivery (ACCEPTED) ✅
- **Pros**: Fast MVP, validated architecture, resource efficient
- **Cons**: Temporary constitution gap
- **Why accepted**: Best balance of speed, quality, and constitution compliance path

---

## Review & Approval

### Stakeholders
- [x] Architecture Team: APPROVED
- [x] Product Management: APPROVED (prioritizes market validation)
- [x] Engineering Team: APPROVED (prefers phased approach)
- [ ] Constitution Review: PENDING (documented exception with commitment)

### Conditions
1. ✅ Roadmap público com dates específicos
2. ✅ README menciona "Console coming Q2 2025"
3. ✅ GitHub Project Board tracking Phase 2/3
4. ✅ ADR documentado e commitado

---

## References

- Constitution §VIII: Documentation Requirements
- Constitution §VIII linhas 604-624: Console Client 20 Languages
- Analysis Report: `/speckit.analyze` - CC3/CC4 violations
- Market precedents: AWS CLI, kubectl, Terraform console

---

**Decision**: ACCEPTED  
**Status**: ACTIVE (MVP in progress)  
**Review Date**: Q1 2025 (after MVP release)  
**Next Review**: Validate Phase 2 start date after MVP feedback
