from typing import List, Dict, Any, Set, Optional
from collections import Counter
from loguru import logger

from src.novel_agent.utils import calculate_text_similarity


class DuplicateDetector:
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
        self.min_duplicate_length = 50

    def check_chapter_duplicates(
        self,
        new_content: str,
        existing_content: str
    ) -> Dict[str, Any]:
        if not existing_content or not new_content:
            return {
                "has_duplicate": False,
                "similarity": 0.0,
                "duplicate_segments": []
            }

        similarity = calculate_text_similarity(new_content, existing_content)

        if similarity >= self.similarity_threshold:
            return {
                "has_duplicate": True,
                "similarity": similarity,
                "duplicate_segments": ["整体内容高度相似"]
            }

        duplicate_segments = self._find_duplicate_segments(new_content, existing_content)

        return {
            "has_duplicate": len(duplicate_segments) > 0,
            "similarity": similarity,
            "duplicate_segments": duplicate_segments
        }

    def _find_duplicate_segments(
        self,
        new_content: str,
        existing_content: str
    ) -> List[str]:
        duplicates = []

        sentences_new = self._split_sentences(new_content)
        sentences_existing = self._split_sentences(existing_content)

        existing_counter = Counter(sentences_existing)

        for sentence in sentences_new:
            if len(sentence) >= self.min_duplicate_length:
                normalized = self._normalize_text(sentence)
                if existing_counter.get(normalized, 0) > 0:
                    duplicates.append(sentence[:100] + "..." if len(sentence) > 100 else sentence)

        phrases = self._extract_key_phrases(new_content)
        for phrase in phrases:
            if phrase in existing_content:
                count = existing_content.count(phrase)
                if count >= 2:
                    duplicates.append(f"关键短语重复: {phrase} (出现{count + 1}次)")

        return duplicates[:10]

    def _split_sentences(self, text: str) -> List[str]:
        import re
        sentences = re.split(r'[。！？\n]', text)
        return [s.strip() for s in sentences if s.strip()]

    def _normalize_text(self, text: str) -> str:
        import re
        text = re.sub(r'\s+', '', text)
        text = text.lower()
        return text

    def _extract_key_phrases(self, text: str, min_length: int = 4) -> List[str]:
        import re
        chinese_chars = re.findall(r'[\u4e00-\u9fff]+', text)
        phrases = []

        for chars in chinese_chars:
            for i in range(len(chars) - min_length + 1):
                phrase = chars[i:i+min_length]
                if phrase not in phrases:
                    phrases.append(phrase)

        return phrases

    def check_within_chapter_duplicates(self, content: str) -> Dict[str, Any]:
        sentences = self._split_sentences(content)
        duplicate_sentences = []

        seen = {}
        for i, sentence in enumerate(sentences):
            if len(sentence) < self.min_duplicate_length:
                continue

            normalized = self._normalize_text(sentence)
            if normalized in seen:
                duplicate_sentences.append({
                    "sentence": sentence[:50] + "..." if len(sentence) > 50 else sentence,
                    "first_appearance": seen[normalized],
                    "current_position": i
                })
            else:
                seen[normalized] = i

        return {
            "has_duplicates": len(duplicate_sentences) > 0,
            "duplicate_count": len(duplicate_sentences),
            "duplicates": duplicate_sentences
        }

    def check_character_dialogue_patterns(
        self,
        content: str,
        character_names: List[str]
    ) -> Dict[str, Any]:
        import re

        dialogue_pattern = re.compile(r'["""\'\'\']([^"""\']+)["""\']')
        dialogues = dialogue_pattern.findall(content)

        pattern_issues = []
        for char in character_names:
            char_dialogues = [d for d in dialogues if char in d]
            if len(set(char_dialogues)) < len(char_dialogues) * 0.5:
                pattern_issues.append(f"角色{char}的对话可能存在重复模式")

        return {
            "has_pattern_issues": len(pattern_issues) > 0,
            "issues": pattern_issues
        }

    def batch_check_chapters(
        self,
        chapters: List[str]
    ) -> List[Dict[str, Any]]:
        results = []

        for i, chapter in enumerate(chapters):
            result = {
                "chapter_number": i + 1,
                "duplicates_with_previous": None,
                "within_chapter_duplicates": None
            }

            if i > 0:
                dup_result = self.check_chapter_duplicates(chapter, chapters[i-1])
                result["duplicates_with_previous"] = dup_result

            within_result = self.check_within_chapter_duplicates(chapter)
            result["within_chapter_duplicates"] = within_result

            results.append(result)

        return results


_duplicate_detector: Optional[DuplicateDetector] = None


def get_duplicate_detector() -> DuplicateDetector:
    global _duplicate_detector
    if _duplicate_detector is None:
        _duplicate_detector = DuplicateDetector()
    return _duplicate_detector
