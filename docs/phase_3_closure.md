# Phase 3 Closure — Deterministic Rules Engine
Date: 2026-09-21
## Status
**COMPLETE**
Phase 3 implements and validates NERIA's deterministic expense
compliance and decision engine.
## Implemented components
- Admission Engine for R11-R14.
- Rules Engine for R01-R10.
- Decision Engine for compliance, risk, routing, assessment
  completeness and permitted actions.
- Protected benchmark evaluator.
- DEVELOPMENT and HOLDOUT evaluation protocol.
- Engine and dataset hashing for reproducibility.
- Metamorphic relationship testing.
- Explicit financial-authority boundary.
## Rules covered
- R01 — Receipt requirement.
- R02 — Category spending limits.
- R03 — Prohibited items.
- R04 — Possible duplicates.
- R05 — Receipt/transaction amount mismatch.
- R06 — Expense age.
- R07 — Mandatory high-value review.
- R08 — Airfare class.
- R09 — Missing critical context.
- R10 — Policy applicability.
- R11 — Invalid input.
- R12 — Out of scope.
- R13 — Financial authority denied.
- R14 — Technical failure.
## DEVELOPMENT evaluation
- Cases: 180
- Full decisions correct:
  180/180
- Rule states correct:
  324/324
- Decision accuracy:
  100.00%
- Rule-state accuracy:
  100.00%
- Decision mismatches:
  0
- Rule mismatches:
  0
DEVELOPMENT was formally frozen before HOLDOUT evaluation.
Freeze tag:
`phase3-dev-freeze-v1`
## HOLDOUT evaluation
- Cases: 120
- Full decisions correct:
  120/120
- Rule states correct:
  216/216
- Decision accuracy:
  100.00%
- Rule-state accuracy:
  100.00%
- Decision mismatches:
  0
- Rule mismatches:
  0
The first HOLDOUT result was preserved without changing the engine.
HOLDOUT tag:
`phase3-holdout-eval-v1`
## Combined benchmark evidence
- Synthetic benchmark cases: 300
- Full decisions correct: 300/300
- Evaluated rule states correct: 540/540
- DEVELOPMENT cases: 180
- HOLDOUT cases: 120
## Cryptographic identity
Dataset SHA-256:
`fd7e61d316d3ddbd84b730f33e85978102b756d0bbd95612e9465928638731d7`
Engine SHA-256:
`3b2a1c51f588aae11159c0fb9ebca53112497928fef419fbdac5ec1ebcb91c35`
Engine version:
`deterministic-rules-v1.0.0`
Dataset version:
`0.2.1-300`
## Governance boundary
NERIA may:
- evaluate expense-policy compliance;
- identify violations, uncertainty and risk signals;
- request information;
- request policy clarification;
- route cases to human review;
- record screening results;
- request technical recovery.
NERIA may not:
- approve payments;
- release reimbursements;
- exercise financial authority;
- automatically accuse a person of fraud.
## Interpretation
The 100% results apply to NERIA's controlled synthetic benchmark.
They are not evidence of 100% accuracy on real-world expense data.
Production performance must later be measured using appropriate
real-world validation and governance controls.
## Phase 3 conclusion
Phase 3 acceptance is satisfied.
The deterministic engine is complete and may now serve as the trusted
rules layer beneath later API, workflow and AI components.
## Next phase
**Phase 4 — REST API**
The next objective is to expose the deterministic decision capability
through a controlled application interface without weakening the
authority, auditability or reproducibility boundaries established in
Phases 1-3.
