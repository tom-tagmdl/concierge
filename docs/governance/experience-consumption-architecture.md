# Experience Consumption Architecture

## Purpose

This document defines the authoritative E6 experience consumption architecture baseline.

This document is architecture and governance only.

This document does not define experience selection, routing, execution planning, orchestration logic, recommendation logic, or experience lifecycle engines.

## Authority Relationship

Experience Governance Authority remains external through HTBW experience authorities.

Experience Definition Authority remains external through HTBW experience authorities.

Experience Contract Authority remains external through HTBW contract authority.

Experience Model Authority remains external through HTBW model authority.

Coordinator Consumption Authority:

- consumes experiences
- integrates experience consumption with capability outputs

Coordinator consumes experiences.

Coordinator does not own experiences.

## E5 Dependencies

E6 consumes:

- `docs/governance/capability-projection-consumption-readiness-review.md`
- `docs/governance/capability-consumption-architecture.md`
- `docs/governance/capability-resolution-pipeline-architecture.md`
- `docs/governance/room-aware-capability-consumption-architecture.md`
- `docs/governance/merged-room-capability-consumption-architecture.md`
- `docs/governance/composite-room-capability-consumption-architecture.md`
- `docs/governance/guest-aware-capability-filtering-architecture.md`
- `docs/governance/capability-explainability-framework.md`
- `docs/governance/capability-discovery-foundation.md`
- `docs/governance/capability-diagnostics-surface.md`

E6 consumes all.

E6 redefines none.

## Experience Authority Inputs

E6 consumes:

- HTBW #18 Experience Model ADR
- HTBW #30 Experience Contract
- HTBW #43 Experience Model

These remain authoritative.

## Experience Consumption Model

Experience consumption means Coordinator consumes governed experience outputs and preserves external experience ownership.

Coordinator consumption means Coordinator uses experience outputs as governed inputs for downstream household-facing behavior.

Consumption participation means Coordinator may reference, present, and carry forward experience outputs without taking ownership of experience meaning.

This section defines architecture only.

## Experience Lifecycle Participation Model

Coordinator participates in experience lifecycle activities by consuming governed lifecycle outputs and preserving source-of-record boundaries.

Coordinator participates.

Coordinator does not govern lifecycle.

This section defines architecture only.

## Experience Access Pattern Model

Coordinator accesses experiences through governed experience references and experience identifiers.

Experience references participate as stable references to governed experience outputs.

Experience identities participate as stable identifiers for consumed experience outputs.

This section defines architecture only.

## Coordinator Integration Model

Capability consumption outputs participate in experience consumption as upstream context.

Room-aware outputs participate as room-scoped context.

Guest-aware outputs participate as guest-safe visibility and restriction context.

Explainability participates as bounded explanation references.

Diagnostics participates as bounded trace and troubleshooting references.

Discovery participates as discovery-context references for experience surfaces.

This section defines architecture only.

## Capability -> Experience Foundation

Capability Output
  -> Experience Consumption
  -> Experience Eligibility
  -> Experience Selection Input

This foundation is architecture only.

Do not define selection logic.

## Room-Aware Experience Participation

Room-aware capability outputs participate in experience consumption by narrowing or qualifying experience visibility and availability context.

This section defines architecture only.

## Merged-Room Experience Participation

Merged-room capability outputs participate in experience consumption by carrying merged-room context into experience visibility and availability inputs.

This section defines architecture only.

## Composite-Room Experience Participation

Composite-room capability outputs participate in experience consumption by carrying hierarchy-aware and scope-aware context into experience visibility and availability inputs.

Hierarchy-aware outputs participate as governed scope context.

This section defines architecture only.

## Guest-Aware Experience Participation

Guest-aware capability outputs participate in experience consumption by applying guest-safe visibility and restriction context to experience inputs.

Eligibility participation occurs through governed guest-safe context and downstream experience availability decisions.

This section defines architecture only.

## Explainability Participation

Reference:

- `docs/governance/capability-explainability-framework.md`

Capability explainability participates in experience consumption by providing lineage and ownership-boundary references for consumed capability outputs.

## Diagnostics Participation

Reference:

- `docs/governance/capability-diagnostics-surface.md`

Capability diagnostics participates in experience consumption by providing trace and troubleshooting references for consumed capability outputs.

## Discovery Participation

Reference:

- `docs/governance/capability-discovery-foundation.md`

Capability discovery participates in experience consumption by providing discoverable capability context for experience surfaces.

## Asset Intelligence Boundary

Experience consumption may consume capability outputs that consumed Asset Intelligence-informed context.

Coordinator does not own Asset Intelligence meaning.

Coordinator does not own Asset Intelligence outputs.

Coordinator does not reinterpret:

- advisories
- risk outputs
- human_health outputs
- significance
- relevance

as experience-owned truth.

## Experience Ownership Protection

Coordinator does not own:

- experience governance
- experience definitions
- experience categories
- experience contracts
- experience models

Coordinator consumes all of the above.

## Nonexistent Output Protection

Current implementation does not expose:

- significance assessments
- relevance assessments
- asset narratives
- room-health narratives
- collection narratives
- environmental narratives
- priority-context outputs

E6 must not assume these outputs exist.

## Ownership Matrix

| Area | Authority | Coordinator Role | Status |
|---|---|---|---|
| Experience Governance | HTBW experience governance | Consumer | PASS |
| Experience Definitions | HTBW experience authorities | Consumer | PASS |
| Experience Categories | HTBW experience authorities | Consumer | PASS |
| Capability Outputs | HTBW capability governance | Consumer | PASS |
| Asset Intelligence Outputs | Asset Intelligence | Consumer | PASS |
| Explainability | governed explainability artifacts | Consumer | PASS |
| Diagnostics | governed diagnostics artifacts | Consumer | PASS |
| Discovery | governed discovery artifacts | Consumer | PASS |

