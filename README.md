# THE WARDEN

**Engine:** Unreal Engine 5.7
**Setting:** Harrow Territory, England, 1903

---

## Sprint 1 Deliverables

### Environment
- [ ] `L_HarrowEstate` level created and optimized
- [ ] Estate exterior: gate, path, stable, grounds, facade
- [ ] 5 interior rooms: Entry Hall, Study, Kitchen, Library (exterior), East Wing Corridor
- [ ] All rooms seamlessly connected (no loading screens)
- [ ] Dynamic weather (rain system)
- [ ] Full day/night cycle with correct lighting
- [ ] All Quixel Megascans assets properly sourced, UV'd, and placed

### Player Character
- [ ] `BP_PlayerWarden` with third/first-person switching
- [ ] Sanity system (all 8 visual effect tiers implemented)
- [ ] `SightEndurance` system
- [ ] Interaction system (E key, single dot prompt)

### The Sight
- [ ] `BP_SightLens` with transition effects
- [ ] `M_PostProcess_Sight` material (single consolidated material)
- [ ] `BP_PlaneManager` with zone-specific density
- [ ] Millicent Grey visible in East Wing (Bleed layer) — observer only in Sprint 1

### NPC
- [ ] `BP_NPC_Oswald` with MetaHuman character
- [ ] Full schedule system implemented
- [ ] `WBP_DialoguePanel` dialogue UI
- [ ] `BP_AIBridge` stub with canned responses for testing
- [ ] `OswaldRelationship` variable updating based on interaction frequency

### Systems
- [ ] `BP_WorldState` (all Sprint 1 variables)
- [ ] Evidence system with `DT_Evidence` data table
- [ ] Evidence collection for all 7 Sprint 1 items (EV_001 through EV_007)
- [ ] Auto-journal entries on evidence collection

### UI
- [ ] `WBP_HUD` (minimal — sanity vignette, Sight indicator, evidence notification, dot prompt)
- [ ] `WBP_Journal` (all 5 sections, Sprint 1 content pre-populated)

### Audio
- [ ] Mundane ambient audio layer
- [ ] Bleed audio layer (Sight active)
- [ ] Rain audio system
- [ ] East Wing lamp flicker audio (3-1-3 pattern, midnight variant)
- [ ] NPC footstep audio

---

## Developer-Owned Systems (Not Built Here)
- Full AI backend (Python FastAPI)
- `AIBridge.h/.cpp` implementation (stub provided in `Source/TheWarden/`)
- NPC persona construction logic
- WebSocket server for real-time Unreal communication

---

## Plugin Installation Order
1. **UnrealGenAISupport** (runtime AI integration)
2. **UnrealClaude** (editor automation via Claude Code CLI, MIT license — [Natfii/UnrealClaude](https://github.com/Natfii/UnrealClaude))

### UnrealClaude Installation Notes
This plugin must be built from source. Clone with submodules, build via `RunUAT BuildPlugin`, copy the output to `Plugins/UnrealClaude/`, then install MCP bridge dependencies (`npm install` in `Resources/mcp-bridge`). Requires Claude Code CLI (`npm install -g @anthropic-ai/claude-code`) and authentication via `claude auth login`. No separate API key is needed — uses your existing Claude Code session.

---

## Out of Scope for Sprint 1
- Village zone
- Forest zone
- Lake zone
- Magic/spell casting system
- Full NPC roster
- Library interior
- Bedroom (rest/time skip)
- Deep plane
- The Barrow
- Dominion spell system
- Council correspondence system
- Any combat system
