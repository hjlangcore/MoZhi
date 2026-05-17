from typing import Dict, Any, List, Optional
from loguru import logger

from src.novel_agent.state import NovelState, NovelSettingModel


STYLE_ANCHORS = {
    "凡人流": {
        "tone": "沉稳内敛，富有哲理",
        "narrative": "以主角成长为中心，注重修炼过程的描写",
        "dialogue": "简洁有力，富有深意",
        "keywords": ["修炼", "顿悟", "机缘", "磨砺", "心境"]
    },
    "洪荒流": {
        "tone": "大气磅礴，史诗感强",
        "narrative": "注重天道运转，因果轮回",
        "dialogue": "古朴典雅，富有天道至理",
        "keywords": ["天道", "因果", "气运", "功德", "圣人"]
    },
    "都市": {
        "tone": "贴近生活，代入感强",
        "narrative": "以现实都市为背景，强调人情世故",
        "dialogue": "生动自然，富有生活气息",
        "keywords": ["职场", "商战", "情感", "都市生活"]
    },
    "科幻": {
        "tone": "理性冷静，逻辑性强",
        "narrative": "注重科技细节，想象力丰富",
        "dialogue": "简洁专业，富有科技感",
        "keywords": ["科技", "探索", "星际", "未来"]
    },
    "番茄模式": {
        "tone": "快节奏强爽感，通俗直白不矫情，下沉市场接地气",
        "narrative": "每章一个小爽点，3章一次打脸，10章一次大高潮，节奏要快要炸",
        "dialogue": "对话简短有力，拒绝长篇大论，人物说话带情绪和态度",
        "keywords": ["系统", "金手指", "碾压", "打脸", "震惊", "逆袭", "满级", "神级", "秒杀", "横扫"]
    },
}


class StyleAnchor:
    def __init__(self, style_type: str):
        self.style_type = style_type
        self.anchors = STYLE_ANCHORS.get(style_type, STYLE_ANCHORS["凡人流"])

    def get_style_prompt(self) -> str:
        prompt_parts = [
            f"文风类型: {self.style_type}",
            f"整体基调: {self.anchors['tone']}",
            f"叙事风格: {self.anchors['narrative']}",
            f"对话风格: {self.anchors['dialogue']}",
            "关键词指引: " + "、".join(self.anchors["keywords"])
        ]
        return "\n".join(prompt_parts)

    def validate_content(self, content: str) -> Dict[str, Any]:
        issues = []
        warnings = []

        content_lower = content.lower()

        keyword_matches = sum(
            1 for kw in self.anchors["keywords"]
            if kw in content_lower
        )

        if keyword_matches < 2:
            warnings.append(
                f"内容可能偏离{self.style_type}风格，"
                f"建议增加相关关键词: {', '.join(self.anchors['keywords'][:3])}"
            )

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "keyword_coverage": keyword_matches / len(self.anchors["keywords"])
        }


class StyleAnchorManager:
    def __init__(self):
        self.style_anchors: Dict[str, StyleAnchor] = {}
        for style_type in STYLE_ANCHORS.keys():
            self.style_anchors[style_type] = StyleAnchor(style_type)

    def get_anchor(self, style_type: str) -> StyleAnchor:
        if style_type not in self.style_anchors:
            self.style_anchors[style_type] = StyleAnchor(style_type)
        return self.style_anchors[style_type]

    def get_style_guidance(self, style_type: str) -> str:
        anchor = self.get_anchor(style_type)
        return anchor.get_style_prompt()

    def validate_novel_style(
        self,
        novel_state: NovelState,
        target_style: Optional[str] = None
    ) -> Dict[str, Any]:
        style_type = target_style or (novel_state.setting.style_type if novel_state.setting else None)

        if not style_type:
            return {
                "validated": False,
                "issues": ["未指定文风类型"]
            }

        anchor = self.get_anchor(style_type)

        all_content = self._collect_all_content(novel_state)

        validation_result = anchor.validate_content(all_content)

        return {
            "validated": validation_result["valid"],
            "style_type": style_type,
            "validation_result": validation_result
        }

    def _collect_all_content(self, novel_state: NovelState) -> str:
        parts = []

        if novel_state.setting:
            if novel_state.setting.world_framework:
                parts.append(novel_state.setting.world_framework)
            if novel_state.setting.power_system:
                parts.append(novel_state.setting.power_system)
            if novel_state.setting.style_description:
                parts.append(novel_state.setting.style_description)

        for chapter in novel_state.chapters:
            if chapter.content:
                parts.append(chapter.content)

        return " ".join(parts)

    def suggest_style_adjustments(
        self,
        novel_state: NovelState
    ) -> List[str]:
        suggestions = []

        if not novel_state.setting or not novel_state.setting.style_type:
            suggestions.append("建议为作品指定明确的文风类型")
            return suggestions

        style_type = novel_state.setting.style_type
        anchor = self.get_anchor(style_type)

        all_content = self._collect_all_content(novel_state)

        if len(all_content) < 500:
            return suggestions

        validation = anchor.validate_content(all_content)

        if validation["keyword_coverage"] < 0.3:
            suggestions.append(
                f"建议在内容中增加更多{style_type}类型的典型元素，"
                f"如: {', '.join(anchor.anchors['keywords'][:3])}"
            )

        return suggestions

    def create_style_guide(self, style_type: str) -> Dict[str, Any]:
        if style_type not in STYLE_ANCHORS:
            available_styles = list(STYLE_ANCHORS.keys())
            return {
                "error": f"未知文风类型，可选: {', '.join(available_styles)}"
            }

        anchor = self.style_anchors[style_type]

        return {
            "style_type": style_type,
            "tone": anchor.anchors["tone"],
            "narrative_style": anchor.anchors["narrative"],
            "dialogue_style": anchor.anchors["dialogue"],
            "keywords": anchor.anchors["keywords"],
            "example_prompt": anchor.get_style_prompt()
        }


_global_style_manager = None


def get_style_anchor_manager() -> StyleAnchorManager:
    global _global_style_manager
    if _global_style_manager is None:
        _global_style_manager = StyleAnchorManager()
    return _global_style_manager
