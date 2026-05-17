from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import json


class NovelStatus(str, Enum):
    DRAFT = "draft"
    WRITING = "writing"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class ChapterStatus(str, Enum):
    DRAFT = "draft"
    WRITTEN = "written"
    POLISHED = "polished"
    PROOFREAD = "proofread"
    APPROVED = "approved"


class SceneStatus(str, Enum):
    DRAFT = "draft"
    WRITTEN = "written"
    REVISED = "revised"


class RelationshipType(str, Enum):
    ALLY = "ally"
    RIVAL = "rival"
    MENTOR = "mentor"
    ENEMY = "enemy"
    FAMILY = "family"
    ROMANCE = "romance"
    NEUTRAL = "neutral"


class CharacterRelationship(BaseModel):
    """角色之间的关系"""
    target_name: str
    relation_type: RelationshipType = RelationshipType.NEUTRAL
    description: str = ""
    intimacy: int = Field(default=50, ge=0, le=100)  # 亲密度
    last_changed_chapter: int = 0


class CharacterState(BaseModel):
    """角色动态状态 — 随章节推进而变化（状态回写目标）"""
    current_realm: str = ""           # 当前境界
    current_location: str = ""        # 当前位置
    current_goal: str = ""            # 当前目标
    health: str = "正常"
    alive: bool = True
    inventory: List[str] = Field(default_factory=list)
    known_secrets: List[str] = Field(default_factory=list)


class StateChange(BaseModel):
    """状态变更记录 — 用于状态回写追踪"""
    chapter_number: int
    character_name: str
    field_changed: str               # 变更的字段名
    old_value: str = ""
    new_value: str = ""
    reason: str = ""                 # 变更原因


class CharacterModel(BaseModel):
    name: str
    role: str
    description: str
    background: Optional[str] = None
    personality: Optional[str] = None
    motivation: Optional[str] = None
    relationship_with_protagonist: Optional[str] = None
    importance: str = "supporting"
    # 新增：动态状态 + 关系网
    dynamic_state: CharacterState = Field(default_factory=CharacterState)
    relationships: List[CharacterRelationship] = Field(default_factory=list)
    first_appearance_chapter: int = 0
    last_appearance_chapter: int = 0
    total_appearances: int = 0


class ForeshadowingModel(BaseModel):
    seed: str
    chapter_introduced: int
    status: str = "unresolved"
    planned_reveal_chapter: Optional[int] = None
    description: str


class SceneModel(BaseModel):
    """场景 — 章内的最小叙事单元，借鉴马良AI的四层结构"""
    scene_number: int                          # 章内场景序号
    title: str = ""                            # 场景标题
    content: str = ""                          # 场景正文
    status: SceneStatus = SceneStatus.DRAFT
    word_count: int = 0
    scene_type: str = "normal"                 # normal/action/dialogue/description/transition/climax
    characters_present: List[str] = Field(default_factory=list)  # 在场角色
    location: str = ""                         # 场景地点
    emotion_tone: str = ""                     # 情绪基调


class ChapterModel(BaseModel):
    chapter_number: int
    title: str
    content: str = ""
    status: ChapterStatus = ChapterStatus.DRAFT
    word_count: int = 0
    foreshadowing_used: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    # 新增：章节内场景
    scenes: List[SceneModel] = Field(default_factory=list)
    # 新增：章节质量评分（由审计门禁写入）
    quality_score: float = 0.0
    gate_report: Optional[Dict[str, Any]] = None


class VolumeModel(BaseModel):
    volume_number: int
    title: str
    core_conflict: str
    character_growth: str
    foreshadowing_seeds: List[str] = Field(default_factory=list)
    climax_type: str
    chapter_range: Tuple[int, int] = (0, 0)
    # 新增：卷级统计
    total_words: int = 0
    status: str = "planned"    # planned/writing/completed


