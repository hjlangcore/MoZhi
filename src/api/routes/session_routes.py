from fastapi import APIRouter, HTTPException, Depends
from typing import List
from loguru import logger

from src.api.schemas import (
    SessionCreate, SessionResponse, NovelCreate, NovelResponse,
    NovelSettingResponse, BaseResponse, ChapterResponse, WorkflowStatusResponse
)
from src.core.session_store import get_session_store
from src.novel_agent.state import SessionModel, NovelState
from src.core.exceptions import SessionNotFoundError, NovelNotFoundError

router = APIRouter(prefix="/sessions", tags=["sessions"])


def get_store():
    return get_session_store()


@router.post("/", response_model=BaseResponse)
async def create_session(data: SessionCreate, store=Depends(get_store)):
    logger.info(f"Creating session: {data.session_name}")
    session = store.create_session(data.session_name)
    return BaseResponse(
        code=200,
        message="Session created successfully",
        data=SessionResponse(
            session_id=session.session_id,
            session_name=session.session_name,
            current_novel_id=session.current_novel_id,
            is_active=session.is_active,
            created_at=session.created_at,
            updated_at=session.updated_at
        ).model_dump()
    )


@router.get("/", response_model=BaseResponse)
async def list_sessions(store=Depends(get_store)):
    sessions = store.list_sessions()
    session_list = [
        SessionResponse(
            session_id=s.session_id,
            session_name=s.session_name,
            current_novel_id=s.current_novel_id,
            is_active=s.is_active,
            created_at=s.created_at,
            updated_at=s.updated_at
        ).model_dump()
        for s in sessions
    ]
    return BaseResponse(code=200, message="success", data=session_list)


@router.get("/{session_id}", response_model=BaseResponse)
async def get_session(session_id: str, store=Depends(get_store)):
    session = store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return BaseResponse(
        code=200,
        message="success",
        data=SessionResponse(
            session_id=session.session_id,
            session_name=session.session_name,
            current_novel_id=session.current_novel_id,
            is_active=session.is_active,
            created_at=session.created_at,
            updated_at=session.updated_at
        ).model_dump()
    )



@router.get('/{session_id}/novels', response_model=BaseResponse)
async def list_session_novels(session_id: str, store=Depends(get_store)):
    session = store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail='Session not found')

    novels = store.list_session_novels(session_id)
    novel_list = [
        {
            'novel_id': n.novel_id,
            'title': n.setting.novel_title if n.setting else '????',
            'theme': n.setting.novel_title if n.setting else '',
            'status': n.status,
            'total_words': n.total_words,
            'current_chapter': n.current_chapter,
            'style_type': n.setting.style_type if n.setting else '',
            'created_at': str(n.created_at)
        }
        for n in novels
    ]
    return BaseResponse(code=200, message='success', data=novel_list)

@router.delete("/{session_id}", response_model=BaseResponse)
async def delete_session(session_id: str, store=Depends(get_store)):
    success = store.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return BaseResponse(code=200, message="Session deleted successfully")
