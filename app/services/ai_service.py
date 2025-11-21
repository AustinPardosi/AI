import asyncio
from typing import List

import google.generativeai as genai

from app.core.config import get_settings


class AIServiceError(Exception):
    pass


settings = get_settings()
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=(
        "You are an empathetic museum assistant. Summarize the following visitor comments into a cohesive, emotional, and inclusive narrative in Indonesian. Avoid bullet points, make it flow like a story. Keep it under 150 words."
    ),
)


async def generate_summary_async(comments: List[str]) -> str:
    if not comments:
        raise AIServiceError("No comments provided")
    text = "\n".join(comments)
    try:
        resp = await asyncio.to_thread(model.generate_content, text)
        if not hasattr(resp, "text") or not resp.text:
            raise AIServiceError("Empty AI response")
        return resp.text.strip()
    except Exception as e:
        raise AIServiceError(str(e))