class NovelSettingModel(BaseModel):
    novel_title: str
    world_framework: str
    power_system: str
    major_factions: str
    main_character: CharacterModel
    supporting_characters: List[CharacterModel] = Field(default_factory=list)
    antagonists: List[CharacterModel] = Field(default_factory=list)
    righteous_characters: List[CharacterModel] = Field(default_factory=list)
    minor_characters: List[CharacterModel] = Field(default_factory=list)
    character_arcs: List[Dict[str, str]] = Field(default_factory=list)
    main_plot_thread: str
    volume_threads: List[VolumeModel] = Field(default_factory=list)
    core_conflicts: str
    style_type: str
    style_description: str


class NovelKnowledgeBase(BaseModel):
    """统一知识库 — 合并角色卡、世界观、情节记忆

    借鉴 NovelClaw 的 Memory-First 架构：
    - 所有创作知识集中管理
    - 支持动态权重
    - 支持状态回写
    """
    # 角色知识
    characters: Dict[str, CharacterModel] = Field(default_factory=dict)      # name → CharacterModel
    character_relationships: List[CharacterRelationship] = Field(default_factory=list)
    # 世界观知识
    world_facts: Dict[str, str] = Field(default_factory=dict)                # key → fact
    power_system_details: Dict[str, str] = Field(default_factory=dict)       # 境界 → 描述
    faction_details: Dict[str, str] = Field(default_factory=dict)            # 势力名 → 描述
    location_descriptions: Dict[str, str] = Field(default_factory=dict)      # 地点 → 描述
    # 情节知识
    plot_milestones: Dict[int, str] = Field(default_factory=dict)            # chapter → event summary
    foreshadowing_registry: List[ForeshadowingModel] = Field(default_factory=list)
    # 文风知识
    style_rules: List[str] = Field(default_factory=list)
    forbidden_words: List[str] = Field(default_factory=list)

    def get_character_context(self, name: str) -> str:
        char = self.characters.get(name)
        if not char:
            return ""
        parts = [f"【{char.name}】{char.role}"]
        if char.personality:
            parts.append(f"性格：{char.personality}")
        if char.dynamic_state.current_realm:
            parts.append(f"当前境界：{char.dynamic_state.current_realm}")
        if char.dynamic_state.current_location:
            parts.append(f"当前位置：{char.dynamic_state.current_location}")
        return " | ".join(parts)

    def update_character_state(self, name: str, **kwargs) -> Optional[StateChange]:
        char = self.characters.get(name)
        if not char:
            return None
        change = None
        for field, new_val in kwargs.items():
            if hasattr(char.dynamic_state, field):
                old_val = getattr(char.dynamic_state, field)
                if str(old_val) != str(new_val):
                    setattr(char.dynamic_state, field, new_val)
                    change = StateChange(
                        chapter_number=0,  # 调用方负责填充
                        character_name=name,
                        field_changed=field,
                        old_value=str(old_val),
                        new_value=str(new_val),
                    )
        return change

    def add_character_appearance(self, name: str, chapter_number: int):
        char = self.characters.get(name)
        if char:
            char.last_appearance_chapter = chapter_number
            char.total_appearances += 1
            if char.first_appearance_chapter == 0:
                char.first_appearance_chapter = chapter_number


class NovelState(BaseModel):
    novel_id: Optional[str] = None
    session_id: Optional[str] = None
    status: NovelStatus = NovelStatus.DRAFT
    setting: Optional[NovelSettingModel] = None
    world_view: Optional[Dict[str, Any]] = None
    chapters: List[ChapterModel] = Field(default_factory=list)
    foreshadowing_tracking: List[ForeshadowingModel] = Field(default_factory=list)
    total_words: int = 0
    current_chapter: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    # 新增：统一知识库
    knowledge_base: NovelKnowledgeBase = Field(default_factory=NovelKnowledgeBase)
    # 新增：状态变更日志
    state_changes: List[StateChange] = Field(default_factory=list)
    # 新增：卷级进度追踪
    current_volume: int = 1

    class Config:
        use_enum_values = True


class SessionModel(BaseModel):
    session_id: str
    session_name: str
    current_novel_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True


