"""Truth Files 数据模型 — 参考 InkOS 的状态持久化架构

维护7个独立的状态文件，实时追踪：
1. characters.json - 角色状态矩阵
2. world.json - 世界观约束
3. plot.json - 剧情伏笔追踪
4. vocabulary.json - 词汇使用频率
5. pacing.json - 节奏控制
6. emotion.json - 情绪弧线
7. memory.json - 滚动记忆

核心目的：消除多章节长篇写作中的AI幻觉灾难
"""
import json
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from loguru import logger


@dataclass
class CharacterState:
    """角色状态"""
    name: str
    current_location: str = ""
    emotional_state: str = "平静"
    relationships: Dict[str, str] = field(default_factory=dict)
    knowledge: Set[str] = field(default_factory=set)
    inventory: List[str] = field(default_factory=list)
    last_appearance_chapter: int = 0
    total_appearances: int = 0
    character_arc_stage: str = "introduction"
    notes: str = ""


@dataclass
class WorldConstraint:
    """世界观约束"""
    key: str
    value: str
    constraint_type: str  # "hard" | "soft"
    source_chapter: int
    last_verified_chapter: int
    is_active: bool = True


@dataclass
class PlotThread:
    """剧情线"""
    thread_id: str
    name: str
    status: str  # "active" | "resolved" | "abandoned"
    introduced_chapter: int
    resolved_chapter: Optional[int] = None
    key_events: List[int] = field(default_factory=list)
    characters_involved: List[str] = field(default_factory=list)
    importance: int = 5  # 1-10
    description: str = ""


@dataclass
class Foreshadowing:
    """伏笔"""
    item_id: str
    description: str
    planted_chapter: int
    planted_context: str = ""
    resolved_chapter: Optional[int] = None
    resolution_context: str = ""
    is_resolved: bool = False
    importance: int = 5


@dataclass
class VocabularyEntry:
    """词汇条目"""
    word: str
    total_count: int
    chapters_used: List[int] = field(default_factory=list)
    last_used_chapter: int = 0
    is_fatigue: bool = False
    alternatives: List[str] = field(default_factory=list)


@dataclass
class PacingPoint:
    """节奏点"""
    chapter_number: int
    intensity: float  # 0-1
    event_type: str  # "action" | "dialogue" | "description" | "reflection"
    word_count: int = 0
    tension_level: float = 0.5


@dataclass
class EmotionArc:
    """情绪弧线"""
    chapter_number: int
    primary_emotion: str
    intensity: float  # 0-1
    secondary_emotions: List[str] = field(default_factory=list)
    trigger_event: str = ""


@dataclass
class MemoryEntry:
    """记忆条目"""
    content: str
    chapter_number: int
    importance: float  # 0-1
    entry_type: str  # "event" | "dialogue" | "description" | "character"
    timestamp: datetime = field(default_factory=datetime.now)
    decay_factor: float = 1.0


