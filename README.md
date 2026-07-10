
![Concierge Banner](custom_components/concierge/brand/Concierge-Banner.png)

## How It Works
![Concierge Flow](custom_components/concierge/brand/Concierge-Flow.png)


# 🏠 Concierge

**Concierge is the Household Coordination Engine for the Homes That Behave Well platform.**

Concierge transforms governed household knowledge into deterministic, explainable, room-aware experiences.

Rather than controlling devices directly, Concierge coordinates context, capabilities, experiences, identity, continuity, occupancy, restoration, messaging, productivity, and household awareness into a unified interaction system.

---

# ⚠ Current Release Status

## Concierge V1 (Current Release)

The current release focuses on:

- Room-aware interactions
- Alias-driven execution
- Scene activation
- Signals
- Global context
- Dashboard experiences
- Deterministic execution

## Concierge V2 (Roadmap Vision)

The architecture documented in this repository represents the future Concierge V2 platform.

Coordinator V2 expands Concierge into a complete household coordination engine capable of consuming:

- Vocabulary
- Capabilities
- Experiences
- Continuity
- Affinity
- Restoration
- Occupancy
- Presence
- Messaging
- Household Memory
- Productivity Context
- Provenance

---

# 🌎 Platform Position

Homes That Behave Well separates responsibility across several platform services.

```text
Foundation
    What is true?

Asset Intelligence
    What matters?

Voice Identity
    Who is interacting?

Concierge
    What should happen?
```

Concierge does not define truth.

Concierge consumes governed context and determines how the home should respond.

---

# 🧠 Coordinator V2

Coordinator V2 is the runtime heart of Concierge.

Coordinator consumes governed platform knowledge and transforms that knowledge into household behavior.

Coordinator consumes:

- Room Vocabulary
- Capability Projections
- Experiences
- Person Continuity
- Person-Room Affinity
- Experience Restoration
- Occupancy
- Presence
- Messaging Context
- Productivity Context
- Household Provenance

Coordinator does not own governance.

Governance remains in **Homes That Behave Well (HTBW)**.

---

# ✨ What Concierge Does

Concierge bridges the gap between:

- what the home knows
- what the home can do
- what the household needs
- what the household experiences

It provides a deterministic coordination layer that creates predictable household behavior.

---

# 🧠 Context-Aware Interactions

Concierge responds based on:

- room context
- occupancy
- presence
- household state
- experience eligibility
- household priorities

Every interaction is grounded in known context.

No runtime guessing.

No ambiguous device selection.

No uncontrolled discovery.

---

# ⚡ Deterministic Planning and Execution

Concierge is designed around predictable behavior.

Execution follows governed models rather than runtime inference.

Examples:

```text
Close the shades
```

→ Executes the appropriate room capability.

```text
Movie time
```

→ Selects the experience appropriate to the room, occupancy, and context.

```text
What should I know?
```

→ Produces a synthesized household briefing.

---

# 🏠 Room-Aware by Design

Every experience begins with room context.

Concierge understands:

- Rooms
- Merged Rooms
- Composite Rooms
- Floors
- Occupancy Zones

The household interacts with places.

Not devices.

---

# 👤 Person-Aware Experiences

Through Voice Identity and governed household models, Concierge can consume:

- Identity attribution
- Room affinity
- Communication preferences
- Restoration preferences
- Household continuity

This allows the home to adapt while remaining deterministic and explainable.

---

# 🔄 Continuity and Restoration

Concierge can preserve continuity across interactions.

Examples:

- Restore media
- Restore lighting scenes
- Restore work context
- Restore household experiences

Every restoration decision remains explainable.

Questions the platform should always answer:

```text
Why was this restored?
Why wasn't it restored?
Why was restoration suppressed?
```

---

# 🚶 Occupancy and Presence Awareness

Concierge consumes:

- Occupancy state
- Presence state
- Confidence state
- Multi-occupant context

