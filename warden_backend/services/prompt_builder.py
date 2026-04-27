"""
prompt_builder.py

STUB — Developer implements this.

Responsible for constructing the full system prompt injected into each NPC's
Gemini API call. The prompt is assembled from four layers:

    1. NPC persona        — canonical personality, secrets gated by relationship
                            level, speech patterns, and what the NPC will never
                            volunteer. Source: Document 02 (NPC Roster).
    2. World state        — current in-game day, time, weather, mystery layer,
                            binding degradation, and Council awareness level.
    3. Relationship state — the player's current relationship level with this
                            NPC and the information tier it unlocks.
    4. Evidence context   — the subset of collected evidence IDs that this NPC
                            would plausibly be aware of or affected by.

The assembled prompt is passed to npc_service.py, which injects it as the
system instruction for the Gemini API call.

──────────────────────────────────────────────────────────────────────────────
IMPLEMENTATION NOTES FOR THE DEVELOPER
──────────────────────────────────────────────────────────────────────────────

NPC persona data lives in Document 02. Each NPC entry defines:
  - Core personality paragraph
  - What they know at each relationship level (0–4)
  - What they will never volunteer
  - Speech patterns / register

The prompt must enforce the CRITICAL RULE from Document 02:
  "No NPC ever volunteers a secret unprompted. Secrets are revealed through:
   (1) sufficient trust level, (2) specific questions that corner them,
   (3) spell use, or (4) world events that make silence impossible."

Sanity-driven prompt modification:
  - sanity >= 0.5: No modification.
  - 0.3 <= sanity < 0.5: NPCs perceive something is wrong with the player.
    Oswald becomes more guarded. Agnes becomes more concerned.
  - sanity < 0.3: NPCs react to visible distress. Responses shorter, more
    alarmed. Some NPCs refuse to continue conversation.

The Voice (NPC-S03) requires a completely separate prompt architecture —
it does not use the standard persona template. Implement separately.

──────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

from typing import Any


def build_system_prompt(
    npc_id: str,
    relationship: int,
    sanity: float,
    world_state: dict[str, Any],
    collected_evidence: list[str],
) -> str:
    """
    STUB — Developer implements this.

    Assemble and return the full system prompt string for the given NPC,
    incorporating persona, world state, relationship level, and evidence context.

    Args:
        npc_id:             Canonical NPC identifier (e.g. "NPC-001").
        relationship:       Current relationship level (0–4).
        sanity:             Player's current sanity (0.0–1.0).
        world_state:        Dict from memory_service.get_world_state().
        collected_evidence: List of evidence IDs the player has collected.

    Returns:
        A fully assembled system prompt string ready for the Gemini API.
    """
    # STUB — Developer implements this
    # Replace this placeholder with the full persona construction logic.
    return (
        f"You are NPC {npc_id}. "
        f"Relationship level: {relationship}. "
        f"Player sanity: {sanity:.2f}. "
        f"Day {world_state.get('current_day', 1)}, "
        f"time {world_state.get('current_time_of_day', 8.0):.1f}. "
        f"Evidence collected: {', '.join(collected_evidence) or 'none'}. "
        "Respond in character. Keep responses under 80 words."
    )
