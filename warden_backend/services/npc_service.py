"""
npc_service.py

Handles all Gemini API calls for NPC dialogue.

Responsibilities:
  - Select the correct model (standard vs. critical) based on NPC ID.
  - Inject the system prompt from prompt_builder.
  - Inject conversation history from memory_service.
  - Stream the response token-by-token back to the WebSocket caller.
  - Persist the completed turn via memory_service.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Any

import vertexai
from vertexai.generative_models import (
    Content,
    GenerationConfig,
    GenerativeModel,
    Part,
)

from config import CRITICAL_NPC_IDS, settings
from services.memory_service import (
    append_turn,
    get_conversation_history,
    get_world_state,
    update_relationship,
)
from services.prompt_builder import build_system_prompt

logger = logging.getLogger(__name__)

# Initialise Vertex AI once at module import time.
# On Cloud Run, Application Default Credentials are used automatically.
vertexai.init(project=settings.gcp_project_id, location=settings.gcp_location)


def _select_model(npc_id: str) -> str:
    """Return the appropriate Gemini model name for the given NPC."""
    return (
        settings.model_critical
        if npc_id in CRITICAL_NPC_IDS
        else settings.model_standard
    )


def _build_history(
    raw_history: list[dict[str, str]],
) -> list[Content]:
    """
    Convert the flat role/content list from memory_service into the
    Vertex AI Content format expected by GenerativeModel.start_chat().
    """
    history: list[Content] = []
    for turn in raw_history:
        vertex_role = "user" if turn["role"] == "player" else "model"
        history.append(Content(role=vertex_role, parts=[Part.from_text(turn["content"])]))
    return history


async def generate_npc_response(
    save_slot: int,
    npc_id: str,
    player_message: str,
    sanity: float,
    game_day: int,
    game_time: float,
) -> AsyncIterator[str]:
    """
    Generate a streaming NPC response.

    Yields string chunks as they arrive from the Gemini API.
    Persists the completed turn to the database after streaming finishes.

    Args:
        save_slot:      Save slot identifier.
        npc_id:         Canonical NPC identifier (e.g. "NPC-001").
        player_message: The player's raw text input.
        sanity:         Current player sanity (0.0–1.0).
        game_day:       Current in-game day.
        game_time:      Current in-game time (0.0–24.0).

    Yields:
        String chunks of the NPC's response.
    """
    # ── 1. Fetch context from database ───────────────────────────────────────
    world_state: dict[str, Any] = await get_world_state(save_slot)
    relationship: int = await update_relationship(save_slot, npc_id, game_day)
    history = await get_conversation_history(save_slot, npc_id)
    collected_evidence: list[str] = world_state.get("collected_evidence") or []

    # ── 2. Build system prompt ────────────────────────────────────────────────
    system_prompt = build_system_prompt(
        npc_id=npc_id,
        relationship=relationship,
        sanity=sanity,
        world_state=world_state,
        collected_evidence=collected_evidence,
    )

    # ── 3. Initialise model and chat session ──────────────────────────────────
    model_name = _select_model(npc_id)
    model = GenerativeModel(
        model_name=model_name,
        system_instruction=system_prompt,
        generation_config=GenerationConfig(
            max_output_tokens=settings.max_response_tokens,
            temperature=0.85,
            top_p=0.95,
        ),
    )
    chat = model.start_chat(history=_build_history(history))

    # ── 4. Stream response ────────────────────────────────────────────────────
    full_response_parts: list[str] = []

    try:
        responses = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None,
                lambda: list(chat.send_message(player_message, stream=True)),
            ),
            timeout=settings.response_timeout_seconds,
        )
        for chunk in responses:
            text = chunk.text
            if text:
                full_response_parts.append(text)
                yield text
    except asyncio.TimeoutError:
        logger.warning("Gemini response timed out for NPC %s", npc_id)
        fallback = "..."
        full_response_parts.append(fallback)
        yield fallback
    except Exception:
        logger.exception("Gemini API error for NPC %s", npc_id)
        fallback = "..."
        full_response_parts.append(fallback)
        yield fallback

    # ── 5. Persist completed turn ─────────────────────────────────────────────
    full_response = "".join(full_response_parts)
    if full_response:
        await append_turn(
            save_slot=save_slot,
            npc_id=npc_id,
            player_message=player_message,
            npc_response=full_response,
            game_day=game_day,
            game_time=game_time,
        )
