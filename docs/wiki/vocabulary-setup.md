# Vocabulary Setup

Vocabulary means the words your household uses for rooms, devices, and actions.

Concierge works best when these words are clear and consistent.

## The Most Useful Prompt

Use this prompt while standing in the room:

- What do you call this?

This helps you confirm whether Concierge understands the room the same way your household does.

It also reminds you to define clear vocabulary words for device groups in that room.

## Easy Setup Method

1. Go room by room.
2. Ask: What do you call this?
3. Add or update room aliases until the answer is correct.
4. In room setup, use What do you call this to name device groups.
5. Select only the matching devices for each vocabulary word.
6. Test with action prompts.

## Device Vocabulary Example: Lamps vs Lights

You can create separate vocabulary words even when Home Assistant sees all devices as lights.

Example setup for one room:

1. Create a device group with What do you call this = Lamps.
2. Select only lamp devices.
3. Create another group with What do you call this = Lights.
4. Select only overhead light devices.
5. Optional: create a third group with What do you call this = Colored lights.
6. Select only color-capable light devices.

Result:

- Turn on the lamps controls only lamp devices.
- Turn on the lights controls only overhead lights.
- Turn on the colored lights controls only the colored light group.

## Device Vocabulary Example: TV vs Apple TV

You can also split media players into separate vocabulary words.

Example setup for one room:

1. Create a device group with What do you call this = TV.
2. Select only the television device.
3. Create another group with What do you call this = Apple TV.
4. Select only the Apple TV media player device.

Result:

- Turn on the TV controls only the television device.
- Play music on Apple TV controls only the Apple TV device.

## Good Examples

- Living room, TV room
- Main bedroom, primary bedroom
- Kitchen island lights

## Avoid

- using the same nickname for different rooms
- very long names
- names that sound too similar

## Final Test Prompts

- What do you call this?
- What can I do here?
- Turn on the lights.
- Turn on the lamps.
- Turn on the colored lights.
- Turn on the TV.
- Play music on Apple TV.
- Close the shades.
