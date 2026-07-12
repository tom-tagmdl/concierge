# Asset Intelligence Vocabulary Consumption Architecture

## Purpose

This artifact defines how Coordinator V2 consumes Asset Intelligence-related vocabulary anchors and room-scoped Asset Intelligence output as part of E4 Room Vocabulary Consumption.

This is E4 Room Vocabulary Consumption.

This is not E5 Capability Projection Consumption.

This is not Asset Intelligence governance.

This is not runtime implementation.

This artifact defines how room-aware asset vocabulary is resolved and how Coordinator may hand off to or retrieve existing Asset Intelligence-produced descriptive, advisory, status, risk, and human_health output after E4 resolution.

## Authority and Sources

Authority order:

1. ADRs
2. Contracts
3. Models
4. Existing implementation
5. GitHub issue

GitHub Issue #190 was read last.

### ADRs Reviewed

- `homes_that_behave_well/docs/architecture/adr-coordinator-v2-governance.md`
- `homes_that_behave_well/docs/architecture/adr-room-vocabulary-governance.md`
- `homes_that_behave_well/docs/architecture/canonical-architecture.md`
- `homes_that_behave_well/docs/architecture/concierge-runtime-architecture.md`
- `homes_that_behave_well/docs/architecture/system-flow.md`

### Contracts Reviewed

- `homes_that_behave_well/docs/contracts/asset-intelligence-contract.md`
- `homes_that_behave_well/docs/contracts/room-vocabulary-registry-contract.md`
- `homes_that_behave_well/docs/contracts/room-interaction-contract.md`
- `homes_that_behave_well/docs/contracts/concierge-contract.md`
- `homes_that_behave_well/docs/contracts/service-contracts.md`
- `homes_that_behave_well/docs/contracts/experience-projection-contract.md`

### Models Reviewed

- `homes_that_behave_well/docs/models/asset-model.md`
- `homes_that_behave_well/docs/models/environment-model.md`
- `homes_that_behave_well/docs/models/room-vocabulary-registry-model.md`

### Concierge Governance Documents Reviewed

- `docs/governance/coordinator-v2-foundation-summary.md`
- `docs/governance/room-context-aware-vocabulary-consumption-architecture.md`
- `docs/governance/vocabulary-explainability-framework.md`
- `docs/governance/vocabulary-discovery-framework.md`
- `docs/governance/vocabulary-diagnostics-framework.md`
- `docs/governance/e4-vocabulary-consumption-readiness-review.md`
- `docs/governance/concierge-v1-outcome-preservation-baseline.md`
- `docs/governance/v1-to-v2-capability-parity-matrix.md`
- `docs/governance/v1-outcome-regression-checklist.md`
- `docs/governance/v1-preservation-readiness-review.md`
- `docs/governance/merged-room-outcome-preservation-contract.md`
- `docs/governance/execution-hierarchy-outcome-preservation-contract.md`

### Concierge Development Documents Reviewed

- `docs/development/architecture-guardrails.md`
- `docs/development/implementation-checklist.md`

### Implementation Evidence Reviewed

Asset Intelligence:

- `asset_intelligence/README.md`
- `asset_intelligence/custom_components/asset_intelligence/__init__.py`
- `asset_intelligence/custom_components/asset_intelligence/advisory.py`
- `asset_intelligence/custom_components/asset_intelligence/asset_entity.py`
- `asset_intelligence/custom_components/asset_intelligence/binary_sensor.py`
- `asset_intelligence/custom_components/asset_intelligence/coordinator.py`
- `asset_intelligence/custom_components/asset_intelligence/diagnostics.py`
- `asset_intelligence/custom_components/asset_intelligence/document_models.py`
- `asset_intelligence/custom_components/asset_intelligence/document_storage.py`
- `asset_intelligence/custom_components/asset_intelligence/environment.py`
- `asset_intelligence/custom_components/asset_intelligence/evaluation.py`
- `asset_intelligence/custom_components/asset_intelligence/models.py`
- `asset_intelligence/custom_components/asset_intelligence/panel.py`
- `asset_intelligence/custom_components/asset_intelligence/sensor.py`
- `asset_intelligence/custom_components/asset_intelligence/storage.py`
- `asset_intelligence/custom_components/asset_intelligence/services.yaml`
- `asset_intelligence/custom_components/asset_intelligence/services/document_retrieval.py`
- `asset_intelligence/custom_components/asset_intelligence/helpers/document_resolver.py`
- `asset_intelligence/custom_components/asset_intelligence/docs/asset_intelligence.md`
- `asset_intelligence/custom_components/asset_intelligence/docs/asset_intelligence_examples.md`
- `asset_intelligence/custom_components/asset_intelligence/docs/asset_intelligence_troubleshooting.md`
- `asset_intelligence/custom_components/asset_intelligence/docs/quality_scale_audit.md`
- `asset_intelligence/custom_components/asset_intelligence/frontend/panel.js`
- `asset_intelligence/custom_components/asset_intelligence/frontend/panel_v5.js`

