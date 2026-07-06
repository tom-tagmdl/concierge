## Summary

Describe what changed and why.

## Architecture Alignment Checklist

- [ ] I reviewed `docs/development/architecture-guardrails.md`.
- [ ] Room/area behavior remains anchored to Home Assistant Areas as source of truth.
- [ ] For UI/control changes, I checked the canonical Home Assistant docs/design references before using a fallback pattern.
- [ ] UI changes use Home Assistant-native dialog and selector patterns.
- [ ] Lifecycle/service changes include regression tests.
- [ ] If any rule is temporarily bypassed, I added/updated an entry in `docs/development/architecture-exceptions.md`.

## Validation

- [ ] `python scripts/validate_architecture_guardrails.py`
- [ ] `pytest -q`
