# Phase 3 — HOLDOUT Evaluation
Date: 2026-09-21
## Governance statement
This is the first formal HOLDOUT evaluation performed after the
DEVELOPMENT freeze.
The deterministic engine was not modified after the DEVELOPMENT
results were frozen.
## Frozen engine
- DEVELOPMENT freeze tag: `phase3-dev-freeze-v1`
- Evaluation commit before HOLDOUT: `c21fcb8960d38c46582207cac79b991427d8c7a7`
- Engine version: `deterministic-rules-v1.0.0`
- Dataset version: `0.2.1-300`
## Cryptographic identity
- Dataset SHA-256:
  `fd7e61d316d3ddbd84b730f33e85978102b756d0bbd95612e9465928638731d7`
- Engine SHA-256:
  `3b2a1c51f588aae11159c0fb9ebca53112497928fef419fbdac5ec1ebcb91c35`
## HOLDOUT results
- Cases: 120
- Full decisions correct:
  120/120
- Full decision accuracy:
  100.00%
- Rule states correct:
  216/216
- Rule-state accuracy:
  100.00%
- Decision mismatches:
  0
- Rule mismatches:
  0
## Interpretation rule
These results are preserved as observed.
The engine must not be modified to improve this same HOLDOUT
evaluation.
Any later correction belongs to a new engine version and a new
evaluation protocol.
