# Concierge V1 Capability Reconstruction (Production Evidence)

## 1. Executive Summary
- This artifact reconstructs Concierge V1 behavior from authenticated production Home Assistant runtime evidence before any V1-to-V2 parity scoring.
- Authority label used: Abilities Concierge.
- In-scope: 19 production automations, 42 production scripts, and labeled helper inventory.
- User policy exclusions applied: Bedtime (Concierge), Good Morning (Concierge), Goodnight (Concierge).
- Concierge and Voice Identity integration service domains are not installed in production; V1 behavior is implemented through HA automations/scripts/helpers.

## 2. Production Evidence Sources Used
- Live production URL session: https://ha.tagmdl.com/config/automation/dashboard (authenticated as production user).
- Home Assistant API: /api/config, /api/states, /api/services, /api/config/automation/config/{unique_id}, /api/config/script/config/{unique_id}.
- HA registries via websocket in authenticated session: config/entity_registry/list, config/label_registry/list, config/area_registry/list, config_entries/get.

## 3. Scope and Exclusions
- Scope includes production entities labeled abilities_concierge across automation and script domains plus helper dependencies.
- Excluded by explicit policy from V2 parity scope:
  - automation.bedtime_concierge
  - automation.good_morning_concierge
  - automation.goodnight_concierge

## 4. In-Scope Automation List (19)
- automation.lamp_profile_learn_on_use — Lighting Profile â€“ Learn on Use
- automation.concierge_voice_entry_ha_voice — Concierge â€“ Voice Entry (HA Voice)
- automation.concierge_follow_up_commands_ha_voice — Concierge â€“ Follow-Up Commands (HA Voice)
- automation.concierge_intentional_learning_ha_voice — Concierge â€” Intentional Learning (HA Voice)
- automation.music_genre_observe_playback_all_sources — Music Genre â€“ Observe Playback (All Sources)
- automation.music_capture_last_media_on_playback — Music â€“ Capture Last Media (Robust)
- automation.primary_bedroom_alarm_started — Primary Bedroom â€“ Alarm Started
- automation.primary_bedroom_alarm_repeat — Primary Bedroom â€“ Alarm Repeat
- automation.primary_bedroom_alarm_escalation — Primary Bedroom â€“ Alarm Escalation
- automation.primary_bedroom_alarm_stop — Primary Bedroom â€“ Alarm Stop
- automation.voice_play_music — Voice â€“ Play Music
- automation.voice_continue_playing — Voice â€“ Continue Playing
- automation.voice_play_jazz — Voice â€“ Music Follow-Ups
- automation.learn_music_volume_on_sonos_change — Learn Music Volume â€“ On Sonos Change
- automation.concierge_shade_percentage_catcher_ha_voice — Concierge â€“ Shade Percentage Catcher (HA Voice)
- automation.concierge_lighting_percentage_catcher_ha_voice — Concierge â€“ Lighting Percentage Catcher (HA Voice)
- automation.duck_sonos_when_any_assist_satellite_is_listening — Duck Sonos When Any Assist Satellite Is Listening
- automation.concierge_room_monitoring_awareness_ha_voice — Concierge â€“ Room Monitoring Awareness (HA Voice)
- automation.concierge_follow_up_sensor_queries_ha_voice — Concierge â€“ Follow-Up Sensor Queries (HA Voice)

## 5. In-Scope Script List (42)
- script.resolve_speaker_profile — Resolve Speaker Profile
- script.room_audio_resolver_keystone — Room & Audio Resolver (Keystone)
- script.sonos_speak_with_ducking_room — Sonos Speak with Ducking (Room)
- script.room_capabilities_snapshot_debug — Room Capabilities â€” Snapshot (Debug)
- script.learn_lighting_usual_room — Learn Lighting â€” Usual (Room)
- script.learn_music_volume_room — Learn Music Volume â€” Room
- script.resolve_music_player_room — Resolve Music Player â€“ Room
- script.update_last_media_room — Music â€“ Update Last Media (Room)
- script.start_music_usual_room — Start Music â€“ Usual (Room)
- script.determine_music_genre_audit — Music â€“ Determine Genre (Audit, Room)
- script.play_genre_room — Play Genre â€“ Room
- script.play_artist_room — Play Artist â€“ Room (MA)
- script.primary_bedroom_play_alarm_chime — Alarm â€“ Play Chime (Room)
- script.alarm_sonos_snapshot — Alarm â€“ Sonos Snapshot
- script.play_album_room_ma — Play Album â€“ Room (MA)
- script.surprise_me_room — Surprise Me â€“ Room
- script.continue_playing_room — Continue Playing â€“ Room
- script.what_s_playing_room — Whatâ€™s Playing? â€“ Room
- script.why_did_you_play_this_room — Why Did You Play This? â€“ Room
- script.music_debug_snapshot_room — Music Debug Snapshot â€“ Room
- script.voice_assistant_speak_fallback — Voice Assistant Speak (Fallback)
- script.room_abilities_speak_unified — Room Abilities â€” Speak (Unified)
- script.ensure_main_living_area_sonos_group — Ensure Main Living Area Sonos Group
- script.turn_on_lamps_usual_room — Turn On Lamps â€” Usual (Room)
- script.turn_on_lights_usual_room — Turn On Lights â€” Usual (Room)
- script.set_room_posture — Set Room Posture
- script.resolve_bedroom_context — Resolve Bedroom Context
- script.bedroom_context_not_valid_speak — Bedroom Context Not Valid Speak
- script.kiosk_set_overnight_mode — Kiosk Set Overnight Mode
- script.kiosk_set_day_mode — Kiosk Set Day Mode
- script.concierge_bedtime — Concierge Bedtime
- script.concierge_goodnight — Concierge Goodnight
- script.concierge_good_morning — Concierge Good Morning
- script.duck_sonos_while_assist_is_listening_room — Duck Sonos While Assist Is Listening (Room)
- script.room_monitoring_abilities_speak — Room Monitoring Abilities â€” Speak
- script.speak_room_temperature — Speak Room Temperature
- script.speak_room_humidity — Speak Room Humidity
- script.speak_room_light_level — Speak Room Light Level
- script.speak_room_air_quality — Speak Room Air Quality
- script.speak_room_noise_level — Speak Room Noise Level
- script.speak_capability_not_available — Speak Capability Not Available
- script.speak_room_air_quality_ai_assessment — Speak Room Air Quality (AI Assessment)

## 6. In-Scope Helper Summary
- Labeled helper count (input/timer/counter family): 112
- counter: 19
- input_boolean: 8
- input_datetime: 3
- input_number: 54
- input_select: 2
- input_text: 26
- Note: this recount includes input_datetime entities, yielding 112 total helper-family entities.

## 7. Execution Graph Summary
- Graph roots: 19 in-scope automations.
- Recursive traversal rule: automation called_scripts + transitive script.called_scripts.
- Chain outputs include service calls, helper reads/writes, and entity references across room/audio/media/monitoring domains.

### 7A. Automation Graph Details
#### automation.lamp_profile_learn_on_use
- Friendly name: Lighting Profile â€“ Learn on Use
- Labels: abilities_concierge, policy
- Triggers: {"trigger":"state","entity_id":["light.den_corner_lamp","light.david_s_lamp","light.dresser_lamps","light.tom_s_lamp","light.den_bookcase_lamp","light.den_sofa_lamp","light.eames_lounge_lamp","light.guest_bedside_lamp","light.guest_corner_lamp","light.living_room_sofa_lamp","light.living_room_torches","light.lamplinc_dimmer_2e_ba_36","light.tom_s_office_overhead","light.david_s_office_overhead","light.den_overhead","light.piano_art","light.den_art","light.piano_overhead","light.dining_room_overhead","light.dining_room_chandelier","light.dining_room_art","light.downstairs_bathroom_sconce","light.downstairs_bathroom_overhead","light.entryway_art_main","light.guest_bathroom_shower","light.guest_closet","light.guest_sconce","light.guest_bedroom_overhead","light.guest_bedroom_art","light.kitchen_overhead","light.kitchen_island","light.kitchen_table","light.kitchen_cabinets","light.switchlinc_relay_dual_band_50_fc_23","light.switchlinc_relay_dual_band_51_1d_3f","light.living_room_overhead","light.living_room_art","light.carport_lights","light.patio_lights","light.powder_room_lights","light.primary_toilet_light","light.primary_bathroom_overhead","light.primary_bathroom_skylight","light.primary_bathroom_sconce","light.primary_bedroom_overhead","light.primary_bedroom_art","light.primary_closet_lights","light.stairway_art","light.stairway_skylight","light.guest_hallway_light_main"],"attribute":"brightness","for":{"seconds":30}}
- Conditions: 
- Actions: [{"variables":{"light_entity":"{{ trigger.entity_id }}","brightness_raw":"{{ state_attr(light_entity, \u0027brightness\u0027) | int(0) }}","brightness_pct":"{{ (brightness_raw / 255 * 100) | round(0) | int }}","helper":"input_number.{{ light_entity.split(\u0027.\u0027)[1] }}_learned_brightness"}},{"condition":"template","value_template":"{{ is_state(light_entity, \u0027on\u0027) and brightness_pct \u003e 0 }}"},{"choose":[{"conditions":[{"condition":"template","value_template":"{{ states(helper) not in [\u0027unknown\u0027, \u0027unavailable\u0027] }}"}],"sequence":[{"action":"input_number.set_value","target":{"entity_id":"{{ helper }}"},"data":{"value":"{{ brightness_pct }}"}},{"choose":[{"conditions":[{"condition":"template","value_template":"{{ states(\u0027input_datetime.lamp_brightness_profile_last_updated\u0027) not in [\u0027unknown\u0027,\u0027unavailable\u0027] }}"}],"sequence":[{"action":"input_datetime.set_datetime","target":{"entity_id":"input_datetime.lamp_brightness_profile_last_updated"},"data":{"datetime":"{{ now().strftime(\u0027%Y-%m-%d %H:%M:%S\u0027) }}"}}]}]}]}]}]
- Called scripts (direct): 
- Called scripts (transitive): 
- Called services (chain): input_datetime.set_datetime, input_number.set_value
- Helpers read: input_datetime.lamp_brightness_profile_last_updated
- Helpers written: input_datetime.set_datetime, input_number.set_value
- Template sensors read: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: light.carport_lights, light.david_s_lamp, light.david_s_office_overhead, light.den_art, light.den_bookcase_lamp, light.den_corner_lamp, light.den_overhead, light.den_sofa_lamp, light.dining_room_art, light.dining_room_chandelier, light.dining_room_overhead, light.downstairs_bathroom_overhead, light.downstairs_bathroom_sconce, light.dresser_lamps, light.eames_lounge_lamp, light.entryway_art_main, light.guest_bathroom_shower, light.guest_bedroom_art, light.guest_bedroom_overhead, light.guest_bedside_lamp, light.guest_closet, light.guest_corner_lamp, light.guest_hallway_light_main, light.guest_sconce, light.kitchen_cabinets, light.kitchen_island, light.kitchen_overhead, light.kitchen_table, light.lamplinc_dimmer_2e_ba_36, light.living_room_art, light.living_room_overhead, light.living_room_sofa_lamp, light.living_room_torches, light.patio_lights, light.piano_art, light.piano_overhead, light.powder_room_lights, light.primary_bathroom_overhead, light.primary_bathroom_sconce, light.primary_bathroom_skylight, light.primary_bedroom_art, light.primary_bedroom_overhead, light.primary_closet_lights, light.primary_toilet_light, light.stairway_art, light.stairway_skylight, light.switchlinc_relay_dual_band_50_fc_23, light.switchlinc_relay_dual_band_51_1d_3f, light.tom_s_lamp, light.tom_s_office_overhead
- Covers/shades referenced: 
- Assist satellites referenced: 
- Person entities referenced: 
- Presence entities referenced: 
- Calendars/todo referenced: 
- Labels used: abilities_concierge, policy
- Areas used: 
- Rooms inferred: 
- Fallback behavior: No explicit fallback detected in extracted chain
- Error handling behavior: No explicit error handler visible in extracted YAML
- Silent/no-speech behavior: Likely silent success path
- Logging behavior: No explicit error handler visible in extracted YAML
- State capture behavior: State capture/update observed
- State restore behavior: No explicit restore call observed
- Learning behavior: Learning/profile writes observed
- Cooldown/suppression behavior: Cooldown/suppression helper pattern present
- Guardrail behavior: Policy/guardrail markers present
- Scope classification: room/entity scoped

