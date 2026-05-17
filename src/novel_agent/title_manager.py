import re
import json
from pathlib import Path
from difflib import SequenceMatcher
from typing import Optional
from loguru import logger


class TitleManager:

    _SYNONYM_MAP: dict[str, list[str]] = {
        "启动": ["发动", "开启", "运转", "激活"],
        "探秘": ["探索", "深入", "搜寻", "勘察"],
        "秘密": ["隐秘", "玄机", "奥秘", "谜团"],
        "战斗": ["激战", "厮杀", "对决", "交锋"],
        "突破": ["冲破", "闯过", "越狱", "脱困"],
        "发现": ["察觉", "窥见", "洞悉", "识破"],
        "危机": ["险境", "凶兆", "劫难", "难关"],
        "相遇": ["邂逅", "重逢", "碰面", "照面"],
    }

    _CHINESE_NUMERALS = [
        "", "一", "二", "三", "四", "五",
        "六", "七", "八", "九", "十",
    ]

class TitleManager:
    def __init__(self, storage_path: Optional[str] = None, similarity_threshold: float = 0.55):
        self.storage_path = storage_path
        self.similarity_threshold = similarity_threshold
        self._used_titles: set[str] = set()
        self._title_list: list[str] = []
        if storage_path and Path(storage_path).exists():
            self._load()

    def register_title(self, title: str) -> bool:
        normalized = self.normalize_title(title)
        if not normalized:
            return False
        if normalized in self._used_titles:
            logger.warning(f"标题已存在，跳过注册: {normalized}")
            return False
        self._used_titles.add(normalized)
        self._title_list.append(normalized)
        logger.debug(f"注册标题: {normalized}")
        return True

    def calculate_similarity(self, title_a: str, title_b: str) -> float:
        a = self.normalize_title(title_a)
        b = self.normalize_title(title_b)
        if not a or not b:
            return 0.0
        edit_sim = SequenceMatcher(None, a, b).ratio()
        chars_a = set(a)
        chars_b = set(b)
        if not chars_a or not chars_b:
            jaccard = 0.0
        else:
            jaccard = len(chars_a & chars_b) / len(chars_a | chars_b)
        return edit_sim * 0.5 + jaccard * 0.5

    def is_duplicate(self, title: str) -> tuple[bool, Optional[str]]:
        normalized = self.normalize_title(title)
        if normalized in self._used_titles:
            return True, normalized
        best_match: Optional[str] = None
        best_score = 0.0
        for existing in self._title_list:
            score = self.calculate_similarity(normalized, existing)
            if score > best_score:
                best_score = score
                best_match = existing
        if best_score >= self.similarity_threshold and best_match is not None:
            return True, best_match
        return False, None

    def normalize_title(self, title: str) -> str:
        title = title.strip()
        title = re.sub(r'[a-zA-Z]+', '', title)
        title = title.replace('（', '(').replace('）', ')')
        title = title.replace('【', '[').replace('】', ']')
        title = title.replace('《', '<').replace('》', '>')
        title = title.replace('"', '"').replace('"', '"')
        title = title.replace(''', "'").replace(''', "'")
        title = re.sub(r'\s+', '', title)
        while title.startswith(('(', '[', '<', '。', '，', '、', '！', '？', '~', '-')):
            title = title[1:]
        while title.endswith(('(', '[', '<', '。', '，', '、', '！', '？', '~', '-')):
            title = title[:-1]
        return title or "未命名章节"

    def generate_unique_title(
        self,
        base_title: str,
        context: dict | None = None,
        max_retries: int = 10,
    ) -> str:
        normalized = self.normalize_title(base_title)
        is_dup, _ = self.is_duplicate(normalized)
        if not is_dup:
            self.register_title(normalized)
            return normalized

        for attempt in range(1, max_retries + 1):
            candidate = self._apply_transform(normalized, attempt, context)
            candidate_normalized = self.normalize_title(candidate)
            still_dup, _ = self.is_duplicate(candidate_normalized)
            if not still_dup:
                self.register_title(candidate_normalized)
                logger.info(f"生成唯一标题(尝试{attempt}次): {candidate_normalized}")
                return candidate_normalized

        from datetime import datetime
        ts_suffix = datetime.now().strftime("%H%M%S")
        fallback = f"{normalized}_{ts_suffix}"
        fallback_normalized = self.normalize_title(fallback)
        self.register_title(fallback_normalized)
        logger.warning(f"标题生成已达最大重试次数，使用时间戳后缀: {fallback_normalized}")
        return fallback_normalized

    def suggest_alternatives(self, original: str, count: int = 5) -> list[str]:
        normalized = self.normalize_title(original)
        alternatives: list[str] = []
        seen: set[str] = {normalized}

        for i in range(1, count + 20):
            candidate = self._apply_transform(normalized, i, None)
            cand_norm = self.normalize_title(candidate)
            if cand_norm not in seen and cand_norm != normalized:
                seen.add(cand_norm)
                is_dup, _ = self.is_duplicate(cand_norm)
                if not is_dup:
                    alternatives.append(cand_norm)
                    if len(alternatives) >= count:
                        break

        while len(alternatives) < count:
            suffix = f"_alt_{len(alternatives) + 1}"
            alt = f"{normalized}{suffix}"
            if alt not in seen:
                seen.add(alt)
                alternatives.append(alt)

        return alternatives[:count]

    def batch_check_titles(self, titles: list[str]) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {}
        for title in titles:
            norm = self.normalize_title(title)
            if norm not in result:
                result[norm] = []
            result[norm].append(title)

        duplicates = {
            k: v for k, v in result.items() if len(v) > 1
        }
        similar_groups: dict[str, list[str]] = {}
        checked: set[str] = set()
        norm_list = list(result.keys())
        for i, a in enumerate(norm_list):
            if a in checked:
                continue
            group = [a]
            checked.add(a)
            for j in range(i + 1, len(norm_list)):
                b = norm_list[j]
                if b in checked:
                    continue
                sim = self.calculate_similarity(a, b)
                if sim >= self.similarity_threshold:
                    group.append(b)
                    checked.add(b)
            if len(group) > 1:
                key = min(group, key=len)
                chapters_for_group: list[str] = []
                for g in group:
                    chapters_for_group.extend(result.get(g, []))
                similar_groups[key] = chapters_for_group

        all_issues = {}
        all_issues.update(duplicates)
        all_issues.update(similar_groups)
        return all_issues

    def fix_duplicate_in_batch(
        self,
        titles_with_chapters: list[tuple[str, str]],
    ) -> list[tuple[str, str, str]]:
        mappings: list[tuple[str, str, str]] = []
        grouped: dict[str, list[tuple[int, str]]] = {}

        for idx, (title, chapter) in enumerate(titles_with_chapters):
            norm = self.normalize_title(title)
            if norm not in grouped:
                grouped[norm] = []
            grouped[norm].append((idx, chapter))

        processed_titles: set[str] = set()
        for _, entries in grouped.items():
            first_idx, first_chapter = entries[0]
            original_title = titles_with_chapters[first_idx][0]
            original_norm = self.normalize_title(original_title)

            if original_norm not in processed_titles:
                self.register_title(original_norm)
                processed_titles.add(original_norm)
                mappings.append((original_title, original_norm, first_chapter))
            else:
                new_title = self.generate_unique_title(original_title)
                mappings.append((original_title, new_title, first_chapter))

            for entry_idx, chapter in entries[1:]:
                entry_title = titles_with_chapters[entry_idx][0]
                new_title = self.generate_unique_title(entry_title)
                mappings.append((entry_title, new_title, chapter))

        return mappings

    def get_stats(self) -> dict:
        return {
            "total_registered": len(self._used_titles),
            "storage_path": self.storage_path,
            "similarity_threshold": self.similarity_threshold,
            "titles_sample": self._title_list[:20],
        }

    def save(self) -> None:
        if not self.storage_path:
            logger.warning("未设置存储路径，跳过保存")
            return
        path = Path(self.storage_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "titles": self._title_list,
            "similarity_threshold": self.similarity_threshold,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.debug(f"标题管理器已保存到: {path}")

    def _load(self) -> None:
        if not self.storage_path:
            return
        path = Path(self.storage_path)
        if not path.exists():
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            loaded_titles = data.get("titles", [])
            for t in loaded_titles:
                norm = self.normalize_title(t)
                if norm and norm not in self._used_titles:
                    self._used_titles.add(norm)
                    self._title_list.append(norm)
            threshold = data.get("similarity_threshold")
            if threshold is not None:
                self.similarity_threshold = float(threshold)
            logger.info(f"从文件加载了 {len(self._used_titles)} 个已用标题: {path}")
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error(f"加载标题文件失败: {e}")

    def _apply_transform(self, base: str, attempt: int, context: dict | None) -> str:
        strategy = (attempt - 1) % 4

        if strategy == 0:
            num_index = ((attempt - 1) // 4) % len(self._CHINESE_NUMERALS)
            num_index = max(2, num_index + 2)
            if num_index < len(self._CHINESE_NUMERALS):
                cn_num = self._CHINESE_NUMERALS[num_index]
                return f"{base}（{cn_num}）"
            return f"{base}（{attempt}）"

        elif strategy == 1:
            for word, synonyms in self._SYNONYM_MAP.items():
                if word in base:
                    syn_idx = (attempt // 4) % len(synonyms)
                    replacement = synonyms[syn_idx]
                    return base.replace(word, replacement, 1)
            return f"{base}（变体{attempt}）"

        elif strategy == 2:
            parts = base.split("的")
            if len(parts) == 2:
                return f"{parts[1]}中的{parts[0]}"
            parts = base.split("中")
            if len(parts) == 2:
                return f"{parts[1]}之{parts[0]}"
            return f"{base}篇"

        else:
            prefixes = ["古老", "神秘", "暗道", "深处", "绝境"]
            ctx_prefix = ""
            if context:
                location = context.get("location", "")
                character = context.get("character", "")
                emotion = context.get("emotion", "")
                if location:
                    ctx_prefix = location
                elif character:
                    ctx_prefix = character
                elif emotion:
                    ctx_prefix = emotion

            if ctx_prefix:
                return f"{ctx_prefix}{base}"

            prefix_idx = (attempt // 4) % len(prefixes)
            return f"{prefixes[prefix_idx]}{base}"
