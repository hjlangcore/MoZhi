from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

from src.novel_agent.state import NovelState, ForeshadowingModel


class ForeshadowingManager:
    def __init__(self):
        self.max_foreshadowing_per_novel = 50

    def create_foreshadowing(
        self,
        novel_state: NovelState,
        seed: str,
        chapter_introduced: int,
        planned_reveal_chapter: Optional[int] = None,
        description: Optional[str] = None
    ) -> ForeshadowingModel:
        if len(novel_state.foreshadowing_tracking) >= self.max_foreshadowing_per_novel:
            logger.warning(f"Novel {novel_state.novel_id} has reached max foreshadowing limit")
            raise ValueError(f"Maximum foreshadowing limit ({self.max_foreshadowing_per_novel}) reached")

        foreshadowing = ForeshadowingModel(
            seed=seed,
            chapter_introduced=chapter_introduced,
            planned_reveal_chapter=planned_reveal_chapter,
            status="unresolved",
            description=description
        )

        novel_state.foreshadowing_tracking.append(foreshadowing)
        logger.info(f"Created foreshadowing '{seed}' at chapter {chapter_introduced}")

        return foreshadowing

    def reveal_foreshadowing(
        self,
        novel_state: NovelState,
        seed: str,
        reveal_chapter: int,
        actual_content: str
    ) -> bool:
        for fs in novel_state.foreshadowing_tracking:
            if fs.seed == seed and fs.status == "unresolved":
                fs.status = "resolved"
                fs.actual_reveal_chapter = reveal_chapter
                fs.reveal_content = actual_content
                fs.resolved_at = datetime.now()
                logger.info(f"Foreshadowing '{seed}' revealed at chapter {reveal_chapter}")
                return True

        return False

    def check_foreshadowing_readiness(
        self,
        novel_state: NovelState,
        current_chapter: int
    ) -> Dict[str, Any]:
        unresolved = [fs for fs in novel_state.foreshadowing_tracking if fs.status == "unresolved"]
        overdue = []
        ready_to_reveal = []
        upcoming = []

        for fs in unresolved:
            if fs.planned_reveal_chapter:
                if current_chapter > fs.planned_reveal_chapter + 2:
                    overdue.append({
                        "seed": fs.seed,
                        "introduced_chapter": fs.chapter_introduced,
                        "planned_reveal": fs.planned_reveal_chapter,
                        "overdue_by": current_chapter - fs.planned_reveal_chapter
                    })
                elif current_chapter >= fs.planned_reveal_chapter - 1:
                    ready_to_reveal.append({
                        "seed": fs.seed,
                        "introduced_chapter": fs.chapter_introduced,
                        "planned_reveal": fs.planned_reveal_chapter
                    })
                else:
                    upcoming.append({
                        "seed": fs.seed,
                        "introduced_chapter": fs.chapter_introduced,
                        "planned_reveal": fs.planned_reveal_chapter,
                        "chapters_until_reveal": fs.planned_reveal_chapter - current_chapter
                    })
            else:
                chapters_since_intro = current_chapter - fs.chapter_introduced
                if chapters_since_intro > 10:
                    overdue.append({
                        "seed": fs.seed,
                        "introduced_chapter": fs.chapter_introduced,
                        "chapters_ago": chapters_since_intro
                    })

        return {
            "unresolved_count": len(unresolved),
            "overdue": overdue,
            "ready_to_reveal": ready_to_reveal,
            "upcoming": upcoming
        }

    def suggest_foreshadowing_placement(
        self,
        novel_state: NovelState,
        current_chapter: int
    ) -> List[Dict[str, Any]]:
        suggestions = []

        unresolved = [fs for fs in novel_state.foreshadowing_tracking if fs.status == "unresolved"]
        if len(unresolved) < 3:
            suggestions.append({
                "type": "add_foreshadowing",
                "suggestion": "建议添加更多伏笔以增加故事深度",
                "priority": "medium"
            })

        if len(unresolved) > 30:
            suggestions.append({
                "type": "reduce_foreshadowing",
                "suggestion": "伏笔过多，建议回收部分旧伏笔或减少新伏笔添加",
                "priority": "high"
            })

        old_unresolved = [fs for fs in unresolved if current_chapter - fs.chapter_introduced > 15]
        if old_unresolved:
            suggestions.append({
                "type": "reveal_old_foreshadowing",
                "suggestion": f"有{len(old_unresolved)}个伏笔已超过15章未回收，建议尽快处理",
                "priority": "high",
                "foreshadowing": [fs.seed for fs in old_unresolved]
            })

        return suggestions

    def get_foreshadowing_summary(self, novel_state: NovelState) -> Dict[str, Any]:
        tracking = novel_state.foreshadowing_tracking

        total = len(tracking)
        resolved = len([fs for fs in tracking if fs.status == "resolved"])
        unresolved = total - resolved

        return {
            "total_foreshadowing": total,
            "resolved": resolved,
            "unresolved": unresolved,
            "resolution_rate": resolved / total if total > 0 else 0,
            "foreshadowing_list": [
                {
                    "seed": fs.seed,
                    "status": fs.status,
                    "introduced_chapter": fs.chapter_introduced,
                    "planned_reveal": fs.planned_reveal_chapter
                }
                for fs in tracking
            ]
        }

    def validate_foreshadowing_coherence(
        self,
        foreshadowing: ForeshadowingModel,
        reveal_content: str
    ) -> Dict[str, Any]:
        issues = []

        seed_words = foreshadowing.seed.split()
        matching_count = sum(1 for word in seed_words if word in reveal_content)

        if matching_count < len(seed_words) * 0.3:
            issues.append("伏笔回收内容与伏笔种子关联度不高")

        if len(reveal_content) < 50:
            issues.append("伏笔回收内容过短，可能过于突兀")

        if foreshadowing.planned_reveal_chapter:
            if foreshadowing.actual_reveal_chapter:
                chapters_diff = abs(
                    foreshadowing.actual_reveal_chapter - foreshadowing.planned_reveal_chapter
                )
                if chapters_diff > 3:
                    issues.append(f"伏笔回收时机偏离计划{chapters_diff}章")

        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