#### automation.concierge_voice_entry_ha_voice
- Friendly name: Concierge â€“ Voice Entry (HA Voice)
- Labels: guest, abilities_concierge, policy
- Triggers: {"trigger":"conversation","command":["what can I do here","what can I do","what can I say","help","what voice commands can I use","what can I control","what can I do in here","what room am I in","where am I"]}
- Conditions: 
- Actions: [{"variables":{"room_resolved":"{{ area_id(trigger.device_id) }}"}},{"condition":"template","value_template":"{{ room_resolved is not none and room_resolved != \u0027\u0027 }}"},{"action":"script.room_abilities_speak_unified","data":{"room":"{{ room_resolved }}"}}]
- Called scripts (direct): script.room_abilities_speak_unified
- Called scripts (transitive): script.ensure_main_living_area_sonos_group, script.room_abilities_speak_unified, script.sonos_speak_with_ducking_room, script.voice_assistant_speak_fallback
- Called services (chain): assist_satellite.announce, media_player.join, media_player.media_play, media_player.volume_set, persistent_notification.create, tts.cloud_say, tts.speak
- Helpers read: 
- Helpers written: 
- Template sensors read: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: media_player.kitchen, media_player.kitchen_sonos, media_player.living_room_sonos
- Lights referenced: 
- Covers/shades referenced: 
- Assist satellites referenced: assist_satellite.primary_bedroom
- Person entities referenced: 
- Presence entities referenced: 
- Calendars/todo referenced: 
- Labels used: guest, abilities_concierge, policy
- Areas used: 
- Rooms inferred: 
- Fallback behavior: Explicit fallback/refusal path present
- Error handling behavior: Notification/log path present
- Silent/no-speech behavior: Speech/media output path present
- Logging behavior: Notification/log path present
- State capture behavior: No explicit capture call observed
- State restore behavior: Restore/playback continuation path observed
- Learning behavior: No learning writes observed
- Cooldown/suppression behavior: No explicit cooldown helper detected
- Guardrail behavior: Policy/guardrail markers present
- Scope classification: guest-default / room-scoped voice flow

#### automation.concierge_follow_up_commands_ha_voice
- Friendly name: Concierge â€“ Follow-Up Commands (HA Voice)
- Labels: abilities_concierge, policy
- Triggers: {"trigger":"conversation","command":["lamps","lamps on","lamps off","turn on the lamps","turn off the lamps","turn on lamps","turn off lamps","lights","lights on","lights off","turn on the lights","turn off the lights","turn on lights","turn off lights","lights usual","usual lights","open shades","open the shades","shades open","close shades","close the shades","shades close","open blinds","open the blinds","close blinds","close the blinds","music","music play","music pause","music stop","music off","play music","pause music","stop music","tv","tv on","turn on the tv","tv off","turn off the tv","television","television on","turn on the television","television off","turn off the television"]}
- Conditions: 
- Actions: [{"variables":{"room_resolved":"{{ area_id(trigger.device_id) }}","spoken":"{{ trigger.sentence | lower }}","pre_action_delay":"00:00:00.3"}},{"condition":"template","value_template":"{{ room_resolved is not none }}"},{"variables":{"room_entities":"{{ area_entities(room_resolved) | default([]) }}","room_lights":"{{ expand(room_entities)\n   | selectattr(\u0027domain\u0027,\u0027eq\u0027,\u0027light\u0027)\n   | map(attribute=\u0027entity_id\u0027)\n   | list }}","lamps":"{{ label_devices(\u0027Lamps\u0027)\n   | map(\u0027device_entities\u0027)\n   | sum(start=[])\n   | intersect(room_lights)\n   | list }}","labeled_overhead_lights":"{{ label_devices(\u0027Lights\u0027)\n   | map(\u0027device_entities\u0027)\n   | sum(start=[])\n   | intersect(room_lights)\n   | reject(\u0027in\u0027, lamps)\n   | list }}","unlabeled_lights":"{{ room_lights\n   | reject(\u0027in\u0027, lamps)\n   | reject(\u0027in\u0027, labeled_overhead_lights)\n   | list }}","overhead_lights":"{{ (labeled_overhead_lights + unlabeled_lights) | unique | list }}","sonos_players":"{{ expand(room_entities)\n   | selectattr(\u0027domain\u0027,\u0027eq\u0027,\u0027media_player\u0027)\n   | map(attribute=\u0027entity_id\u0027)\n   | select(\u0027search\u0027,\u0027sonos\u0027)\n   | list }}","tv_players":"{{ label_devices(\u0027AppleTV\u0027)\n   | map(\u0027device_entities\u0027)\n   | sum(start=[])\n   | select(\u0027search\u0027,\u0027^media_player\\\\.\u0027)\n   | list }}"}},{"variables":{"want_off":"{{ \u0027 off\u0027 in (\u0027 \u0027 ~ spoken) or spoken.startswith(\u0027turn off\u0027) }}","want_open":"{{ \u0027open\u0027 in spoken }}","want_close":"{{ \u0027close\u0027 in spoken }}","want_pause":"{{ \u0027pause\u0027 in spoken }}","want_stop":"{{ \u0027stop\u0027 in spoken }}","want_usual":"{{ \u0027usual\u0027 in spoken }}","is_lamps":"{{ \u0027lamp\u0027 in spoken }}","is_lights":"{{ \u0027light\u0027 in spoken and not is_lamps }}","is_shades":"{{ \u0027shade\u0027 in spoken or \u0027blind\u0027 in spoken }}","is_music":"{{ \u0027music\u0027 in spoken }}","is_tv":"{{ \u0027tv\u0027 in spoken or \u0027television\u0027 in spoken }}"}},{"variables":{"lamps_message":"{{ \u0027Turning off the lamps.\u0027 if want_off else \u0027Turning on the lamps.\u0027 }}","lights_message":"{{ \u0027Turning off the lights.\u0027 if want_off else \u0027Turning on the lights.\u0027 }}","lights_usual_message":"Setting the lights to their usual levels.","shades_open_message":"Opening the shades.","shades_close_message":"Closing the shades.","music_message":"{% if want_pause %}Pausing music. {% elif want_stop %}Stopping music. {% else %}Playing music.{% endif %}","tv_message":"{{ \u0027Turning off the TV.\u0027 if want_off else \u0027Turning on the TV.\u0027 }}"}},{"variables":{"shade_open_scene":"{% set m = {\n  \u0027den\u0027: \u0027scene.powerview_controller_ods\u0027,\n  \u0027dining_room\u0027: \u0027scene.powerview_controller_odrs\u0027,\n  \u0027living_room\u0027: \u0027scene.powerview_controller_olrs\u0027,\n  \u0027primary_bedroom\u0027: \u0027scene.powerview_controller_ombs\u0027\n} %} {{ m.get(room_resolved) }}","shade_close_scene":"{% set m = {\n  \u0027den\u0027: \u0027scene.powerview_controller_cds\u0027,\n  \u0027dining_room\u0027: \u0027scene.powerview_controller_cdrs\u0027,\n  \u0027living_room\u0027: \u0027scene.powerview_controller_clrs\u0027,\n  \u0027primary_bedroom\u0027: \u0027scene.powerview_controller_cmbs\u0027\n} %} {{ m.get(room_resolved) }}"}},{"choose":[{"conditions":[{"condition":"template","value_template":"{{ is_lamps and lamps | length \u003e 0 }}"}],"sequence":[{"parallel":[{"action":"script.sonos_speak_with_ducking_room","data":{"room":"{{ room_resolved }}","message":"{{ lamps_message }}"}},{"sequence":[{"delay":"{{ pre_action_delay }}"},{"choose":[{"conditions":[{"condition":"template","value_template":"{{ want_off }}"}],"sequence":[{"action":"light.turn_off","target":{"entity_id":"{{ lamps }}"}}]}],"default":[{"data":{"room":"{{ room_resolved }}"},"action":"script.turn_on_lamps_usual_room"}]}]}]}]},{"conditions":[{"condition":"template","value_template":"{{ is_lights and overhead_lights | length \u003e 0 }}"}],"sequence":[{"parallel":[{"action":"script.sonos_speak_with_ducking_room","data":{"room":"{{ room_resolved }}","message":"{{ lights_usual_message if not want_off else lights_message }}"}},{"sequence":[{"delay":"{{ pre_action_delay }}"},{"choose":[{"conditions":[{"condition":"template","value_template":"{{ want_off }}"}],"sequence":[{"action":"light.turn_off","target":{"entity_id":"{{ overhead_lights }}"}}]}],"default":[{"data":{"room":"{{ room_resolved }}"},"action":"script.turn_on_lights_usual_room"}]}]}]}]},{"conditions":[{"condition":"template","value_template":"{{ is_shades }}"}],"sequence":[{"choose":[{"conditions":[{"condition":"template","value_template":"{{ want_open and shade_open_scene is not none }}"}],"sequence":[{"parallel":[{"action":"script.sonos_speak_with_ducking_room","data":{"room":"{{ room_resolved }}","message":"{{ shades_open_message }}"}},{"sequence":[{"delay":"{{ pre_action_delay }}"},{"action":"scene.turn_on","target":{"entity_id":"{{ shade_open_scene }}"}}]}]}]},{"conditions":[{"condition":"template","value_template":"{{ want_close and shade_close_scene is not none }}"}],"sequence":[{"parallel":[{"action":"script.sonos_speak_with_ducking_room","data":{"room":"{{ room_resolved }}","message":"{{ shades_close_message }}"}},{"sequence":[{"delay":"{{ pre_action_delay }}"},{"action":"scene.turn_on","target":{"entity_id":"{{ shade_close_scene }}"}}]}]}]}]}]},{"conditions":[{"condition":"template","value_template":"{{ is_music and sonos_players | length \u003e 0 }}"}],"sequence":[{"parallel":[{"action":"script.sonos_speak_with_ducking_room","data":{"room":"{{ room_resolved }}","message":"{{ music_message }}"}},{"sequence":[{"delay":"{{ pre_action_delay }}"},{"choose":[{"conditions":[{"condition":"template","value_template":"{{ want_pause }}"}],"sequence":[{"action":"media_player.media_pause","target":{"entity_id":"{{ sonos_players }}"}}]},{"conditions":[{"condition":"template","value_template":"{{ want_stop }}"}],"sequence":[{"action":"media_player.media_stop","target":{"entity_id":"{{ sonos_players }}"}}]}],"default":[{"action":"media_player.media_play","target":{"entity_id":"{{ sonos_players }}"}}]}]}]}]},{"conditions":[{"condition":"template","value_template":"{{ is_tv and tv_players | length \u003e 0 }}"}],"sequence":[{"parallel":[{"action":"script.sonos_speak_with_ducking_room","data":{"room":"{{ room_resolved }}","message":"{{ tv_message }}"}},{"sequence":[{"delay":"{{ pre_action_delay }}"},{"choose":[{"conditions":[{"condition":"template","value_template":"{{ want_off }}"}],"sequence":[{"target":{"entity_id":"{{ tv_players }}"},"action":"media_player.turn_off"}]}],"default":[{"target":{"entity_id":"{{ tv_players }}"},"action":"media_player.turn_on"}]}]}]}]}]}]
- Called scripts (direct): script.sonos_speak_with_ducking_room, script.turn_on_lamps_usual_room, script.turn_on_lights_usual_room
- Called scripts (transitive): script.sonos_speak_with_ducking_room, script.turn_on_lamps_usual_room, script.turn_on_lights_usual_room, script.voice_assistant_speak_fallback
- Called services (chain): assist_satellite.announce, light.turn_off, light.turn_on, media_player.media_pause, media_player.media_play, media_player.media_stop, media_player.turn_off, media_player.turn_on, media_player.volume_set, persistent_notification.create, scene.turn_on, tts.cloud_say, tts.speak
- Helpers read: 
- Helpers written: 
- Template sensors read: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: light.split
- Covers/shades referenced: 
- Assist satellites referenced: assist_satellite.primary_bedroom
- Person entities referenced: 
- Presence entities referenced: 
- Calendars/todo referenced: 
- Labels used: abilities_concierge, policy
- Areas used: 
- Rooms inferred: 
- Fallback behavior: Explicit fallback/refusal path present
- Error handling behavior: Notification/log path present
- Silent/no-speech behavior: Speech/media output path present
- Logging behavior: Notification/log path present
- State capture behavior: No explicit capture call observed
- State restore behavior: Restore/playback continuation path observed
- Learning behavior: No learning writes observed
- Cooldown/suppression behavior: No explicit cooldown helper detected
- Guardrail behavior: Policy/guardrail markers present
- Scope classification: room/entity scoped