Concierge:

- `custom_components/concierge/models.py`
- `custom_components/concierge/panel.py`
- `custom_components/concierge/frontend/panel.js`
- `custom_components/concierge/services.yaml`

## Scope

This artifact covers:

- asset label resolution
- asset type/category resolution
- asset identity/name metadata used as resolution context
- room-context application
- Concierge `asset_groups` as room-scoped vocabulary configuration where currently implemented
- handoff to Asset Intelligence-authored answer content after resolution
- retrieval or reference of Asset Intelligence-produced descriptive, advisory, status, risk, and human_health output where already exposed
- explainability requirements
- discovery requirements
- diagnostics requirements
- guest-safe behavior requirements

This artifact treats room-aware asset interactions as E4 vocabulary consumption with a post-resolution handoff boundary to Asset Intelligence-authored output.

## Non-Scope

Coordinator does not:

- evaluate assets
- evaluate environments
- derive significance
- derive relevance
- generate room-health conclusions
- generate human-health conclusions
- generate asset-condition conclusions
- synthesize narratives
- modify Asset Intelligence output
- redefine Asset Intelligence contracts
- redefine Asset Intelligence models
- govern Asset Intelligence
- own Asset Intelligence vocabulary
- own Asset Intelligence advisory/status output

RV8a does not bring these future or non-E4 surfaces into E4 scope:

- document metadata
- document access
- physical document locations
- custody / loan outputs
- history timeline
- measurement outputs
- inventory export
- panel/bootstrap APIs
- raw document bytes
- event bus notifications

## Ownership Model

| Authority | Owned Authority | Consumable Outputs | Non-Rights | Source-of-Record Boundary |
|---|---|---|---|---|
| HTBW | canonical architecture, ADRs, contracts, models, governance, execution standards | governance direction and boundary rules | does not become runtime orchestration | architecture authority remains outside Concierge runtime |
| Foundation | room truth, area truth, device truth, what is true | area and room context used to narrow asset vocabulary | does not evaluate assets or author asset output | room truth remains external to Coordinator |
| Asset Intelligence | asset evaluation, environmental evaluation, asset descriptions, advisory/status output, risk/advisory generation, asset-condition output, room human_health output, environmental interpretation, what matters | labels, asset_type/category, identity/name metadata, descriptions, risk_state, candidate_state, reasons, exposure risk, advisories, primary_advisory, room environment projection, human_health output, source_status, room confidence metadata | does not transfer evaluation or authoring rights into Coordinator | Asset Intelligence remains authority for asset/environment interpretation and output generation |
| Concierge / Coordinator V2 | runtime consumption, orchestration, resolution, routing, planning, execution behavior, Concierge-local governance artifacts describing governed input consumption, current room-scoped `asset_groups` configuration where implemented | room-context application, asset_groups room configuration, explainability, discovery, diagnostics, presentation/routing of Asset Intelligence-authored output | does not own Asset Intelligence governance, evaluation, advisory generation, human_health generation, or room truth | Coordinator consumes governed inputs and does not become a source of record |

Key rules:

- Asset Intelligence owns evaluation, advisory, risk, environmental interpretation, asset descriptions, and human_health output.
- Concierge owns runtime consumption and current `asset_groups` room configuration where implemented.
- Foundation owns room truth.
- HTBW owns canonical architecture, contracts, models, and governance.

## Output Classification Model

### A. E4 Vocabulary Anchors

These are resolution anchors used to match or narrow room-aware asset queries.

Examples:

- asset labels
- `asset_type` / category
- asset identity/name metadata
- Concierge room `asset_groups`
- `source_status` / room confidence metadata for explainability

### B. Asset Intelligence-Authored Answer Content After E4 Resolution

These are existing Asset Intelligence-produced outputs that may be retrieved, referenced, presented, or routed after E4 has resolved the vocabulary target and room context.

