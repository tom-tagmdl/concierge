# Voice Identity Integration (Planned)

Concierge will integrate with Voice Identity as an optional capability.

## Intent

Concierge remains responsible for:

- room context
- people configuration
- permissions
- coordinator behavior
- enrollment orchestration
- user experience

Voice Identity will provide:

- speaker fingerprint generation
- fingerprint artifact lifecycle
- runtime speaker attribution
- confidence scoring
- identity-resolution reason codes

## Integration Model

Concierge consumes Voice Identity through explicit contracts and capability checks.

No Concierge runtime implementation changes are defined in this document.

This document is architecture guidance only.
