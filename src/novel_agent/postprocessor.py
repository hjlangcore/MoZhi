import re
from typing import Optional, Dict, List, Tuple
from loguru import logger


AI_MARKERS: Dict[str, List[str]] = {
    "仿佛": ["宛如", "好似", "如同", "犹如"],
    "忽然": ["骤然", "蓦地", "倏忽", "猛然"],
    "突然": ["猝然", "陡然", "忽而", "顷刻间"],
    "缓缓": ["徐徐", "慢慢", "渐渐", "轻缓"],
    "眼中闪过一丝": ["目光微动", "神色微变", "眸光一凝"],
    "不由得": ["不禁", "情不自禁", "下意识"],
    "心中涌起": ["心头泛起", "内心升起", "胸中翻涌"],
    "深吸一口气": ["长舒一口气", "稳住心神", "平复气息"],
    "一股...力量": ["一道劲力", "一股气劲", "浑身之力"],
    "微微": ["略微", "稍许", "些许"],
    "不禁": ["不由", "难以自禁", "忍不住"],
    "显然": ["显而易见", "不言而喻", "毋庸置疑"],
}

META_PATTERNS = [
    r"通过这样的结构[内容安排]*",
    r"有效提升",
    r"这样结束故事如何",
    r"激发读者的好奇心",
    r"整体连贯性",
]

SKELETON_PATTERNS = [
    r"^###\s+(对决正式开始|钩子要求|场景总结与伏笔埋设|写作要点|情节推进|人物塑造|冲突升级|悬念设置|情感铺垫|节奏把控|结构设计|叙事技巧|章节小结|本章目标|核心事件|转折点|高潮设计|收尾策略|伏笔回收|角色弧光|世界观展示|力量体系|战斗描写|对话设计|心理描写|环境渲染|氛围营造|细节刻画|逻辑链条|因果关联|时间线|空间转换|视角切换|叙述者介入|元评论|创作意图|读者预期|阅读体验)",
    r"^####\s+(对决正式开始|钩子要求|场景总结与伏笔埋设|写作要点|情节推进|人物塑造|冲突升级|悬念设置|情感铺垫|节奏把控|结构设计|叙事技巧|章节小结|本章目标|核心事件|转折点|高潮设计|收尾策略|伏笔回收|角色弧光|世界观展示|力量体系|战斗描写|对话设计|心理描写|环境渲染|氛围营造|细节刻画|逻辑链条|因果关联|时间线|空间转换|视角切换|叙述者介入|元评论|创作意图|读者预期|阅读体验)",
]

CHAPTER_NUM_PATTERN = re.compile(r"(#{1,3})\s*第(\d+)章")


