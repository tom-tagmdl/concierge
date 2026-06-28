# 🏠 Concierge

**Concierge is a Home Assistant integration that turns your home into a calm, context-aware, and explainable system.**

It connects your devices, rooms, and data into a single interaction layer—so your home doesn’t just react… it understands.

***

## ✨ What Concierge Does

Concierge bridges the gap between:

* what your home knows
* what your home can do
* what you actually experience

It provides a unified layer that brings clarity, speed, and predictability to your smart home.

***

### 🧠 Context-Aware Interactions

Concierge responds based on:

* the room you are in
* what devices and systems exist there
* what is happening in your home

No guessing. No scanning. No ambiguity.

***

### ⚡ Fast, Deterministic Actions

Concierge executes instantly because it already knows what to do.

* No runtime discovery
* No layered automation delays
* No inconsistent behavior

Examples:

“close the shades” → executes configured scene immediately  
“movie time” → triggers a scene via alias

***

### 🏠 Room-Based Experience

Every interaction is grounded in **room context**:

* devices and sensors in that room
* scenes and execution behavior
* signals relevant to that space

You do not control devices—you interact with a space.

***

### 🌍 Whole-Home Awareness

Concierge integrates global context:

* weather
* news
* calendar
* email summaries
* household signals (laundry, dishwasher, etc.)

So your home can answer:

* “what should I know?”
* “what’s happening today?”
* “is anything done?”

***

### 📊 Unified Voice + UI Experience

Concierge connects:

* Voice (Home Assistant Assist, alias-first)
* UI (room dashboards and interaction panels)
* System state (signals and context)

Everything stays in sync.

***

## 🧩 Key Concepts

### Signals

Stateful conditions in the home:

* laundry complete
* upcoming meetings
* shopping list

***

### Global Context

Informational awareness:

* weather
* time
* news
* email summaries

***

### Interactions

What the system surfaces:

* actions you can take
* things you should know
* guided workflows

***

### Execution Patterns

How actions happen:

1. Scene (preferred)
2. Group
3. Entity fallback

Always fast. Always predictable.

***

## 🧠 Design Principles

Concierge follows the **Homes That Behave Well** philosophy:

* Calm by default
* Deterministic behavior
* Explainable decisions
* Local-first execution
* Configuration over discovery

***

## 🚫 Not Just Another Voice Assistant

Concierge is **not Alexa or Google Assistant**.

It does NOT:

* guess what you meant
* scan devices at runtime
* rely on cloud-first interpretation

It DOES:

* understand your configured home
* execute immediately
* explain what it is doing

***

## 🛠 Configuration Model

Concierge separates configuration into two layers:

### ⚙️ System Configuration (Integration Settings / Gear Icon)

* AI providers (optional)
* External integrations (M365, etc.)
* Authentication and system behavior

***

### 🏠 UI Configuration (Concierge Interface)

* rooms and composite rooms
* scenes and aliases
* signals and global context
* execution behavior

***

## 🧪 Example Interactions

### Voice

User: close the shades  
→ scene executes immediately

User: what should I know?  
→ calendar + weather + signals combined

***

### UI (Room Panel)

Great Room

Context

* Weather
* News

Signals

* Laundry complete

Actions

* Close shades
* Movie mode

***

## ⚡ Performance by Design

Concierge is fast because it:

* eliminates runtime discovery
* uses precomputed configuration
* prefers single-call execution
* bypasses unnecessary layers

The system never hesitates once intent is known.

***

## 📦 Repository Structure

custom\_components/concierge/  
services.py  
coordinator.py  
store.py

docs/  
contracts/  
models/  
patterns/  
architecture/  
philosophy/

***

## 🚀 Development

### Install dependencies

pip install -r requirements-dev.txt

***

### Run tests

pytest -q

***

## ✅ Release Requirements

* Update version in `manifest.json`
* Pass HACS validation
* Pass hassfest
* Pass tests
* Tag and publish release

***

## 🏁 Vision

Concierge is not about controlling your home.

It is about creating a home that:

* understands context
* behaves predictably
* explains itself

A home that simply works.

***

## 🧭 Learn More

Explore the full architecture:

* /docs/philosophy/
* /docs/contracts/
* /docs/patterns/
* /docs/architecture/

***

**Concierge is part of the Homes That Behave Well platform.**

***
