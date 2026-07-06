# Architecture Guardrails

These guardrails keep Concierge implementation aligned with platform architecture.

## Non-Negotiable Rules

- Home Assistant Area registry remains the room source of truth.
- Concierge room state is extension data keyed by `area_id`, not a parallel room registry.
- UI must use Home Assistant-native dialog patterns (`ha-dialog`) rather than custom dialog frameworks.
- UI control decisions must start from official Home Assistant references before any fallback implementation is chosen.
- New lifecycle services must include regression tests for state transitions.
- Room language and voice selectors must use Home Assistant provider capability metadata as the single source of truth; Concierge must not maintain a static or duplicate TTS language/voice catalog.

## Canonical UI References

Review these sources first whenever adding or changing controls, selectors, dialogs, or TTS flows:

- Frontend architecture and patterns: https://developers.home-assistant.io/docs/frontend/
- Official selector reference: https://www.home-assistant.io/docs/blueprint/selectors/
- Selector component behavior demos: https://design.home-assistant.io/#components/ha-selector
- TTS building block behavior and constraints: https://www.home-assistant.io/integrations/tts/

If Concierge cannot directly use the documented Home Assistant pattern in the custom panel surface, document the reason in `docs/development/architecture-exceptions.md` and use the closest stable fallback.

## Required PR Checks

- Architecture impact reviewed and documented.
- Canonical Home Assistant docs were consulted for UI/control changes before choosing a fallback.
- Exceptions documented with owner and expiry in `docs/development/architecture-exceptions.md`.
- `scripts/validate_architecture_guardrails.py` passes.
- Test coverage added or updated for changed lifecycle behavior.
