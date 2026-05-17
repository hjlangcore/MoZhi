from typing import Dict, Any, List, Set, Optional
from collections import Counter
import re
from loguru import logger

from src.novel_agent.utils import calculate_text_similarity


class RepetitionGuard:
    def __init__(
        self,
        max_repetition_ratio: float = 0.15,
        min_unique_words_ratio: float = 0.3
    ):
        self.max_repetition_ratio = max_repetition_ratio
        self.min_unique_words_ratio = min_unique_words_ratio
        self.phrase_blacklist: Set[str] = set()
        self.character_dialogue_patterns: Dict[str, List[str]] = {}

    def check_repetition(
        self,
        new_content: str,
        existing_content: str = ""
    ) -> Dict[str, Any]:
        issues = []
        warnings = []

        if existing_content:
            similarity = calculate_text_similarity(new_content, existing_content)
            if similarity > 0.8:
                issues.append(f"新章节与前文高度相似 (相似度: {similarity:.2%})")
                return {
                    "passed": False,
                    "issues": issues,
                    "warnings": warnings,
                    "similarity": similarity
                }

        char_counter = Counter(new_content)
        total_chars = len(new_content)

        if total_chars > 0:
            char_repetition = sum(
                count for char, count in char_counter.items() if count > 1
            ) / total_chars

            if char_repetition > self.max_repetition_ratio * 2:
                issues.append("字符重复率过高，可能存在乱码或生成问题")

        words = self._extract_words(new_content)
        if words:
            word_counter = Counter(words)
            repeated_words = [
                (word, count) for word, count in word_counter.items()
                if count > 3 and len(word) > 2
            ]

            if len(repeated_words) > 10:
                warnings.append(f"发现{len(repeated_words)}个高频重复词汇")

        phrase_issues = self._check_phrase_repetition(new_content)
        if phrase_issues:
            warnings.extend(phrase_issues)

        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "warnings": warnings
        }

    def _extract_words(self, text: str) -> List[str]:
        chinese_words = re.findall(r'[\u4e00-\u9fff]{2,}', text)
        return chinese_words

    def _check_phrase_repetition(self, content: str) -> List[str]:
        warnings = []

        common_phrases = [
            "只见", "却是", "不过", "虽然", "但是", "于是", "因此",
            "随即", "忽然", "蓦然", "猛然", "陡然", "骤然",
            "缓缓", "慢慢", "渐渐", "徐徐"
        ]

        content_lower = content.lower()
        for phrase in common_phrases:
            count = content_lower.count(phrase)
            if count > 10:
                warnings.append(f"'{phrase}'出现次数过多 ({count}次)，建议减少使用")

        return warnings

    def check_dialogue_patterns(
        self,
        content: str,
        character_name: str,
        historical_dialogues: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        dialogue_pattern = re.compile(r'["""\'\'\']([^"""\']+)["""\']')
        dialogues = dialogue_pattern.findall(content)

        character_dialogues = [d for d in dialogues if character_name in d]

        if not historical_dialogues:
            historical_dialogues = []

        warnings = []
        issues = []

        if len(character_dialogues) > 0:
            unique_dialogues = set(character_dialogues)
            if len(unique_dialogues) < len(character_dialogues) * 0.5:
                issues.append(f"角色{character_name}对话重复率过高")
                warnings.append("建议为角色添加更多样化的对话")

        for hist_diag in historical_dialogues[-5:]:
            for curr_diag in character_dialogues:
                if len(hist_diag) > 20 and len(curr_diag) > 20:
                    similarity = calculate_text_similarity(hist_diag, curr_diag)
                    if similarity > 0.7:
                        warnings.append(
                            f"角色{character_name}的对话与历史对话高度相似"
                        )
                        break

        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "dialogue_count": len(character_dialogues),
            "unique_count": len(set(character_dialogues))
        }

    def add_to_blacklist(self, phrase: str):
        self.phrase_blacklist.add(phrase)

    def remove_from_blacklist(self, phrase: str):
        self.phrase_blacklist.discard(phrase)

    def check_blacklist_violations(self, content: str) -> Dict[str, Any]:
        violations = []

        for phrase in self.phrase_blacklist:
            if phrase in content:
                count = content.count(phrase)
                violations.append({
                    "phrase": phrase,
                    "count": count
                })

        return {
            "has_violations": len(violations) > 0,
            "violations": violations
        }

    def analyze_chapter_complexity(self, content: str) -> Dict[str, Any]:
        words = self._extract_words(content)
        unique_words = set(words)

        char_count = len(content)
        word_count = len(words)
        unique_word_count = len(unique_words)

        unique_ratio = unique_word_count / word_count if word_count > 0 else 0

        avg_word_freq = sum(
            Counter(words)[w] for w in unique_words
        ) / unique_word_count if unique_word_count > 0 else 0

        complexity_score = 100
        if unique_ratio < 0.2:
            complexity_score -= 30
        if avg_word_freq > 5:
            complexity_score -= 20

        return {
            "char_count": char_count,
            "word_count": word_count,
            "unique_word_count": unique_word_count,
            "unique_ratio": unique_ratio,
            "avg_word_frequency": avg_word_freq,
            "complexity_score": complexity_score,
            "complexity_level": self._get_complexity_level(complexity_score)
        }

    def _get_complexity_level(self, score: int) -> str:
        if score >= 80:
            return "excellent"
        elif score >= 60:
            return "good"
        elif score >= 40:
            return "fair"
        else:
            return "poor"

    def suggest_improvements(
        self,
        content: str,
        existing_content: str = ""
    ) -> List[str]:
        suggestions = []

        analysis = self.analyze_chapter_complexity(content)

        if analysis["unique_ratio"] < 0.3:
            suggestions.append("词汇多样性不足，建议使用更多同义词和表达方式")

        if analysis["avg_word_frequency"] > 4:
            suggestions.append("部分词汇使用过于频繁，建议减少重复")

        warnings = self._check_phrase_repetition(content)
        for warning in warnings:
            suggestions.append(warning.replace("建议", "应"))

        if existing_content:
            similarity = calculate_text_similarity(content, existing_content)
            if similarity > 0.5:
                suggestions.append("与前文相似度较高，建议增加新内容或改变叙述角度")

        return suggestions
