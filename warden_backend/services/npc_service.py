"""
npc_service.py

Handles all Gemini API calls for NPC dialogue via Vertex AI.

Model selection strategy:
  - Primary:  gemini-3-flash-preview  (standard) / gemini-3.1-pro-preview  (critical)
  - Fallback: gemini-2.5-flash        (standard) / gemini-2.5-pro          (critical)

Retry policy:
  - Up to 3 attempts with exponential backoff on 503 / 429 responses.
  - If all primary-model attempts fail, one final attempt on the fallback model.
  - The model actually used is logged at INFO level for every call.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator

import vertexai
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable
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

vertexai.init(project=settings.gcp_project_id, location=settings.gcp_location)

# Retryable HTTP status codes from the Vertex AI SDK
_RETRYABLE_EXCEPTIONS = (ServiceUnavailable, ResourceExhausted)

# Exponential backoff delays in seconds for attempts 1, 2, 3
_BACKOFF_SECONDS = (1.0, 2.0, 4.0)

# Maximum retry attempts before switching to the fallback model
_MAX_RETRIES = 3


def _model_pair(npc_id: str) -> tuple[str, str]:
    """Return (primary_model, fallback_model) for the given NPC."""
    if npc_id in CRITICAL_NPC_IDS:
        return settings.model_critical, settings.model_critical_fallback
    return settings.model_standard, settings.model_standard_fallback


def _build_history(raw_history: list[dict[str, str]]) -> list[Content]:
    """Convert memory_service history to Vertex AI Content format."""
    history: list[Content] = []
    for turn in raw_history:
        vertex_role = "user" if turn["role"] == "player" else "model"
        history.append(
            Content(role=vertex_role, parts=[Part.from_text(turn["content"])])
        )
    return history


def _make_model(model_name: str, system_prompt: str) -> GenerativeModel:
    return GenerativeModel(
        model_name=model_name,
        system_instruction=system_prompt,
        generation_config=GenerationConfig(
            max_output_tokens=settings.max_response_tokens,
            temperature=0.85,
            top_p=0.95,
        ),
    )


async def _call_with_retry(
    model_name: str,
    system_prompt: str,
    history: list[Content],
    player_message: str,
) -> list[str]:
    """
    Attempt to call the Gemini API up to _MAX_RETRIES times with exponential
    backoff on retryable errors. Returns a list of response text chunks.
    Raises the last exception if all attempts fail.
    """
    last_exc: Exception | None = None

    for attempt in range(_MAX_RETRIES):
        try:
            model = _make_model(model_name, system_prompt)
            chat = model.start_chat(history=history)

            chunks: list[str] = []
            loop = asyncio.get_event_loop()
            responses = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: list(chat.send_message(player_message, stream=True)),
                ),
                timeout=settings.response_timeout_seconds,
            )
            for chunk in responses:
                if chunk.text:
                    chunks.append(chunk.text)

            logger.info("Model used: %s (attempt %d)", model_name, attempt + 1)
            return chunks

        except _RETRYABLE_EXCEPTIONS as exc:
            last_exc = exc
            wait = _BACKOFF_SECONDS[min(attempt, len(_BACKOFF_SECONDS) - 1)]
            logger.warning(
                "Retryable error on model %s attempt %d/%d: %s — retrying in %.1fs",
                model_name,
                attempt + 1,
                _MAX_RETRIES,
                exc,
                wait,
            )
            await asyncio.sleep(wait)

        except asyncio.TimeoutError as exc:
            last_exc = exc
            logger.warning(
                "Timeout on model %s attempt %d/%d",
                model_name,
                attempt + 1,
                _MAX_RETRIES,
            )
            # Do not retry on timeout — fall through to fallback immediately
            break

    raise last_exc or RuntimeError(f"All {_MAX_RETRIES} attempts failed for {model_name}")


async def generate_npc_response(
    save_slot: int,
    npc_id: str,
    player_message: str,
    sanity: float,
    game_day: int,
    game_time: float,
) -> AsyncIterator[str]:
    """
    Generate a streaming NPC response with automatic model fallback.

    Yields string chunks as they arrive. Persists the completed turn to the
    database after streaming finishes.
    """
    # ── 1. Fetch context ──────────────────────────────────────────────────────
    world_state = await get_world_state(save_slot)
    relationship = await update_relationship(save_slot, npc_id, game_day)
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

    vertex_history = _build_history(history)
    primary_model, fallback_model = _model_pair(npc_id)

    # ── 3. Call primary model with retry, then fallback ───────────────────────
    chunks: list[str] = []
    model_used = primary_model

    try:
        chunks = await _call_with_retry(
            primary_model, system_prompt, vertex_history, player_message
        )
    except Exception as primary_exc:
        logger.error(
            "Primary model %s failed for NPC %s after %d attempts: %s — trying fallback %s",
            primary_model,
            npc_id,
            _MAX_RETRIES,
            primary_exc,
            fallback_model,
        )
        try:
            chunks = await _call_with_retry(
                fallback_model, system_prompt, vertex_history, player_message
            )
            model_used = fallback_model
            logger.info("Fallback model %s succeeded for NPC %s", fallback_model, npc_id)
        except Exception as fallback_exc:
            logger.error(
                "Fallback model %s also failed for NPC %s: %s",
                fallback_model,
                npc_id,
                fallback_exc,
            )
            chunks = ["..."]
            model_used = "none"

    # ── 4. Yield chunks ───────────────────────────────────────────────────────
    for chunk in chunks:
        yield chunk

    # ── 5. Persist turn ───────────────────────────────────────────────────────
    full_response = "".join(chunks)
    if full_response and model_used != "none":
        await append_turn(
            save_slot=save_slot,
            npc_id=npc_id,
            player_message=player_message,
            npc_response=full_response,
            game_day=game_day,
            game_time=game_time,
        )
