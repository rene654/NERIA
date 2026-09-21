# Phase 3 — DEVELOPMENT Freeze
Date: 2026-09-21
## Purpose
This document freezes the deterministic NERIA engine before the
HOLDOUT benchmark is opened.
The DEVELOPMENT benchmark may no longer be used to modify the engine
after HOLDOUT evaluation begins.
## Frozen source
- Branch: feat/phase-3-rules-engine
- Source commit: `4fbb9916a9e6e0054e566c3a77cf5c17814fef76`
- Engine version: `deterministic-rules-v1.0.0`
- Dataset version: `0.2.1-300`
## Cryptographic identity
- Dataset SHA-256:
  `fd7e61d316d3ddbd84b730f33e85978102b756d0bbd95612e9465928638731d7`
- Engine SHA-256:
  `3b2a1c51f588aae11159c0fb9ebca53112497928fef419fbdac5ec1ebcb91c35`
## DEVELOPMENT results
- Cases: 180
- Full decisions correct:
  180/180
- Full decision accuracy:
  100.00%
- Rule states correct:
  324/324
- Rule-state accuracy:
  100.00%
- Decision mismatches:
  0
- Rule mismatches:
  0
## Governance rule
After this freeze, HOLDOUT may be evaluated once.
The deterministic engine must not be modified in response to HOLDOUT
results for the purpose of improving that evaluation.
Any later engine modification creates a new engine version and requires
a new evaluation protocol.
## Authority boundary
NERIA provides compliance intelligence and routing recommendations.
NERIA does not approve payments, release reimbursements, or exercise
financial authority.
