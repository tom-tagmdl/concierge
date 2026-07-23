# Experience Continuity Helper-Family Disposition Matrix

## Purpose

This artifact is the governed disposition matrix for V1 helper-backed state families referenced by in-scope Experience Continuity outcomes.

It translates V1 helper persistence into V2 state strategy without preserving the V1 helper schema as the V2 storage model.

## Governing Sources

- [Experience Continuity Scope Decisions](experience-continuity-scope-decisions.md)
- [Experience Continuity Requirements Backlog](experience-continuity-requirements-backlog.md)
- [V1 Capability Reconstruction](v1-capability-reconstruction.md)
- [V1-to-V2 Capability Parity Matrix](v1-to-v2-capability-parity-matrix.md)
- [Experience Restoration Context Model](../../../../homes_that_behave_well/docs/models/experience-restoration-context-model.md)
- [Room Model](../../../../homes_that_behave_well/docs/models/room-model.md)

## Disposition Vocabulary

Each helper family must use exactly one of these dispositions:

- migrate
- seed
- re-learn
- replace with room default
- replace with person plus room default
- retire

Interpretation rules:

- migrate means the V1 value is deterministic, safe, and maps cleanly to a V2 continuity model or retained-operational-value field.
- seed means the V1 value is useful as initial V2 configuration but should not remain a live helper schema dependency.
- re-learn means the V1 helper value is an inferred history artifact and should be rebuilt from future governed events.
- replace with room default means V2 should use a room-scoped default or room-model retained value instead of helper persistence.
- replace with person plus room default means V2 should resolve the value from person-aware continuity with a room fallback.
- retire means the V1 helper is out of scope or has no continuity owner in V2.

## Inventory Basis

The V1 reconstruction documents 112 helper-family entities across these helper types:

- input_boolean
- input_datetime
- input_number
- input_select
- input_text
- counter

The matrix below groups those helpers by continuity family rather than by individual helper entity.

## Helper-Family Matrix

| Family ID | V1 Helper Family Evidence | V1 Outcome Family | Disposition | V2 State Strategy | Rationale | Downstream Follow-Up |
|---|---|---|---|---|---|---|
| HSF-01 | input_number.*_learned_brightness and input_datetime.lamp_brightness_profile_last_updated | Lighting preference learning and usual lighting restore | migrate | Map into room-model retained_operational_values for room-scoped brightness memory | The value is deterministic, room-scoped, and already matches the retained-operational-values concept in the room model. | Lighting continuity implementation and restoration tests |
| HSF-02 | input_text.*_speaker_profile_last_media and input_datetime.speaker_profile_last_updated | Audio continuity and media continuation context | migrate | Map into room-scoped retained_operational_values.media.last_media and profile freshness metadata | The value captures durable room continuity context and can seed the V2 continuity model without reinterpreting the helper schema. | Audio continuity and media continuation implementation |
| HSF-03 | input_text.music_genre_uri_map | Genre routing lookup for media play flows | seed | Seed a V2 configuration-backed genre routing map and detach it from runtime helper storage | The mapping is useful initialization data, but it is configuration-like rather than user history and should not remain helper-owned. | Media routing configuration follow-up |
| HSF-04 | counter.music_genre_* | Music genre observation and preference accumulation | re-learn | Rebuild preference aggregation from governed playback events instead of preserving raw counters | The counters are derived history, not authoritative state, so V2 should learn from events rather than carry forward the count schema. | Preference aggregation and media analytics implementation |
| HSF-05 | input_select.room_posture_guest_bedroom and input_select.room_posture_primary_bedroom | Room posture selection and mode application | replace with room default | Replace helper-backed posture storage with room-model posture defaults and stable group_key vocabulary | The posture helper is a room-mode selector, not durable user memory, so the V2 model should own the default directly. | Room posture model and mode application implementation |
| HSF-06 | input_boolean.alarm_primary_bedroom_ringing | Primary Bedroom Alarm orchestration state | retire | Remove from initial Experience Continuity state strategy; the alarm domain is out of scope for this install gate | The alarm helper supports an explicitly out-of-scope V1-only behavior and should not be retained as continuity state. | No continuity follow-up in this roadmap |

## Inventory Reconciliation

This table reconciles the helper-backed continuity families identified in the V1 reconstruction against the current disposition matrix and parity scope.

| Family Name | Helper Types | V1 Purpose | Scope Ownership | Evidence Source | Matrix Entry Present |
|---|---|---|---|---|---|
| Lighting brightness learning and usual restore | input_number, input_datetime | Learn room brightness and restore usual lighting | room | V1 reconstruction lighting learning evidence; room retained-operational-values model | Yes |
| Speaker profile last-media context | input_text, input_datetime | Preserve room media continuity and speaker profile freshness | room | V1 reconstruction audio/media continuity evidence; room retained-operational-values model | Yes |
| Genre routing lookup map | input_text | Route genre playback flows from stored URI mapping | configuration / room-adjacent | V1 reconstruction music follow-up evidence; parity matrix media continuity scope | Yes |
| Music genre observation counters | counter | Track observed genre preference accumulation | person + room analytics | V1 reconstruction genre-observation evidence; parity matrix preference-resolution scope | Yes |
| Room posture selectors | input_select | Select room posture for room-specific mode application | room | V1 reconstruction room posture evidence; room model group_key and retained values | Yes |
| Primary Bedroom Alarm ringing flag | input_boolean | Drive alarm start/repeat/escalation/stop orchestration | out of scope for initial install gate | V1 reconstruction alarm evidence; scope decisions mark alarm replacement out of scope | Yes |

## Coverage Notes

- This matrix covers the helper families referenced in the in-scope continuity outcomes documented by the V1 reconstruction.
- It intentionally excludes out-of-scope routine replacement behavior and other alarm replacement behavior.
- The matrix is schema-independent: it names the disposition and V2 state strategy, not a helper-to-helper migration payload.

## Completeness Validation

Validation date: 2026-07-22

Evidence sources:

- [V1 Capability Reconstruction](v1-capability-reconstruction.md)
- [V1-to-V2 Capability Parity Matrix](v1-to-v2-capability-parity-matrix.md)
- [Experience Continuity Scope Decisions](experience-continuity-scope-decisions.md)

Counts:

- helper family count discovered: 6
- helper family count mapped: 6
- helper family count excluded: 0
- helper family count lacking disposition: 0

Validation result:

- all helper-backed continuity families in scope have a disposition entry
- no helper-backed continuity family remains unclassified
- matrix validation test passed

Validation command:

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 r:/HomesPlatformRepos/concierge/.venv/Scripts/python.exe -m pytest -q tests/test_experience_continuity_helper_family_disposition_matrix.py`

Validation execution summary:

- return code: 0
- pass count: 2
- fail count: 0

## Validation Notes

- Every listed helper family must appear exactly once.
- Every disposition must be one of the approved vocabulary terms.
- The doc must remain aligned with EC-REQ-082 and EC-REQ-083.