Examples:

- asset descriptions
- `risk_state`
- `candidate_state`
- `reasons`
- exposure risk
- advisories
- `primary_advisory`
- `human_health.state`
- `human_health.reasons`
- `human_health.advisory_reasons`
- room environment projection

### C. Future or Non-E4 Surfaces

These outputs exist or are evidenced in implementation but are not RV8a scope.

Examples:

- documents
- custody
- loans
- history
- measurement
- inventory export
- raw document bytes
- panel/bootstrap APIs
- event bus notifications

E4 resolves vocabulary and target context, then may hand off to or retrieve Asset Intelligence-authored content without becoming the author or owner of that content.

## Asset Intelligence Output Inventory

| Output name | Description | Source file(s) | Owner | User-facing | Room-aware | Asset-aware | Vocabulary relevance | E4 classification | Explainability requirement | Diagnostics requirement | RV8a scope decision |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Asset identity record | asset_id, name, area, timestamps, purchase, valuation, custody, linkage metadata | `asset_intelligence/custom_components/asset_intelligence/sensor.py`, `asset_intelligence/custom_components/asset_intelligence/storage.py` | Asset Intelligence | Yes | Partial | Yes | direct resolution context | E4 vocabulary anchor | explain matched identity/name source | trace identity/name match path | Include |
| Asset labels | Home Assistant registry labels surfaced through coordinator and UI | `asset_intelligence/custom_components/asset_intelligence/coordinator.py`, `asset_intelligence/custom_components/asset_intelligence/frontend/panel_v5.js` | Asset Intelligence consumes and exposes registry-backed labels | Yes | Partial | Yes | direct resolution anchor | E4 vocabulary anchor | explain matched label source | trace label match path | Include |
| Asset type/category | `asset_type` and type metadata surfaced in asset state | `asset_intelligence/custom_components/asset_intelligence/sensor.py` | Asset Intelligence | Yes | No | Yes | category resolution anchor | E4 vocabulary anchor | explain matched category source | trace category match path | Include |
| Asset descriptions | descriptive guest/owner/insurance output stored on asset records | `asset_intelligence/custom_components/asset_intelligence/sensor.py`, `asset_intelligence/custom_components/asset_intelligence/frontend/panel_v5.js` | Asset Intelligence | Yes | Partial | Yes | post-resolution answer content | Asset Intelligence-authored answer content after E4 resolution | explain which description field was consumed | trace description retrieval source | Include as answer-content handoff |
| Asset evaluation projection | `risk_state`, `candidate_state`, `reasons`, debounce metadata, timestamps | `asset_intelligence/custom_components/asset_intelligence/coordinator.py`, `asset_intelligence/custom_components/asset_intelligence/evaluation.py`, `asset_intelligence/custom_components/asset_intelligence/sensor.py` | Asset Intelligence | Yes | Yes | Yes | post-resolution answer content | Asset Intelligence-authored answer content after E4 resolution | explain consumed evaluation source | trace `risk_state` and `reasons` source | Include as answer-content handoff |
| Advisory outputs | structured advisory list with severity, message, action, confidence | `asset_intelligence/custom_components/asset_intelligence/advisory.py`, `asset_intelligence/custom_components/asset_intelligence/sensor.py` | Asset Intelligence | Yes | Yes | Yes | post-resolution answer content | Asset Intelligence-authored answer content after E4 resolution | explain advisory source and consumption-only boundary | trace advisory retrieval source | Include as answer-content handoff |
| Primary advisory | highest-priority advisory for concise output | `asset_intelligence/custom_components/asset_intelligence/advisory.py`, `asset_intelligence/custom_components/asset_intelligence/sensor.py` | Asset Intelligence | Yes | Yes | Yes | post-resolution answer content | Asset Intelligence-authored answer content after E4 resolution | explain primary advisory source | trace primary advisory retrieval source | Include as answer-content handoff |
| Exposure risk | exposure classification and reasons grounded in placement and room conditions | `asset_intelligence/custom_components/asset_intelligence/evaluation.py`, `asset_intelligence/custom_components/asset_intelligence/coordinator.py` | Asset Intelligence | Yes | Yes | Yes | post-resolution answer content | Asset Intelligence-authored answer content after E4 resolution | explain exposure-risk source | trace exposure-risk retrieval source | Include as answer-content handoff |
| Spatial context | placement/window/sun context supporting exposure interpretation | `asset_intelligence/custom_components/asset_intelligence/evaluation.py`, `asset_intelligence/custom_components/asset_intelligence/sensor.py` | Asset Intelligence | Partial | Yes | Yes | explainability support rather than user vocabulary | Future / non-E4 surface | show when used for support context | trace availability and retrieval failures | Exclude from core RV8a scope |
| Room environment projection | room climate, light, air, particulate, biological, safety, structural, context, control, and external environment projection | `asset_intelligence/custom_components/asset_intelligence/environment.py`, `asset_intelligence/custom_components/asset_intelligence/coordinator.py`, `asset_intelligence/custom_components/asset_intelligence/sensor.py` | Asset Intelligence interpretation layer consuming Foundation truth inputs | Yes | Yes | No | post-resolution answer content for room-health and asset-condition queries | Asset Intelligence-authored answer content after E4 resolution | explain room output source | trace room projection retrieval source | Include as answer-content handoff |
| Room human_health output | state, confidence, reasons, advisory reasons, readings, ranges, signal counts | `asset_intelligence/custom_components/asset_intelligence/evaluation.py`, `asset_intelligence/custom_components/asset_intelligence/coordinator.py`, `asset_intelligence/custom_components/asset_intelligence/sensor.py` | Asset Intelligence | Yes | Yes | No | post-resolution answer content for room-health queries | Asset Intelligence-authored answer content after E4 resolution | explain human_health source and signal coverage | trace human_health retrieval source | Include as answer-content handoff |
| Source-status / room confidence metadata | configured signals, reporting counts, missing counts, confidence state | `asset_intelligence/custom_components/asset_intelligence/environment.py`, `asset_intelligence/custom_components/asset_intelligence/sensor.py` | Asset Intelligence | Yes | Yes | No | explainability anchor for room-aware output confidence | E4 vocabulary anchor | explain confidence/source_status when answers depend on coverage | trace confidence/source_status source | Include |
| Document metadata projection | normalized document metadata for assets | `asset_intelligence/custom_components/asset_intelligence/document_models.py`, `asset_intelligence/custom_components/asset_intelligence/services/document_retrieval.py`, `asset_intelligence/custom_components/asset_intelligence/sensor.py` | Asset Intelligence | Yes | No | Yes | not RV8a vocabulary scope | Future / non-E4 surface | explain exclusion | trace if later consumed | Exclude |
| Document access info | safe metadata and access information for stored documents | `asset_intelligence/custom_components/asset_intelligence/__init__.py`, `asset_intelligence/custom_components/asset_intelligence/document_storage.py` | Asset Intelligence | Yes | No | Yes | not RV8a vocabulary scope | Future / non-E4 surface | explain exclusion | trace if later consumed | Exclude |
| Document availability / storage status | document storage availability and per-document availability checks | `asset_intelligence/custom_components/asset_intelligence/__init__.py`, `asset_intelligence/custom_components/asset_intelligence/diagnostics.py` | Asset Intelligence | Partial | No | Partial | supportability only | Internal / supportability only | no RV8a explainability obligation | support-only diagnostics | Exclude |
| Physical document locations | physical-only or linked physical document storage references | `asset_intelligence/custom_components/asset_intelligence/sensor.py`, `asset_intelligence/custom_components/asset_intelligence/services.yaml` | Asset Intelligence | Yes | Partial | Yes | not RV8a vocabulary scope | Future / non-E4 surface | explain exclusion | trace if later consumed | Exclude |
| Custody / loan outputs | custody state, loan records, loan events | `asset_intelligence/custom_components/asset_intelligence/sensor.py`, `asset_intelligence/custom_components/asset_intelligence/services.yaml` | Asset Intelligence | Yes | Partial | Yes | not RV8a vocabulary scope | Future / non-E4 surface | explain exclusion | trace if later consumed | Exclude |
| Activity / history timeline | backend history payload and audit summaries | `asset_intelligence/custom_components/asset_intelligence/__init__.py`, `asset_intelligence/custom_components/asset_intelligence/sensor.py` | Asset Intelligence | Yes | Partial | Yes | not RV8a vocabulary scope | Future / non-E4 surface | explain exclusion | trace if later consumed | Exclude |
| Measurement outputs | active measurement state, sessions, room measurement history | `asset_intelligence/custom_components/asset_intelligence/__init__.py`, `asset_intelligence/custom_components/asset_intelligence/sensor.py`, `asset_intelligence/custom_components/asset_intelligence/frontend/panel_v5.js` | Asset Intelligence | Yes | Yes | Yes | not RV8a vocabulary scope | Future / non-E4 surface | explain exclusion | trace if later consumed | Exclude |
| Inventory export dataset | CSV/JSON export rows for inventory and insurance addendum | `asset_intelligence/custom_components/asset_intelligence/__init__.py` | Asset Intelligence | Yes | Partial | Yes | not RV8a vocabulary scope | Future / non-E4 surface | explain exclusion | trace if later consumed | Exclude |
| Diagnostics payload | config-entry diagnostics and runtime diagnostics information | `asset_intelligence/custom_components/asset_intelligence/diagnostics.py` | Asset Intelligence | Partial | No | Partial | supportability only | Internal / supportability only | no RV8a explainability obligation | support-only diagnostics | Exclude |
| Panel/bootstrap APIs | panel version and storage snapshot endpoints | `asset_intelligence/custom_components/asset_intelligence/panel.py` | Asset Intelligence | Frontend-only | Partial | Partial | not RV8a vocabulary scope | Internal / supportability only | explain exclusion | trace if later consumed | Exclude |
| Raw document bytes endpoint | authenticated document content retrieval endpoint | `asset_intelligence/custom_components/asset_intelligence/__init__.py` | Asset Intelligence | Yes | No | Yes | not RV8a vocabulary scope | Future / non-E4 surface | explain exclusion | trace if later consumed | Exclude |
| Event bus notifications | integration action and status events | `asset_intelligence/custom_components/asset_intelligence/__init__.py` | Asset Intelligence | Partial | Partial | Yes | not RV8a vocabulary scope | Future / non-E4 surface | explain exclusion | trace if later consumed | Exclude |

