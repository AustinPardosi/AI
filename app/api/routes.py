from datetime import datetime
from typing import Dict
from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.services.supabase_client import (
    fetch_collection_meta,
    fetch_latest_comment_ts,
    fetch_latest_comments,
    update_collection_summary,
)
from app.services.ai_service import generate_summary_async, AIServiceError


router = APIRouter(prefix="/api/v1")


@router.post("/summarize/{collection_id}")
async def summarize(collection_id: UUID) -> Dict[str, str]:
    cid = str(collection_id)
    ai_summary_text, last_summary_generated_at = await fetch_collection_meta(cid)
    if ai_summary_text is None and last_summary_generated_at is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    max_comment_ts = await fetch_latest_comment_ts(cid)
    if ai_summary_text and last_summary_generated_at and (
        max_comment_ts is None or last_summary_generated_at > max_comment_ts
    ):
        return {"summary": ai_summary_text}

    comments = await fetch_latest_comments(cid, limit=50)
    if len(comments) < 3:
        return {"summary": "Belum cukup data untuk merangkum."}

    try:
        summary = await generate_summary_async(comments)
    except AIServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))

    await update_collection_summary(cid, summary)
    return {"summary": summary}