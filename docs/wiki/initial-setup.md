# Initial Setup

This page helps you get Concierge running for the first time.

## Before You Start

- Make sure Home Assistant is running.
- Make sure Concierge is installed.
- If you want calendar, email, tasks, or shopping support, install those integrations first.
- Set up attached storage in Home Assistant (for example, /media on local or NAS storage).

### Why Attached Storage Matters

Concierge uses attached storage for features that keep larger or longer-lived files:

- Voice profile enrollment artifacts and captured voice samples.
- Activity archive exports and longer history retention beyond normal Home Assistant activity views.
- Optional archive reference files used for deeper explainability/history review.

If attached storage is not available, these features may be limited or unavailable.

## Add Concierge In Home Assistant

1. Go to Settings.
2. Open Devices and Services.
3. Select Add Integration.
4. Search for Concierge.
5. Complete the setup form.

## What To Fill In During Setup

You will see Concierge Integration Settings fields similar to:

- Action provider
- Text-to-speech provider
- Media provider
- Asset Intelligence provider
- Voice Identity linked (on or off)
- Audit archive destination and retention

### About Asset Intelligence and Voice Identity

Asset Intelligence and Voice Identity are separate integrations that connect to Concierge.

- Asset Intelligence helps Concierge understand and use asset-related context in a room.
- Voice Identity helps Concierge identify who is speaking so responses can be more person-aware.

Important:

- Asset Intelligence provider is only available if Asset Intelligence is already installed.
- Voice Identity linked is only available if Voice Identity is already installed.

If you do not see one of those options, install that integration first, then return to Concierge Integration Settings.

If you are unsure, start with defaults. You can change these later in Concierge Integration Settings.

## First Checks After Setup

1. Confirm Concierge appears in Devices and Services.
2. Open Concierge from the integrations list and confirm you can access both Concierge Global Settings and Concierge Integration Settings.
3. Complete [Initial Person Setup](person-setup.md).
4. Complete [Initial Room Setup](room-setup.md).
5. Open Developer Tools, then Services, and confirm Concierge services are available.
6. Test a basic question such as: What should I know?
7. Test a room action such as: Turn on the lights.
8. If you plan to use media continuity and Follow-Me behavior, confirm Media provider is configured and available in Concierge Integration Settings.

## Next Steps

1. [Configuration Guide](configuration.md)
2. [Concierge Global Settings](global-settings.md)
3. [Concierge Integration Settings](integration-settings.md)
4. [Initial Person Setup](person-setup.md)
5. [Initial Room Setup](room-setup.md)
