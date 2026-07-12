# Runtime Attribution Consumption Boundary

## 1. Purpose

Define the authoritative E11-VI2 architecture baseline for runtime attribution consumption.

This document defines runtime attribution intake, runtime attribution consumption, runtime attribution lineage, and consumer responsibilities only.

This document is architecture and governance only.

This document does not define attribution truth, attribution internals, speaker resolution, confidence determination, identity resolution, diagnostics behavior, or runtime attribution implementation.

## 2. Scope Reviewed

Reviewed mandatory authorities and dependencies:

- Concierge #101
- HTBW #61
- Voice Identity contracts.md
- Voice Identity attribution.md
- Voice Identity identity-context.md
- Voice Identity diagnostics.md
- Voice Identity architecture.md

Reviewed associated Voice Identity governance and public surfaces:

- Voice Identity privacy and security guidance
- Voice Identity README
- Voice Identity public service surfaces for attribution, identity context, diagnostics, health, telemetry, and repairs

Authority-order treatment:

- ADRs, contracts, and models are architecture authority.
- Existing implementation is supporting evidence only.
- Issues (#101, #61, #151) are execution inputs and are not architecture authority.

Authority conflict review:

- No conflicts identified between VI2 outputs and authoritative ADR/contract/model artifacts.

## 3. Attribution Ownership Validation

Validation scope:

- attribution ownership
- attribution governance
- attribution authority
- attribution lifecycle authority

Result: PASS

Validated statements:

- Attribution ownership remains in Voice Identity.
- Attribution governance remains in Voice Identity.
- Attribution authority remains in Voice Identity.
- Attribution lifecycle authority remains in Voice Identity.
- Concierge consumes attribution outcomes.
- Concierge does not redefine attribution semantics.

## 4. Confidence Ownership Validation

Validation scope:

- confidence ownership
- confidence governance
- confidence authority
- confidence lifecycle authority

Result: PASS

Validated statements:

- Confidence ownership remains in Voice Identity.
- Confidence governance remains in Voice Identity.
- Confidence authority remains in Voice Identity.
- Confidence lifecycle authority remains in Voice Identity.
- Concierge consumes confidence outcomes.
- Concierge does not define confidence rules.

## 5. Speaker Identity Validation

Validation scope:

- speaker identity ownership
- speaker determination authority
- speaker lifecycle authority

Result: PASS

Validated statements:

- Speaker identity ownership remains in Voice Identity.
- Speaker determination authority remains in Voice Identity.
- Speaker lifecycle authority remains in Voice Identity.
- Concierge consumes speaker outcomes.
- Concierge does not define speaker identity.

## 6. VI1 Alignment Review

Validation scope:

- ownership matrix alignment
- contract alignment
- dependency alignment

Result: PASS

VI2 conforms to VI1 ownership matrix, contract surface, and dependency boundaries.

## 7. Runtime Attribution Architecture

Validation scope:

- attribution participation
- attribution consumption
- attribution outcomes

Result: PASS

Architecture-only runtime attribution consumption:

- attribution participation: consume Voice Identity attribution evidence as bounded runtime inputs.
- attribution consumption: consume attribution outcomes without creating attribution truth.
- attribution outcomes: preserve safe attribution outcomes and lineage references for household-facing experiences.

## 8. Runtime Attribution Intake Review

Validation scope:

- intake participation
- intake consumption
- intake lineage

Result: PASS

Runtime attribution intake remains bounded to Voice Identity safe public outputs and explicit lineage anchors.

## 9. Attribution Outcome Review

Validation scope:

- outcome participation
- outcome consumption
- outcome lineage

Result: PASS

Attribution outcomes remain consumption-only:

- Concierge consumes attribution outcomes.
- Concierge does not define attribution truth.
- Attribution outcome lineage remains tied to Voice Identity advisory evidence outputs.

## 10. Attribution Confidence Review

Validation scope:

- confidence participation
- confidence consumption
- confidence lineage

Result: PASS

Confidence participation is consumption-only:

- Coordinator consumes confidence outcomes.
- Coordinator does not define confidence rules.
- Confidence lineage remains tied to Voice Identity confidence outputs.

## 11. Speaker Outcome Review

Validation scope:

- speaker participation
- speaker outcome consumption
- speaker lineage

Result: PASS

Speaker participation is consumption-only:

- Coordinator consumes speaker outcomes.
- Coordinator does not define speaker identity.
- Speaker lineage remains tied to Voice Identity speaker-determination outputs.

## 12. Consumer Responsibility Review

Validation scope:

- attribution consumption responsibilities
- explanation responsibilities
- runtime responsibilities

Result: PASS

Consumer responsibilities:

- consume safe attribution and confidence outcomes.
- present household-facing explanations without redefining attribution truth.
- preserve runtime boundary separation between Voice Identity and Concierge.

## 13. Attribution Lineage Review

Validation scope:

- attribution lineage
- attribution traceability
- attribution consumption lineage

Result: PASS

Attribution lineage remains explicit and traceable across Voice Identity outputs and Concierge consumption paths.

## 14. Runtime Identity Relationship Review

Validation scope:

- speaker participation
- attribution participation
- confidence participation

Result: PASS

Speaker, attribution, and confidence participation remain distinct and externally owned by Voice Identity.

## 15. Diagnostics Relationship Review

Validation scope:

- diagnostics participation
- attribution diagnostics participation
- diagnostics lineage

Result: PASS

Validated statements:

- Diagnostics participation remains bounded to safe public Voice Identity diagnostics outputs.
- Attribution diagnostics participation is consumption-only.
- Diagnostics lineage remains external to Concierge ownership.

## 16. Household-Facing Attribution Review

Validation scope:

- attribution explanations
- attribution outcomes
- attribution visibility

Result: PASS

Household-facing attribution remains a Concierge experience layer over Voice Identity-owned attribution outcomes.

## 17. Contract Surface Review

Validation scope:

- provided contracts
- consumed contracts
- dependency contracts

Result: PASS

Contract surface:

- provided Voice Identity contracts/surfaces: attribution, identity context, diagnostics, health, telemetry, repairs.
- consumed Concierge contracts: Voice Identity safe public outputs only.
- dependency contracts remain explicit and privacy-safe.

## 18. Replacement Path Review

Validation scope:

- legacy attribution assumptions
- replacement attribution model
- replacement references

Result: PASS

Validated statements:

- Legacy Concierge fingerprint assumptions remain replaced by Voice Identity public attribution and identity-context references.
- Replacement references exist in Voice Identity public surfaces and VI1 alignment outputs.
- Legacy issues may only be superseded after replacement references exist.

## 19. Runtime Attribution Traceability Review

Validation scope:

- attribution traceability
- confidence traceability
- speaker traceability

Result: PASS

Traceability is preserved across attribution, confidence, and speaker participation with explicit lineage anchors.

## 20. Future Diagnostics Alignment Review

Validation scope:

- future support for E11-VI5 Runtime Attribution Diagnostics Consumption

Result: PASS

Diagnostics supportability remains aligned for downstream E11 work through safe public Voice Identity diagnostics outputs.

## 21. Future Permission Alignment Review

Validation scope:

- future support for E11-VI4 Permission Gating Consumption

Result: PASS

Permission supportability remains aligned through external permission outcomes consumed by Concierge without ownership transfer.

## 22. Future Confidence Alignment Review

Validation scope:

- future support for E11-VI3 Speaker Confidence Policy Consumption

Result: PASS

Confidence alignment remains sufficiently documented for downstream E11 work with Voice Identity ownership preserved.

## 23. Ownership Matrix Validation

Validation scope:

- attribution
- confidence
- speaker identity
- speaker resolution
- enrollment
- voiceprints
- embeddings

Result: PASS

Ownership matrix:

- attribution: Voice Identity
- confidence: Voice Identity
- speaker identity: Voice Identity
- speaker resolution: Voice Identity
- enrollment: Voice Identity
- voiceprints: Voice Identity
- embeddings: Voice Identity

## 24. Ownership Drift Analysis

Validation scope:

No transfer of:

- attribution ownership
- confidence ownership
- speaker identity ownership
- enrollment ownership
- voiceprint ownership
- embedding ownership

Result: PASS

No ownership drift identified.

## 25. VI2 Foundation Determination

Result: PASS

Runtime attribution consumption boundaries are sufficiently documented for downstream E11 work.

## 26. Final Determination

E11-VI2 RUNTIME ATTRIBUTION CONSUMPTION BOUNDARY

APPROVED AS THE AUTHORITATIVE BASELINE

FOR RUNTIME ATTRIBUTION CONSUMPTION
