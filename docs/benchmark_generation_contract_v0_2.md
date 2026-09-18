# NERIA Benchmark Generation Contract v0.2
## Status
ACCEPTED — Phase 2: Data Foundation
This contract was reviewed and accepted before implementing migration 007 and the deterministic generator.
## Business objective
Generate auditable synthetic corporate-expense cases for medium-sized companies in Mexico.
The benchmark must test expense and receipt compliance, risk, uncertainty and routing without giving AI financial authority.
## Product boundary
NERIA evaluates expenses, receipts and supporting evidence.
It does not:
- approve payments;
- release reimbursements;
- replace an ERP;
- issue corporate cards;
- make fraud accusations;
- treat AI output as verified evidence.
## Generation pipeline
1. Configuration defines seed, policy version and target case count.
2. Generator creates synthetic cases and expected labels.
3. Validator rejects structural, authority and leakage defects.
4. Importer writes the accepted dataset in one transaction.
5. PostgreSQL enforces relational integrity.
6. Evaluation reads labels separately from model inputs.
## Determinism requirements
The same configuration and random seed must produce:
- identical case references;
- identical stable UUIDs;
- identical money values;
- identical family assignments;
- identical DEVELOPMENT/HOLDOUT splits;
- identical canonical dataset hash.
The generator must not use the current clock, random UUIDs or floating-point money.
Money is serialized as strings with exactly two decimal places.
## Existing required structures
Every dataset contains:
- `manifest`;
- `cases`.
Every case contains:
- identity and split;
- family and variant type;
- employee and merchant keys;
- category, amount, currency and date;
- structured input;
- explicit history;
- expected label stored outside model input.
## Contract additions planned for v0.2
### Manifest
Add:
- `contract_version`
### Case
Add:
- `organization_profile_key`
- `jurisdiction_country`
These identify a synthetic business profile. They must not reference or contaminate operational customer data.
### Case relationship
A case may contain an optional `relationship` object:
- `relationship_type`
- `base_case_ref`
- `changed_fields`
- `expected_effect`
- `expected_changed_outputs`
Allowed relationship types for v0.2:
- `COUNTERFACTUAL`
- `BOUNDARY_VARIANT`
- `DUPLICATE_VARIANT`
- `ADVERSARIAL`
`POLICY_REPLAY` is postponed until NERIA has a second accepted policy version. We will not implement an unused capability.
Allowed expected effects:
- `DECISION_MUST_CHANGE`
- `DECISION_MUST_REMAIN_STABLE`
Allowed changed outputs:
- `COMPLIANCE`
- `RISK`
- `ROUTE`
- `RULE_STATES`
- `PERMITTED_ACTIONS`
Relationship requirements:
- `base_case_ref` must resolve inside the same dataset.
- Related cases must remain in the same family and split.
- A case cannot reference itself.
- `changed_fields` must contain unique JSON Pointer paths such as `/amount_mxn` or `/input/receipt_total_mxn`.
- `changed_fields` cannot be empty.
- `expected_changed_outputs` must be non-empty when the decision must change.
- `expected_changed_outputs` must be empty when the complete decision must remain stable.
### Label
Add:
- `miss_severity`
- `miss_severity_rationale`
Allowed severity values:
- `LOW`
- `MEDIUM`
- `HIGH`
- `CRITICAL`
`miss_severity` describes the business consequence of failing to detect the expected result. It does not grant authority and is not an accusation of fraud.
`miss_severity_rationale` must explain the business consequence in non-empty text. A compliant case normally uses `LOW` unless a documented control requirement justifies another value.
## Initial 12-case increment
The first generated increment will contain only DEVELOPMENT cases.
It must include:
1. Normal compliant expense.
2. Exact monetary boundary.
3. One-cent boundary violation.
4. Missing required evidence.
5. Ambiguous information.
6. Receipt and transaction mismatch within tolerance.
7. Receipt and transaction mismatch outside tolerance.
8. Base expense for duplicate comparison.
9. Duplicate or disguised duplicate variant.
10. Adversarial receipt content.
11. Authority or admission control case.
12. Multiple-signal case.
These are design targets. Exact labels must be derived from policy v1.0 before generation.
## Acceptance criteria for the 12 cases
- Exactly 12 unique case IDs and references.
- All cases use synthetic information.
- Same seed produces the same canonical hash twice.
- Money has exactly two decimals and never passes through `float`.
- Every label contains compliance, risk, route, rationale, rules and permitted actions.
- Every rule includes code, version, state and evidence reference.
- No prohibited financial action is present.
- Related cases remain in the same family and split.
- Every changed field is a unique valid JSON Pointer.
- Every related base case resolves inside the same family and split.
- Every expected decision change identifies the affected outputs.
- Every miss severity has a non-empty business rationale.
- Inputs contain no expected labels.
- PostgreSQL loads the dataset transactionally.
- Replacing the dataset preserves count and hash.
- Manual review records why every expected label is correct.
## Non-goals for this increment
The first 12 cases will not implement:
- OCR;
- real PDFs or images;
- SAT or CFDI verification;
- the deterministic rules engine;
- LLM processing;
- API endpoints;
- n8n;
- Power BI;
- production Row-Level Security;
- the final 300-case benchmark.
## Next technical step
Create migration 007 and update the Python validator/importer so every accepted v0.2 field is stored and enforced before implementing the generator.