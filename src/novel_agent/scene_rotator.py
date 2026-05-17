from collections import deque
import random
import re
import json
from pathlib import Path
from typing import Optional
from loguru import logger


SCENE_POOL = [
    {"id": "cave", "name": "山洞/洞穴", "aliases": ["山洞", "洞穴", "密室", "石室", "地下空间"]},
    {"id": "city", "name": "城市/城镇", "aliases": ["城市", "城镇", "街道", "集市", "坊市"]},
    {"id": "sect", "name": "宗门/门派", "aliases": ["宗门", "门派", "宗派", "山门", "殿宇"]},
    {"id": "wilderness", "name": "野外/森林", "aliases": ["野外", "森林", "密林", "荒野", "丛林"]},
    {"id": "battlefield", "name": "战场/遗迹", "aliases": ["战场", "遗迹", "废墟", "古战场"]},
    {"id": "palace", "name": "宫殿/府邸", "aliases": ["宫殿", "府邸", "豪宅", "官府", "王府"]},
    {"id": "secret_realm", "name": "秘境/异空间", "aliases": ["秘境", "异空间", "结界", "阵法空间"]},
    {"id": "water", "name": "水下/湖海", "aliases": ["水下", "湖泊", "海边", "江河", "深渊"]},
]


class SceneRotator:
    def __init__(
        self,
        history_size: int = 10,
        ban_recent: int = 3,
        warning_threshold: int = 5,
        scene_pool: list[dict] | None = None,
    ):
        self.history_size = history_size
        self.ban_recent = ban_recent
        self.warning_threshold = warning_threshold
        self.scene_pool = scene_pool or SCENE_POOL
        self.history: deque[dict] = deque(maxlen=history_size)
        self._consecutive_count: dict[str, int] = {}
        self._last_scene_id: Optional[str] = None

    def record_scene(self, chapter_num: int, scene_id: str, scene_name: str, context: str = "") -> None:
        entry = {
            "chapter": chapter_num,
            "scene_id": scene_id,
            "scene_name": scene_name,
            "context": context[:200] if context else "",
        }
        self.history.append(entry)

        if self._last_scene_id == scene_id:
            self._consecutive_count[scene_id] = self._consecutive_count.get(scene_id, 0) + 1
        else:
            if self._last_scene_id is not None:
                self._consecutive_count[self._last_scene_id] = 0
            self._consecutive_count[scene_id] = 1
            self._last_scene_id = scene_id

        logger.debug(
            f"[SceneRotator] Chapter {chapter_num} recorded scene: {scene_name} ({scene_id}), "
            f"consecutive={self._consecutive_count.get(scene_id, 0)}"
        )

    def detect_scene_from_text(self, text: str) -> Optional[dict]:
        if not text or not text.strip():
            return None

        scores: dict[str, int] = {}
        for scene in self.scene_pool:
            total = 0
            for alias in scene.get("aliases", []):
                matches = re.findall(re.escape(alias), text)
                total += len(matches)
            if total > 0:
                scores[scene["id"]] = total

        if not scores:
            return None

        best_id = max(scores, key=scores.get)
        best_scene = next((s for s in self.scene_pool if s["id"] == best_id), None)

        logger.debug(
            f"[SceneRotator] Detected scene from text: {best_scene['name'] if best_scene else 'unknown'} "
            f"(score={scores[best_id]}, all_scores={scores})"
        )
        return best_scene

    def get_allowed_scenes(self) -> list[dict]:
        recent_ids: set[str] = set()
        for entry in list(self.history)[-self.ban_recent:]:
            recent_ids.add(entry["scene_id"])

        allowed = [s for s in self.scene_pool if s["id"] not in recent_ids]
        logger.debug(f"[SceneRotator] Allowed scenes (banned={recent_ids}): {[s['id'] for s in allowed]}")
        return allowed

    def pick_scene_for_next_chapter(
        self,
        preferred: Optional[str] = None,
        forbidden: Optional[list[str]] = None,
    ) -> dict:
        forbidden_set = set(forbidden or [])
        warning = self.check_consecutive_warning()

        if warning and warning["scene_id"]:
            forbidden_set.add(warning["scene_id"])
            logger.warning(
                f"[SceneRotator] Consecutive warning triggered: "
                f"{warning['scene_id']} x{warning['count']}, forcing switch"
            )

        allowed = self.get_allowed_scenes()
        candidates = [s for s in allowed if s["id"] not in forbidden_set]

        if not candidates:
            candidates = [s for s in self.scene_pool if s["id"] not in forbidden_set]
        if not candidates:
            candidates = list(self.scene_pool)

        if preferred:
            pref_match = next((s for s in candidates if s["id"] == preferred), None)
            if pref_match:
                logger.info(f"[SceneRotator] Picked preferred scene: {pref_match['name']}")
                return pref_match

        picked = random.choice(candidates)
        logger.info(f"[SceneRotator] Picked random scene: {picked['name']}")
        return picked

    def check_consecutive_warning(self) -> Optional[dict]:
        if not self._last_scene_id:
            return None

        count = self._consecutive_count.get(self._last_scene_id, 0)
        if count >= self.warning_threshold:
            scene_name = next(
                (s["name"] for s in self.scene_pool if s["id"] == self._last_scene_id),
                self._last_scene_id,
            )
            result = {
                "scene_id": self._last_scene_id,
                "scene_name": scene_name,
                "count": count,
                "warning": (
                    f"场景 '{scene_name}' 已连续使用 {count} 章，"
                    f"超过阈值 {self.warning_threshold}，建议切换场景类型"
                ),
            }
            logger.warning(f"[SceneRotator] {result['warning']}")
            return result
        return None

    def force_switch_scene(self) -> dict:
        all_used_ids: set[str] = {entry["scene_id"] for entry in self.history}
        fresh = [s for s in self.scene_pool if s["id"] not in all_used_ids]

        if fresh:
            picked = random.choice(fresh)
            logger.info(f"[SceneRotator] Force-switched to fresh scene: {picked['name']}")
            return picked

        usage_count: dict[str, int] = {}
        for entry in self.history:
            sid = entry["scene_id"]
            usage_count[sid] = usage_count.get(sid, 0) + 1

        sorted_by_usage = sorted(usage_count.items(), key=lambda x: x[1])
        least_used_id = sorted_by_usage[0][0]
        picked = next((s for s in self.scene_pool if s["id"] == least_used_id), self.scene_pool[0])

        logger.info(
            f"[SceneRotator] Force-switched to least-used scene: {picked['name']} "
            f"(used {usage_count.get(least_used_id, 0)} times)"
        )
        return picked

    def get_scene_constraint_prompt(self, current_chapter: int) -> str:
        picked = self.pick_scene_for_next_chapter()
        banned = list({entry["scene_id"] for entry in list(self.history)[-self.ban_recent:]})
        banned_names = [
            next((s["name"] for s in self.scene_pool if s["id"] == bid), bid)
            for bid in banned
        ]

        history_lines = []
        for entry in list(self.history)[-5:]:
            history_lines.append(f"  第{entry['chapter']}章: {entry['scene_name']}")

        warning_info = ""
        warning = self.check_consecutive_warning()
        if warning:
            warning_info = f"\n- ⚠️ 警告：{warning['warning']}"

        prompt = (
            f"【场景约束】\n"
            f"- 本章推荐场景：{picked['name']}\n"
            f"- 禁止使用场景：{'、'.join(banned_names) if banned_names else '无'}\n"
            f"- 最近{min(5, len(self.history))}章场景历史：\n"
            f"{chr(10).join(history_lines) if history_lines else '  （暂无历史）'}"
            f"{warning_info}\n"
            f"- 注意：请确保本章场景与最近章节有明显区别"
        )

        logger.debug(f"[SceneRotator] Generated constraint prompt for chapter {current_chapter}")
        return prompt

    def save_state(self, path: str) -> None:
        state = {
            "history_size": self.history_size,
            "ban_recent": self.ban_recent,
            "warning_threshold": self.warning_threshold,
            "history": list(self.history),
            "consecutive_count": self._consecutive_count,
            "last_scene_id": self._last_scene_id,
        }
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"[SceneRotator] State saved to {path}")

    @classmethod
    def load_state(cls, path: str) -> "SceneRotator":
        p = Path(path)
        raw = json.loads(p.read_text(encoding="utf-8"))

        instance = cls(
            history_size=raw.get("history_size", 10),
            ban_recent=raw.get("ban_recent", 3),
            warning_threshold=raw.get("warning_threshold", 5),
        )
        instance.history = deque(raw.get("history", []), maxlen=instance.history_size)
        instance._consecutive_count = raw.get("consecutive_count", {})
        instance._last_scene_id = raw.get("last_scene_id")

        logger.info(f"[SceneRotator] State loaded from {path}, history entries={len(instance.history)}")
        return instance