#### automation.concierge_intentional_learning_ha_voice
- Friendly name: Concierge â€” Intentional Learning (HA Voice)
- Labels: abilities_concierge, policy
- Triggers: {"trigger":"conversation","command":["this is good","that\u0027s good","that\u0027s perfect","remember this","save this","remember lighting","remember volume"]}
- Conditions: 
- Actions: [{"variables":{"pre_action_delay":"00:00:00.2","room_resolved":"{{ area_id(trigger.device_id) }}","spoken":"{{ trigger.sentence | lower }}"}},{"condition":"template","value_template":"{{ room_resolved is not none }}"},{"variables":{"room_entities":"{{ area_entities(room_resolved) | default([]) }}","room_lights":"{{ expand(room_entities)\n   | selectattr(\u0027domain\u0027,\u0027eq\u0027,\u0027light\u0027)\n   | map(attribute=\u0027entity_id\u0027)\n   | list }}","lights_on_count":"{% set ns = namespace(n=0) %} {% for l in room_lights %}\n  {% if is_state(l, \u0027on\u0027) and state_attr(l, \u0027brightness\u0027) is not none %}\n    {% set ns.n = ns.n + 1 %}\n  {% endif %}\n{% endfor %} {{ ns.n }}","sonos_players":"{{ expand(room_entities)\n   | selectattr(\u0027domain\u0027,\u0027eq\u0027,\u0027media_player\u0027)\n   | map(attribute=\u0027entity_id\u0027)\n   | select(\u0027search\u0027,\u0027sonos\u0027)\n   | list }}","has_sonos":"{{ sonos_players | length \u003e 0 }}","force_lighting":"{{ \u0027lighting\u0027 in spoken }}","force_volume":"{{ \u0027volume\u0027 in spoken }}"}},{"choose":[{"conditions":[{"condition":"template","value_template":"{{ force_lighting and lights_on_count | int \u003e 0 }}"}],"sequence":[{"parallel":[{"action":"script.sonos_speak_with_ducking_room","data":{"room":"{{ room_resolved }}","message":"Got it. Iâ€™ll remember this lighting."}},{"sequence":[{"delay":"{{ pre_action_delay }}"},{"action":"script.learn_lighting_usual_room","data":{"room":"{{ room_resolved }}"}}]}]}]},{"conditions":[{"condition":"template","value_template":"{{ force_volume and has_sonos }}"}],"sequence":[{"parallel":[{"action":"script.sonos_speak_with_ducking_room","data":{"room":"{{ room_resolved }}","message":"Got it. Iâ€™ll remember this volume."}},{"sequence":[{"delay":"{{ pre_action_delay }}"},{"action":"script.learn_music_volume_room","data":{"room":"{{ room_resolved }}"}}]}]}]},{"conditions":[{"condition":"template","value_template":"{{ not force_volume and lights_on_count | int \u003e 0 }}"}],"sequence":[{"parallel":[{"action":"script.sonos_speak_with_ducking_room","data":{"room":"{{ room_resolved }}","message":"Got it. Iâ€™ll remember this lighting."}},{"sequence":[{"delay":"{{ pre_action_delay }}"},{"action":"script.learn_lighting_usual_room","data":{"room":"{{ room_resolved }}"}}]}]}]},{"conditions":[{"condition":"template","value_template":"{{ has_sonos }}"}],"sequence":[{"parallel":[{"action":"script.sonos_speak_with_ducking_room","data":{"room":"{{ room_resolved }}","message":"Got it. Iâ€™ll remember this volume."}},{"sequence":[{"delay":"{{ pre_action_delay }}"},{"action":"script.learn_music_volume_room","data":{"room":"{{ room_resolved }}"}}]}]}]}]}]
- Called scripts (direct): script.sonos_speak_with_ducking_room, script.learn_lighting_usual_room, script.learn_music_volume_room
- Called scripts (transitive): script.learn_lighting_usual_room, script.learn_music_volume_room, script.sonos_speak_with_ducking_room, script.voice_assistant_speak_fallback
- Called services (chain): assist_satellite.announce, input_datetime.set_datetime, input_number.set_value, input_text.set_value, media_player.media_play, media_player.volume_set, persistent_notification.create, tts.cloud_say, tts.speak
- Helpers read: input_datetime.lamp_brightness_profile_last_updated, input_datetime.speaker_profile_last_updated
- Helpers written: input_datetime.set_datetime, input_number.set_value, input_text.set_value
- Template sensors read: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: light.split
- Covers/shades referenced: 
- Assist satellites referenced: assist_satellite.primary_bedroom
- Person entities referenced: 
- Presence entities referenced: 
- Calendars/todo referenced: 
- Labels used: abilities_concierge, policy
- Areas used: 
- Rooms inferred: 
- Fallback behavior: Explicit fallback/refusal path present
- Error handling behavior: Notification/log path present
- Silent/no-speech behavior: Speech/media output path present
- Logging behavior: Notification/log path present
- State capture behavior: State capture/update observed
- State restore behavior: Restore/playback continuation path observed
- Learning behavior: Learning/profile writes observed
- Cooldown/suppression behavior: Cooldown/suppression helper pattern present
- Guardrail behavior: Policy/guardrail markers present
- Scope classification: room/entity scoped

#### automation.music_genre_observe_playback_all_sources
- Friendly name: Music Genre â€“ Observe Playback (All Sources)
- Labels: abilities_concierge
- Triggers: {"entity_id":["input_text.den_speaker_profile_last_media","input_text.living_room_speaker_profile_last_media","input_text.powder_room_speaker_profile_last_media","input_text.kitchen_speaker_profile_last_media","input_text.primary_bathroom_speaker_profile_last_media","input_text.primary_bedroom_speaker_profile_last_media","input_text.downstairs_bathroom_speaker_profile_last_media","input_text.tom_s_office_speaker_profile_last_media","input_text.david_s_office_speaker_profile_last_media","input_text.guest_bedroom_speaker_profile_last_media","input_text.guest_bathroom_speaker_profile_last_media","media_player.outside_sonos"],"trigger":"state"}
- Conditions: [{"condition":"template","value_template":"{{ trigger.to_state.state | length \u003e 0 }}"},{"condition":"template","value_template":"{% set s = trigger.to_state.state | lower %} {{ not (\n  \u0027pink_noise\u0027 in s or\n  \u0027pink noise\u0027 in s or\n  \u0027pink_noise_wav\u0027 in s\n) }}"}]
- Actions: [{"variables":{"media":"{{ trigger.to_state.state | lower }}","genre":"{% if \u0027jazz swing\u0027 in media %}jazz_swing {% elif \u0027jazz vocal\u0027 in media %}jazz_vocal {% elif \u0027smooth jazz\u0027 in media %}smooth_jazz {% elif \u0027jazz\u0027 in media %}jazz {% elif \u0027soundtrack\u0027 in media or \u0027lord of the rings\u0027 in media %}soundtrack {% elif \u0027musical\u0027 in media or \u0027broadway\u0027 in media %}musicals {% elif \u0027opera\u0027 in media %}opera {% elif \u0027classical\u0027 in media %}classical {% elif \u0027choral\u0027 in media %}choral {% elif \u0027big band\u0027 in media %}big_band {% elif \u0027latin\u0027 in media %}latin {% elif \u0027country\u0027 in media %}country {% elif \u0027rock\u0027 in media %}rock {% elif \u0027pop\u0027 in media %}pop {% elif \u0027r\u0026b\u0027 in media or \u0027rnb\u0027 in media %}rnb {% else %}unknown {% endif %}"}},{"target":{"entity_id":"counter.music_genre_{{ genre }}"},"action":"counter.increment"}]
- Called scripts (direct): 
- Called scripts (transitive): 
- Called services (chain): counter.increment
- Helpers read: input_text.david_s_office_speaker_profile_last_media, input_text.den_speaker_profile_last_media, input_text.downstairs_bathroom_speaker_profile_last_media, input_text.guest_bathroom_speaker_profile_last_media, input_text.guest_bedroom_speaker_profile_last_media, input_text.kitchen_speaker_profile_last_media, input_text.living_room_speaker_profile_last_media, input_text.powder_room_speaker_profile_last_media, input_text.primary_bathroom_speaker_profile_last_media, input_text.primary_bedroom_speaker_profile_last_media, input_text.tom_s_office_speaker_profile_last_media
- Helpers written: counter.increment
- Template sensors read: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: media_player.outside_sonos
- Lights referenced: 
- Covers/shades referenced: 
- Assist satellites referenced: 
- Person entities referenced: 
- Presence entities referenced: 
- Calendars/todo referenced: 
- Labels used: abilities_concierge
- Areas used: 
- Rooms inferred: 
- Fallback behavior: No explicit fallback detected in extracted chain
- Error handling behavior: No explicit error handler visible in extracted YAML
- Silent/no-speech behavior: Likely silent success path
- Logging behavior: No explicit error handler visible in extracted YAML
- State capture behavior: State capture/update observed
- State restore behavior: No explicit restore call observed
- Learning behavior: Learning/profile writes observed
- Cooldown/suppression behavior: Cooldown/suppression helper pattern present
- Guardrail behavior: No explicit guardrail marker in labels
- Scope classification: room/entity scoped

