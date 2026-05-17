from typing import Dict, Any, List, Optional
from loguru import logger

from src.novel_agent.state import NovelState, ChapterModel
from src.novel_agent.utils import calculate_text_similarity


class ContinuityChecker:
    def __init__(self):
        self.issue_types = [
            "character_state_inconsistency",
            "timeline_error",
            "location_error",
            "plot_logic_error",
            "power_level_inconsistency",
            "relationship_inconsistency"
        ]

    def check_chapter_continuity(
        self,
        novel_state: NovelState,
        chapter_number: int
    ) -> Dict[str, Any]:
        if chapter_number <= 1 or len(novel_state.chapters) < 2:
            return {
                "passed": True,
                "score": 100,
                "issues": [],
                "suggestions": []
            }

        current_chapter = novel_state.chapters[chapter_number - 1]
        prev_chapter = novel_state.chapters[chapter_number - 2]

        issues = []
        suggestions = []
        score = 100

        character_issues = self._check_character_continuity(prev_chapter, current_chapter, novel_state)
        if character_issues:
            issues.extend(character_issues)
            score -= 20

        timeline_issues = self._check_timeline_continuity(prev_chapter, current_chapter)
        if timeline_issues:
            issues.extend(timeline_issues)
            score -= 15

        location_issues = self._check_location_continuity(prev_chapter, current_chapter)
        if location_issues:
            issues.extend(location_issues)
            score -= 10

        plot_issues = self._check_plot_continuity(novel_state, chapter_number)
        if plot_issues:
            issues.extend(plot_issues)
            score -= 25

        score = max(0, score)

        return {
            "passed": score >= 60,
            "score": score,
            "issues": issues,
            "suggestions": suggestions
        }

    def _check_character_continuity(
        self,
        prev_chapter: ChapterModel,
        current_chapter: ChapterModel,
        novel_state: NovelState
    ) -> List[str]:
        issues = []

        if not novel_state.setting:
            return issues

        protagonist = novel_state.setting.main_character
        if not protagonist:
            return issues

        protagonist_name = protagonist.name

        prev_lower = prev_chapter.content.lower()
        curr_lower = current_chapter.content.lower()

        if protagonist_name not in curr_lower and protagonist_name not in prev_lower:
            pass
        elif protagonist_name in prev_lower and protagonist_name not in curr_lower:
            if current_chapter.content[:100].lower() != prev_chapter.content[-100:].lower():
                issues.append(f"主角{protagonist_name}的状态可能不一致，需要确保角色状态连贯")

        return issues

    def _check_timeline_continuity(
        self,
        prev_chapter: ChapterModel,
        current_chapter: ChapterModel
    ) -> List[str]:
        issues = []

        time_markers = ["第二天", "三天后", "一年后", "数月后", "片刻之后", "转眼间"]
        prev_has_marker = any(marker in prev_chapter.content for marker in time_markers)
        curr_has_marker = any(marker in current_chapter.content for marker in time_markers)

        if prev_has_marker and not curr_has_marker:
            pass

        return issues

    def _check_location_continuity(
        self,
        prev_chapter: ChapterModel,
        current_chapter: ChapterModel
    ) -> List[str]:
        issues = []

        common_locations = ["宗门", "山谷", "城中", "洞府", "山巅"]
        prev_locations = [loc for loc in common_locations if loc in prev_chapter.content]
        curr_locations = [loc for loc in common_locations if loc in current_chapter.content]

        if prev_locations and curr_locations:
            if prev_locations[0] != curr_locations[0]:
                if len(prev_chapter.content) > 50 and len(current_chapter.content) > 50:
                    issues.append(f"场景可能跳跃：从{prev_locations[0]}直接转到{curr_locations[0]}，建议增加过渡")

        return issues

    def _check_plot_continuity(
        self,
        novel_state: NovelState,
        chapter_number: int
    ) -> List[str]:
        issues = []

        unresolved = [fs for fs in novel_state.foreshadowing_tracking if fs.status == "unresolved"]

        for fs in unresolved:
            if fs.chapter_introduced >= chapter_number - 3 and fs.chapter_introduced < chapter_number:
                if fs.planned_reveal_chapter and fs.planned_reveal_chapter < chapter_number:
                    issues.append(f"伏笔'{fs.seed}'应在本章或之前回收，但尚未处理")

        return issues

    def validate_character_consistency(
        self,
        novel_state: NovelState,
        chapter_number: int
    ) -> Dict[str, Any]:
        if not novel_state.setting:
            return {"consistent": True, "issues": []}

        current_content = novel_state.chapters[chapter_number - 1].content if chapter_number <= len(novel_state.chapters) else ""

        all_characters = [novel_state.setting.main_character]
        all_characters.extend(novel_state.setting.supporting_characters)
        all_characters.extend(novel_state.setting.antagonists)

        issues = []
        for char in all_characters:
            if not char or not char.name:
                continue

            appearances = current_content.count(char.name)
            if appearances == 0:
                if chapter_number == 1:
                    issues.append(f"主角{char.name}未在第一章出现")
                elif chapter_number > 1:
                    prev_content = novel_state.chapters[chapter_number - 2].content
                    prev_appearances = prev_content.count(char.name)
                    if prev_appearances > 0:
                        issues.append(f"角色{char.name}在前一章出现但本章消失，可能不一致")

        return {
            "consistent": len(issues) == 0,
            "issues": issues
        }


_continuity_checker: Optional[ContinuityChecker] = None


def get_continuity_checker() -> ContinuityChecker:
    global _continuity_checker
    if _continuity_checker is None:
        _continuity_checker = ContinuityChecker()
    return _continuity_checker
