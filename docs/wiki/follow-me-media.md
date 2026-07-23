# Follow-Me Media

Follow-Me Media is a post-install enhancement that lets music hand off from one room to another when policy allows.

## What Follow-Me Is

Follow-Me evaluates a room transition and identity context, then decides whether media should hand off.

It is separate from:

- room-aware playback
- merged-room playback

## Core Rule

Follow-Me behavior is policy-governed.

It is not "motion detected, immediately move music" behavior.

## What Must Be True For Handoff

- Follow-Me is enabled in request context.
- Identity is recognized with sufficient confidence.
- Room transition is clear (source and destination are known and different).
- Manual-stop protection is not active.
- Manual-stop cooldown is not active.
- Destination room has configured and valid playback targets.

## What Blocks Handoff

Common refusal causes:

- Follow-Me disabled
- identity authority insufficient
- competing identity sources
- room transition ambiguous
- source or destination room unavailable
- manual stop active
- cooldown active

## Merged-Room Boundary

Follow-Me does not override merged-room behavior.

Merged-room playback remains grouped-room behavior. Follow-Me remains room-transition handoff behavior.

## Example Prompts

- follow me music
- move music here
- bring music here
- move playback here

## Related Pages

- [How To Use Concierge](how-to-use.md)
- [Merged Rooms](merged-rooms.md)
- [Services Reference](services-reference.md)
- [Troubleshooting](troubleshooting.md)