#### automation.music_capture_last_media_on_playback
- Friendly name: Music â€“ Capture Last Media (Robust)
- Labels: abilities_concierge
- Triggers: [{"entity_id":["media_player.den_sonos","media_player.living_room_sonos","media_player.kitchen_sonos","media_player.primary_bedroom_sonos","media_player.tom_s_office_sonos","media_player.davids_office_sonos","media_player.downstairs_bathroom_sonos","media_player.powder_room_sonos","media_player.guest_bedroom_sonos","media_player.primary_bathroom_sonos","media_player.outside_sonos"],"attribute":"media_title","trigger":"state"},{"entity_id":["media_player.den_sonos","media_player.living_room_sonos","media_player.kitchen_sonos","media_player.primary_bedroom_sonos","media_player.tom_s_office_sonos","media_player.davids_office_sonos","media_player.downstairs_bathroom_sonos","media_player.powder_room_sonos","media_player.guest_bedroom_sonos","media_player.primary_bathroom_sonos","media_player.outside_sonos"],"attribute":"media_content_id","trigger":"state"},{"entity_id":["media_player.den_sonos","media_player.living_room_sonos","media_player.kitchen_sonos","media_player.primary_bedroom_sonos","media_player.tom_s_office_sonos","media_player.davids_office_sonos","media_player.downstairs_bathroom_sonos","media_player.powder_room_sonos","media_player.guest_bedroom_sonos","media_player.primary_bathroom_sonos","media_player.outside_sonos"],"to":"playing","trigger":"state"}]
- Conditions: [{"condition":"template","value_template":"{{ states(trigger.entity_id) == \u0027playing\u0027 }}"},{"condition":"template","value_template":"{{ area_id(trigger.entity_id) not in [\u0027\u0027,\u0027unknown\u0027] }}"},{"condition":"template","value_template":"{% set t = state_attr(trigger.entity_id, \u0027media_title\u0027) | default(\u0027\u0027, true) | lower %} {{ \u0027pink_noise\u0027 not in t and \u0027pink noise\u0027 not in t }}"}]
- Actions: [{"variables":{"area_slug":"{{ area_id(trigger.entity_id) }}"}},{"data":{"room":"{{ area_slug }}","started_by":"observed"},"action":"script.update_last_media_room"},{"delay":"00:00:01"},{"data":{"room":"{{ area_slug }}"},"action":"script.determine_music_genre_audit"}]
- Called scripts (direct): script.update_last_media_room, script.determine_music_genre_audit
- Called scripts (transitive): script.determine_music_genre_audit, script.update_last_media_room
- Called services (chain): ai_task.generate_data, input_text.set_value
- Helpers read: 
- Helpers written: input_text.set_value
- Template sensors read: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: media_player.davids_office_sonos, media_player.den_sonos, media_player.downstairs_bathroom_sonos, media_player.guest_bedroom_sonos, media_player.kitchen_sonos, media_player.living_room_sonos, media_player.outside_sonos, media_player.powder_room_sonos, media_player.primary_bathroom_sonos, media_player.primary_bedroom_sonos, media_player.tom_s_office_sonos
- Lights referenced: 
- Covers/shades referenced: 
- Assist satellites referenced: 
- Person entities referenced: 
- Presence entities referenced: 
- Calendars/todo referenced: 
- Labels used: abilities_concierge
- Areas used: 
- Rooms inferred: 
- Fallback behavior: No explicit fallback detected in extracted chain
- Error handling behavior: No explicit error handler visible in extracted YAML
- Silent/no-speech behavior: Likely silent success path
- Logging behavior: No explicit error handler visible in extracted YAML
- State capture behavior: State capture/update observed
- State restore behavior: No explicit restore call observed
- Learning behavior: Learning/profile writes observed
- Cooldown/suppression behavior: No explicit cooldown helper detected
- Guardrail behavior: No explicit guardrail marker in labels
- Scope classification: room/entity scoped

#### automation.primary_bedroom_alarm_started
- Friendly name: Primary Bedroom â€“ Alarm Started
- Labels: abilities_concierge
- Triggers: {"entity_id":"input_boolean.alarm_primary_bedroom_ringing","to":"on","trigger":"state"}
- Conditions: 
- Actions: [{"data":{"room":"primary_bedroom"},"action":"script.turn_on_lamps_usual"},{"action":"script.primary_bedroom_play_alarm_chime"}]
- Called scripts (direct): script.turn_on_lamps_usual, script.primary_bedroom_play_alarm_chime
- Called scripts (transitive): script.primary_bedroom_play_alarm_chime, script.sonos_speak_with_ducking_room, script.turn_on_lamps_usual, script.voice_assistant_speak_fallback
- Called services (chain): assist_satellite.announce, media_player.media_play, media_player.volume_set, persistent_notification.create, tts.cloud_say, tts.speak
- Helpers read: input_boolean.alarm_primary_bedroom_ringing
- Helpers written: 
- Template sensors read: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers/shades referenced: 
- Assist satellites referenced: assist_satellite.primary_bedroom
- Person entities referenced: 
- Presence entities referenced: 
- Calendars/todo referenced: 
- Labels used: abilities_concierge
- Areas used: 
- Rooms inferred: 
- Fallback behavior: Explicit fallback/refusal path present
- Error handling behavior: Notification/log path present
- Silent/no-speech behavior: Speech/media output path present
- Logging behavior: Notification/log path present
- State capture behavior: No explicit capture call observed
- State restore behavior: Restore/playback continuation path observed
- Learning behavior: No learning writes observed
- Cooldown/suppression behavior: No explicit cooldown helper detected
- Guardrail behavior: Policy/guardrail markers present
- Scope classification: household scoped or routing scoped

#### automation.primary_bedroom_alarm_repeat
- Friendly name: Primary Bedroom â€“ Alarm Repeat
- Labels: abilities_concierge
- Triggers: {"entity_id":"input_boolean.alarm_primary_bedroom_ringing","to":"on","trigger":"state"}
- Conditions: 
- Actions: {"repeat":{"while":[{"condition":"state","entity_id":"input_boolean.alarm_primary_bedroom_ringing","state":"on"}],"sequence":[{"delay":"00:00:45"},{"action":"script.primary_bedroom_play_alarm_chime"}]}}
- Called scripts (direct): script.primary_bedroom_play_alarm_chime
- Called scripts (transitive): script.primary_bedroom_play_alarm_chime, script.sonos_speak_with_ducking_room, script.voice_assistant_speak_fallback
- Called services (chain): assist_satellite.announce, media_player.media_play, media_player.volume_set, persistent_notification.create, tts.cloud_say, tts.speak
- Helpers read: input_boolean.alarm_primary_bedroom_ringing
- Helpers written: 
- Template sensors read: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers/shades referenced: 
- Assist satellites referenced: assist_satellite.primary_bedroom
- Person entities referenced: 
- Presence entities referenced: 
- Calendars/todo referenced: 
- Labels used: abilities_concierge
- Areas used: 
- Rooms inferred: 
- Fallback behavior: Explicit fallback/refusal path present
- Error handling behavior: Notification/log path present
- Silent/no-speech behavior: Speech/media output path present
- Logging behavior: Notification/log path present
- State capture behavior: No explicit capture call observed
- State restore behavior: Restore/playback continuation path observed
- Learning behavior: No learning writes observed
- Cooldown/suppression behavior: No explicit cooldown helper detected
- Guardrail behavior: Policy/guardrail markers present
- Scope classification: household scoped or routing scoped

#### automation.primary_bedroom_alarm_escalation
- Friendly name: Primary Bedroom â€“ Alarm Escalation
- Labels: abilities_concierge
- Triggers: {"entity_id":"input_boolean.alarm_primary_bedroom_ringing","to":"on","for":"00:02:00","trigger":"state"}
- Conditions: {"condition":"state","entity_id":"input_boolean.alarm_primary_bedroom_ringing","state":"on"}
- Actions: {"data":{"room":"primary_bedroom","media_source":"media-source://media_source/local/music/morning_ambient.mp3"},"action":"script.room_audio_duck_and_play"}
- Called scripts (direct): script.room_audio_duck_and_play
- Called scripts (transitive): script.room_audio_duck_and_play
- Called services (chain): 
- Helpers read: input_boolean.alarm_primary_bedroom_ringing
- Helpers written: 
- Template sensors read: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers/shades referenced: 
- Assist satellites referenced: 
- Person entities referenced: 
- Presence entities referenced: 
- Calendars/todo referenced: 
- Labels used: abilities_concierge
- Areas used: 
- Rooms inferred: 
- Fallback behavior: No explicit fallback detected in extracted chain
- Error handling behavior: No explicit error handler visible in extracted YAML
- Silent/no-speech behavior: Likely silent success path
- Logging behavior: No explicit error handler visible in extracted YAML
- State capture behavior: No explicit capture call observed
- State restore behavior: No explicit restore call observed
- Learning behavior: No learning writes observed
- Cooldown/suppression behavior: No explicit cooldown helper detected
- Guardrail behavior: No explicit guardrail marker in labels
- Scope classification: household scoped or routing scoped

#### automation.primary_bedroom_alarm_stop
- Friendly name: Primary Bedroom â€“ Alarm Stop
- Labels: abilities_concierge
- Triggers: {"entity_id":"input_boolean.alarm_primary_bedroom_ringing","to":"off","trigger":"state"}
- Conditions: 
- Actions: {"action":"script.room_audio_restore"}
- Called scripts (direct): script.room_audio_restore
- Called scripts (transitive): script.room_audio_restore
- Called services (chain): 
- Helpers read: input_boolean.alarm_primary_bedroom_ringing
- Helpers written: 
- Template sensors read: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers/shades referenced: 
- Assist satellites referenced: 
- Person entities referenced: 
- Presence entities referenced: 
- Calendars/todo referenced: 
- Labels used: abilities_concierge
- Areas used: 
- Rooms inferred: 
- Fallback behavior: No explicit fallback detected in extracted chain
- Error handling behavior: No explicit error handler visible in extracted YAML
- Silent/no-speech behavior: Likely silent success path
- Logging behavior: No explicit error handler visible in extracted YAML
- State capture behavior: No explicit capture call observed
- State restore behavior: No explicit restore call observed
- Learning behavior: No learning writes observed
- Cooldown/suppression behavior: No explicit cooldown helper detected
- Guardrail behavior: No explicit guardrail marker in labels
- Scope classification: household scoped or routing scoped

#### automation.voice_play_music
- Friendly name: Voice â€“ Play Music
- Labels: automation_helper, abilities_concierge
- Triggers: {"command":["play music","start music"],"trigger":"conversation"}
- Conditions: 
- Actions: [{"variables":{"room":"{{ area_id(trigger.device_id) }}"}},{"action":"script.start_music_usual_room","data":{"room":"{{ room }}"}}]
- Called scripts (direct): script.start_music_usual_room
- Called scripts (transitive): script.resolve_music_player_room, script.start_music_usual_room, script.update_last_media_room
- Called services (chain): input_text.set_value, media_player.media_play, media_player.play_media, media_player.volume_set
- Helpers read: 
- Helpers written: input_text.set_value
- Template sensors read: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: media_player.living_room_sonos
- Lights referenced: 
- Covers/shades referenced: 
- Assist satellites referenced: 
- Person entities referenced: 
- Presence entities referenced: 
- Calendars/todo referenced: 
- Labels used: automation_helper, abilities_concierge
- Areas used: 
- Rooms inferred: 
- Fallback behavior: No explicit fallback detected in extracted chain
- Error handling behavior: No explicit error handler visible in extracted YAML
- Silent/no-speech behavior: Speech/media output path present
- Logging behavior: No explicit error handler visible in extracted YAML
- State capture behavior: State capture/update observed
- State restore behavior: Restore/playback continuation path observed
- Learning behavior: Learning/profile writes observed
- Cooldown/suppression behavior: No explicit cooldown helper detected
- Guardrail behavior: No explicit guardrail marker in labels
- Scope classification: room/entity scoped

#### automation.voice_continue_playing
- Friendly name: Voice â€“ Continue Playing
- Labels: automation_helper, abilities_concierge
- Triggers: {"command":["continue playing","resume music"],"trigger":"conversation"}
- Conditions: 
- Actions: [{"variables":{"room":"{{ area_id(trigger.device_id) }}"}},{"action":"script.continue_playing_room","data":{"room":"{{ room }}"}}]
- Called scripts (direct): script.continue_playing_room
- Called scripts (transitive): script.continue_playing_room, script.resolve_music_player_room, script.room_speak_sonos, script.start_music_usual_room, script.update_last_media_room
- Called services (chain): input_text.set_value, media_player.media_play, media_player.play_media, media_player.volume_set
- Helpers read: 
- Helpers written: input_text.set_value
- Template sensors read: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: media_player.living_room_sonos
- Lights referenced: 
- Covers/shades referenced: 
- Assist satellites referenced: 
- Person entities referenced: 
- Presence entities referenced: 
- Calendars/todo referenced: 
- Labels used: automation_helper, abilities_concierge
- Areas used: 
- Rooms inferred: 
- Fallback behavior: No explicit fallback detected in extracted chain
- Error handling behavior: No explicit error handler visible in extracted YAML
- Silent/no-speech behavior: Speech/media output path present
- Logging behavior: No explicit error handler visible in extracted YAML
- State capture behavior: State capture/update observed
- State restore behavior: Restore/playback continuation path observed
- Learning behavior: Learning/profile writes observed
- Cooldown/suppression behavior: No explicit cooldown helper detected
- Guardrail behavior: No explicit guardrail marker in labels
- Scope classification: room/entity scoped

