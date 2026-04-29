"""
main.py

FastAPI WebSocket server for THE WARDEN AI backend.

The Unreal Engine client (via AIBridge.h) connects to /ws/{save_slot} and
sends JSON messages. The server streams NPC responses back token-by-token,
allowing Oswald's "thinking" animation to play while the response arrives.

──────────────────────────────────────────────────────────────────────────────
WebSocket Message Protocol
──────────────────────────────────────────────────────────────────────────────

CLIENT → SERVER  (JSON)
{
    "type":     "npc_message",
    "npc_id":   "NPC-001",
    "message":  "What do you know about Eleanor?",
    "sanity":   0.85,
    "game_day": 1,
    "game_time": 14.5
}

SERVER → CLIENT  (JSON, one or more per request)
{
    "type":   "chunk",
    "npc_id": "NPC-001",
    "text":   "She left in a hurry."
}

SERVER → CLIENT  (JSON, final message)
{
    "type":   "done",
    "npc_id": "NPC-001"
}

SERVER → CLIENT  (JSON, on error)
{
    "type":    "error",
    "message": "..."
}

──────────────────────────────────────────────────────────────────────────────
REST Endpoints
──────────────────────────────────────────────────────────────────────────────

GET /health          — Liveness probe for Cloud Run.
GET /world/{slot}    — Return current world state for a save slot.
POST /evidence       — Record a newly collected evidence item.
POST /spell          — Log a spell cast (for Council awareness calculation).
"""

from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from config import settings
from db.database import close_pool, get_pool, init_pool
from services.memory_service import get_world_state
from services.npc_service import generate_npc_response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ── Application lifecycle ─────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
    logger.info("Database pool initialised.")
    yield
    await close_pool()
    logger.info("Database pool closed.")


app = FastAPI(title="Warden Backend", lifespan=lifespan)


# ── REST endpoints ────────────────────────────────────────────────────────────

@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.get("/world/{save_slot}")
async def world_state(save_slot: int) -> JSONResponse:
    state = await get_world_state(save_slot)
    return JSONResponse(state)


class EvidencePayload(BaseModel):
    save_slot: int = 1
    evidence_id: str
    game_day: int
    game_time: float


@app.post("/evidence")
async def record_evidence(payload: EvidencePayload) -> JSONResponse:
    pool = get_pool()
    await pool.execute(
        """
        INSERT INTO evidence_log (save_slot, evidence_id, game_day, game_time)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (save_slot, evidence_id) DO NOTHING
        """,
        payload.save_slot,
        payload.evidence_id,
        payload.game_day,
        payload.game_time,
    )
    # Append to world_state collected_evidence array (no-op if already present)
    await pool.execute(
        """
        UPDATE world_state
        SET collected_evidence = array_append(collected_evidence, $2),
            updated_at = NOW()
        WHERE save_slot = $1
        AND NOT ($2 = ANY(collected_evidence))
        """,
        payload.save_slot,
        payload.evidence_id,
    )
    return JSONResponse({"status": "recorded", "evidence_id": payload.evidence_id})


class SpellPayload(BaseModel):
    save_slot: int = 1
    spell_name: str
    zone: str
    game_day: int
    game_time: float


@app.post("/spell")
async def log_spell(payload: SpellPayload) -> JSONResponse:
    pool = get_pool()
    await pool.execute(
        """
        INSERT INTO spell_log (save_slot, spell_name, zone, game_day, game_time)
        VALUES ($1, $2, $3, $4, $5)
        """,
        payload.save_slot,
        payload.spell_name,
        payload.zone,
        payload.game_day,
        payload.game_time,
    )
    return JSONResponse({"status": "logged"})


# ── WebSocket endpoint ────────────────────────────────────────────────────────

@app.websocket("/ws/{save_slot}")
async def websocket_endpoint(websocket: WebSocket, save_slot: int) -> None:
    await websocket.accept()
    logger.info("WebSocket connected — save_slot=%d", save_slot)

    try:
        while True:
            raw = await websocket.receive_text()

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(
                    json.dumps({"type": "error", "message": "Invalid JSON."})
                )
                continue

            msg_type = data.get("type")

            if msg_type == "npc_message":
                npc_id: str = data.get("npc_id", "")
                player_message: str = data.get("message", "")
                sanity: float = float(data.get("sanity", 1.0))
                game_day: int = int(data.get("game_day", 1))
                game_time: float = float(data.get("game_time", 8.0))

                if not npc_id or not player_message:
                    await websocket.send_text(
                        json.dumps(
                            {"type": "error", "message": "npc_id and message are required."}
                        )
                    )
                    continue

                # Stream response chunks back to Unreal
                async for chunk in generate_npc_response(
                    save_slot=save_slot,
                    npc_id=npc_id,
                    player_message=player_message,
                    sanity=sanity,
                    game_day=game_day,
                    game_time=game_time,
                ):
                    await websocket.send_text(
                        json.dumps({"type": "chunk", "npc_id": npc_id, "text": chunk})
                    )

                # Signal end of response
                await websocket.send_text(
                    json.dumps({"type": "done", "npc_id": npc_id})
                )

            else:
                await websocket.send_text(
                    json.dumps({"type": "error", "message": f"Unknown message type: {msg_type}"})
                )

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected — save_slot=%d", save_slot)
    except Exception:
        logger.exception("Unhandled WebSocket error — save_slot=%d", save_slot)


# ── Entry point (local dev) ───────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