class TruthFiles:
    """Truth Files 管理器"""
    
    def __init__(self, novel_id: str, base_path: str = "data/truth_files"):
        self.novel_id = novel_id
        self.base_path = Path(base_path) / novel_id
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.characters: Dict[str, CharacterState] = {}
        self.world_constraints: Dict[str, WorldConstraint] = {}
        self.plot_threads: Dict[str, PlotThread] = {}
        self.foreshadowings: Dict[str, Foreshadowing] = {}
        self.vocabulary: Dict[str, VocabularyEntry] = {}
        self.pacing: List[PacingPoint] = []
        self.emotion_arcs: List[EmotionArc] = []
        self.memories: List[MemoryEntry] = []
        
        self._load_all()
    
    def _load_all(self) -> None:
        """加载所有 Truth Files"""
        self._load_characters()
        self._load_world()
        self._load_plot()
        self._load_vocabulary()
        self._load_pacing()
        self._load_emotion()
        self._load_memory()
    
    def _get_file_path(self, name: str) -> Path:
        return self.base_path / f"{name}.json"
    
    def _load_characters(self) -> None:
        path = self._get_file_path("characters")
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                for name, state in data.items():
                    state["knowledge"] = set(state.get("knowledge", []))
                    self.characters[name] = CharacterState(**state)
            except Exception as e:
                logger.error(f"Load characters failed: {e}")
    
    def _load_world(self) -> None:
        path = self._get_file_path("world")
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                for key, constraint in data.items():
                    self.world_constraints[key] = WorldConstraint(**constraint)
            except Exception as e:
                logger.error(f"Load world failed: {e}")
    
    def _load_plot(self) -> None:
        path = self._get_file_path("plot")
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                for tid, thread in data.get("threads", {}).items():
                    self.plot_threads[tid] = PlotThread(**thread)
                for fid, foreshadow in data.get("foreshadowings", {}).items():
                    self.foreshadowings[fid] = Foreshadowing(**foreshadow)
            except Exception as e:
                logger.error(f"Load plot failed: {e}")
    
    def _load_vocabulary(self) -> None:
        path = self._get_file_path("vocabulary")
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                for word, entry in data.items():
                    self.vocabulary[word] = VocabularyEntry(**entry)
            except Exception as e:
                logger.error(f"Load vocabulary failed: {e}")
    
    def _load_pacing(self) -> None:
        path = self._get_file_path("pacing")
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                self.pacing = [PacingPoint(**p) for p in data]
            except Exception as e:
                logger.error(f"Load pacing failed: {e}")
    
    def _load_emotion(self) -> None:
        path = self._get_file_path("emotion")
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                self.emotion_arcs = [EmotionArc(**e) for e in data]
            except Exception as e:
                logger.error(f"Load emotion failed: {e}")
    
    def _load_memory(self) -> None:
        path = self._get_file_path("memory")
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                for m in data:
                    if "timestamp" in m and isinstance(m["timestamp"], str):
                        m["timestamp"] = datetime.fromisoformat(m["timestamp"])
                    self.memories.append(MemoryEntry(**m))
            except Exception as e:
                logger.error(f"Load memory failed: {e}")
    
    def save_all(self) -> None:
        """保存所有 Truth Files"""
        self._save_characters()
        self._save_world()
        self._save_plot()
        self._save_vocabulary()
        self._save_pacing()
        self._save_emotion()
        self._save_memory()
        logger.info(f"TruthFiles: 已保存所有状态文件 - {self.novel_id}")
    
    def _save_characters(self) -> None:
        path = self._get_file_path("characters")
        data = {}
        for name, state in self.characters.items():
            d = asdict(state)
            d["knowledge"] = list(d["knowledge"])
            data[name] = d
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    
    def _save_world(self) -> None:
        path = self._get_file_path("world")
        data = {k: asdict(v) for k, v in self.world_constraints.items()}
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    
    def _save_plot(self) -> None:
        path = self._get_file_path("plot")
        data = {
            "threads": {k: asdict(v) for k, v in self.plot_threads.items()},
            "foreshadowings": {k: asdict(v) for k, v in self.foreshadowings.items()}
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    
    def _save_vocabulary(self) -> None:
        path = self._get_file_path("vocabulary")
        data = {k: asdict(v) for k, v in self.vocabulary.items()}
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    
    def _save_pacing(self) -> None:
        path = self._get_file_path("pacing")
        data = [asdict(p) for p in self.pacing]
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    
    def _save_emotion(self) -> None:
        path = self._get_file_path("emotion")
        data = [asdict(e) for e in self.emotion_arcs]
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    
    def _save_memory(self) -> None:
        path = self._get_file_path("memory")
        data = []
        for m in self.memories:
            d = asdict(m)
            d["timestamp"] = d["timestamp"].isoformat()
            data.append(d)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    
    def update_character(self, name: str, chapter: int, **kwargs) -> CharacterState:
        """更新角色状态"""
        if name not in self.characters:
            self.characters[name] = CharacterState(name=name)
        
        char = self.characters[name]
        for key, value in kwargs.items():
            if hasattr(char, key):
                setattr(char, key, value)
        
        char.last_appearance_chapter = chapter
        char.total_appearances += 1
        
        return char
    
    def add_world_constraint(self, key: str, value: str, chapter: int, 
                            constraint_type: str = "hard") -> WorldConstraint:
        """添加世界观约束"""
        constraint = WorldConstraint(
            key=key,
            value=value,
            constraint_type=constraint_type,
            source_chapter=chapter,
            last_verified_chapter=chapter
        )
        self.world_constraints[key] = constraint
        return constraint
    
    def add_plot_thread(self, thread_id: str, name: str, chapter: int,
                       characters: List[str] = None, importance: int = 5) -> PlotThread:
        """添加剧情线"""
        thread = PlotThread(
            thread_id=thread_id,
            name=name,
            status="active",
            introduced_chapter=chapter,
            characters_involved=characters or [],
            importance=importance
        )
        self.plot_threads[thread_id] = thread
        return thread
    
    def plant_foreshadowing(self, item_id: str, description: str, chapter: int,
                           importance: int = 5) -> Foreshadowing:
        """埋下伏笔"""
        foreshadow = Foreshadowing(
            item_id=item_id,
            description=description,
            planted_chapter=chapter,
            importance=importance
        )
        self.foreshadowings[item_id] = foreshadow
        return foreshadow
    
    def resolve_foreshadowing(self, item_id: str, chapter: int, context: str = "") -> bool:
        """回收伏笔"""
        if item_id in self.foreshadowings:
            f = self.foreshadowings[item_id]
            f.is_resolved = True
            f.resolved_chapter = chapter
            f.resolution_context = context
            return True
        return False
    
    def track_vocabulary(self, word: str, chapter: int) -> VocabularyEntry:
        """追踪词汇使用"""
        if word not in self.vocabulary:
            self.vocabulary[word] = VocabularyEntry(word=word, total_count=0)
        
        entry = self.vocabulary[word]
        entry.total_count += 1
        if chapter not in entry.chapters_used:
            entry.chapters_used.append(chapter)
        entry.last_used_chapter = chapter
        
        if entry.total_count > 5 and len(entry.chapters_used) > 3:
            entry.is_fatigue = True
        
        return entry
    
    def add_pacing_point(self, chapter: int, intensity: float, 
                        event_type: str, word_count: int = 0) -> PacingPoint:
        """添加节奏点"""
        point = PacingPoint(
            chapter_number=chapter,
            intensity=intensity,
            event_type=event_type,
            word_count=word_count
        )
        self.pacing.append(point)
        return point
    
    def add_emotion_arc(self, chapter: int, emotion: str, 
                       intensity: float, trigger: str = "") -> EmotionArc:
        """添加情绪弧线点"""
        arc = EmotionArc(
            chapter_number=chapter,
            primary_emotion=emotion,
            intensity=intensity,
            trigger_event=trigger
        )
        self.emotion_arcs.append(arc)
        return arc
    
    def add_memory(self, content: str, chapter: int, 
                  importance: float, entry_type: str) -> MemoryEntry:
        """添加记忆"""
        entry = MemoryEntry(
            content=content,
            chapter_number=chapter,
            importance=importance,
            entry_type=entry_type
        )
        self.memories.append(entry)
        
        if len(self.memories) > 100:
            self.memories.sort(key=lambda x: x.importance * x.decay_factor, reverse=True)
            self.memories = self.memories[:80]
        
        return entry
    
    def get_unresolved_foreshadowings(self) -> List[Foreshadowing]:
        """获取未回收的伏笔"""
        return [f for f in self.foreshadowings.values() if not f.is_resolved]
    
    def get_active_plot_threads(self) -> List[PlotThread]:
        """获取活跃的剧情线"""
        return [t for t in self.plot_threads.values() if t.status == "active"]
    
    def get_fatigue_vocabulary(self) -> List[VocabularyEntry]:
        """获取疲劳词汇"""
        return [v for v in self.vocabulary.values() if v.is_fatigue]
    
    def get_character_summary(self) -> Dict[str, Any]:
        """获取角色摘要"""
        return {
            name: {
                "appearances": char.total_appearances,
                "last_chapter": char.last_appearance_chapter,
                "state": char.emotional_state,
                "arc_stage": char.character_arc_stage
            }
            for name, char in self.characters.items()
        }
    
    def get_report(self) -> Dict[str, Any]:
        """获取 Truth Files 报告"""
        return {
            "novel_id": self.novel_id,
            "characters": len(self.characters),
            "world_constraints": len(self.world_constraints),
            "active_threads": len(self.get_active_plot_threads()),
            "unresolved_foreshadowings": len(self.get_unresolved_foreshadowings()),
            "vocabulary_tracked": len(self.vocabulary),
            "fatigue_words": len(self.get_fatigue_vocabulary()),
            "pacing_points": len(self.pacing),
            "emotion_arcs": len(self.emotion_arcs),
            "memories": len(self.memories)
        }


_truth_files_cache: Dict[str, TruthFiles] = {}


def get_truth_files(novel_id: str, base_path: str = "data/truth_files") -> TruthFiles:
    """获取 Truth Files 实例"""
    if novel_id not in _truth_files_cache:
        _truth_files_cache[novel_id] = TruthFiles(novel_id, base_path)
    return _truth_files_cache[novel_id]
