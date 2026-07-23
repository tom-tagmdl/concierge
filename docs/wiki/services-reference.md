# Services Reference

Most people can use Concierge through normal voice and UI interactions.

This page is for advanced users who build automations and scripts in Home Assistant.

## Most Useful Services For Daily Operation

- concierge.get_summary
- concierge.execute
- concierge.push_person_message
- concierge.resolve_mobile_context

## execute Context Examples (Advanced)

You can pass a context object to concierge.execute for governed media behavior.

Example: continue music with room and identity defaults.

```yaml
service: concierge.execute
data:
	target: continue music
	area_id: area.kitchen
	context:
		identity_context:
			state: known
			confidence_band: high
			source: voice_identity
		room_default_media_query: room-default
		household_default_media_query: house-default
		system_safe_media_query: safe-music
```

Example: explicit Follow-Me handoff request.

```yaml
service: concierge.execute
data:
	target: follow me music
	area_id: area.kitchen
	context:
		follow_me_enabled: true
		identity_context:
			state: known
			confidence_band: high
			source: voice_identity
		room_transition:
			source_room_id: area.living_room
			destination_room_id: area.kitchen
			source: presence_runtime
```

## Follow-Me Explainability Fields

When media continuity responses include Follow-Me evaluation, inspect:

- follow_me_enabled
- follow_me_candidate
- follow_me_allowed
- follow_me_decision
- follow_me_reason
- identity_authority_source
- room_transition_source
- cooldown_blocked
- manual_stop_blocked
- source_room
- destination_room

## Direct Output With push_person_message

Advanced users can direct message output with the target_id field on concierge.push_person_message.

Common target choices:

- voice_assistant or assistant: route to the room voice assistant target.
- speaker or tts: route to the room speaker/media player target.
- assist_satellite.<entity_id>: route to a specific voice assistant entity.
- media_player.<entity_id>: route to a specific speaker/media player entity.
- notify.<mobile_target>: route to a specific mobile notify target.
- web_ui: route to a persistent UI notification.

If target_id is not set, Concierge uses its normal fallback routing.

## Setup and Configuration Services

- concierge.update_room_config
- concierge.update_composite_config
- concierge.sync_rooms
- concierge.sync_composites
- concierge.refresh_entity_structure
- concierge.update_person_profile
- concierge.update_identity_profile
- concierge.update_voice_profile

## Voice Enrollment Services

Voice Enrollment Services are only available when the Voice Identity integration is installed and Voice Identity is turned on in Concierge Integration Settings.

If Voice Identity is not installed or not enabled, these services will not be available.

- concierge.start_voice_enrollment
- concierge.capture_voice_enrollment_sample
- concierge.remove_voice_enrollment_sample
- concierge.build_voice_profile
- concierge.reset_voice_profile
- concierge.delete_voice_profile

## Activity and History Services

- concierge.record_activity_event
- concierge.close_activity_outcome
- concierge.get_activity_timeline
- concierge.export_activity_archive

## Complete Service List

For full service fields and parameters, see:

- custom_components/concierge/services.yaml
