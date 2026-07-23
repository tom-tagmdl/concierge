# Voice Identity and Concierge Alignment

This guide defines the required alignment between Concierge and Voice Identity so enrollment and profile build work predictably.

## Compatibility Baseline

Use aligned versions of both integrations from the same validation window.

- Concierge: install current tested build.
- Voice Identity: install current tested build.
- Home Assistant: restart after every integration update.

## Required Runtime Settings

In Voice Identity settings:

1. Enable the service runtime.
2. Keep storage provider as local_filesystem unless you have an approved alternative.
3. Keep model preference in supported_models.
4. For development test environments, enable experimental models to activate deterministic development model execution.

When Concierge linkage is enabled in Concierge integration settings, Concierge now auto-aligns key Voice Identity entry options:

1. service.enabled is set true.
2. generation.model_preference is normalized (default ecapa_v1).
3. generation.supported_models is updated to include model_preference.
4. feature_flags.enable_experimental_models is set true for development workflow continuity.

Concierge also posts a persistent notification summarizing exactly which Voice Identity fields were updated.

In Concierge settings:

1. Enable Voice Identity linkage.
2. Complete person setup before enrollment.
3. Use one enrollment person to one voice profile mapping.

## Post-Install Verification

Run this checklist before interactive enrollment:

1. Voice Identity services are registered.
2. Concierge enrollment services are registered.
3. Voice Identity health is available.
4. Concierge completion readiness does not report generation operation unavailable.

## Enrollment and Build Validation

1. Start enrollment from Concierge person setup.
2. Capture at least target samples with category and distance coverage.
3. Confirm completion status reads ready.
4. Build profile and confirm success toast.

## Error to Remediation Map

- completion_not_ready:generation_operation_unavailable:
  Voice Identity generate operation not loaded. Restart Voice Identity and Concierge.
- completion_not_ready:generation_backend_unavailable:
  Voice Identity model backend is unavailable. In development, enable experimental models.
- completion_not_ready:generation_failed:model_provider_unavailable:model_failed:
  Generation request reached Voice Identity, but provider cannot execute model path.
- completion_not_ready:validation_failed:*:
  Enrollment sample set failed validation checks. Capture additional clean samples.
- extra keys not allowed at data[min_samples]:
  Service schema drift. Update Concierge service schemas and reload.

## Operational Notes

- local_filesystem storage controls persistence location, not model execution readiness.
- Model backend readiness gates generation even when enrollment count and quality pass.
- During development, deterministic backend mode is for workflow validation, not production biometric fidelity.