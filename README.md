# Concierge

Concierge is a Home Assistant custom integration that provides the interaction and orchestration layer for the Homes Platform.

It is designed to follow Homes That Behave Well principles:

- Calm by default
- Deterministic behavior
- Explainable decisions
- Clear service boundaries

## Scope

Concierge is responsible for:

- user-facing orchestration
- interaction workflows
- capability routing to other integrations

Concierge does not own:

- persistent domain data
- core evaluation logic
- direct state mutation outside service contracts

## Development goals

- HACS-compatible distribution
- Home Assistant quality-focused architecture
- Platinum-level readiness posture

## Repository layout

- `custom_components/concierge/`: Home Assistant integration package
- `.github/workflows/`: HACS, hassfest, and test CI
- `tests/`: integration and flow tests

## Local development

1. Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

2. Run tests:

```bash
pytest -q
```

## Release expectations

- Update `custom_components/concierge/manifest.json` version
- Ensure HACS validation passes
- Ensure hassfest passes
- Ensure tests pass
- Tag and publish release