#### automation.voice_play_jazz
- Friendly name: Voice â€“ Music Follow-Ups
- Labels: automation_helper, abilities_concierge
- Triggers: {"command":["continue playing","resume music","stop music","pause music","music off","surprise me","play ambient","play jazz","play jazz vocal","play jazz swing","play smooth jazz","play classical","play pop","play rock","play country","play easy listening","play latin","play opera","play soundtrack","play musicals","play r and b","play r\u0026b","play news","play 80s","play 80\u0027s","play eighties","play artist {artist}","what\u0027s playing","what is this music","what music is this","why did you play this","why is music playing"],"trigger":"conversation"}
- Conditions: 
- Actions: {"choose":[{"conditions":[{"condition":"template","value_template":"{{ spoken_clean in [\u0027stop music\u0027,\u0027pause music\u0027,\u0027music off\u0027] }}"}],"sequence":[{"variables":{"room_players":"{{ expand(area_entities(room))\n   | selectattr(\u0027domain\u0027,\u0027eq\u0027,\u0027media_player\u0027)\n   | map(attribute=\u0027entity_id\u0027)\n   | select(\u0027search\u0027,\u0027sonos\u0027)\n   | list }}","active_player":"{% set active = room_players | select(\u0027is_state\u0027,\u0027playing\u0027) | list %} {{ active[0] if active | length \u003e 0 else \u0027\u0027 }}"}},{"condition":"template","value_template":"{{ active_player != \u0027\u0027 }}"},{"action":"media_player.media_pause","target":{"entity_id":"{{ active_player }}"}}]},{"conditions":[{"condition":"template","value_template":"{{ spoken_clean in [\u0027continue playing\u0027,\u0027resume music\u0027] }}"}],"sequence":[{"action":"script.continue_playing_room","data":{"room":"{{ room }}"}}]},{"conditions":[{"condition":"template","value_template":"{{ spoken_clean == \u0027surprise me\u0027 }}"}],"sequence":[{"action":"script.surprise_me_room","data":{"room":"{{ room }}"}}]},{"conditions":[{"condition":"template","value_template":"{{ matched_genre | length \u003e 0 }}"}],"sequence":[{"action":"script.play_genre_room","data":{"room":"{{ room }}","genre":"{{ matched_genre }}"}}]},{"conditions":[{"condition":"template","value_template":"{{ trigger.slots.artist is defined\n   and (trigger.slots.artist | string | length \u003e 0) }}"}],"sequence":[{"action":"script.play_artist_room","data":{"room":"{{ room }}","artist":"{{ trigger.slots.artist }}"}}]},{"conditions":[{"condition":"template","value_template":"{{ spoken_clean in [\u0027whats playing\u0027,\u0027what is this music\u0027,\u0027what music is this\u0027] }}"}],"sequence":[{"action":"script.whats_playing_room","data":{"room":"{{ room }}"}}]},{"conditions":[{"condition":"template","value_template":"{{ spoken_clean in [\u0027why did you play this\u0027,\u0027why is music playing\u0027] }}"}],"sequence":[{"action":"script.why_did_you_play_this_room","data":{"room":"{{ room }}"}}]}]}
- Called scripts (direct): script.continue_playing_room, script.surprise_me_room, script.play_genre_room, script.play_artist_room, script.whats_playing_room, script.why_did_you_play_this_room
- Called scripts (transitive): script.continue_playing_room, script.ensure_main_living_area_sonos_group, script.play_artist_room, script.play_genre_room, script.resolve_music_player_room, script.room_speak_sonos, script.start_music_usual_room, script.surprise_me_room, script.update_last_media_room, script.whats_playing_room, script.why_did_you_play_this_room
- Called services (chain): input_select.select_option, input_text.set_value, media_player.join, media_player.media_pause, media_player.media_play, media_player.media_stop, media_player.play_media, media_player.volume_set, persistent_notification.create
- Helpers read: input_text.music_genre_uri_map
- Helpers written: input_select.select_option, input_text.set_value
- Template sensors read: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: media_player.kitchen, media_player.kitchen_sonos, media_player.living_room_sonos
- Lights referenced: 
- Covers/shades referenced: 
- Assist satellites referenced: 
- Person entities referenced: 
- Presence entities referenced: 
- Calendars/todo referenced: 
- Labels used: automation_helper, abilities_concierge
- Areas used: 
- Rooms inferred: 
- Fallback behavior: Explicit fallback/refusal path present
- Error handling behavior: Notification/log path present
- Silent/no-speech behavior: Speech/media output path present
- Logging behavior: Notification/log path present
- State capture behavior: State capture/update observed
- State restore behavior: Restore/playback continuation path observed
- Learning behavior: Learning/profile writes observed
- Cooldown/suppression behavior: No explicit cooldown helper detected
- Guardrail behavior: Policy/guardrail markers present
- Scope classification: room/entity scoped

#### automation.learn_music_volume_on_sonos_change
- Friendly name: Learn Music Volume â€“ On Sonos Change
- Labels: automation_helper, abilities_concierge
- Triggers: {"entity_id":["media_player.den_sonos","media_player.living_room_sonos","media_player.kitchen_sonos","media_player.primary_bedroom_sonos","media_player.guest_bedroom_sonos_beam","media_player.powder_room_sonos","media_player.downstairs_bathroom_sonos","media_player.davids_office_sonos","media_player.guest_bathroom_sonos","media_player.tom_s_office_sonos","media_player.primary_bathroom_sonos"],"attribute":"volume_level","trigger":"state"}
- Conditions: [{"condition":"template","value_template":"{{ trigger.from_state is not none\n   and trigger.to_state is not none\n   and trigger.from_state.attributes.volume_level is not none\n   and trigger.to_state.attributes.volume_level is not none\n   and (trigger.to_state.attributes.volume_level\n        | float\n        - trigger.from_state.attributes.volume_level | float)\n        | abs \u003e 0.03 }}\n"},{"condition":"template","value_template":"{{ states(trigger.entity_id) == \u0027playing\u0027 }}"}]
- Actions: [{"delay":"00:00:05"},{"condition":"template","value_template":"{{ states(trigger.entity_id) == \u0027playing\u0027 }}"},{"variables":{"room":"{{ area_name(trigger.entity_id) }}"}},{"action":"script.learn_music_volume_room","data":{"room":"{{ room }}"}}]
- Called scripts (direct): script.learn_music_volume_room
- Called scripts (transitive): script.learn_music_volume_room
- Called services (chain): input_datetime.set_datetime, input_text.set_value
- Helpers read: input_datetime.speaker_profile_last_updated
- Helpers written: input_datetime.set_datetime, input_text.set_value
- Template sensors read: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: media_player.davids_office_sonos, media_player.den_sonos, media_player.downstairs_bathroom_sonos, media_player.guest_bathroom_sonos, media_player.guest_bedroom_sonos_beam, media_player.kitchen_sonos, media_player.living_room_sonos, media_player.powder_room_sonos, media_player.primary_bathroom_sonos, media_player.primary_bedroom_sonos, media_player.tom_s_office_sonos
- Lights referenced: 
- Covers/shades referenced: 
- Assist satellites referenced: 
- Person entities referenced: 
- Presence entities referenced: 
- Calendars/todo referenced: 
- Labels used: automation_helper, abilities_concierge
- Areas used: 
- Rooms inferred: 
- Fallback behavior: No explicit fallback detected in extracted chain
- Error handling behavior: No explicit error handler visible in extracted YAML
- Silent/no-speech behavior: Likely silent success path
- Logging behavior: No explicit error handler visible in extracted YAML
- State capture behavior: State capture/update observed
- State restore behavior: No explicit restore call observed
- Learning behavior: Learning/profile writes observed
- Cooldown/suppression behavior: Cooldown/suppression helper pattern present
- Guardrail behavior: No explicit guardrail marker in labels
- Scope classification: room/entity scoped

#### automation.concierge_shade_percentage_catcher_ha_voice
- Friendly name: Concierge â€“ Shade Percentage Catcher (HA Voice)
- Labels: automation_helper, abilities_concierge, policy
- Triggers: {"trigger":"conversation","command":["set shade {percent}","set shades {percent}","set the shade {percent}","set the shades {percent}","set shade to {percent}","set shades to {percent}","set the shade to {percent}","set the shades to {percent}","open shade {percent}","open shades {percent}","close shade {percent}","close shades {percent}","open the shade {percent}","open the shades {percent}","close the shade {percent}","close the shades {percent}","set blind {percent}","set blinds {percent}","set the blind {percent}","set the blinds {percent}","set blind to {percent}","set blinds to {percent}","set the blind to {percent}","set the blinds to {percent}","open blind {percent}","open blinds {percent}","close blind {percent}","close blinds {percent}","open the blind {percent}","open the blinds {percent}","close the blind {percent}","close the blinds {percent}"]}
- Conditions: 
- Actions: [{"variables":{"room_resolved":"{{ area_id(trigger.device_id) }}","spoken":"{{ trigger.sentence | lower }}","pre_action_delay":"00:00:00.3","raw_percent":"{% if trigger.slots is defined and trigger.slots.percent is defined %}\n  {{ trigger.slots.percent }}\n{% else %}\n  {{ \u0027\u0027 }}\n{% endif %}","shade_percent":"{% set raw = (raw_percent | string | lower) %} {% if raw | length == 0 %}\n  {% set raw = spoken %}\n{% endif %} {% set matches = raw | regex_findall(\u0027([0-9]{1,3})\u0027) %} {% if matches | length \u003e 0 %}\n  {% set p = (matches[0] | int) %}\n  {{ p if 0 \u003c= p \u003c= 100 else none }}\n{% else %}\n  {{ none }}\n{% endif %}","target_noun":"{{ \u0027blinds\u0027 if \u0027blind\u0027 in spoken else \u0027shades\u0027 }}"}},{"condition":"template","value_template":"{{ room_resolved is not none }}"},{"condition":"template","value_template":"{{ shade_percent is not none }}"},{"variables":{"room_entities":"{{ area_entities(room_resolved) | default([]) }}","room_covers":"{{ room_entities | select(\u0027match\u0027,\u0027^cover\\\\.\u0027) | list }}","room_shade_covers":"{{ expand(room_covers)\n   | selectattr(\u0027attributes.device_class\u0027,\u0027in\u0027,[\u0027shade\u0027,\u0027blind\u0027,\u0027curtain\u0027,\u0027awning\u0027])\n   | map(attribute=\u0027entity_id\u0027)\n   | list }}","target_covers":"{{ room_shade_covers if room_shade_covers | length \u003e 0 else room_covers }}"}},{"condition":"template","value_template":"{{ target_covers | length \u003e 0 }}"},{"parallel":[{"action":"script.sonos_speak_with_ducking_room","data":{"room":"{{ room_resolved }}","message":"Setting the {{ target_noun }} to {{ shade_percent }} percent."}},{"sequence":[{"delay":"{{ pre_action_delay }}"},{"action":"cover.set_cover_position","target":{"entity_id":"{{ target_covers }}"},"data":{"position":"{{ shade_percent }}"}}]}]}]
- Called scripts (direct): script.sonos_speak_with_ducking_room
- Called scripts (transitive): script.sonos_speak_with_ducking_room, script.voice_assistant_speak_fallback
- Called services (chain): assist_satellite.announce, cover.set_cover_position, media_player.media_play, media_player.volume_set, persistent_notification.create, tts.cloud_say, tts.speak
- Helpers read: 
- Helpers written: 
- Template sensors read: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers/shades referenced: 
- Assist satellites referenced: assist_satellite.primary_bedroom
- Person entities referenced: 
- Presence entities referenced: 
- Calendars/todo referenced: 
- Labels used: automation_helper, abilities_concierge, policy
- Areas used: 
- Rooms inferred: 
- Fallback behavior: Explicit fallback/refusal path present
- Error handling behavior: Notification/log path present
- Silent/no-speech behavior: Speech/media output path present
- Logging behavior: Notification/log path present
- State capture behavior: No explicit capture call observed
- State restore behavior: Restore/playback continuation path observed
- Learning behavior: No learning writes observed
- Cooldown/suppression behavior: No explicit cooldown helper detected
- Guardrail behavior: Policy/guardrail markers present
- Scope classification: household scoped or routing scoped

