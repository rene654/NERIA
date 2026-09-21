# NERIA Phase 2 — Data Foundation Closure

## Status

COMPLETE — Phase 2: Data Foundation

Closure date: 2026-09-18

## Objective

Build a reproducible, auditable and tenant-aware data foundation for
corporate expense and receipt compliance evaluation.

Phase 2 prepares the data required to develop and evaluate NERIA. It does
not implement the deterministic decision engine or artificial intelligence.

## Delivered capabilities

- PostgreSQL 17 development environment in Docker.
- Eight ordered and reproducible database migrations.
- Core structures for organizations, employees, merchants, expenses,
  versions, receipts, evidence, policies and duplicate observations.
- Relational tenant isolation through `organization_id`.
- Isolated benchmark structures for inputs, labels, rules, actions,
  history and case relationships.
- Versioned policies, rules and benchmark contracts.
- Technical rejection of prohibited financial-authority actions.
- Transactional and replaceable benchmark imports.
- Canonical SHA-256 dataset hashing.
- Deterministic benchmark generation from a fixed seed.
- Separate DEVELOPMENT and HOLDOUT families.
- Automated benchmark coverage and leakage auditing.

## Database migrations

1. `001_core_foundation.sql`
2. `002_policy_evidence.sql`
3. `003_benchmark_schema.sql`
4. `004_benchmark_inputs.sql`
5. `005_label_authority.sql`
6. `006_organization_tenancy.sql`
7. `007_benchmark_assurance_contract.sql`
8. `008_benchmark_rule_outcomes.sql`

All migrations were applied successfully from an empty database.

## Constraint evidence

Eight SQL test suites validate 66 negative and positive database controls.

The controls include:

- orphan and invalid operational records;
- amounts, currencies, categories and dates;
- receipts, evidence and duplicate observations;
- benchmark manifests, inputs, labels and rule versions;
- prohibited financial actions;
- cross-organization references;
- assurance metadata and scoped relationships;
- R01-R14 outcomes, routes and policy-clarification actions.

All suites complete inside transactions and leave no test residue.

## Benchmark evidence

| Measure | Result |
|---|---:|
| Total cases | 300 |
| DEVELOPMENT cases | 180 |
| HOLDOUT cases | 120 |
| Total families | 150 |
| Leaked families | 0 |
| Incorrectly sized families | 0 |
| Case inputs | 300 |
| Labels | 300 |
| Label-rule results | 540 |
| Permitted actions | 310 |
| Case relationships | 150 |
| Rules covered | R01-R14 |
| Categories covered | 6 |
| Routes covered | 6 |

Relationship coverage:

- 40 `ADVERSARIAL`
- 50 `BOUNDARY_VARIANT`
- 50 `COUNTERFACTUAL`
- 10 `DUPLICATE_VARIANT`

## Reproducibility identity

- Dataset: `NERIA_BENCHMARK_300`
- Dataset version: `0.2.1-300`
- Contract version: `v0.2`
- Generator version: `deterministic-0.2.0`
- Policy: `CORPORATE_EXPENSE v1.0`
- Source migration: `008`
- Seed: `20260918`
- Canonical dataset hash:
  `fd7e61d316d3ddbd84b730f33e85978102b756d0bbd95612e9465928638731d7`
- Benchmark implementation commit: `87892f0`
- Phase 3 validation correction: R03 meal fixtures include `attendee_count=1` so R02 is fully evaluable while R03 remains the isolated changed control.

Two independent generations produced identical files and the same canonical
hash. Replacing the imported dataset twice preserved one manifest, 300 cases
and the same hash.

## Review basis

The initial 12-case increment was manually reviewed and accepted before
scaling. The 300-case benchmark expands controlled scenario templates and
validates their structure, relationships, coverage and expected labels
automatically.

The 300 cases are not 300 independent human reviews and must not be presented
as real customer transactions or evidence of production accuracy.

## Authority boundary

Benchmark labels may recommend recording, requesting information, routing,
retrying or raising a technical alert.

They cannot approve payments, release reimbursements or exercise financial
authority. PostgreSQL and the Python validator reject prohibited actions.

## Deferred work

Phase 2 does not include:

- deterministic rule execution;
- OCR or document extraction;
- SAT or CFDI verification;
- LLM reasoning;
- REST APIs;
- n8n or Power BI;
- production Row-Level Security;
- real customer data;
- measured production accuracy.

These exclusions are intentional and do not block Data Foundation closure.

## Closure decision

Phase 2 acceptance criteria are satisfied.

The next phase is Phase 3 — Deterministic Rules Engine. Phase 3 must calculate
results from benchmark inputs and compare them against the stored labels
without exposing HOLDOUT labels to the implementation process.
