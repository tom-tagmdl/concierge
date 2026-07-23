# Voice Identity Personalization

This page explains what changes in Concierge when a user has completed a voice profile and is recognized.

## Short Answer

When recognition succeeds, Concierge can use that person's profile to personalize responses and routing.

Recognition does not replace setup. It activates the setup you already defined for that person.

## What Personalization Looks Like

When the recognized voice maps to a Concierge person profile, Concierge can use:

- that person's calendar source
- that person's email source
- that person's task source
- that person's shopping source
- that person's mobile notification target
- that person's linked room context

In practice, this means:

- What is on my calendar today can use the recognized person's calendar binding.
- Summarize important email can use the recognized person's mailbox binding.
- What is on my shopping list can use the recognized person's shopping source binding.
- Reminders and follow-up notifications can route to that person's mobile target.

## What Must Be Configured First

For this to work well, all of these must be true:

1. Voice Identity integration is installed.
2. Voice Identity linkage is turned on in Concierge Integration Settings.
3. The person is configured in Concierge Person Setup.
4. The person completes the interactive voice enrollment process to build the voice profile.
5. That voice profile is linked to the correct person in Concierge.
6. Calendar/email/task/shopping/mobile bindings are set for that person.

If these are incomplete, personalization is partial or unavailable.

## What Happens If Recognition Is Low Confidence

Concierge can treat low-confidence or unavailable recognition as unresolved identity.

In those cases, personal routing may not apply, and behavior can fall back to less personalized responses until identity is confidently resolved.

For Follow-Me behavior, unresolved or low-confidence identity can block cross-room handoff.

Competing identity sources can also block Follow-Me handoff.

## How To Validate It

Use quick checks after enrollment:

1. Ask: What is on my calendar today?
2. Ask: Summarize important email.
3. Ask: What is on my shopping list?
4. Send a reminder and confirm it goes to the expected mobile target.

If results are wrong, review [Initial Person Setup](person-setup.md) and [Concierge Integration Settings](integration-settings.md).

For installation/runtime alignment and failure-code remediation, review [Voice Identity and Concierge Alignment](voice-identity-alignment.md).