#### automation.concierge_lighting_percentage_catcher_ha_voice
- Friendly name: Concierge â€“ Lighting Percentage Catcher (HA Voice)
- Labels: automation_helper, abilities_concierge
- Triggers: {"trigger":"conversation","command":["set lights {percent}","set lights to {percent}","set the lights {percent}","set the lights to {percent}","dim lights {percent}","dim lights to {percent}","dim the lights {percent}","dim the lights to {percent}","lights {percent}","lights to {percent}","set lamps {percent}","set lamps to {percent}","set the lamps {percent}","set the lamps to {percent}","dim lamps {percent}","dim lamps to {percent}","dim the lamps {percent}","dim the lamps to {percent}","lamps {percent}","lamps to {percent}","set lamp {percent}","set lamp to {percent}","dim lamp {percent}","dim lamp to {percent}","set light {percent}","set light to {percent}","dim light {percent}","dim light to {percent}"]}
- Conditions: 
- Actions: [{"variables":{"room_resolved":"{{ area_id(trigger.device_id) }}","spoken":"{{ trigger.sentence | lower }}","pre_action_delay":"00:00:00.3","raw_percent":"{% if trigger.slots is defined and trigger.slots.percent is defined %}\n  {{ trigger.slots.percent }}\n{% else %}\n  {{ \u0027\u0027 }}\n{% endif %}","brightness_pct":"{% set raw = raw_percent | string | lower %} {% if raw | length == 0 %}\n  {% set raw = spoken %}\n{% endif %} {% set matches = raw | regex_findall(\u0027([0-9]{1,3})\u0027) %} {% if matches | length \u003e 0 %}\n  {% set p = matches[0] | int %}\n  {{ p if 0 \u003c= p \u003c= 100 else none }}\n{% else %}\n  {{ none }}\n{% endif %}"}},{"condition":"template","value_template":"{{ room_resolved is not none }}"},{"condition":"template","value_template":"{{ brightness_pct is not none }}"},{"variables":{"room_entities":"{{ area_entities(room_resolved) | default([]) }}","room_lights":"{{ expand(room_entities)\n   | selectattr(\u0027domain\u0027,\u0027eq\u0027,\u0027light\u0027)\n   | map(attribute=\u0027entity_id\u0027)\n   | list }}","lamps":"{{ label_devices(\u0027Lamps\u0027)\n   | map(\u0027device_entities\u0027)\n   | sum(start=[])\n   | intersect(room_lights)\n   | list }}","labeled_overhead_lights":"{{ label_devices(\u0027Lights\u0027)\n   | map(\u0027device_entities\u0027)\n   | sum(start=[])\n   | intersect(room_lights)\n   | reject(\u0027in\u0027, lamps)\n   | list }}","unlabeled_lights":"{{ room_lights\n   | reject(\u0027in\u0027, lamps)\n   | reject(\u0027in\u0027, labeled_overhead_lights)\n   | list }}","overhead_lights":"{{ (labeled_overhead_lights + unlabeled_lights) | unique | list }}","wants_lamps":"{{ \u0027lamp\u0027 in spoken }}","wants_lights":"{{ \u0027light\u0027 in spoken }}","target_lights":"{% if wants_lamps %}\n  {{ lamps }}\n{% elif wants_lights %}\n  {{ overhead_lights }}\n{% else %}\n  {{ [] }}\n{% endif %}","target_noun":"{% if wants_lamps %}\n  lamps\n{% else %}\n  lights\n{% endif %}"}},{"condition":"template","value_template":"{{ target_lights | length \u003e 0 }}"},{"parallel":[{"action":"script.sonos_speak_with_ducking_room","data":{"room":"{{ room_resolved }}","message":"Setting the {{ target_noun }} to {{ brightness_pct }} percent."}},{"sequence":[{"delay":"{{ pre_action_delay }}"},{"choose":[{"conditions":[{"condition":"template","value_template":"{{ brightness_pct == 0 }}"}],"sequence":[{"action":"light.turn_off","target":{"entity_id":"{{ target_lights }}"}}]}],"default":[{"action":"light.turn_on","target":{"entity_id":"{{ target_lights }}"},"data":{"brightness_pct":"{{ brightness_pct }}"}}]}]}]}]
- Called scripts (direct): script.sonos_speak_with_ducking_room
- Called scripts (transitive): script.sonos_speak_with_ducking_room, script.voice_assistant_speak_fallback
- Called services (chain): assist_satellite.announce, light.turn_off, light.turn_on, media_player.media_play, media_player.volume_set, persistent_notification.create, tts.cloud_say, tts.speak
- Helpers read: 
- Helpers written: 
- Template sensors read: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers/shades referenced: 
- Assist satellites referenced: assist_satellite.primary_bedroom
- Person entities referenced: 
- Presence entities referenced: 
- Calendars/todo referenced: 
- Labels used: automation_helper, abilities_concierge
- Areas used: 
- Rooms inferred: 
- Fallback behavior: Explicit fallback/refusal path present
- Error handling behavior: Notification/log path present
- Silent/no-speech behavior: Speech/media output path present
- Logging behavior: Notification/log path present
- State capture behavior: No explicit capture call observed
- State restore behavior: Restore/playback continuation path observed
- Learning behavior: No learning writes observed
- Cooldown/suppression behavior: No explicit cooldown helper detected
- Guardrail behavior: Policy/guardrail markers present
- Scope classification: household scoped or routing scoped

#### automation.duck_sonos_when_any_assist_satellite_is_listening
- Friendly name: Duck Sonos When Any Assist Satellite Is Listening
- Labels: automation_helper, abilities_concierge
- Triggers: {"entity_id":["assist_satellite.home_assistant_voice_david_s_office_assist_satellite","assist_satellite.home_assistant_voice_den_assist_satellite","assist_satellite.home_assistant_voice_downstairs_bathroom_assist_satellite","assist_satellite.home_assistant_voice_guest_bathroom_assist_satellite","assist_satellite.home_assistant_voice_guest_bedroom_assist_satellite","assist_satellite.home_assistant_voice_kitchen_assist_satellite","assist_satellite.home_assistant_voice_laundry_room_assist_satellite","assist_satellite.home_assistant_voice_living_room_assist_satellite","assist_satellite.home_assistant_voice_pantry_assist_satellite","assist_satellite.home_assistant_voice_powder_room_assist_satellite","assist_satellite.home_assistant_voice_primary_bathroom_assist_satellite","assist_satellite.home_assistant_voice_primary_bedroom_assist_satellite","assist_satellite.voice_assistant_tom_s_office_assist_satellite"],"to":"listening","trigger":"state"}
- Conditions: 
- Actions: [{"variables":{"room":"{{ area_name(trigger.entity_id)\n   | lower\n   | replace(\"â€™s\",\"_s\")\n   | replace(\"\u0027s\",\"_s\")\n   | replace(\"\u0027\",\"\")\n   | replace(\" \",\"_\") }}"}},{"data":{"room":"{{ room }}","satellite_entity":"{{ trigger.entity_id }}"},"action":"script.duck_sonos_while_assist_is_listening_room"}]
- Called scripts (direct): script.duck_sonos_while_assist_is_listening_room
- Called scripts (transitive): script.duck_sonos_while_assist_is_listening_room
- Called services (chain): media_player.volume_set
- Helpers read: 
- Helpers written: 
- Template sensors read: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers/shades referenced: 
- Assist satellites referenced: assist_satellite.home_assistant_voice_david_s_office_assist_satellite, assist_satellite.home_assistant_voice_den_assist_satellite, assist_satellite.home_assistant_voice_downstairs_bathroom_assist_satellite, assist_satellite.home_assistant_voice_guest_bathroom_assist_satellite, assist_satellite.home_assistant_voice_guest_bedroom_assist_satellite, assist_satellite.home_assistant_voice_kitchen_assist_satellite, assist_satellite.home_assistant_voice_laundry_room_assist_satellite, assist_satellite.home_assistant_voice_living_room_assist_satellite, assist_satellite.home_assistant_voice_pantry_assist_satellite, assist_satellite.home_assistant_voice_powder_room_assist_satellite, assist_satellite.home_assistant_voice_primary_bathroom_assist_satellite, assist_satellite.home_assistant_voice_primary_bedroom_assist_satellite, assist_satellite.primary_bedroom_voice, assist_satellite.voice_assistant_tom_s_office_assist_satellite
- Person entities referenced: 
- Presence entities referenced: 
- Calendars/todo referenced: 
- Labels used: automation_helper, abilities_concierge
- Areas used: 
- Rooms inferred: 
- Fallback behavior: No explicit fallback detected in extracted chain
- Error handling behavior: No explicit error handler visible in extracted YAML
- Silent/no-speech behavior: Likely silent success path
- Logging behavior: No explicit error handler visible in extracted YAML
- State capture behavior: No explicit capture call observed
- State restore behavior: Restore/playback continuation path observed
- Learning behavior: No learning writes observed
- Cooldown/suppression behavior: No explicit cooldown helper detected
- Guardrail behavior: No explicit guardrail marker in labels
- Scope classification: household scoped or routing scoped

#### automation.concierge_room_monitoring_awareness_ha_voice
- Friendly name: Concierge â€“ Room Monitoring Awareness (HA Voice)
- Labels: abilities_concierge
- Triggers: {"command":["what can this room monitor","what does this room monitor","what can this room sense","what can you monitor here","what do you monitor here","what sensors are in this room","what can you sense here"],"trigger":"conversation"}
- Conditions: 
- Actions: [{"variables":{"room_resolved":"{{ area_id(trigger.device_id) }}"}},{"condition":"template","value_template":"{{ room_resolved not in [\u0027\u0027, none] }}"},{"action":"script.room_audio_resolver_keystone","data":{"room":"{{ room_resolved }}","speak_awareness":true,"debug_notification":false}}]
- Called scripts (direct): script.room_audio_resolver_keystone
- Called scripts (transitive): script.room_audio_resolver_keystone, script.room_monitoring_abilities_speak, script.sonos_speak_with_ducking_room, script.speak_capability_not_available, script.speak_room_air_quality, script.speak_room_air_quality_assessment, script.speak_room_humidity, script.speak_room_light_level, script.speak_room_noise_level, script.speak_room_temperature, script.voice_assistant_speak_fallback
- Called services (chain): assist_satellite.announce, input_datetime.set_datetime, input_text.set_value, media_player.media_play, media_player.volume_set, persistent_notification.create, tts.cloud_say, tts.speak
- Helpers read: input_datetime.speaker_profile_last_updated
- Helpers written: input_datetime.set_datetime, input_text.set_value
- Template sensors read: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers/shades referenced: 
- Assist satellites referenced: assist_satellite.primary_bedroom
- Person entities referenced: 
- Presence entities referenced: 
- Calendars/todo referenced: 
- Labels used: abilities_concierge
- Areas used: 
- Rooms inferred: 
- Fallback behavior: Explicit fallback/refusal path present
- Error handling behavior: Notification/log path present
- Silent/no-speech behavior: Speech/media output path present
- Logging behavior: Notification/log path present
- State capture behavior: State capture/update observed
- State restore behavior: Restore/playback continuation path observed
- Learning behavior: Learning/profile writes observed
- Cooldown/suppression behavior: Cooldown/suppression helper pattern present
- Guardrail behavior: Policy/guardrail markers present
- Scope classification: household scoped or routing scoped

