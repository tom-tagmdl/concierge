# Weather Response Quality Contract

## 1. Purpose
Preserve the V1 Good Morning weather outcome quality in Concierge V2 by generating calm, concise, spoken weather responses from structured forecast fields with bounded local weather warning awareness.

## 2. Governance Sources
- tmp/phase1/prod_v1_scripts.json
- tmp/ec_issue_updates/weather-response-replication.md
- docs/governance/experience-continuity/room-runtime-authority-contract.md
- docs/governance/experience-continuity/v1-capability-reconstruction.md

## 3. Forecast Source Authority
- Forecast source selection is configuration-authored from room configuration.
- Source is read from `room.weather_source_entity_ids` for the resolved room context.
- Runtime discovery is not used to locate weather providers.
- Unrelated weather entities are ignored.

## 4. Forecast Parsing Model
- Concierge requests daily forecasts through `weather.get_forecasts` using the configured room weather source.
- Concierge parses structured fields from the first daily forecast row.
- Parsed fields include:
  - condition
  - high temperature
  - low temperature
  - humidity
  - precipitation probability
  - wind
- Raw provider prose is not used directly as the spoken output.

## 5. Spoken Summary Construction
- Response style is calm, concise, and deterministic.
- Summary is composed from parsed fields, not emitted as fragmented key-value output.
- If both forecast and warning are present, Concierge combines both in one bounded response.
- If only forecast is present, Concierge returns forecast-only speech.

## 6. Weather Emergency Integration
- Warning source is bounded to local warning authority (`sensor.nws_alerts_alerts`).
- Concierge surfaces warning headline when warning data is available.
- Concierge does not interpret emergency severity beyond headline inclusion.
- Warning messaging remains calm and concise.

## 7. Fallback Behavior
- Forecast unavailable + warning available: warning-only fallback response.
- Forecast unavailable + warning unavailable: graceful forecast fallback response.
- Forecast available + warning unavailable: forecast-only response.
- Forecast source missing from room configuration: deterministic configured-source-missing response.
- Warning source issues never block forecast response when forecast is available.

## 8. Explainability Requirements
Concierge weather responses expose:
- weather_source
- forecast_provider
- forecast_data_available
- warning_source
- warning_available
- warning_headline
- weather_response_strategy
- fallback_reason

Additionally, room authority explainability must remain visible:
- room_authority_source
- room_configuration_loaded
- vocabulary_source
- information_source_origin
- asset_authority_source
- environment_source_origin
- merged_room_authority_source
- person_authority_source

## 9. Validation Scenarios
- Normal forecast response
- Condition parsing
- High temperature inclusion
- Low temperature inclusion
- Humidity inclusion
- Precipitation inclusion
- Wind inclusion
- Warning present
- Warning absent
- Forecast unavailable
- Warning source unavailable
- Forecast unavailable and warning present
- Forecast present and warning unavailable
- Configured weather source used
- Runtime discovery not used
- Unrelated weather entity ignored
- Graceful fallback speech
- Calm warning presentation
- Explainability fields emitted
- V1 weather outcome quality preserved

## 10. Non-Goals
- Do not build new weather platforms.
- Do not scan Home Assistant inventory for weather sources.
- Do not infer providers from unrelated entities.
- Do not perform severe weather intelligence analysis.
- Do not implement monitoring roadmap enhancements from issue #413 in this contract.