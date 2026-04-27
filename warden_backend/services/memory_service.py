"""
memory_service.py

Manages per-NPC conversation memory and relationship state.

Each NPC maintains a rolling window of conversation history that is injected
into their system prompt. Older turns are pruned once the window exceeds the
configured limit. Relationship levels persist across sessions in PostgreSQL.
"""

from __future__ import annotations

from typing import Any

from db.database import get_pool

# Maximum number of conversation turns (player + NPC pairs) to retain per NPC.
MEMORY_WINDOW = 20


async def get_relationship(save_slot: int, npc_id: str) -> int:
    """Return the current relationship level (0–4) for an NPC."""
    pool = get_pool()
    row = await pool.fetchrow(
        "SELECT relationship FROM npc_relationships WHERE save_slot=$1 AND npc_id=$2",
        save_slot,
        npc_id,
    )
    return row["relationship"] if row else 0


async def update_relationship(
    save_slot: int,
    npc_id: str,
    current_day: int,
) -> int:
    """
    Increment relationship by 1 if the player has not spoken to this NPC today.
    Caps at 4. Returns the new relationship level.
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO npc_relationships (save_slot, npc_id, relationship, last_spoken_day)
            VALUES ($1, $2, 0, $3)
            ON CONFLICT (save_slot, npc_id) DO UPDATE
                SET relationship = LEAST(
                        npc_relationships.relationship +
                        CASE WHEN npc_relationships.last_spoken_day < $3 THEN 1 ELSE 0 END,
                        4
                    ),
                    last_spoken_day = $3,
                    updated_at = NOW()
            RETURNING relationship
            """,
            save_slot,
            npc_id,
            current_day,
        )
    return row["relationship"]


async def get_conversation_history(
    save_slot: int,
    npc_id: str,
) -> list[dict[str, str]]:
    """
    Return the most recent MEMORY_WINDOW turns as a list of
    {"role": "player"|"npc", "content": "..."} dicts, oldest first.
    """
    pool = get_pool()
    rows = await pool.fetch(
        """
        SELECT role, content
        FROM (
            SELECT role, content, created_at
            FROM conversation_memory
            WHERE save_slot=$1 AND npc_id=$2
            ORDER BY created_at DESC
            LIMIT $3
        ) sub
        ORDER BY created_at ASC
        """,
        save_slot,
        npc_id,
        MEMORY_WINDOW * 2,  # each turn = 2 rows (player + npc)
    )
    return [{"role": r["role"], "content": r["content"]} for r in rows]


async def append_turn(
    save_slot: int,
    npc_id: str,
    player_message: str,
    npc_response: str,
    game_day: int,
    game_time: float,
) -> None:
    """Persist a completed conversation turn (player message + NPC response)."""
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.executemany(
            """
            INSERT INTO conversation_memory
                (save_slot, npc_id, role, content, game_day, game_time)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            [
                (save_slot, npc_id, "player", player_message, game_day, game_time),
                (save_slot, npc_id, "npc", npc_response, game_day, game_time),
            ],
        )
    await _prune_old_turns(save_slot, npc_id)


async def _prune_old_turns(save_slot: int, npc_id: str) -> None:
    """Delete turns beyond the memory window to keep the table bounded."""
    pool = get_pool()
    await pool.execute(
        """
        DELETE FROM conversation_memory
        WHERE id IN (
            SELECT id FROM conversation_memory
            WHERE save_slot=$1 AND npc_id=$2
            ORDER BY created_at DESC
            OFFSET $3
        )
        """,
        save_slot,
        npc_id,
        MEMORY_WINDOW * 2,
    )


async def get_world_state(save_slot: int) -> dict[str, Any]:
    """Return the current world state snapshot for a save slot."""
    pool = get_pool()
    row = await pool.fetchrow(
        "SELECT * FROM world_state WHERE save_slot=$1",
        save_slot,
    )
    if row is None:
        return {}
    return dict(row)