class PostProcessor:

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.min_words: int = self.config.get("min_words", 1500)
        self.max_words: int = self.config.get("max_words", 3000)
        self.marker_threshold: int = self.config.get("marker_threshold", 2)
        self.ai_markers: Dict[str, List[str]] = self.config.get(
            "ai_markers", AI_MARKERS
        )
        self.meta_patterns: List[str] = self.config.get(
            "meta_patterns", META_PATTERNS
        )
        self.skeleton_patterns: List[str] = self.config.get(
            "skeleton_patterns", SKELETON_PATTERNS
        )

    def process(self, text: str, chapter_num: int = None) -> Tuple[str, Dict]:
        report: Dict = {"steps": []}

        text = self._remove_meta_narrative(text)
        report["steps"].append("meta_narrative_removed")

        text = self._clean_markdown_skeleton(text)
        report["steps"].append("markdown_skeleton_cleaned")

        text = self._reduce_ai_markers(text)
        report["steps"].append("ai_markers_reduced")

        if chapter_num is not None:
            text = self._validate_chapter_number(text, chapter_num)
            report["steps"].append(f"chapter_number_validated_to_{chapter_num}")

        text, word_report = self._check_word_count(text)
        report.update(word_report)

        logger.info(
            f"PostProcessor pipeline complete: steps={report['steps']}, "
            f"word_count={report.get('word_count', 'N/A')}, "
            f"status={report.get('status', 'unknown')}"
        )

        return text, report

    def _remove_meta_narrative(self, text: str) -> str:
        removed_count = 0

        for pattern_str in self.meta_patterns:
            pattern = re.compile(pattern_str)
            matches = list(pattern.finditer(text))
            if not matches:
                continue

            for match in reversed(matches):
                start = match.start()
                line_start = text.rfind("\n", 0, start) + 1
                line_end = text.find("\n", start)
                if line_end == -1:
                    line_end = len(text)

                line_text = text[line_start:line_end]
                text = text[:line_start] + text[line_end:]
                removed_count += 1
                logger.debug(f"Removed meta-narrative line: {line_text.strip()[:80]}")

        if removed_count > 0:
            logger.info(f"Removed meta-narrative leakage ({removed_count} segments)")

        return text

    def _clean_markdown_skeleton(self, text: str) -> str:
        lines = text.split("\n")
        cleaned_lines: List[str] = []
        removed_count = 0

        for line in lines:
            stripped = line.strip()
            is_skeleton = False

            for pattern_str in self.skeleton_patterns:
                if re.match(pattern_str, stripped):
                    is_skeleton = True
                    break

            if is_skeleton:
                removed_count += 1
                logger.debug(f"Removed skeleton line: {stripped[:80]}")
            else:
                cleaned_lines.append(line)

        if removed_count > 0:
            logger.info(f"Cleaned Markdown skeleton残留 ({removed_count} lines)")

        return "\n".join(cleaned_lines)

    def _reduce_ai_markers(self, text: str) -> str:
        marker_counts: Dict[str, int] = {}
        replacements_made: Dict[str, int] = {}

        for marker, synonyms in self.ai_markers.items():
            count = 0
            syn_idx = 0

            def _replacer(match):
                nonlocal count, syn_idx
                count += 1
                if count > self.marker_threshold:
                    replacement = synonyms[syn_idx % len(synonyms)]
                    syn_idx += 1
                    return replacement
                return match.group(0)

            pattern = re.compile(re.escape(marker))
            new_text, n_replacements = pattern.subn(_replacer, text)
            text = new_text

            if n_replacements > self.marker_threshold:
                actual_replaced = n_replacements - self.marker_threshold
                replacements_made[marker] = actual_replaced

        if replacements_made:
            total = sum(replacements_made.values())
            logger.info(
                f"Reduced AI markers ({total} replacements): "
                f"{ {k: v for k, v in replacements_made.items() if v > 0} }"
            )

        return text

    def _validate_chapter_number(self, text: str, expected: int) -> str:
        match = CHAPTER_NUM_PATTERN.search(text)
        if not match:
            logger.debug("No chapter number heading found in text")
            return text

        prefix = match.group(1)
        current_num = int(match.group(2))

        if current_num != expected:
            old_heading = match.group(0)
            new_heading = f"{prefix} 第{expected}章"
            text = text[:match.start()] + new_heading + text[match.end():]
            logger.info(
                f"Chapter number corrected: {current_num} -> {expected} "
                f"(was: {old_heading})"
            )
        else:
            logger.debug(f"Chapter number verified correct: 第{expected}章")

        return text

    def _check_word_count(self, text: str) -> Tuple[str, Dict]:
        chinese_chars = [c for c in text if "\u4e00" <= c <= "\u9fff"]
        char_count = len(chinese_chars)

        if char_count < self.min_words:
            logger.warning(
                f"Word count insufficient: {char_count} (min={self.min_words})"
            )
            return text, {
                "word_count": char_count,
                "status": "warning",
                "warning": f"\u5b57\u6570\u4e0d\u8db3: {char_count}",
                "needs_supplement": True,
            }

        if char_count > self.max_words:
            truncated = self._truncate_to_word_limit(text, self.max_words)
            logger.warning(
                f"Word count exceeded: {char_count} (max={self.max_words}), truncated"
            )
            return truncated, {
                "word_count": self.max_words,
                "status": "truncated",
                "warning": (
                    f"\u5b57\u6570\u8d85\u6807: {char_count}, \u5df2\u88c1\u526a"
                ),
                "was_truncated": True,
            }

        return text, {
            "word_count": char_count,
            "status": "ok",
        }

    @staticmethod
    def _truncate_to_word_limit(text: str, limit: int) -> str:
        chinese_count = 0
        result_chars: List[str] = []

        for c in text:
            result_chars.append(c)
            if "\u4e00" <= c <= "\u9fff":
                chinese_count += 1
                if chinese_count >= limit:
                    break

        return "".join(result_chars)


def get_post_processor(config: Optional[dict] = None) -> PostProcessor:
    return PostProcessor(config=config)
