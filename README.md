# CONTRACTOR

CONTRACTOR is a multi-tenant, contract-driven analytics runtime designed to execute
natural language queries (/ask) over real data sources with determinism, governance,
and enterprise-grade controls.

It is built around explicit contracts (ontology, entities, policies, templates),
strong separation of concerns, and a clear control plane vs data plane architecture.

---

## Why CONTRACTOR exists

Most “AI over data” systems fail in production because they:
- mix governance and execution
- rely on hidden heuristics
- blur the line between data and explanation
- lack quality gates, auditability, and rollback

CONTRACTOR was designed to solve these problems from day one.

---

## Core Principles

- **Contracts first**
  Ontology, entities, policies, templates, and quality suites are the source of truth.

- **Determinism by design**
  Same input + same bundle = same result.

- **Control Plane ≠ Data Plane**
  Governance and execution are isolated by architecture.

- **Compute-on-read**
  CONTRACTOR executes real queries against customer data.
  It does not persist domain data.

- **Multi-tenant, enterprise-ready**
  Isolation, observability, security, and billing are first-class concerns.

---

## Architecture Overview

### Control Plane
Responsible for:
- tenant management
- artifact registry (bundles)
- validation and quality gates
- version promotion (draft → candidate → current)
- secrets and connections
- audit logs

### Data Plane (Runtime)
Responsible for:
- executing /ask
- resolving ontology and planner decisions
- generating SQL
- executing queries
- formatting responses
- enforcing policies (cache, rate limits, RAG boundaries)

The runtime is stateless and tenant-aware.

---

## Artifact Model

All behavior is defined by **Bundles**, which are immutable sets of artifacts:

- ontology
- entity catalog and contracts
- policies (cache, quality, rag, security, limits)
- templates
- quality suites

Each bundle has a unique `bundle_id`.
Aliases (`draft`, `candidate`, `current`) point to bundles atomically.

---

## Multi-Tenant Model

- Every request is scoped by `tenant_id`
- Cache, metrics, limits, and secrets are tenant-scoped
- Runtime supports:
  - shared pool (default)
  - dedicated runtime (enterprise)

---

## Security & Privacy

- Privacy-by-design (LGPD/GDPR aligned)
- No persistence of customer domain data
- Mandatory redaction in logs and traces
- Secrets managed via secure backends (KMS/Secrets Manager)
- Templates executed in sandboxed environments

---

## Quality & Reliability

- Quality Gates are mandatory for promotion
- Routing accuracy, execution validity, and security checks are enforced
- SLOs and Incident Management are defined explicitly
- Rollback is a first-class operation

---

## Maturity Stages

CONTRACTOR evolves through explicit stages:

- Stage 0 — Foundation
- Stage 1 — MVP (Early Adopters)
- Stage 2 — Production Ready
- Stage 3 — Enterprise Ready
- Stage 4 — Platform Ecosystem

Features cannot skip stages.

---

## Reference Tenant

Araquem is used as the **reference tenant (tenant zero)**:
- regression testing
- benchmark
- architectural validation

The platform never depends on Araquem, but Araquem validates the platform.

---

## Documentation

- `docs/FOUNDATION.md` — Guardrails v0
- `docs/ADR/` — Architecture Decision Records
- `docs/C4/` — Architecture diagrams
- `docs/SECURITY/` — Threat model and data handling

---

## Non-Goals

- No heuristic-based behavior
- No hidden business logic in code
- No domain-specific assumptions
- No persistence of customer data

---

## Status

Current stage: **Stage 0 — Foundation**

CONTRACTOR is under active development and not yet a commercial product.
