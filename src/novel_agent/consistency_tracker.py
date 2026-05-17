from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger


class MilestoneStatus(str, Enum):
    PENDING = "pending"
    ACHIEVED = "achieved"
    LOCKED = "locked"


class ForeshadowStatus(str, Enum):
    PLANTED = "planted"
    REMINDED = "reminded"
    RESOLVED = "resolved"
    OVERDUE = "overdue"


@dataclass(frozen=True)
class CharacterCard:
    name: str
    gender: str
    identity: str
    abilities: list[str] = field(default_factory=list)
    personality_traits: list[str] = field(default_factory=list)
    speech_style: str = ""
    first_appearance: int = 0
    relationships: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MilestoneRecord:
    name: str
    description: str
    achieved_at: Optional[int] = None
    status: MilestoneStatus = MilestoneStatus.PENDING


@dataclass
class ForeshadowRecord:
    id: str
    content: str
    planted_at: int
    planned_resolve_by: int
    resolved_at: Optional[int] = None
    status: ForeshadowStatus = ForeshadowStatus.PLANTED
    related_characters: list[str] = field(default_factory=list)


class ConsistencyState:
    VALID_ANTAGONIST_STATES = {"alive", "dead", "fled", "dormant"}

    def __init__(self, novel_id: str = "") -> None:
        self.novel_id: str = novel_id
        self.characters: Dict[str, CharacterCard] = {}
        self.milestones: List[MilestoneRecord] = []
        self.foreshadows: List[ForeshadowRecord] = []
        self.antagonists: Dict[str, dict] = {}

    # ── 角色卡管理 ──

    def add_character(self, card: CharacterCard) -> None:
        if card.name in self.characters:
            logger.debug(f"角色卡 '{card.name}' 已存在，忽略重复添加")
            return
        self.characters[card.name] = card
        logger.info(f"已注册角色卡: {card.name} ({card.identity})")

    def get_character(self, name: str) -> Optional[CharacterCard]:
        return self.characters.get(name)

    # ── 里程碑管理 ──

    def achieve_milestone(self, name: str, chapter: int) -> bool:
        for ms in self.milestones:
            if ms.name == name:
                if ms.status == MilestoneStatus.ACHIEVED or ms.status == MilestoneStatus.LOCKED:
                    logger.warning(f"里程碑 '{name}' 已锁定/达成，无法重复触发")
                    return False
                ms.status = MilestoneStatus.ACHIEVED
                ms.achieved_at = chapter
                logger.info(f"里程碑 '{name}' 在第 {chapter} 章达成")
                return True
        logger.warning(f"未找到里程碑: {name}")
        return False

    def is_milestone_achieved(self, name: str) -> bool:
        for ms in self.milestones:
            if ms.name == name:
                return ms.status == MilestoneStatus.ACHIEVED
        return False

    def register_milestone(self, record: MilestoneRecord) -> None:
        existing_names = {ms.name for ms in self.milestones}
        if record.name in existing_names:
            logger.warning(f"里程碑 '{record.name}' 已存在，跳过注册")
            return
        self.milestones.append(record)
        logger.info(f"已注册里程碑: {record.name}")

    # ── 伏笔追踪 ──

    def plant_foreshadow(self, record: ForeshadowRecord) -> None:
        existing_ids = {fs.id for fs in self.foreshadows}
        if record.id in existing_ids:
            logger.warning(f"伏笔 ID '{record.id}' 已存在，跳过注册")
            return
        self.foreshadows.append(record)
        logger.info(f"已埋设伏笔 [{record.id}]: {record.content[:40]}...")

    def get_pending_foreshadows(self, current_chapter: int) -> list[ForeshadowRecord]:
        pending: list[ForeshadowRecord] = []
        for fs in self.foreshadows:
            if fs.status not in (ForeshadowStatus.PLANTED, ForeshadowStatus.REMINDED):
                continue
            if current_chapter >= fs.planned_resolve_by - 1:
                pending.append(fs)
        return pending

    def resolve_foreshadow(self, foreshadow_id: str, chapter: int) -> bool:
        for fs in self.foreshadows:
            if fs.id == foreshadow_id:
                if fs.status == ForeshadowStatus.RESOLVED:
                    logger.warning(f"伏笔 '{foreshadow_id}' 已回收，无法重复操作")
                    return False
                fs.status = ForeshadowStatus.RESOLVED
                fs.resolved_at = chapter
                logger.info(f"伏笔 [{foreshadow_id}] 在第 {chapter} 章回收")
                return True
        logger.warning(f"未找到伏笔: {foreshadow_id}")
        return False

    def remind_foreshadow(self, foreshadow_id: str) -> bool:
        for fs in self.foreshadows:
            if fs.id == foreshadow_id:
                if fs.status == ForeshadowStatus.RESOLVED:
                    return False
                if fs.status != ForeshadowStatus.REMINDED:
                    fs.status = ForeshadowStatus.REMINDED
                    logger.info(f"伏笔 [{foreshadow_id}] 已标记为提醒状态")
                    return True
                return True
        return False

    def get_overdue_foreshadows(self, current_chapter: int) -> list[ForeshadowRecord]:
        overdue: list[ForeshadowRecord] = []
        for fs in self.foreshadows:
            if fs.status in (ForeshadowStatus.RESOLVED, ForeshadowStatus.OVERDUE):
                continue
            if current_chapter > fs.planned_resolve_by:
                fs.status = ForeshadowStatus.OVERDUE
                overdue.append(fs)
                logger.warning(f"伏笔 [{fs.id}] 超期未回收，计划章节 {fs.planned_resolve_by}")
        return overdue

    # ── 反派状态管理 ──

    def set_antagonist_status(self, name: str, status: str, chapter: int) -> None:
        if status not in self.VALID_ANTAGONIST_STATES:
            raise ValueError(
                f"无效的反派状态 '{status}'，可选值: {self.VALID_ANTAGONIST_STATES}"
            )
        old = self.antagonists.get(name, {}).get("status", "未知")
        self.antagonists[name] = {"status": status, "updated_at": chapter}
        logger.info(f"反派 '{name}' 状态变更: {old} -> {status} (第{chapter}章)")

    def get_antagonist_status(self, name: str) -> Optional[str]:
        entry = self.antagonists.get(name)
        return entry["status"] if entry else None

    # ── 核心约束输出 ──

    def get_constraints_for_chapter(self, chapter_num: int) -> Dict[str, Any]:
        achieved = [asdict(ms) for ms in self.milestones if ms.status == MilestoneStatus.ACHIEVED]
        forbidden = [ms.name for ms in self.milestones if ms.status == MilestoneStatus.ACHIEVED]

        active_to_remind = [
            asdict(fs) for fs in self.get_pending_foreshadows(chapter_num)
        ]
        overdue_list = [
            asdict(fs) for fs in self.get_overdue_foreshadows(chapter_num)
        ]
        dead_antagonists = [
            name for name, info in self.antagonists.items()
            if info.get("status") == "dead"
        ]

        max_chapter = max(
            (
                fs.planted_at
                for fs in self.foreshadows
                if fs.resolved_at is not None
            ),
            default=chapter_num,
        )
        max_chapter = max(max_chapter, *(ms.achieved_at or 0 for ms in self.milestones))
        if self.antagonists:
            max_chapter = max(max_chapter, *(info.get("updated_at", 0) for info in self.antagonists.values()))

        return {
            "characters": [card.to_dict() for card in self.characters.values()],
            "achieved_milestones": achieved,
            "forbidden_milestones": forbidden,
            "active_foreshadows_to_remind": active_to_remind,
            "overdue_foreshadows": overdue_list,
            "dead_antagonists": dead_antagonists,
            "chapter_context": {
                "current": chapter_num,
                "total_so_far": max(chapter_num, max_chapter),
            },
        }

    # ── 持久化 ──

    def save_to_file(self, path: str) -> None:
        data: Dict[str, Any] = {
            "novel_id": self.novel_id,
            "characters": [card.to_dict() for card in self.characters.values()],
            "milestones": [asdict(ms) for ms in self.milestones],
            "foreshadows": [asdict(fs) for fs in self.foreshadows],
            "antagonists": self.antagonists,
        }
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"一致性状态已保存至: {path}")

    @classmethod
    def load_from_file(cls, path: str) -> ConsistencyState:
        target = Path(path)
        if not target.exists():
            raise FileNotFoundError(f"一致性状态文件不存在: {path}")

        raw = json.loads(target.read_text(encoding="utf-8"))
        state = cls(novel_id=raw.get("novel_id", ""))

        for cd in raw.get("characters", []):
            card = CharacterCard(
                name=cd["name"],
                gender=cd["gender"],
                identity=cd["identity"],
                abilities=cd.get("abilities", []),
                personality_traits=cd.get("personality_traits", []),
                speech_style=cd.get("speech_style", ""),
                first_appearance=cd.get("first_appearance", 0),
                relationships=cd.get("relationships", []),
            )
            state.characters[card.name] = card

        for md in raw.get("milestones", []):
            achieved_at = md.get("achieved_at")
            state.milestones.append(MilestoneRecord(
                name=md["name"],
                description=md["description"],
                achieved_at=int(achieved_at) if achieved_at is not None else None,
                status=MilestoneStatus(md.get("status", "pending")),
            ))

        for fd in raw.get("foreshadows", []):
            resolved_at = fd.get("resolved_at")
            state.foreshadows.append(ForeshadowRecord(
                id=fd["id"],
                content=fd["content"],
                planted_at=int(fd["planted_at"]),
                planned_resolve_by=int(fd["planned_resolve_by"]),
                resolved_at=int(resolved_at) if resolved_at is not None else None,
                status=ForeshadowStatus(fd.get("status", "planted")),
                related_characters=fd.get("related_characters", []),
            ))

        state.antagonists = raw.get("antagonists", {})
        logger.info(f"一致性状态已从文件恢复: {path}")
        return state

    # ── 辅助方法 ──

    def get_all_characters(self) -> List[CharacterCard]:
        return list(self.characters.values())

    def get_milestone_summary(self) -> Dict[str, Any]:
        total = len(self.milestones)
        achieved = sum(1 for ms in self.milestones if ms.status == MilestoneStatus.ACHIEVED)
        return {
            "total": total,
            "achieved": achieved,
            "pending": total - achieved,
            "details": [{"name": ms.name, "status": ms.status.value} for ms in self.milestones],
        }

    def get_foreshadow_summary(self) -> Dict[str, Any]:
        from collections import Counter
        counter = Counter(fs.status.value for fs in self.foreshadows)
        return {
            "total": len(self.foreshadows),
            **dict(counter),
            "details": [
                {
                    "id": fs.id,
                    "content": fs.content[:60],
                    "status": fs.status.value,
                    "planted_at": fs.planted_at,
                    "planned_resolve_by": fs.planned_resolve_by,
                }
                for fs in self.foreshadows
            ],
        }

    def __repr__(self) -> str:
        return (
            f"ConsistencyState(novel_id={self.novel_id!r}, "
            f"characters={len(self.characters)}, "
            f"milestones={len(self.milestones)}, "
            f"foreshadows={len(self.foreshadows)}, "
            f"antagonists={len(self.antagonists)})"
        )
