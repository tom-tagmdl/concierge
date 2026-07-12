# Restoration Suppression and Prioritization Framework

## 1. Purpose

Define the authoritative E8-ER7 architecture baseline for suppression and prioritization consumption during restoration-consumption decisions.

This document is architecture and governance only.

This document does not implement restoration behavior, restoration prioritization algorithms, restoration suppression algorithms, restoration eligibility algorithms, restoration execution, diagnostics features, or explainability features.

## 2. Scope Reviewed

Reviewed authorities and governance inputs:

- HTBW #32
- HTBW #39
- HTBW #47
- HTBW #50
- Concierge #110
- ER1 Restoration Consumption Architecture
- ER5 Guest and Unknown Restoration Consumption
- ER6 Multi-Occupant Restoration Conflict Policy

Authority-order treatment:

- ADRs, contracts, and models are architecture authority.
- Existing implementation is supporting evidence only.
- Issues (#32, #39, #47, #50, #110) are execution inputs and are not architecture authority.

## 3. Restoration Authority Validation

Validation scope:

- restoration ownership
- restoration governance
- restoration eligibility ownership
- restoration confidence ownership
- restoration prioritization ownership
- restoration suppression ownership

Result: PASS

Validated statements:

- Restoration ownership remains in HTBW.
- Restoration governance remains in HTBW.
- Restoration eligibility ownership remains in HTBW.
- Restoration confidence ownership remains in HTBW.
- Restoration prioritization ownership remains in HTBW.
- Restoration suppression ownership remains in HTBW.

## 4. Suppression Governance Validation

Validation scope:

- suppression policy authority
- suppression ownership
- suppression governance

Result: PASS

Validated statements:

- Suppression policy authority remains external.
- Suppression ownership remains external to Coordinator.
- Suppression governance remains external to Coordinator.
- Coordinator consumes suppression outcomes and does not define suppression policy.

## 5. Prioritization Governance Validation

Validation scope:

- prioritization authority
- prioritization ownership
- prioritization governance

Result: PASS

Validated statements:

- Prioritization authority remains external.
- Prioritization ownership remains external to Coordinator.
- Prioritization governance remains external to Coordinator.
- Coordinator consumes prioritization outcomes and does not define prioritization policy.

## 6. ER1 Architecture Alignment Review

Result: PASS

ER7 aligns with ER1 restoration ownership boundaries, lifecycle boundaries, and restoration governance constraints.

## 7. ER5 Architecture Alignment Review

Result: PASS

ER7 consumes ER5 guest-safe behavior, unknown occupant behavior, fallback behavior, and privacy-safe behavior outputs without redefining ER5.

## 8. ER6 Architecture Alignment Review

Result: PASS

ER7 consumes ER6 multi-occupant conflict participation, suppression participation, conflict outcomes, and deterministic conflict outputs without redefining conflict governance.

## 9. Suppression Consumption Framework

Validation scope:

- suppression consumption
- suppression outcomes
- suppression participation
- suppression influence points

Result: PASS

Framework architecture:

- suppression consumption: Coordinator consumes governed suppression outcomes from restoration context and policy-governed inputs.
- suppression outcomes: consumed as bounded decision inputs to restoration-consumption participation.
- suppression participation: consumed across room-aware, person-aware, guest-safe, and multi-occupant contexts.
- suppression influence points: consumed at restoration participation boundaries, deferment boundaries, and neutral fallback boundaries.

## 10. Quiet-Hours Suppression Review

Validation scope:

- quiet-hours suppression participation
- quiet-hours consumption
- quiet-hours lineage

Result: PASS

Validated statements:

- Quiet-hours suppression outcomes are consumed.
- Quiet-hours participation is consumed as policy-governed input.
- Quiet-hours lineage is preserved through suppression outcome references.
- Coordinator does not define quiet-hours policy.

## 11. Posture-Aware Suppression Review

Validation scope:

- posture-aware participation
- posture-aware suppression consumption
- posture-aware lineage

Result: PASS

Posture-aware suppression participation is consumed as governed posture outcome context with posture-aware suppression lineage preserved.

## 12. Occupancy-Confidence Suppression Review

Validation scope:

- occupancy-confidence participation
- confidence-based suppression consumption
- confidence lineage

Result: PASS

Occupancy-confidence suppression participation is consumed as governed confidence outcome context with confidence lineage preserved.

## 13. Identity-Confidence Suppression Review

Validation scope:

- identity-confidence participation
- suppression consumption
- confidence lineage

Result: PASS

Identity-confidence suppression participation is consumed as governed identity-confidence outcomes with confidence lineage preserved.

## 14. Guest-Safe Suppression Review

Validation scope:

- guest-safe suppression participation
- privacy-safe suppression participation
- fallback suppression participation

Result: PASS

Guest-safe, privacy-safe, and fallback suppression participation are consumed as governed outcomes and remain ownership-preserving.

## 15. Prioritization Consumption Framework

Validation scope:

- restoration prioritization participation
- prioritization consumption
- prioritization influence
- prioritization lineage

Result: PASS

Framework architecture:

- restoration prioritization participation is consumed through governed prioritization outcomes.
- prioritization consumption is bounded and ownership-preserving.
- prioritization influence participates as governed input into restoration-consumption paths.
- prioritization lineage is preserved through prioritization outcome references.

Validated statement: Coordinator consumes prioritization outcomes and does not define prioritization policy.

## 16. Higher-Priority Experience Review

Validation scope:

- higher-priority experience participation
- prioritization influence
- restoration deferment participation

Result: PASS

Higher-priority experience participation and restoration deferment are consumed through governed prioritization outcomes and bounded deferment participation references.

## 17. Deterministic Behavior Review

Validation scope:

- suppression outcomes
- prioritization outcomes
- deferred restoration
- canceled restoration
- guest-safe suppression
- confidence-based suppression

Result: PASS

Deterministic requirements:

- same governed suppression and prioritization inputs produce the same restoration-consumption participation outcome.
- deferred and canceled restoration participation remains deterministic and traceable.
- guest-safe and confidence-based suppression participation remains deterministic and ownership-preserving.

## 18. Explainability Path Review

Validation scope:

- suppression outcomes
- prioritization outcomes
- deferment outcomes
- restoration avoidance outcomes

Result: PASS

Explainability path support is preserved through bounded references for suppression outcomes, prioritization outcomes, deferment outcomes, and restoration-avoidance outcomes.

## 19. Diagnostics Readiness Review

Validation scope:

- suppression outcomes
- prioritization outcomes
- confidence inputs
- deferment outcomes
- restoration-consumption outcomes

Result: PASS

Traceability is available for suppression outcomes, prioritization outcomes, confidence inputs, deferment outcomes, and restoration-consumption outcomes.

## 20. Ownership Validation

Validation scope:

Coordinator does not own:

- restoration
- restoration prioritization
- restoration suppression
- restoration eligibility
- restoration confidence
- significance
- relevance
- priority context

Result: PASS

Coordinator consumes all listed domains and owns none of them.

## 21. Ownership Drift Analysis

Validation scope:

No transfer of:

- restoration governance
- suppression governance
- prioritization governance
- restoration eligibility
- restoration confidence
- restoration definitions

Result: PASS

No ownership drift identified.

## 22. Downstream Guidance

Provide constraints only. Do not pre-design ER8 through ER10.

- ER8: explainability framework must consume ER7 suppression and prioritization lineage, deferment lineage, and restoration-avoidance references.
- ER9: diagnostics framework must consume ER7 suppression traces, prioritization traces, confidence-input traces, and deferment traces.
- ER10: readiness review must validate suppression and prioritization ownership preservation, deterministic behavior coverage, explainability path coverage, diagnostics readiness, and no ownership drift.

## 23. ER7 Baseline Determination

Result: PASS

Suppression and prioritization architecture is sufficiently documented for downstream E8 work.

## 24. Final Determination

E8-ER7 RESTORATION SUPPRESSION AND PRIORITIZATION FRAMEWORK

APPROVED AS THE AUTHORITATIVE BASELINE

FOR RESTORATION SUPPRESSION AND PRIORITIZATION CONSUMPTION