## Dependency Mapping

| Downstream E6 Consumer | E6 Output Dependency |
|---|---|
| #92 | experience category presentation and surface composition |
| #93 | room-aware experience handling |
| #94 | merged-room experience handling |
| #95 | composite-room experience handling |
| #96 | guest-aware experience handling |
| #97 | experience explainability integration |
| #98 | experience diagnostics integration |
| #99 | experience discovery integration |

## Risks

- experience ownership drift
- experience governance drift
- capability ownership drift
- Asset Intelligence meaning drift
- eligibility ambiguity
- room-awareness drift
- explainability divergence

## Validation Outline

### 1. Grounding Summary

This baseline grounds E6 experience consumption in HTBW experience authorities, the completed E5 capability consumption baseline, and the preserved CP00 through CP9 ownership boundaries.

### 2. Sources Reviewed

Reviewed:

- HTBW ADR-007
- HTBW #18 Experience Model ADR
- HTBW #30 Experience Contract
- HTBW #43 Experience Model
- docs/governance/capability-projection-consumption-readiness-review.md
- docs/governance/capability-consumption-architecture.md
- docs/governance/capability-resolution-pipeline-architecture.md
- docs/governance/room-aware-capability-consumption-architecture.md
- docs/governance/merged-room-capability-consumption-architecture.md
- docs/governance/composite-room-capability-consumption-architecture.md
- docs/governance/guest-aware-capability-filtering-architecture.md
- docs/governance/capability-explainability-framework.md
- docs/governance/capability-discovery-foundation.md
- docs/governance/capability-diagnostics-surface.md

### 3. HTBW Experience Authority Validation

HTBW experience authority remains external and authoritative through:

- #18
- #30
- #43

Coordinator consumes these authorities and does not own them.

### 4. CP00 Validation

CP00 remains the explicit Asset Intelligence boundary authority and is preserved as external to Coordinator experience ownership.

### 5. CP1 Validation

CP1 remains preserved as the base capability consumption foundation feeding later experience consumption.

### 6. CP2 Validation

CP2 remains preserved with explicit nonexistent-output protection and no significance or relevance assumptions.

### 7. CP3 Validation

CP3 remains preserved as the room-aware capability consumption foundation for downstream experience participation.

### 8. CP4 Validation

CP4 remains preserved as the merged-room capability consumption foundation for downstream experience participation.

### 9. CP5 Validation

CP5 remains preserved as the composite-room capability consumption foundation for downstream experience participation.

### 10. CP6 Validation

CP6 remains preserved as the guest-aware capability filtering foundation for downstream experience participation.

### 11. CP7 Validation

CP7 remains preserved as the explainability foundation for downstream experience participation.

### 12. CP8 Validation

CP8 remains preserved as the discovery foundation for downstream experience participation.

### 13. CP9 Validation

CP9 remains preserved as the diagnostics foundation for downstream experience participation.

### 14. Experience Consumption Model Validation

Experience consumption is defined as Coordinator using governed experience outputs as inputs without taking ownership of experience meaning.

### 15. Lifecycle Participation Validation

Lifecycle participation is limited to consuming governed lifecycle outputs while preserving source-of-record boundaries.

### 16. Access Pattern Validation

Access occurs through governed experience references and experience identifiers.

### 17. Coordinator Integration Validation

Coordinator integration is bounded to capability outputs, room-aware context, guest-aware context, explainability, diagnostics, and discovery references.

### 18. Capability→Experience Foundation Validation

The capability-to-experience foundation is documented as an upstream-to-downstream consumption relationship only.

### 19. Room-Aware Participation Validation

Room-aware capability outputs participate in experience consumption by narrowing or qualifying visibility and availability context.

### 20. Merged-Room Participation Validation

Merged-room capability outputs participate in experience consumption by carrying merged-room context into experience inputs.

### 21. Composite-Room Participation Validation

Composite-room capability outputs participate in experience consumption by carrying hierarchy-aware and scope-aware context into experience inputs.

### 22. Guest-Aware Participation Validation

Guest-aware capability outputs participate in experience consumption by applying guest-safe visibility and restriction context.

### 23. Explainability Participation Validation

Explainability participates by providing lineage and ownership-boundary references for consumed capability outputs.

### 24. Diagnostics Participation Validation

Diagnostics participates by providing trace and troubleshooting references for consumed capability outputs.

### 25. Discovery Participation Validation

Discovery participates by providing discoverable capability context for experience surfaces.

### 26. Asset Intelligence Boundary Validation

Asset Intelligence remains externally owned, and Coordinator does not reinterpret its outputs as experience-owned truth.

### 27. Experience Ownership Validation

Coordinator does not own experience governance, experience definitions, experience categories, experience contracts, or experience models.

### 28. Ownership Drift Analysis

No ownership drift is introduced in this baseline. The validated boundary remains: Coordinator consumes experiences and does not own them.

### 29. Dependency Mapping

Downstream E6 work remains mapped to the dependency areas already captured in the ownership matrix and dependency mapping sections.

### 30. Readiness Determination

Experience Consumption Architecture is READY.

## Ownership Preservation Review

Result: PASS

Validated:

- experience governance ownership preserved
- experience definition ownership preserved
- capability governance ownership preserved
- Asset Intelligence ownership preserved
- room truth ownership preserved
- scope truth ownership preserved
- hierarchy truth ownership preserved

No ownership drift introduced in this E6 architecture baseline.

## Readiness Statement

Experience Consumption Architecture is READY.

This document becomes the authoritative experience consumption baseline for E6.