#### automation.concierge_follow_up_sensor_queries_ha_voice
- Friendly name: Concierge â€“ Follow-Up Sensor Queries (HA Voice)
- Labels: abilities_concierge
- Triggers: {"command":["what is the temperature","what\u0027s the temperature","how hot is it","how cold is it","what is the humidity","what\u0027s the humidity","how humid is it","how bright is it","how dark is it","what is the light level","what is the air quality","how is the air","how is the air quality","what is the noise level","how loud is it","is it loud in here"],"trigger":"conversation"}
- Conditions: 
- Actions: [{"variables":{"room_resolved":"{{ area_id(trigger.device_id) }}","spoken":"{{ trigger.sentence | lower }}"}},{"condition":"template","value_template":"{{ room_resolved not in [\u0027\u0027, none] }}"},{"variables":{"speak_temperature":"{{ \u0027temperature\u0027 in spoken or \u0027hot\u0027 in spoken or \u0027cold\u0027 in spoken }}","speak_humidity":"{{ \u0027humidity\u0027 in spoken or \u0027humid\u0027 in spoken }}","speak_light_level":"{{ \u0027bright\u0027 in spoken or \u0027dark\u0027 in spoken or \u0027light level\u0027 in spoken }}","speak_air_quality":"{{\n  (\u0027air quality\u0027 in spoken)\n  or spoken.startswith(\u0027how is the air\u0027)\n}}","speak_noise":"{{ \u0027noise\u0027 in spoken or \u0027loud\u0027 in spoken }}"}},{"action":"script.room_audio_resolver_keystone","data":{"room":"{{ room_resolved }}","debug_notification":false,"speak_awareness":false,"speak_temperature":"{{ speak_temperature }}","speak_humidity":"{{ speak_humidity }}","speak_light_level":"{{ speak_light_level }}","speak_air_quality":"{{ speak_air_quality }}","speak_noise":"{{ speak_noise }}"}}]
- Called scripts (direct): script.room_audio_resolver_keystone
- Called scripts (transitive): script.room_audio_resolver_keystone, script.room_monitoring_abilities_speak, script.sonos_speak_with_ducking_room, script.speak_capability_not_available, script.speak_room_air_quality, script.speak_room_air_quality_assessment, script.speak_room_humidity, script.speak_room_light_level, script.speak_room_noise_level, script.speak_room_temperature, script.voice_assistant_speak_fallback
- Called services (chain): assist_satellite.announce, input_datetime.set_datetime, input_text.set_value, media_player.media_play, media_player.volume_set, persistent_notification.create, tts.cloud_say, tts.speak
- Helpers read: input_datetime.speaker_profile_last_updated
- Helpers written: input_datetime.set_datetime, input_text.set_value
- Template sensors read: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers/shades referenced: 
- Assist satellites referenced: assist_satellite.primary_bedroom
- Person entities referenced: 
- Presence entities referenced: 
- Calendars/todo referenced: 
- Labels used: abilities_concierge
- Areas used: 
- Rooms inferred: 
- Fallback behavior: Explicit fallback/refusal path present
- Error handling behavior: Notification/log path present
- Silent/no-speech behavior: Speech/media output path present
- Logging behavior: Notification/log path present
- State capture behavior: State capture/update observed
- State restore behavior: Restore/playback continuation path observed
- Learning behavior: Learning/profile writes observed
- Cooldown/suppression behavior: Cooldown/suppression helper pattern present
- Guardrail behavior: Policy/guardrail markers present
- Scope classification: household scoped or routing scoped

### 7B. Script Graph Details
#### script.resolve_speaker_profile
- Friendly name: Resolve Speaker Profile
- Labels: abilities_concierge
- Called scripts: 
- Called services: 
- Helpers read: 
- Helpers written: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers referenced: 
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: routing/helper scoped

#### script.room_audio_resolver_keystone
- Friendly name: Room & Audio Resolver (Keystone)
- Labels: abilities_concierge, policy
- Called scripts: script.room_monitoring_abilities_speak, script.speak_room_temperature, script.speak_room_humidity, script.speak_room_light_level, script.speak_room_air_quality, script.speak_room_noise_level, script.speak_capability_not_available, script.sonos_speak_with_ducking_room
- Called services: input_text.set_value, input_datetime.set_datetime, persistent_notification.create
- Helpers read: input_datetime.speaker_profile_last_updated
- Helpers written: input_datetime.set_datetime, input_text.set_value
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers referenced: 
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: routing/helper scoped

#### script.sonos_speak_with_ducking_room
- Friendly name: Sonos Speak with Ducking (Room)
- Labels: abilities_concierge
- Called scripts: script.voice_assistant_speak_fallback
- Called services: media_player.volume_set, tts.speak, media_player.media_play, persistent_notification.create
- Helpers read: 
- Helpers written: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers referenced: 
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: routing/helper scoped

#### script.room_capabilities_snapshot_debug
- Friendly name: Room Capabilities â€” Snapshot (Debug)
- Labels: abilities_concierge
- Called scripts: 
- Called services: persistent_notification.create
- Helpers read: 
- Helpers written: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers referenced: 
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: routing/helper scoped

#### script.learn_lighting_usual_room
- Friendly name: Learn Lighting â€” Usual (Room)
- Labels: abilities_concierge, policy
- Called scripts: 
- Called services: input_number.set_value, input_datetime.set_datetime
- Helpers read: input_datetime.lamp_brightness_profile_last_updated
- Helpers written: input_datetime.set_datetime, input_number.set_value
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: light.split
- Covers referenced: 
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: room/entity scoped

#### script.learn_music_volume_room
- Friendly name: Learn Music Volume â€” Room
- Labels: abilities_concierge, policy
- Called scripts: 
- Called services: input_text.set_value, input_datetime.set_datetime
- Helpers read: input_datetime.speaker_profile_last_updated
- Helpers written: input_datetime.set_datetime, input_text.set_value
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers referenced: 
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: routing/helper scoped

#### script.resolve_music_player_room
- Friendly name: Resolve Music Player â€“ Room
- Labels: abilities_concierge, policy
- Called scripts: 
- Called services: 
- Helpers read: 
- Helpers written: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: media_player.living_room_sonos
- Lights referenced: 
- Covers referenced: 
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: room/entity scoped

#### script.update_last_media_room
- Friendly name: Music â€“ Update Last Media (Room)
- Labels: abilities_concierge
- Called scripts: 
- Called services: input_text.set_value
- Helpers read: 
- Helpers written: input_text.set_value
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers referenced: 
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: routing/helper scoped

#### script.start_music_usual_room
- Friendly name: Start Music â€“ Usual (Room)
- Labels: abilities_concierge
- Called scripts: script.resolve_music_player_room, script.update_last_media_room
- Called services: media_player.volume_set, media_player.play_media, media_player.media_play, input_text.set_value
- Helpers read: 
- Helpers written: input_text.set_value
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers referenced: 
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: routing/helper scoped

#### script.determine_music_genre_audit
- Friendly name: Music â€“ Determine Genre (Audit, Room)
- Labels: automation_helper, abilities_concierge
- Called scripts: 
- Called services: input_text.set_value, ai_task.generate_data
- Helpers read: 
- Helpers written: input_text.set_value
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers referenced: 
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: routing/helper scoped

#### script.play_genre_room
- Friendly name: Play Genre â€“ Room
- Labels: automation_helper, abilities_concierge
- Called scripts: script.ensure_main_living_area_sonos_group
- Called services: input_select.select_option, media_player.media_stop, media_player.play_media
- Helpers read: input_text.music_genre_uri_map
- Helpers written: input_select.select_option
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers referenced: 
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: routing/helper scoped

#### script.play_artist_room
- Friendly name: Play Artist â€“ Room (MA)
- Labels: abilities_concierge
- Called scripts: script.ensure_main_living_area_sonos_group
- Called services: media_player.media_stop, input_select.select_option, input_text.set_value, media_player.play_media, media_player.media_play
- Helpers read: 
- Helpers written: input_select.select_option, input_text.set_value
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers referenced: 
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: routing/helper scoped

#### script.primary_bedroom_play_alarm_chime
- Friendly name: Alarm â€“ Play Chime (Room)
- Labels: abilities_concierge
- Called scripts: script.sonos_speak_with_ducking_room
- Called services: 
- Helpers read: 
- Helpers written: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers referenced: 
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: routing/helper scoped

#### script.alarm_sonos_snapshot
- Friendly name: Alarm â€“ Sonos Snapshot
- Labels: abilities_concierge
- Called scripts: 
- Called services: sonos.snapshot
- Helpers read: 
- Helpers written: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers referenced: 
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: routing/helper scoped

#### script.play_album_room_ma
- Friendly name: Play Album â€“ Room (MA)
- Labels: automation_helper, abilities_concierge
- Called scripts: script.ensure_main_living_area_sonos_group
- Called services: media_player.media_stop, input_select.select_option, music_assistant.get_library, music_assistant.search, persistent_notification.create, input_text.set_value, music_assistant.play_media, media_player.media_play
- Helpers read: 
- Helpers written: input_select.select_option, input_text.set_value
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers referenced: 
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: routing/helper scoped

#### script.surprise_me_room
- Friendly name: Surprise Me â€“ Room
- Labels: automation_helper, abilities_concierge
- Called scripts: script.play_genre_room
- Called services: persistent_notification.create
- Helpers read: 
- Helpers written: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers referenced: 
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: routing/helper scoped

#### script.continue_playing_room
- Friendly name: Continue Playing â€“ Room
- Labels: automation_helper, abilities_concierge
- Called scripts: script.start_music_usual_room, script.room_speak_sonos
- Called services: media_player.media_play
- Helpers read: 
- Helpers written: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers referenced: 
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: routing/helper scoped

#### script.what_s_playing_room
- Friendly name: Whatâ€™s Playing? â€“ Room
- Labels: automation_helper, abilities_concierge
- Called scripts: script.room_speak_sonos
- Called services: 
- Helpers read: 
- Helpers written: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers referenced: 
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: routing/helper scoped

#### script.why_did_you_play_this_room
- Friendly name: Why Did You Play This? â€“ Room
- Labels: automation_helper, abilities_concierge
- Called scripts: script.room_speak_sonos
- Called services: 
- Helpers read: 
- Helpers written: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers referenced: 
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: routing/helper scoped

#### script.music_debug_snapshot_room
- Friendly name: Music Debug Snapshot â€“ Room
- Labels: automation_helper, abilities_concierge
- Called scripts: 
- Called services: persistent_notification.create
- Helpers read: input_datetime.speaker_profile_last_updated
- Helpers written: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers referenced: 
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: routing/helper scoped

#### script.voice_assistant_speak_fallback
- Friendly name: Voice Assistant Speak (Fallback)
- Labels: automation_helper, abilities_concierge
- Called scripts: 
- Called services: assist_satellite.announce, media_player.volume_set, tts.cloud_say
- Helpers read: 
- Helpers written: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers referenced: 
- Assist satellites referenced: assist_satellite.primary_bedroom
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: room/entity scoped

#### script.room_abilities_speak_unified
- Friendly name: Room Abilities â€” Speak (Unified)
- Labels: automation_helper, abilities_concierge
- Called scripts: script.ensure_main_living_area_sonos_group, script.sonos_speak_with_ducking_room
- Called services: 
- Helpers read: 
- Helpers written: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers referenced: 
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: routing/helper scoped

#### script.ensure_main_living_area_sonos_group
- Friendly name: Ensure Main Living Area Sonos Group
- Labels: automation_helper, abilities_concierge
- Called scripts: 
- Called services: media_player.join
- Helpers read: 
- Helpers written: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: media_player.kitchen, media_player.kitchen_sonos, media_player.living_room_sonos
- Lights referenced: 
- Covers referenced: 
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: room/entity scoped

#### script.turn_on_lamps_usual_room
- Friendly name: Turn On Lamps â€” Usual (Room)
- Labels: automation_helper, abilities_concierge
- Called scripts: 
- Called services: light.turn_on
- Helpers read: 
- Helpers written: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: light.split
- Covers referenced: 
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: room/entity scoped

#### script.turn_on_lights_usual_room
- Friendly name: Turn On Lights â€” Usual (Room)
- Labels: automation_helper, abilities_concierge
- Called scripts: 
- Called services: light.turn_on
- Helpers read: 
- Helpers written: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: light.split
- Covers referenced: 
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: room/entity scoped

#### script.set_room_posture
- Friendly name: Set Room Posture
- Labels: automation_helper, abilities_concierge
- Called scripts: 
- Called services: input_select.select_option
- Helpers read: input_select.room_posture_guest_bedroom, input_select.room_posture_primary_bedroom
- Helpers written: input_select.select_option
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers referenced: 
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: routing/helper scoped