Implementation findings that must remain explicit:

- current implementation does not expose first-class asset narratives
- current implementation does not expose first-class asset-condition narratives
- current implementation does not expose first-class collection narratives
- current implementation does not expose first-class environmental narratives
- current implementation does not expose first-class room-health narratives
- current implementation does not expose first-class significance assessments
- current implementation does not expose first-class relevance assessments

When the word `narrative` is used in downstream planning, it must be interpreted narrowly as consumption of existing Asset Intelligence-produced descriptive, advisory, status, risk, or human_health output.

## Source-Output Matrix

| User query type | Matched vocabulary anchor | Room context used | Vocabulary source | Asset Intelligence output consumed after resolution | Grounded source | Owning repository | Consuming repository | Explainability requirement | Diagnostics requirement | Guest-safe consideration |
|---|---|---|---|---|---|---|---|---|---|---|
| Tell me about the artwork. | asset label, asset_type/category, identity/name metadata, or Concierge asset_groups | optional narrowing if current room context exists | Asset Intelligence labels, Asset Intelligence `asset_type`, Asset Intelligence identity/name metadata, or Concierge `asset_groups` | asset descriptions, and where needed advisory/status output | `asset_intelligence/custom_components/asset_intelligence/sensor.py`, `custom_components/concierge/models.py` | Asset Intelligence for output, Concierge for `asset_groups` | Concierge | show matched source and whether room context narrowed the result | trace label/category/name/group match and output source | hide sensitive detail where guest-safe handling requires it |
| Tell me about the artwork in this room. | asset label, asset_type/category, or Concierge asset_groups narrowed by room | yes | Asset Intelligence labels, Asset Intelligence `asset_type`, Concierge `asset_groups`, Foundation room truth | asset descriptions and room-scoped advisory/status output where applicable | `asset_intelligence/custom_components/asset_intelligence/sensor.py`, `custom_components/concierge/frontend/panel.js` | Asset Intelligence for output, Concierge for room config, Foundation for room truth | Concierge | show room context and matched source | trace room-context narrowing and output source | room-scoped details may need guest-safe filtering |
| Are the antiques OK? | asset label, asset_type/category, identity/name metadata, or Concierge asset_groups | optional narrowing if room context exists | Asset Intelligence labels, Asset Intelligence `asset_type`, identity/name metadata, or Concierge `asset_groups` | `risk_state`, `candidate_state`, `reasons`, advisories, `primary_advisory` | `asset_intelligence/custom_components/asset_intelligence/coordinator.py`, `asset_intelligence/custom_components/asset_intelligence/sensor.py` | Asset Intelligence | Concierge | show matched vocabulary and consumed status source | trace match path and `risk_state` / advisory source | limit detail when guest-safe handling applies |
| Is the artwork OK? | asset label, asset_type/category, identity/name metadata, or Concierge asset_groups | optional narrowing if room context exists | Asset Intelligence labels, Asset Intelligence `asset_type`, identity/name metadata, or Concierge `asset_groups` | `risk_state`, `reasons`, advisories, `primary_advisory`, exposure risk where exposed | `asset_intelligence/custom_components/asset_intelligence/sensor.py`, `asset_intelligence/custom_components/asset_intelligence/advisory.py` | Asset Intelligence | Concierge | show matched source and output source | trace match path, advisory source, and retrieval failures | guest-safe handling may need reduced explanation detail |
| Is this room healthy? | room context plus room-aware Asset Intelligence output, not asset-target capability selection | yes | Foundation room truth plus room-aware Asset Intelligence output | `human_health.state`, `human_health.reasons`, `human_health.advisory_reasons`, room environment projection, `source_status`, room confidence | `asset_intelligence/custom_components/asset_intelligence/evaluation.py`, `asset_intelligence/custom_components/asset_intelligence/sensor.py` | Asset Intelligence for output, Foundation for room truth | Concierge | show room context, consumed human_health source, and confidence/source_status | trace room context, human_health source, source_status, stale context, and retrieval failures | health/environment details may require guest-safe limitation |
| Tell me about the collection in this room. | Concierge `asset_groups`, asset labels, asset_type/category, or identity/name metadata narrowed by room | yes | Concierge `asset_groups` room configuration, Asset Intelligence labels, Asset Intelligence `asset_type` | asset descriptions and asset-condition/status output for resolved room-scoped targets | `custom_components/concierge/models.py`, `asset_intelligence/custom_components/asset_intelligence/sensor.py` | Concierge for group naming, Asset Intelligence for output | Concierge | show whether the match came from Concierge `asset_groups` rather than Asset Intelligence ownership | trace group match, room-context narrowing, and output source | guest-safe handling may need to suppress detailed inventory content |

