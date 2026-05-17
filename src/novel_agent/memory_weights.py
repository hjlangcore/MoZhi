"""动态记忆权重系统 — 借鉴 NovelClaw Memory-First 架构

核心理念：不是所有记忆等权重注入 Prompt，而是根据当前章节上下文动态调整。
权重高的记忆优先注入有限的 token 预算中。

权重维度：
  - 章节相关性：角色/情节在当前章是否出现
  - 时间衰减：越久未提及的记忆权重越低
  - 卷目标对齐：与当前卷目标相关的记忆被提升
  - 伏笔紧迫度：即将到期的伏笔权重提高
"""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger


class WeightTier(str, Enum):
    CRITICAL = "critical"    # 始终注入（总大纲、主角状态）
    HIGH = "high"            # 高优先级（当前卷目标、活跃反派）
    MEDIUM = "medium"        # 中等（本章出场配角、近期事件）
    LOW = "low"              # 低优先级（休眠角色、远久历史）


@dataclass
class WeightedMemory:
    """带权重的记忆条目"""
    key: str
    content: str
    category: str           # character / plot / world / foreshadowing / outline
    base_weight: float      # 基础权重 0-1
    dynamic_weight: float = 0.0  # 动态调整后的权重
    tier: WeightTier = WeightTier.MEDIUM
    last_referenced_chapter: int = 0
    is_active: bool = True

    @property
    def effective_weight(self) -> float:
        return self.dynamic_weight


class DynamicMemoryWeighter:
    """动态记忆权重计算器

    根据当前章节上下文，重新计算所有记忆的权重，
    确保有限的 token 预算分配给最重要的记忆。
    """

    def __init__(self, max_memory_tokens: int = 3000):
        self.max_memory_tokens = max_memory_tokens
        self.memories: Dict[str, WeightedMemory] = {}
        self._decay_rate = 0.05       # 每章衰减率
        self._relevance_boost = 0.3   # 章节相关提升
        self._urgency_boost = 0.2     # 伏笔到期提升

    def add_memory(self, key: str, content: str, category: str,
                   base_weight: float = 0.5, tier: WeightTier = WeightTier.MEDIUM):
        self.memories[key] = WeightedMemory(
            key=key,
            content=content,
            category=category,
            base_weight=base_weight,
            dynamic_weight=base_weight,
            tier=tier,
        )

    def update_memory(self, key: str, **kwargs):
        if key in self.memories:
            m = self.memories[key]
            for k, v in kwargs.items():
                if hasattr(m, k):
                    setattr(m, k, v)

    def mark_referenced(self, key: str, chapter_number: int):
        """标记记忆在指定章节被引用"""
        if key in self.memories:
            self.memories[key].last_referenced_chapter = chapter_number

    def compute_weights(self, current_chapter: int,
                        active_characters: List[str] = None,
                        active_plot_keywords: List[str] = None,
                        volume_goal: str = "",
                        urgent_foreshadowing: List[str] = None) -> List[WeightedMemory]:
        """根据当前章节上下文重新计算所有权重

        Args:
            current_chapter: 当前章节号
            active_characters: 本章出场的角色名列表
            active_plot_keywords: 本章涉及的关键词
            volume_goal: 当前卷目标描述
            urgent_foreshadowing: 急需回收的伏笔列表
        """
        active_characters = active_characters or []
        active_plot_keywords = active_plot_keywords or []
        urgent_foreshadowing = urgent_foreshadowing or []

        for key, mem in self.memories.items():
            weight = mem.base_weight

            # 1. 章节相关性提升
            relevance = self._calc_relevance(mem, active_characters, active_plot_keywords, volume_goal)
            weight += relevance * self._relevance_boost

            # 2. 时间衰减
            chapters_since = current_chapter - mem.last_referenced_chapter
            if chapters_since > 0 and mem.category not in ("outline", "world"):
                decay = min(0.5, chapters_since * self._decay_rate)
                weight -= decay

            # 3. 伏笔紧迫度提升
            if mem.category == "foreshadowing" and mem.key in urgent_foreshadowing:
                weight += self._urgency_boost

            # 4. CRITICAL 级别保底
            if mem.tier == WeightTier.CRITICAL:
                weight = max(weight, 0.85)

            # 限制在 0-1 范围
            mem.dynamic_weight = max(0.0, min(1.0, weight))

        # 按动态权重排序
        sorted_memories = sorted(
            self.memories.values(),
            key=lambda m: m.dynamic_weight,
            reverse=True
        )

        logger.debug(
            f"Memory weights computed for ch{current_chapter}: "
            f"{len(sorted_memories)} memories, "
            f"top={sorted_memories[0].key if sorted_memories else 'none'}"
            f"({sorted_memories[0].dynamic_weight:.2f})" if sorted_memories else ""
        )

        return sorted_memories

    def _calc_relevance(self, mem: WeightedMemory,
                        active_characters: List[str],
                        active_keywords: List[str],
                        volume_goal: str) -> float:
        """计算记忆与当前章节的相关度 (0-1)"""
        score = 0.0
        content_lower = mem.content.lower()

        # 角色名匹配
        for name in active_characters:
            if name.lower() in content_lower or name.lower() in mem.key.lower():
                score += 0.3
                break

        # 关键词匹配
        matched_keywords = sum(1 for kw in active_keywords if kw.lower() in content_lower)
        if active_keywords:
            score += 0.2 * (matched_keywords / len(active_keywords))

        # 卷目标匹配
        if volume_goal and any(word in content_lower for word in volume_goal[:20]):
            score += 0.2

        return min(1.0, score)

    def select_for_prompt(self, sorted_memories: List[WeightedMemory],
                          max_tokens: int = None) -> str:
        """从排序后的记忆中选取最高权重的，拼成 Prompt 上下文

        根据 max_tokens 预算截断，确保不超出 token 限制。
        中文字符粗略估计：1 字 ≈ 1.5 tokens
        """
        max_tokens = max_tokens or self.max_memory_tokens
        max_chars = int(max_tokens / 1.5)

        parts = []
        char_count = 0

        for mem in sorted_memories:
            if mem.dynamic_weight < 0.15:  # 权重太低的忽略
                continue

            entry = f"[{mem.category}|权重{mem.dynamic_weight:.1f}] {mem.content}"
            entry_chars = len(entry)

            if char_count + entry_chars > max_chars:
                # 截断：至少保证 CRITICAL 级别能进来
                if mem.tier == WeightTier.CRITICAL:
                    entry = entry[:max_chars - char_count - 10] + "..."
                else:
                    continue

            parts.append(entry)
            char_count += len(entry)

        return "\n".join(parts) if parts else ""

    def get_stats(self) -> Dict[str, Any]:
        """获取记忆权重统计"""
        tiers = {t: 0 for t in WeightTier}
        for m in self.memories.values():
            tiers[m.tier] += 1
        return {
            "total_memories": len(self.memories),
            "by_tier": tiers,
            "avg_weight": sum(m.dynamic_weight for m in self.memories.values()) / max(1, len(self.memories)),
        }


_weighter: Optional[DynamicMemoryWeighter] = None


def get_memory_weighter() -> DynamicMemoryWeighter:
    global _weighter
    if _weighter is None:
        _weighter = DynamicMemoryWeighter()
    return _weighter
