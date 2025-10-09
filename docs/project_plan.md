# Project Plan: AI-Powered Smart Mirror

## Executive Summary

This project will deliver a renter-compatible smart mirror that functions as a personalized daily dashboard and AI assistant. By combining a Raspberry Pi–based display with a two-way mirror and integrated AI software, the mirror will provide actionable, glanceable insights (calendar, weather, news, tasks), switchable views (finance, health, smart home), and natural hands-free control.Drilling and mounting are allowed, but landlord-controlled devices remain off-limits (e.g., thermostat replacement). All smart home integrations will be modular, renter-portable add-ons such as bulbs and plugs.

## Objectives

1. Build a durable, wall-mounted mirror device with hidden cable management.
2. Deliver an AI-first user experience: conversational voice commands, gesture input, natural task flows.
3. Provide modular dashboards with a focus on the Morning Report (MVP), while enabling expansion into Finance, Health, and Smart Home.
4. Ensure the design is portable between apartments by avoiding reliance on landlord-controlled infrastructure.

## Feature Roadmap

### Phase 1 — MVP: Software First

- Morning Report Dashboard
  - Quadrant layout: Calendar | Weather | News | To-Do List.
  - Customizable widgets with AI-assisted setup.
- Mode Switching
  - Software toggle between dashboards (Morning, Finance, Ambient).
- Voice Interaction
  - Bedrock/LLM integration for conversational control.
- Deployment
  - Local Raspberry Pi build, running UI + AI agent client.

### Phase 2 — Hardware Integration

- Mirror Build
  - Two-way mirror glass/film.
  - Raspberry Pi + display panel.
  - Drilled wall-mount frame with routed power.
- Gesture Recognition
  - Embedded camera + basic swipe/selection gestures.
- Smart Home Lite
  - Integration with bulbs/plugs.
  - Mirror as control hub, no reliance on landlord devices.

### Phase 3 — Expansion & Polish

- Finance Dashboard
  - Real-time stocks, investments, portfolio view.
- Health & Fitness View
  - Sync with wearable APIs, daily summary + trends.
- Ambient Mode
  - Visuals, music, or calming content.
- AI Extensions
  - Personalized recommendations.
  - Learning routines from user interactions.

## Constraints

- Allowed: drilling, mounting, routing hidden cabling, replacing temporary fixtures.
- Not Allowed: direct integration with landlord devices (thermostats, built-in appliances).
- Portable: smart home add-ons must be removable and reusable across apartments.

## Risks & Mitigations

- Latency: AI voice/gesture → Mitigate with local pre-processing + cloud fallback.
- Display Clarity: two-way mirror thickness → Test with both film and glass before final.
- AI Reliability: conversational errors → Human-verifiable fallback for commands.
- Apartment Power Access: cord routing visibility → Hide behind mount; optional raceway.

## Deliverables

- Phase 1: Deployed MVP software on Pi.
- Phase 2: Wall-mounted mirror prototype, fully functional with dashboard + voice + gestures.
- Phase 3: Extended dashboards, smart home integrations, polish for daily usability.
- Documentation: hardware build guide, software architecture, integration notes.