## Room Context Integration

Room context narrows or disambiguates asset vocabulary.

- Foundation remains authority for room truth.
- Asset Intelligence remains authority for what matters about assets and environments.
- Concierge applies room context to vocabulary resolution.
- Concierge `asset_groups` are Concierge room configuration, not Asset Intelligence-owned vocabulary.
- Coordinator must not infer asset significance or relevance.

Room context may:

- narrow a label or category match to the current room
- disambiguate overlapping asset labels or categories across rooms
- determine whether a room-scoped query should resolve through Concierge `asset_groups`
- determine whether a room-health query should retrieve room-scoped Asset Intelligence output

Room context does not:

- create new asset semantics
- create significance rankings
- create relevance rankings
- transfer room truth ownership

## Vocabulary Resolution Behavior

Resolution behavior must document and preserve:

- exact match
- label match
- asset type/category match
- asset identity/name metadata match
- Concierge `asset_groups` match
- room-scoped narrowing
- ambiguity handling
- no-match behavior
- stale room context handling
- guest-safe hide/show behavior

Deterministic rules:

- exact asset identity/name match may resolve first when explicitly provided
- label and category matches may resolve through Asset Intelligence-exposed metadata
- room-scoped collection-style phrasing may resolve through Concierge `asset_groups` where configured
- room context may narrow but must not redefine vocabulary meaning
- ambiguous matches must remain explainable and diagnosable
- stale or missing room context must be surfaced rather than hidden behind inference