class SessionStore:
    def __init__(self):
        self._sessions: Dict[str, SessionModel] = {}
        self._novels: Dict[str, NovelState] = {}

    def create_session(self, session_name: str) -> SessionModel:
        import uuid
        session = SessionModel(
            session_id=str(uuid.uuid4()),
            session_name=session_name,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[SessionModel]:
        return self._sessions.get(session_id)

    def list_sessions(self) -> List[SessionModel]:
        return list(self._sessions.values())

    def update_session(self, session_id: str, **kwargs) -> Optional[SessionModel]:
        if session_id in self._sessions:
            session = self._sessions[session_id]
            for key, value in kwargs.items():
                if hasattr(session, key):
                    setattr(session, key, value)
            session.updated_at = datetime.now()
            return session
        return None

    def delete_session(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def create_novel(self, session_id: str, theme: str, style_type: str = "凡人流") -> Optional[NovelState]:
        import uuid
        if session_id not in self._sessions:
            return None

        novel = NovelState(
            novel_id=str(uuid.uuid4()),
            session_id=session_id,
            status=NovelStatus.DRAFT,
            setting=NovelSettingModel(
                novel_title="待定",
                world_framework="",
                power_system="",
                major_factions="",
                main_character=CharacterModel(
                    name="待定",
                    role="主角",
                    description="",
                    importance="main"
                ),
                main_plot_thread="",
                core_conflicts="",
                style_type=style_type,
                style_description=""
            ),
            chapters=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self._novels[novel.novel_id] = novel
        self.update_session(session_id, current_novel_id=novel.novel_id)
        return novel

    def get_novel(self, novel_id: str) -> Optional[NovelState]:
        return self._novels.get(novel_id)

    def update_novel(self, novel_id: str, **kwargs) -> Optional[NovelState]:
        if novel_id in self._novels:
            novel = self._novels[novel_id]
            for key, value in kwargs.items():
                if hasattr(novel, key):
                    setattr(novel, key, value)
            novel.updated_at = datetime.now()
            return novel
        return None

    def add_chapter(self, novel_id: str, chapter: ChapterModel) -> bool:
        if novel_id in self._novels:
            novel = self._novels[novel_id]
            if chapter.chapter_number > len(novel.chapters) + 1:
                return False
            if chapter.chapter_number <= len(novel.chapters):
                novel.chapters[chapter.chapter_number - 1] = chapter
            else:
                novel.chapters.append(chapter)
            novel.updated_at = datetime.now()
            return True
        return False

    def get_chapter(self, novel_id: str, chapter_number: int) -> Optional[ChapterModel]:
        novel = self._novels.get(novel_id)
        if novel and 0 < chapter_number <= len(novel.chapters):
            return novel.chapters[chapter_number - 1]
        return None

    def list_novels(self) -> List[NovelState]:
        return list(self._novels.values())

    def delete_novel(self, novel_id: str) -> bool:
        if novel_id in self._novels:
            del self._novels[novel_id]
            return True
        return False

    def add_foreshadowing(self, novel_id: str, foreshadowing: ForeshadowingModel) -> bool:
        if novel_id in self._novels:
            novel = self._novels[novel_id]
            novel.foreshadowing_tracking.append(foreshadowing)
            novel.updated_at = datetime.now()
            return True
        return False

    def list_session_novels(self, session_id: str):
        novels = [
            n for n in self._novels.values()
            if n.session_id == session_id or
            (n.session_id is None and session_id == "legacy")
        ]
        novels.sort(key=lambda n: n.created_at, reverse=True)
        return novels

    def resolve_foreshadowing(self, novel_id: str, seed: str) -> bool:
        if novel_id in self._novels:
            novel = self._novels[novel_id]
            for fs in novel.foreshadowing_tracking:
                if fs.seed == seed:
                    fs.status = "resolved"
                    novel.updated_at = datetime.now()
                    return True
        return False


_global_store = SessionStore()


def get_session_store() -> SessionStore:
    return _global_store
