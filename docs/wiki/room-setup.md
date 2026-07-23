# Initial Room Setup

This page helps you set up each room so Concierge responds correctly in that space.

Room setup is also your control boundary.

It gives the homeowner the ability to decide what Concierge should include and what it should exclude, instead of giving Concierge free range over every device assigned to that room in Home Assistant.

Only the devices you explicitly select in room setup are the devices Concierge will control for that room vocabulary.

## Setup Steps

1. Sync rooms from Home Assistant areas.
2. Open one room at a time.
3. Add simple room aliases (for example, TV room and living room).
4. Define room vocabulary with the What do you call this field, then attach matching devices.
5. Save and test.

## What To Attach Per Room

- lights and lamps
- shades/covers
- speakers and media players
- TV or display devices
- sensors that matter for that room

## Voice Input and Output Routing

In a room, input and output can be different on purpose.

- Voice assistant device: where spoken commands are heard and where Concierge can announce through the assistant channel.
- Speaker/media player target: where Concierge can play TTS responses through speaker output.

This means you can speak to one device and hear the response on another configured device.

If both are configured, you can choose the output path in automations and service calls.

## How Room Vocabulary Works

The What do you call this field is the vocabulary label for the devices you select in that row.

This lets one room split Home Assistant device types into words your household actually uses.

Example: Home Assistant may treat all of these as lights, but you can separate them in Concierge:

1. Add a row with What do you call this = Lamps.
2. Select only the light devices that are lamps.
3. Add another row with What do you call this = Lights.
4. Select only overhead light devices.
5. Optional: add a third row with What do you call this = Colored lights.
6. Select only your color-capable light devices.

Now each word controls only its mapped devices in that room:

- Turn on the lamps controls only lamp devices.
- Turn on the lights controls only overhead lights.
- Turn on the colored lights controls only the color-capable group.

You can do the same for media players.

Example: Home Assistant may treat your TV and Apple TV as media players, but you can separate them:

1. Add a row with What do you call this = TV.
2. Select only the television device.
3. Add another row with What do you call this = Apple TV.
4. Select only the Apple TV media player device.

Now voice requests can target them separately:

- Turn on the TV controls only the television device.
- Play music on Apple TV controls only Apple TV.

## Test Prompts

- What can I do here?
- Turn on the lights.
- Turn on the lamps.
- Turn on the colored lights.
- Turn on the TV.
- Play music on Apple TV.
- Close the shades.

If a request controls the wrong room, update room aliases and room devices.

See [Vocabulary Setup](vocabulary-setup.md) for room naming tips.