## Answer-Content Handoff Behavior

Boundary rules:

- E4 may identify the asset, room, category, group, or target context.
- Asset Intelligence remains responsible for evaluation, advisory, risk, descriptions, and human_health output.
- Coordinator may present or route Asset Intelligence-authored output.
- Coordinator must not generate alternate conclusions or reinterpret Asset Intelligence output.

Post-resolution handoff examples:

- asset target resolved -> consume asset descriptions
- asset target resolved for status query -> consume `risk_state`, `reasons`, advisories, `primary_advisory`
- room-health target resolved -> consume `human_health` output and room confidence/source_status

## Explainability Requirements

Explainability must show:

- matched vocabulary
- vocabulary source
- room context used
- resolved asset/group/category/label
- whether the matched source was Concierge `asset_groups` or Asset Intelligence exposed metadata
- consumed Asset Intelligence output source
- whether Coordinator consumed rather than authored the output
- ambiguity reason
- no-match reason
- stale room context indication where applicable
- `source_status` / confidence where room-health or human_health answers depend on signal coverage

## Discovery Requirements

Discovery must expose relevant Asset Intelligence-related vocabulary surfaces without implying Coordinator ownership.

Discovery must distinguish:

- vocabulary available for room-aware matching
- Concierge `asset_groups` room configuration
- Asset Intelligence labels, types, and name metadata
- Asset Intelligence output available for consumption after resolution
- outputs hidden or restricted for guest-safe behavior
- future or non-E4 surfaces intentionally excluded from RV8a

