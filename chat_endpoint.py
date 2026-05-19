from fastapi import APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
import anthropic
import os

router = APIRouter()
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SYSTEM_PROMPT = """Tu es l'assistant architectural de Taslim, plateforme du groupe Tijan."""

@router.post("/api/chat")
async def chat(req: Request):
    body = await req.json()
    messages = body.get("messages", [])
    context = body.get("context")
    model = body.get("model", "claude-haiku-4-5-20251001")
    system = SYSTEM_PROMPT + (f"\n\nConcept actuel :\n{context}" if context else "")
    r = client.messages.create(model=model, max_tokens=2048, system=system, messages=messages)
    text = "\n".join(b.text for b in r.content if b.type == "text")
    return {"content": text, "usage": r.usage.dict(), "stop_reason": r.stop_reason}
