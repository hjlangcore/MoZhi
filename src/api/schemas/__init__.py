from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


class BaseResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    code: int
    message: str
    detail: Optional[str] = None


class SessionCreate(BaseModel):
    session_name: str = Field(..., min_length=1, max_length=200)


class SessionResponse(BaseModel):
    session_id: str
    session_name: str
    current_novel_id: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class NovelCreate(BaseModel):
    session_id: str
    theme: str = Field(..., min_length=1)
    style_type: str = Field(default="凡人流")


class NovelResponse(BaseModel):
    novel_id: str
    title: str
    theme: str
    status: str
    total_words: int
    current_chapter: int
    style_type: str
    created_at: datetime
    updated_at: datetime


class NovelSettingResponse(BaseModel):
    novel_title: str
    world_framework: str
    power_system: str
    major_factions: str
    main_character: dict
    supporting_characters: List[dict]
    antagonists: List[dict]
    main_plot_thread: str
    core_conflicts: str
    style_type: str


class ChapterCreate(BaseModel):
    target_words: int = Field(default=2000, ge=500, le=10000)


class ChapterResponse(BaseModel):
    chapter_number: int
    title: str
    content: str
    status: str
    word_count: int
    created_at: datetime
    updated_at: datetime



class WorkflowStatusResponse(BaseModel):
    status: str
    current_chapter: int
    total_words: int
    target_words: int
    progress_percent: float


class HealthResponse(BaseModel):
    status: str
    version: str
    llm_connected: bool


class ChatMessageCreate(BaseModel):
    novel_id: str
    role: str = "user"
    content: str = Field(..., min_length=1)