Discovery must not imply that Coordinator owns or authors Asset Intelligence output.

## Diagnostics Requirements

Diagnostics must cover:

- asset label match
- asset type/category match
- asset identity/name metadata match
- Concierge `asset_groups` match
- room context applied
- asset/group/category/label resolution
- consumed Asset Intelligence output source
- `risk_state` / `reasons` source
- advisory / `primary_advisory` source
- `human_health` source
- room `source_status` / confidence
- guest-safe visibility decision
- ambiguity condition
- no-match condition
- retrieval failure condition
- stale context condition
- ownership-boundary indicator showing Coordinator consumed an Asset Intelligence result rather than authored one

Detailed diagnostics participation for these paths is defined in:

- `docs/governance/vocabulary-diagnostics-framework.md`

Diagnostics must preserve the distinction between:

- Asset Intelligence-exposed labels, `asset_type` / category, identity metadata, `source_status`, and confidence metadata used as consumed inputs
- Concierge `asset_groups` used as Concierge room configuration
- Asset Intelligence-authored answer content consumed after E4 resolution

## Guest-Safe Behavior

Guest-safe handling must follow existing guest-safe governance where available.

This artifact does not invent new guest policy details.

Where a specific guest-safe policy for an Asset Intelligence-derived output is not yet defined, that absence must be treated as a readiness consideration rather than silently resolved in implementation.

Guest-safe behavior should consider:

- hiding or reducing sensitive asset details
- hiding or reducing room health detail when policy requires it
- distinguishing discoverable vocabulary from restricted answer content

## Future Epic Dependency Mapping

| Epic / Issue | Relationship |
|---|---|
| E4 Room Vocabulary Consumption | RV8a is an E4 dependency defining Asset Intelligence-related vocabulary consumption and post-resolution handoff boundaries |
| #79 Vocabulary Diagnostics Framework | must consume the diagnostics requirements defined here after RV8a is defined |
| #80 E4 Readiness Review | must close last and must supersede the previous E4 readiness decision after RV8a and revised #79 are complete |
| E5 Capability Projection Consumption | may consume resolved targets later, but RV8a is not E5 capability selection |
| E6 Experience Consumption | answer composition and presentation of Asset Intelligence-authored output may become relevant downstream |
| Future document/history/custody/measurement epics | document, custody, history, measurement, export, and raw-byte surfaces remain outside RV8a unless explicitly assigned later |

## Risks and Failure Modes

- ownership drift
- hidden inference
- stale room context
- ambiguous asset vocabulary
- no matching asset label/category/group/name
- incorrect attribution of Concierge `asset_groups` to Asset Intelligence
- inaccessible Asset Intelligence output
- guest visibility leakage
- Coordinator-generated interpretation drift
- claiming nonexistent narrative/significance/relevance outputs
- mixing vocabulary anchors with answer content
- prematurely absorbing future or non-E4 surfaces into E4

## Readiness Criteria

RV8a readiness requires:

- artifact exists
- source-output matrix exists
- ownership matrix exists
- output inventory exists
- E4 vocabulary anchors are distinguished from answer content
- future or non-E4 surfaces are explicitly excluded or mapped
- Concierge `asset_groups` ownership is correctly attributed
- nonexistent narrative/significance/relevance outputs are not claimed as current implementation
- explainability requirements documented
- discovery requirements documented
- diagnostics requirements documented
- guest-safe requirements documented
- #190 references this artifact
- #79 update scope is defined
- #80 update scope is defined
- no ownership drift introduced

## Readiness Statement

This artifact is READY as the governance baseline for defining Asset Intelligence-related vocabulary consumption inside E4, subject to updated diagnostics and readiness review artifacts that consume its requirements.