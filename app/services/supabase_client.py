import asyncio
from datetime import datetime, timezone
from typing import Any, Optional

from supabase import AsyncClient, acreate_client

from app.core.config import get_settings


_client: Optional[AsyncClient] = None
_lock = asyncio.Lock()


async def get_client() -> AsyncClient:
    global _client
    if _client is None:
        async with _lock:
            if _client is None:
                s = get_settings()
                _client = await acreate_client(s.SUPABASE_URL, s.SUPABASE_KEY)
    return _client


def _parse_ts(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    v = value.replace("Z", "+00:00")
    return datetime.fromisoformat(v)


async def fetch_collection_meta(collection_id: str) -> tuple[Optional[str], Optional[datetime]]:
    client = await get_client()
    resp = await (
        client.table("collections")
        .select("ai_summary_text,last_summary_generated_at")
        .eq("id", collection_id)
        .maybe_single()
        .execute()
    )
    data: Optional[dict[str, Any]] = resp.data if isinstance(resp.data, dict) else None
    if not data:
        return None, None
    return data.get("ai_summary_text"), _parse_ts(data.get("last_summary_generated_at"))


async def fetch_latest_comment_ts(collection_id: str) -> Optional[datetime]:
    client = await get_client()
    resp = await (
        client.table("comments")
        .select("created_at")
        .eq("collection_id", collection_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    rows = resp.data if isinstance(resp.data, list) else []
    if not rows:
        return None
    return _parse_ts(rows[0].get("created_at"))


async def fetch_latest_comments(collection_id: str, limit: int = 50) -> list[str]:
    client = await get_client()
    resp = await (
        client.table("comments")
        .select("comment_text,created_at")
        .eq("collection_id", collection_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    rows = resp.data if isinstance(resp.data, list) else []
    return [r.get("comment_text", "") for r in rows if r.get("comment_text")]


async def update_collection_summary(collection_id: str, summary: str) -> None:
    client = await get_client()
    now = datetime.now(timezone.utc).isoformat()
    await (
        client.table("collections")
        .update({"ai_summary_text": summary, "last_summary_generated_at": now})
        .eq("id", collection_id)
        .execute()
    )