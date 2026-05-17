from typing import Dict, Any, List, Set
from loguru import logger

from src.novel_agent.state import NovelState, NovelSettingModel


GENRE_KEYWORDS = {
    "凡人流": ["练气", "筑基", "金丹", "灵气", "功法", "修炼", "突破", "境界", "宗门", "法宝", "丹药"],
    "洪荒流": ["盘古", "鸿钧", "天道", "圣人", "功德", "气运", "因果", "量劫", "洪荒", "混沌"],
    "都市": ["总裁", "豪门", "都市", "职场", "创业", "投资", "商业", "都市生活"],
    "科幻": ["星际", "宇宙", "飞船", "科技", "基因", "人工智能", "赛博", "星际"],
    "悬疑": ["推理", "案件", "线索", "犯罪", "心理", "谜团", "破案"],
    "玄幻": ["斗气", "魔法", "异世", "大陆", "强者", "传承", "天赋"],
}


class GenreEnforcer:
    def __init__(self):
        self.genre_keywords = GENRE_KEYWORDS
        self.enforcement_rules = []

    def detect_genre(self, text: str) -> Dict[str, Any]:
        text_lower = text.lower()

        scores = {}
        for genre, keywords in self.genre_keywords.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[genre] = score

        if not scores:
            return {
                "detected_genre": "unknown",
                "confidence": 0.0,
                "scores": {}
            }

        top_genre = max(scores.items(), key=lambda x: x[1])
        max_score = top_genre[1]
        total_score = sum(scores.values())
        confidence = max_score / total_score if total_score > 0 else 0

        return {
            "detected_genre": top_genre[0],
            "confidence": confidence,
            "scores": scores
        }

    def enforce_genre(
        self,
        novel_state: NovelState,
        target_genre: str
    ) -> Dict[str, Any]:
        issues = []
        suggestions = []
        enforced = True

        if target_genre not in self.genre_keywords:
            return {
                "enforced": False,
                "issues": [f"未知题材: {target_genre}"],
                "suggestions": [],
                "missing_keywords": []
            }

        required_keywords = self.genre_keywords[target_genre]

        if not novel_state.setting:
            issues.append("缺少作品设定")
            suggestions.append("请先生成作品设定")
            return {
                "enforced": False,
                "issues": issues,
                "suggestions": suggestions,
                "missing_keywords": required_keywords
            }

        all_text = self._collect_novel_text(novel_state)
        all_text_lower = all_text.lower()

        missing_keywords = []
        for keyword in required_keywords:
            if keyword not in all_text_lower:
                missing_keywords.append(keyword)
                suggestions.append(f"建议添加'{keyword}'相关描写以符合{target_genre}题材")
                issues.append(f"缺少{target_genre}题材关键词: {keyword}")

        content_keywords = [kw for kw in required_keywords if kw in all_text_lower]
        coverage = len(content_keywords) / len(required_keywords) if required_keywords else 0

        return {
            "enforced": len(missing_keywords) < len(required_keywords) * 0.3,
            "issues": issues,
            "suggestions": suggestions,
            "missing_keywords": missing_keywords,
            "coverage": coverage
        }

    def _collect_novel_text(self, novel_state: NovelState) -> str:
        texts = []

        if novel_state.setting:
            if novel_state.setting.world_framework:
                texts.append(novel_state.setting.world_framework)
            if novel_state.setting.power_system:
                texts.append(novel_state.setting.power_system)
            if novel_state.setting.main_plot_thread:
                texts.append(novel_state.setting.main_plot_thread)

        for chapter in novel_state.chapters:
            if chapter.content:
                texts.append(chapter.content)

        return " ".join(texts)

    def validate_chapter_genre_consistency(
        self,
        chapter_content: str,
        setting: NovelSettingModel
    ) -> Dict[str, Any]:
        issues = []
        suggestions = []

        detected = self.detect_genre(chapter_content)
        target_genre = setting.style_type

        if target_genre not in self.genre_keywords:
            return {
                "consistent": True,
                "issues": [],
                "suggestions": []
            }

        required_keywords = self.genre_keywords[target_genre]
        content_lower = chapter_content.lower()

        missing_in_chapter = []
        for keyword in required_keywords[:5]:
            if keyword not in content_lower:
                missing_in_chapter.append(keyword)

        if len(missing_in_chapter) > 3:
            issues.append(f"本章可能偏离{target_genre}题材")
            suggestions.append(f"建议添加: {', '.join(missing_in_chapter[:3])}")

        return {
            "consistent": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions,
            "detected_genre": detected
        }

    def suggest_genre_adjustments(
        self,
        novel_state: NovelState
    ) -> Dict[str, Any]:
        all_text = self._collect_novel_text(novel_state)

        if len(all_text) < 100:
            return {
                "suggestions": [],
                "current_genre": "unknown"
            }

        detected = self.detect_genre(all_text)

        suggestions = []
        if detected["confidence"] < 0.5:
            suggestions.append("作品题材不够明确，建议明确主线类型")
            suggestions.append("可以加强某一题材的典型元素")

        if novel_state.setting:
            current = novel_state.setting.style_type
            if current != detected["detected_genre"]:
                suggestions.append(
                    f"检测到作品可能更适合'{detected['detected_genre']}'题材，"
                    f"而非当前设定的'{current}'"
                )

        return {
            "suggestions": suggestions,
            "current_genre": detected["detected_genre"],
            "confidence": detected["confidence"]
        }