This allows decisions to be informed by:

- Who is present
- Where they are
- Confidence levels
- Household composition

---

# 🌍 Household Awareness

Concierge combines:

- Weather
- Calendar
- Email summaries
- News
- Household signals
- Tasks
- Shopping state
- Productivity context

to answer questions such as:

```text
What should I know?

What happened while I was away?

What still needs attention?
```

---

# 💬 Messaging and Notification Discipline

Concierge follows a calm-by-default philosophy.

Messaging behavior is:

- Deliberate
- Explainable
- Occupant-aware
- Room-aware
- Interruption-aware

Concierge focuses on:

- Useful notifications
- Escalation when appropriate
- Acknowledgement awareness
- Household coordination

---

# 📋 Household Productivity

Concierge can surface governed productivity experiences such as:

- Calendar awareness
- Household briefings
- Task coordination
- Shopping coordination
- Status synthesis
- Knowledge experiences

Calendar and task systems remain systems of record.

Concierge consumes context.

It does not replace provider systems.

---

# 🧠 Household Memory and Explainability

Concierge is designed to explain itself.

Core questions include:

```text
What happened?

Why did it happen?

Why here?

Why now?

Why for this person?

Why didn't it happen?
```

Explainability is a first-class platform concern.

---

# 🧩 Core Concepts

## Vocabulary

Defines how the household refers to spaces and experiences.

## Capabilities

What the household can do.

## Experiences

Meaningful household outcomes.

## Continuity

What was happening previously.

## Affinity

Household preferences and context.

## Restoration

How previous experiences resume.

## Occupancy

Who is present and where.

## Messaging

How the home communicates.

## Provenance

Who did what, when, where, and how.

---

# 🧠 Design Principles

Concierge follows the Homes That Behave Well philosophy:

- Calm by default
- Deterministic behavior
- Explainable decisions
- Local-first execution
- Governed architecture
- Configuration over discovery
- Household-facing outcomes over implementation compatibility

---

# 🚫 What Concierge Is Not

Concierge is not:

- Alexa
- Google Assistant
- A generic LLM wrapper
- A device discovery engine
- A cloud-first orchestration engine

Concierge does not:

- Guess device targets
- Scan devices during execution
- Redefine governance
- Replace systems of record

---

# 🏗 Governance Model

## Homes That Behave Well (HTBW) Owns

- Architecture
- ADRs
- Contracts
- Models
- Governance
- Canonical definitions

## Concierge Owns

- Consumption
- Resolution
- Orchestration
- Planning
- Routing
- Execution behavior

Coordinator V2 consumes governance.

It does not define governance.

---

# 📦 Repository Structure

```text
custom_components/concierge/

coordinator/
consumption/
vocabulary/
capability/
experience/
continuity/
affinity/
restoration/
occupancy/
presence/
messaging/
memory/
productivity/
diagnostics/
explainability/

docs/

architecture/
contracts/
models/
governance/
patterns/
philosophy/
```

---

# 🚀 Development

## Install Dependencies

```bash
pip install -r requirements-dev.txt
```

## Run Tests

```bash
pytest -q
```

---

# ✅ Release Requirements

- Pass hassfest
- Pass HACS validation
- Pass tests
- Pass architecture review
- Pass ownership review
- Pass readiness review
- Publish release

---

# 🏁 Vision

Concierge is not a smart-home controller.

Concierge is the household coordination engine for Homes That Behave Well.

It combines governed household knowledge, identity, context, occupancy, continuity, experiences, restoration, messaging, productivity, memory, and provenance into deterministic household behavior.

A home that understands context.

A home that behaves predictably.

A home that explains itself.

A home that behaves well.

---

# 🧭 Learn More

Explore the platform architecture:

```text
/docs/architecture/
/docs/contracts/
/docs/models/
/docs/governance/
/docs/patterns/
/docs/philosophy/
```

---

**Concierge is part of the Homes That Behave Well platform.**
