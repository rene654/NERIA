# NERIA

**Auditable Expense Intelligence & Compliance**

NERIA is an expense and receipt compliance platform designed initially
for small and medium-sized companies. It combines structured evidence,
versioned policies, deterministic rules and, in later phases, artificial
intelligence for cases that require contextual interpretation.

NERIA provides compliance intelligence and recommendations. It does not
approve payments, release reimbursements or exercise financial authority.

## Product objective

NERIA is being designed to:

- validate expense and receipt information;
- apply versioned corporate policies;
- identify violations, uncertainty and risk signals;
- detect possible duplicates and amount mismatches;
- distinguish missing information from confirmed non-compliance;
- route cases to the appropriate human or technical process;
- preserve evidence and reasoning for every result.

## Project status

| Phase | Status |
|---|---|
| Phase 1 — Process and Policy Design | Complete |
| Phase 2 — Data Foundation | Complete |
| Phase 3 — Deterministic Rules Engine | Complete |
| Phase 4 — REST API | Not started |
| Phase 5 — AI Intelligence Layer | Not started |
| Phase 6 — Workflow and Human Review | Not started |
| Phase 7 — Evaluation and Governance | Not started |

## What is implemented

### Data foundation

- PostgreSQL 17 development environment using Docker.
- Eight ordered and reproducible database migrations.
- Organization-level relational isolation.
- Versioned policies and benchmark contracts.
- Transactional and replaceable benchmark imports.
- Canonical SHA-256 dataset hashing.
- Deterministic 300-case synthetic benchmark.
- Separate DEVELOPMENT and locked HOLDOUT families.
- Coverage for policy rules R01-R14.

### Deterministic rules engine

The current Phase 3 implementation evaluates:

- R01 — receipt requirement;
- R02 — category spending limits;
- R03 — prohibited items;
- R04 — possible duplicate expenses;
- R05 — receipt and transaction mismatch;
- R06 — expense age;
- R07 — mandatory high-value review;
- R08 — airfare class;
- R09 — required contextual information;
- R10 — policy applicability;
- R11-R14 — admission, scope, authority and technical controls.

Individual rules and final decision aggregation are implemented and
validated against the controlled synthetic benchmark. DEVELOPMENT
achieved 180/180 full decisions and HOLDOUT achieved 120/120 on its
first preserved evaluation. These benchmark results are not evidence
of production accuracy on real-world expense data.

## Current limitations

NERIA is not yet a production application. It currently does not include:

- REST API endpoints;
- OCR or document extraction;
- SAT or CFDI verification;
- LLM reasoning;
- n8n workflows;
- Power BI dashboards;
- production Row-Level Security;
- real customer data.

All benchmark information is synthetic and must not be presented as
evidence of production accuracy.

## Quick validation

```bash
source .venv/bin/activate

python -m py_compile scripts/*.py tests/*.py

PYTHONPATH=scripts python -m unittest discover \
  -s tests \
  -p 'test_*.py' \
  -v

python scripts/check_benchmark_coverage.py \
  data/generated/benchmark_300_v0_2.json
```

## Repository structure

- `db/migrations/` — ordered PostgreSQL migrations.
- `db/tests/` — database constraint tests.
- `data/fixtures/` — small validation fixtures.
- `data/generated/` — deterministic synthetic benchmarks.
- `scripts/` — generators, validators, importers and rule engines.
- `tests/` — deterministic Python tests.
- `docs/` — contracts, review evidence and closure records.

## Governance boundary

NERIA may record results, request information, route a case for human
review or request technical recovery. It must never transform an AI or
rules-engine recommendation into an automatic financial approval.
