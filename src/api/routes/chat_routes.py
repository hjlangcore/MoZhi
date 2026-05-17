from fastapi import APIRouter, HTTPException, Depends
from loguru import logger
from src.api.schemas import ChatMessageCreate, BaseResponse
from src.core.session_store import get_session_store
from src.novel_agent.workflow import LLMClient
from src.core.config import settings

router = APIRouter(prefix="/chat", tags=["chat"])

_chat_history = {}
_llm_client = LLMClient(base_url=settings.OLLAMA_BASE_URL, model=settings.OLLAMA_MODEL, timeout=settings.OLLAMA_TIMEOUT)

def get_store():
    return get_session_store()

@router.post("/message", response_model=BaseResponse)
async def send_message(data: ChatMessageCreate, store=Depends(get_store)):
    novel = store.get_novel(data.novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")
    if data.novel_id not in _chat_history:
        _chat_history[data.novel_id] = []
    _chat_history[data.novel_id].append({"id": len(_chat_history[data.novel_id]) + 1, "role": data.role, "content": data.content})
    context = f"Novel: {novel.setting.novel_title}, Style: {novel.setting.style_type}" if novel.setting else ""
    recent = _chat_history[data.novel_id][-6:]
    history = "\n".join([f"{m['role']}: {m['content']}" for m in recent])
    prompt = f"You are helping write a novel. {context}\n\nHistory:\n{history}\n\nPlease reply in Chinese."
    try:
        resp = _llm_client.generate(prompt, temperature=0.7)
    except Exception as e:
        resp = f"Error: {e}"
    _chat_history[data.novel_id].append({"id": len(_chat_history[data.novel_id]) + 1, "role": "assistant", "content": resp})
    return BaseResponse(code=200, message="ok", data={"id": len(_chat_history[data.novel_id]), "role": "assistant", "content": resp})

@router.get("/{novel_id}/history", response_model=BaseResponse)
async def get_history(novel_id: str, store=Depends(get_store)):
    if not store.get_novel(novel_id):
        raise HTTPException(status_code=404, detail="Novel not found")
    return BaseResponse(code=200, message="ok", data=_chat_history.get(novel_id, []))