#### script.resolve_bedroom_context
- Friendly name: Resolve Bedroom Context
- Labels: automation_helper, abilities_concierge
- Called scripts: 
- Called services: 
- Helpers read: 
- Helpers written: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers referenced: 
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: routing/helper scoped

#### script.bedroom_context_not_valid_speak
- Friendly name: Bedroom Context Not Valid Speak
- Labels: automation_helper, abilities_concierge
- Called scripts: script.sonos_speak_with_ducking_room
- Called services: 
- Helpers read: 
- Helpers written: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers referenced: 
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: routing/helper scoped

#### script.kiosk_set_overnight_mode
- Friendly name: Kiosk Set Overnight Mode
- Labels: automation_helper, abilities_concierge
- Called scripts: 
- Called services: rest_command.fk_command, switch.turn_on, switch.turn_off, number.set_value
- Helpers read: 
- Helpers written: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers referenced: 
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: routing/helper scoped

#### script.kiosk_set_day_mode
- Friendly name: Kiosk Set Day Mode
- Labels: automation_helper, abilities_concierge
- Called scripts: 
- Called services: rest_command.fk_command, switch.turn_on, number.set_value
- Helpers read: 
- Helpers written: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers referenced: 
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: routing/helper scoped

#### script.concierge_bedtime
- Friendly name: Concierge Bedtime
- Labels: automation_helper, abilities_concierge
- Called scripts: script.sonos_speak_with_ducking_room
- Called services: media_player.unjoin, media_player.volume_set, scene.turn_on, cover.close_cover, light.turn_on
- Helpers read: 
- Helpers written: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: light.guest_bedside_lamp, light.guest_corner_lamp, light.guest_table_lamp
- Covers referenced: cover.guest_bedroom_shade
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: room/entity scoped

#### script.concierge_goodnight
- Friendly name: Concierge Goodnight
- Labels: automation_helper, abilities_concierge
- Called scripts: script.set_room_posture, script.kiosk_set_overnight_mode
- Called services: media_player.unjoin, light.turn_off, scene.turn_on, cover.close_cover, media_player.turn_off, media_player.volume_set, media_player.repeat_set, media_player.play_media
- Helpers read: 
- Helpers written: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: media_player.appletv_guest_bedroom, media_player.appletv_primary_bedroom
- Lights referenced: 
- Covers referenced: cover.guest_bedroom_shade
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: room/entity scoped

#### script.concierge_good_morning
- Friendly name: Concierge Good Morning
- Labels: automation_helper, abilities_concierge
- Called scripts: script.set_room_posture, script.kiosk_set_day_mode, script.sonos_speak_with_ducking_room
- Called services: media_player.repeat_set, media_player.shuffle_set, media_player.media_stop, media_player.clear_playlist, media_player.volume_set, weather.get_forecasts, cover.set_cover_position, light.turn_on, fan.turn_on, media_player.turn_off
- Helpers read: 
- Helpers written: 
- Sensors read: sensor.nws_alerts_alerts
- Binary sensors read: 
- Media players referenced: media_player.appletv_guest_bedroom, media_player.appletv_primary_bedroom
- Lights referenced: light.david_s_lamp, light.guest_bathroom_shower, light.guest_bedside_lamp, light.guest_closet, light.guest_sconce, light.primary_bathroom_overhead, light.primary_bathroom_sconce, light.primary_bathroom_skylight, light.primary_toilet_light
- Covers referenced: cover.bedroom_shade, cover.guest_bedroom_shade
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: room/entity scoped

#### script.duck_sonos_while_assist_is_listening_room
- Friendly name: Duck Sonos While Assist Is Listening (Room)
- Labels: automation_helper, abilities_concierge
- Called scripts: 
- Called services: media_player.volume_set
- Helpers read: 
- Helpers written: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers referenced: 
- Assist satellites referenced: assist_satellite.primary_bedroom_voice
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: room/entity scoped

#### script.room_monitoring_abilities_speak
- Friendly name: Room Monitoring Abilities â€” Speak
- Labels: abilities_concierge
- Called scripts: script.sonos_speak_with_ducking_room
- Called services: 
- Helpers read: 
- Helpers written: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers referenced: 
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: routing/helper scoped

#### script.speak_room_temperature
- Friendly name: Speak Room Temperature
- Labels: abilities_concierge
- Called scripts: script.sonos_speak_with_ducking_room
- Called services: 
- Helpers read: 
- Helpers written: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers referenced: 
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: routing/helper scoped

#### script.speak_room_humidity
- Friendly name: Speak Room Humidity
- Labels: abilities_concierge
- Called scripts: script.sonos_speak_with_ducking_room
- Called services: 
- Helpers read: 
- Helpers written: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers referenced: 
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: routing/helper scoped

#### script.speak_room_light_level
- Friendly name: Speak Room Light Level
- Labels: abilities_concierge
- Called scripts: script.sonos_speak_with_ducking_room
- Called services: 
- Helpers read: 
- Helpers written: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers referenced: 
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: routing/helper scoped

#### script.speak_room_air_quality
- Friendly name: Speak Room Air Quality
- Labels: abilities_concierge
- Called scripts: script.speak_room_air_quality_assessment, script.sonos_speak_with_ducking_room, script.speak_capability_not_available
- Called services: 
- Helpers read: 
- Helpers written: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers referenced: 
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: routing/helper scoped

#### script.speak_room_noise_level
- Friendly name: Speak Room Noise Level
- Labels: abilities_concierge
- Called scripts: script.sonos_speak_with_ducking_room
- Called services: 
- Helpers read: 
- Helpers written: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers referenced: 
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: routing/helper scoped

#### script.speak_capability_not_available
- Friendly name: Speak Capability Not Available
- Labels: abilities_concierge
- Called scripts: script.sonos_speak_with_ducking_room
- Called services: 
- Helpers read: 
- Helpers written: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers referenced: 
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: routing/helper scoped

#### script.speak_room_air_quality_ai_assessment
- Friendly name: Speak Room Air Quality (AI Assessment)
- Labels: abilities_concierge
- Called scripts: script.sonos_speak_with_ducking_room
- Called services: ai_task.generate_data
- Helpers read: 
- Helpers written: 
- Sensors read: 
- Binary sensors read: 
- Media players referenced: 
- Lights referenced: 
- Covers referenced: 
- Assist satellites referenced: 
- Persons referenced: 
- Calendars/todo referenced: 
- Scope classification: routing/helper scoped

## 8. Capability Reconstruction by User Outcome
### Voice command entry and follow-up resolution
- Outcome: speech commands route to room-aware actions and follow-ups.
- Evidence: concierge voice entry/follow-up automations + room resolver script + monitor/sensor speak scripts.
- Runtime chain: conversation trigger -> room resolution -> capability-specific script/service -> speech or silent action.
- Supports guests: yes (guest label on voice entry automation).

### Lighting preference learning and application
- Outcome: learned brightness is stored and reused for usual lighting behavior.
- Evidence: lamp_profile_learn_on_use writes input_number.*_learned_brightness and updates input_datetime.lamp_brightness_profile_last_updated.
- Runtime chain: brightness state trigger -> helper write -> later turn_on_lamps/lights_usual scripts consume helper profiles.

### Audio continuity and ducking
- Outcome: room speaker profile (chat/music/duck) is seeded/updated and used for speech/music behavior; Sonos ducking path exists.
- Evidence: resolve_speaker_profile, room_audio_resolver_keystone, duck_sonos automation/script family.

### Media continuity and continuation
- Outcome: room-aware music start, genre handling, last-media capture, and continue-playing behavior.
- Evidence: voice_play_music, voice_play_jazz, voice_continue_playing, music_capture_last_media_on_playback, play_* scripts, continue_playing_room script.

### Monitoring and sensor answer capability
- Outcome: room monitoring awareness plus temperature/humidity/light/air/noise follow-up responses where capability exists.
- Evidence: concierge_room_monitoring_awareness_ha_voice, concierge_follow_up_sensor_queries_ha_voice, speak_room_* scripts, speak_capability_not_available fallback.

## 9. Capability Domain Classification
### Voice Interaction
- automation.concierge_voice_entry_ha_voice
- automation.concierge_follow_up_commands_ha_voice
- automation.concierge_follow_up_sensor_queries_ha_voice
- automation.concierge_intentional_learning_ha_voice

### Room Awareness
- script.room_audio_resolver_keystone
- automation.concierge_room_monitoring_awareness_ha_voice
- script.room_monitoring_abilities_speak

### Lighting Continuity
- automation.lamp_profile_learn_on_use
- automation.concierge_lighting_percentage_catcher_ha_voice
- script.turn_on_lamps_usual_room
- script.turn_on_lights_usual_room

### Audio Continuity
- automation.learn_music_volume_on_sonos_change
- automation.duck_sonos_when_any_assist_satellite_is_listening
- script.duck_sonos_while_assist_is_listening_room
- script.resolve_speaker_profile

### Media Continuity
- automation.music_capture_last_media_on_playback
- automation.music_genre_observe_playback_all_sources
- automation.voice_play_music
- automation.voice_play_jazz
- automation.voice_continue_playing
- script.resolve_music_player_room
- script.play_genre_room
- script.play_artist_room
- script.play_album_room_ma
- script.continue_playing_room

### Monitoring and Sensor Follow-Ups
- automation.concierge_room_monitoring_awareness_ha_voice
- automation.concierge_follow_up_sensor_queries_ha_voice
- script.speak_room_temperature
- script.speak_room_humidity
- script.speak_room_light_level
- script.speak_room_air_quality
- script.speak_room_noise_level

### Learning and Preference Memory
- automation.lamp_profile_learn_on_use
- automation.learn_music_volume_on_sonos_change
- automation.concierge_intentional_learning_ha_voice

### Guardrails and Soft Failure Handling
- automation.concierge_voice_entry_ha_voice
- automation.concierge_follow_up_commands_ha_voice
- script.speak_capability_not_available
- script.voice_assistant_speak_fallback

### Experience Continuity
- automation.voice_continue_playing
- automation.music_capture_last_media_on_playback
- automation.learn_music_volume_on_sonos_change
- script.continue_playing_room
- script.room_audio_resolver_keystone

## 10. Experience Continuity Assessment
- Assessment: Partial-to-Strong presence in V1.
- Confirmed continuity elements: learned brightness memory, learned speaker volume profile memory, media continuation, last-media capture, room-aware playback routing, Sonos ducking during assist listening.
- Not fully evidenced in this pass: explicit cross-room follow-me transfer policy and complete restore semantics for every media/light subtype.

## 11. Person-Aware Redesign Assessment (for V2 planning only)
- Lighting learned brightness: currently room/entity scoped; recommend person+room scoped with unknown-speaker fallback to room defaults.
- Music volume learning: currently room/profile helper scoped; recommend person+room+time-of-day scoped where identity confidence is high.
- Continue playing: currently room continuity oriented; recommend person+room continuity with low-confidence fail-closed defaults.
- Monitoring responses: keep room-scoped primarily; person-awareness optional for verbosity/preferences.
- Guest handling: guest-labeled entry exists; retain guest-default suppression for learning/personalization.

## 12. Unknowns and Required Human Confirmation
- Some fallback/cooldown semantics are template-driven and may depend on runtime state not exercised in this static extraction.
- Distinction between manual-stop cooldown and policy suppression needs scenario replay confirmation.
- Cross-room resume policy boundaries require trace-level validation during active room transitions.

## 13. Evidence Limitations
- This pass uses configuration extraction and registry/API references, not live trigger replay traces.
- Regex-derived entity reference extraction includes templates and may over-include pseudo tokens; lists were normalized but may still include non-runtime literals in rare cases.
- Concierge and voice_identity domains are not installed in production, so V1 behavior is inferred from automation/script execution assets only.

## 14. Recommendation Before V1-to-V2 Parity Scoring
- Proceed to parity scoring next: Yes, with this reconstruction as baseline.
- Constraint for next phase: parity should be capability/outcome based, not 1:1 automation-to-service naming based.
