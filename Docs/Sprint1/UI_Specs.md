# UI Specifications
**Version:** 1.1
**Engine:** Unreal Engine 5.7

## 1. Overview
The UI in THE WARDEN is designed to be minimal and immersive. The primary interface is the physical Journal, with the HUD providing only essential ambient awareness.

## 2. WBP_HUD
The HUD is almost invisible, relying on subtle visual cues rather than explicit bars or icons.

- **Sanity Indicator:** A subtle vignette effect at the screen edges that intensifies as Sanity drops. At full sanity (1.0), it is invisible.
- **Sight Indicator:** When the Sight is active, the frame of the screen gains a faint amber tint, simulating the lens.
- **Evidence Notification:** When new evidence is collected, a single short line appears at the top of the screen (e.g., "Evidence Collected: Eleanor's Sight Lens Case"), fading after 4 seconds.
- **Interaction Prompt:** A single small dot appears centered on the screen when near an interactable object or NPC. The player presses 'E' to interact, and the dot disappears.

## 3. WBP_Journal
The Journal is the game's primary information system, accessed via the 'J' key. It is rendered as a physical 3D object with turning pages and a specific handwriting font.

### 3.1 Sections
1. **Notes:** Auto-generated entries from discoveries, encounters, and observations.
2. **Evidence Board:** A visual layout of all collected evidence, with auto-drawn connection lines between linked IDs.
3. **Grimoire:** Current spell list with full entry details. Unfound spells are greyed out.
4. **Maps:** Hand-drawn style maps of explored areas, auto-updating as the player explores.
5. **Correspondence:** All letters received from Council NPCs and Eleanor's letters.

### 3.2 Sprint 1 Pre-populated Content
- **Day 1 Arrival Entry:** Brief, professional, slightly wary. Sets the tone.
- **Estate Condition Note:** Observational, careful.
- **Oswald Note:** "The coachman. Knows more than he's saying. Worth sustained attention."
- **Grimoire:** 5 detection spells listed (starting kit). All others greyed out.

## 4. WBP_DialoguePanel
The dialogue panel is used for interactions with NPCs, specifically Oswald in Sprint 1.

- **Layout:** A clean, unobtrusive text box at the bottom of the screen.
- **Input:** The player types their response directly into the text box.
- **Output:** The NPC's response appears above the input box, with a slight delay to simulate thinking (handled by `BP_AIBridge`).
- **Animation:** While waiting for the response, the NPC plays a "thinking" or "listening" idle animation.
