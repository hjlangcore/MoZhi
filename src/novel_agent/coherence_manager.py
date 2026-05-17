"""长篇连贯性管理器 — 保障50万字+长篇小说的全局一致性"""
from typing import Dict, Any, List, Optional
from collections import defaultdict
from loguru import logger


class CoherenceManager:
    """长篇连贯性追踪器

    三个核心机制：
    1. 滚动摘要链 — 每10章生成一个摘要，串联全局脉络
    2. 角色状态表 — 追踪每个角色在各章节的位置/境界/关系变化
    3. 伏笔时间线 — 确保伏笔有埋有收
    """

    def __init__(self):
        self.chapter_summaries: Dict[int, str] = {}       # chapter → summary
        self.character_timeline: Dict[str, Dict[int, str]] = defaultdict(dict)  # name → {ch: state}
        self.plot_events: Dict[int, List[str]] = {}       # chapter → [events]
        self.contradictions: List[str] = []

    def add_chapter_summary(self, chapter_number: int, summary: str):
        self.chapter_summaries[chapter_number] = summary

    def update_character(self, name: str, chapter_number: int, state: str):
        self.character_timeline[name][chapter_number] = state

    def add_plot_event(self, chapter_number: int, event: str):
        if chapter_number not in self.plot_events:
            self.plot_events[chapter_number] = []
        self.plot_events[chapter_number].append(event)

    def get_recent_context(self, current_chapter: int, window: int = 10) -> str:
        """获取最近N章的摘要上下文"""
        parts = []
        start = max(1, current_chapter - window)
        for ch in range(start, current_chapter):
            if ch in self.chapter_summaries:
                parts.append(f"第{ch}章：{self.chapter_summaries[ch]}")
        return "\n".join(parts) if parts else "暂无前文摘要"

    def get_character_context(self, name: str, current_chapter: int) -> str:
        """获取某角色最近的状态"""
        timeline = self.character_timeline.get(name, {})
        recent = [(ch, st) for ch, st in timeline.items() if ch < current_chapter]
        recent.sort(key=lambda x: x[0], reverse=True)
        if recent:
            return recent[0][1]
        return "未知状态"

    def get_all_character_states(self, current_chapter: int) -> str:
        """获取所有角色在当前时间点的状态"""
        lines = []
        for name, timeline in sorted(self.character_timeline.items()):
            recent = [(ch, st) for ch, st in timeline.items() if ch <= current_chapter]
            if recent:
                recent.sort(key=lambda x: x[0])
                lines.append(f"【{name}】→ {recent[-1][1]}")
        return "\n".join(lines) if lines else "暂无角色状态记录"

    def check_consistency(self, chapter_number: int) -> Dict[str, Any]:
        """检查当前章节的全局一致性"""
        issues = []

        # 检查是否有角色状态跳跃
        for name, timeline in self.character_timeline.items():
            states = sorted(timeline.items())
            for i in range(1, len(states)):
                prev_ch, prev_st = states[i - 1]
                curr_ch, curr_st = states[i]
                if curr_ch == chapter_number and curr_ch - prev_ch > 5:
                    issues.append(f"角色「{name}」距上次出现已过{curr_ch - prev_ch}章，需确认状态连贯")

        return {
            "coherent": len(issues) == 0,
            "issues": issues,
            "chapter": chapter_number
        }

    def generate_prompt_context(self, current_chapter: int, novel_state) -> str:
        """为写作生成连贯性上下文prompt"""
        parts = []

        # 前情提要
        context = self.get_recent_context(current_chapter)
        parts.append(f"【前情提要（最近10章）】\n{context}")

        # 角色状态
        char_states = self.get_all_character_states(current_chapter)
        if char_states != "暂无角色状态记录":
            parts.append(f"【角色当前状态】\n{char_states}")

        # 待收伏笔
        unresolved = [fs for fs in novel_state.foreshadowing_tracking
                      if fs.status == "unresolved" and current_chapter - fs.chapter_introduced > 10]
        if unresolved:
            parts.append("【过期未收伏笔（需尽快处理）】")
            for fs in unresolved[:5]:
                parts.append(f"  - {fs.seed} (第{fs.chapter_introduced}章埋入)")

        return "\n\n".join(parts)

    def auto_summarize_chapter(self, chapter, llm_client=None) -> str:
        """自动生成章节摘要（使用LLM或启发式方法）"""
        content = chapter.content

        if llm_client:
            try:
                prompt = f"""用2-3句话总结以下章节的关键剧情（50字以内）：
{content[:1000]}
只输出摘要，不要其他内容。"""
                return llm_client.generate(prompt, temperature=0.3).strip()
            except Exception:
                pass

        # 回退：取前200字作为摘要
        return content[:200].replace("\n", " ") + "..."

    def get_global_summary(self) -> str:
        """获取全篇摘要"""
        lines = [f"共记录 {len(self.chapter_summaries)} 章摘要"]
        lines.append(f"追踪角色：{len(self.character_timeline)} 人")
        lines.append(f"剧情事件：{sum(len(e) for e in self.plot_events.values())} 条")
        if self.contradictions:
            lines.append(f"⚠️ 发现 {len(self.contradictions)} 处矛盾")
        return "\n".join(lines)


_coherence_manager: Optional[CoherenceManager] = None


def get_coherence_manager() -> CoherenceManager:
    global _coherence_manager
    if _coherence_manager is None:
        _coherence_manager = CoherenceManager()
    return _coherence_manager
