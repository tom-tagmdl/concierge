# Troubleshooting

Use this page when Concierge is not behaving the way you expect.

## Concierge Is Not Loading

1. Restart Home Assistant.
2. Check Home Assistant logs for Concierge errors.
3. Confirm Concierge is listed in Devices and Services.

## Concierge Services Are Missing

1. Confirm Concierge loaded successfully.
2. Reload Home Assistant.
3. Re-open Developer Tools and check services again.

## Concierge Uses The Wrong Room

1. Update room aliases.
2. Update room device lists.
3. If using merged rooms, verify merged-room membership.
4. Test again with: What can I do here?

## Person Responses Are Wrong

1. Check person setup.
2. Check mobile target for that person.
3. Check calendar/email/list choices for that person.
4. If using Voice Identity, confirm it is linked and configured.

## Calendar, Email, To-Do, Or Shopping Are Missing

1. Confirm the related integrations work in Home Assistant.
2. Confirm each person is mapped to the right calendar, mailbox, and lists in Concierge.
3. Test again with a simple prompt.

## Vocabulary Is Confusing

1. Ask: What do you call this?
2. Fix aliases until the room name is correct.
3. Re-test with a short command.

## Follow-Me Does Not Move Media

1. Confirm you used an explicit Follow-Me prompt like Follow me music.
2. Confirm identity is recognized with acceptable confidence.
3. Confirm source room and destination room are both known and different.
4. Confirm manual stop is not active in current media continuity context.
5. Confirm manual-stop cooldown is not active.
6. Confirm destination room has valid configured speaker/media-player targets.
7. If using merged rooms, confirm you are not expecting Follow-Me to override merged-room grouped behavior.

Useful fields to inspect in response payloads:

- follow_me_allowed
- follow_me_reason
- manual_stop_blocked
- cooldown_blocked
- source_room
- destination_room

## Still Not Working

1. Capture what you asked and what Concierge answered.
2. Capture activity timeline output for the same time window.
3. Compare with your person setup and room setup.
