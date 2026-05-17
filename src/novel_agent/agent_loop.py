"""Agent Loop 动态调度 — 借鉴 NovelClaw Claw模式 + kimi-writer Agentic Loop

核心理念：不是固定的"写→润色→校对→审计"流水线，而是
主编Agent动态决定每章需要执行哪些操作、按什么顺序、是否需要重做。

决策引擎：
  - 规则驱动（快速，处理80%场景）
  - LLM驱动（复杂决策，如"是否需要重写整个场景"）

调度策略：
  1. 必做：写作 + 门禁检查
  2. 按需：润色（低分时）/ 校对（AI痕迹重时）/ 联网搜索（新增设定时）
  3. 补救：修正（门禁FAIL时）/ 重写（连续FAIL时）/ 深度审计（趋势下滑时）

Human Review Gate:
  - 每N章自动暂停，等待人工审核
  - 确保内容方向符合创作者意图
"""
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from loguru import logger

from src.novel_agent.human_review_gate import (
    get_human_review_gate,
    HumanReviewGate,
    ReviewGateConfig,
    ReviewStatus
)


class ActionType(str, Enum):
    """主编可调度的操作类型"""
    # 核心操作
    WRITE = "write_chapter"
    POLISH = "polish_chapter"
    PROOFREAD = "proofread_chapter"
    # 质量检查
    GATE_CHECK = "gate_check"
    DEEP_AUDIT = "deep_audit"
    SCENE_ANALYSIS = "scene_analysis"
    # 知识操作
    WEB_SEARCH = "web_search"
    WEB_FETCH = "web_fetch"
    STATE_WRITEBACK = "state_writeback"
    CONTEXT_COMPRESS = "context_compress"
    # 补救操作
    AUTO_FIX = "auto_fix"
    REGENERATE = "regenerate"
    EXTEND_CONTENT = "extend_content"
    # 规划操作
    REASONING_PLAN = "reasoning_plan"
    MEMORY_REWEIGHT = "memory_reweight"


@dataclass
class Action:
    """主编调度的一个操作"""
    action_type: ActionType
    priority: int = 5               # 1-10，10最高
    reason: str = ""
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LoopDecision:
    """主编的一次决策"""
    chapter_number: int
    iteration: int
    actions: List[Action] = field(default_factory=list)
    reasoning: str = ""             # 为什么做这个决策
    quality_before: float = 0.0
    quality_after: float = 0.0


@dataclass
class ChapterLoopResult:
    """一章的完整 Agent Loop 结果"""
    chapter_number: int
    iterations: int
    decisions: List[LoopDecision] = field(default_factory=list)
    final_quality: float = 0.0
    actions_executed: List[str] = field(default_factory=list)
    total_llm_calls: int = 0
    success: bool = False

    @property
    def efficiency_ratio(self) -> float:
        """效率比：最少操作数 / 实际操作数"""
        if not self.success:
            return 0.0
        minimum = 3  # write + gate + title = 3
        return minimum / max(minimum, len(self.actions_executed))


class EditorAgent:
    """主编Agent — Agent Loop 的决策核心

    负责：
    1. 分析章节状态，决定下一步操作
    2. 调度工具执行
    3. 追踪执行效果
    4. Human Review Gate 管理
    """

    def __init__(
        self, 
        max_iterations: int = 8, 
        quality_threshold: float = 65.0,
        review_gate_config: Optional[ReviewGateConfig] = None
    ):
        self.max_iterations = max_iterations
        self.quality_threshold = quality_threshold
        self.decision_history: Dict[int, List[LoopDecision]] = {}
        self.review_gate = get_human_review_gate(review_gate_config)
    
    def check_review_gate(self, chapter_number: int, quality_score: float = 100.0) -> bool:
        """检查是否需要暂停等待人工审核"""
        return self.review_gate.should_pause(chapter_number, quality_score)
    
    def is_paused_for_review(self) -> bool:
        """是否暂停等待审核"""
        return self.review_gate.is_paused
    
    def get_review_gate_status(self) -> str:
        """获取审核门控状态"""
        return self.review_gate.get_status_text()

    def decide_next_actions(
        self,
        chapter_number: int,
        iteration: int,
        current_quality: float,
        gate_results: Optional[Dict[str, Any]] = None,
        audit_report: Optional[Any] = None,
        chapter_length: int = 0,
        target_length: int = 2000,
        ai_trace_score: float = 0.0,
        style_type: str = "",
    ) -> List[Action]:
        """核心决策：基于当前状态决定下一步操作

        规则驱动的快速决策（处理80%场景），复杂情况用LLM辅助。
        """
        actions = []
        reasoning_parts = []

        # ================================================================
        # 决策规则
        # ================================================================

        # 规则1: 门禁FAIL → 立即修正
        if gate_results and hasattr(gate_results, 'needs_fix') and gate_results.needs_fix:
            fail_gates = [g.gate_name for g in gate_results.gates if hasattr(g, 'result') and str(g.result) == 'fail']
            reasoning_parts.append(f"门禁失败: {fail_gates}")

            if iteration < 2:
                actions.append(Action(
                    ActionType.AUTO_FIX, priority=10,
                    reason=f"门禁失败需修正: {', '.join(fail_gates)}",
                    params={"fix_instructions": gate_results.get_fix_instructions() if hasattr(gate_results, 'get_fix_instructions') else ""}
                ))
            else:
                # 连续失败 → 重写
                reasoning_parts.append("连续修正失败，升级为重写")
                actions.append(Action(
                    ActionType.REGENERATE, priority=10,
                    reason="连续修正失败，需全章重写"
                ))

        # 规则2: 字数不足 → 扩展
        if chapter_length < target_length * 0.7:
            reasoning_parts.append(f"字数严重不足({chapter_length}/{target_length})")
            actions.append(Action(
                ActionType.EXTEND_CONTENT, priority=9,
                reason=f"字数不足，需从{chapter_length}扩展到{target_length}",
                params={"target_words": target_length, "current_words": chapter_length}
            ))

        # 规则3: AI痕迹过重 → 去AI + 校对
        if ai_trace_score > 60:
            reasoning_parts.append(f"AI痕迹过重({ai_trace_score:.0f})")
            actions.append(Action(
                ActionType.PROOFREAD, priority=8,
                reason="AI痕迹重，需校对去AI化"
            ))

        # 规则4: 质量偏低 → 润色
        if current_quality < 70 and current_quality >= self.quality_threshold:
            reasoning_parts.append(f"质量偏低({current_quality:.0f})，建议润色")
            actions.append(Action(
                ActionType.POLISH, priority=7,
                reason=f"质量分{current_quality:.0f}，润色提升文笔"
            ))

        # 规则5: 质量严重偏低 → 深度审计 + 修正
        if current_quality < self.quality_threshold and current_quality >= 40:
            reasoning_parts.append(f"质量不达标({current_quality:.0f})，触发深度审计")
            actions.append(Action(
                ActionType.DEEP_AUDIT, priority=8,
                reason="深度分析质量问题"
            ))
            actions.append(Action(
                ActionType.AUTO_FIX, priority=7,
                reason="根据深度审计结果修正"
            ))

        # 规则6: 极低质量 → 直接重写
        if current_quality < 40 and iteration > 0:
            reasoning_parts.append(f"质量极低({current_quality:.0f})，需要重写")
            actions.append(Action(
                ActionType.REGENERATE, priority=10,
                reason=f"质量极低({current_quality:.0f})，重写更高效"
            ))

        # 规则7: 每10章 → 状态回写 + 上下文压缩
        if chapter_number % 10 == 0 and iteration == 0:
            actions.append(Action(
                ActionType.STATE_WRITEBACK, priority=5,
                reason="定期状态回写"
            ))
            actions.append(Action(
                ActionType.CONTEXT_COMPRESS, priority=5,
                reason="定期上下文压缩"
            ))

        # 规则8: 每5章 → 联网搜索（如果还没做）
        if chapter_number % 5 == 0 and iteration == 0:
            actions.append(Action(
                ActionType.WEB_SEARCH, priority=4,
                reason="定期联网补充知识"
            ))

        # 排序：按优先级降序
        actions.sort(key=lambda a: a.priority, reverse=True)

        # 去重：同类型只保留最高优先级的
        seen_types = set()
        deduped = []
        for a in actions:
            if a.action_type not in seen_types:
                deduped.append(a)
                seen_types.add(a.action_type)

        logger.info(
            f"EditorAgent ch{chapter_number} iter{iteration}: "
            f"quality={current_quality:.0f}, decisions={[a.action_type.value for a in deduped]}"
            + (f" | {'; '.join(reasoning_parts[:2])}" if reasoning_parts else "")
        )

        return deduped

    def should_continue(
        self,
        iteration: int,
        current_quality: float,
        previous_quality: float = 0.0,
        actions_taken: List[ActionType] = None,
    ) -> Tuple[bool, str]:
        """判断是否应该继续迭代

        Returns:
            (是否继续, 原因)
        """
        if iteration >= self.max_iterations:
            return False, f"达到最大迭代次数({self.max_iterations})"

        if current_quality >= self.quality_threshold + 10:  # 高于阈值10分就停止
            return False, f"质量达标({current_quality:.0f} >= {self.quality_threshold + 10:.0f})"

        if current_quality >= self.quality_threshold and current_quality <= previous_quality + 3:
            return False, f"质量已收敛({current_quality:.0f})，继续迭代收益不大"

        if iteration >= 3 and current_quality < previous_quality:
            return False, f"质量未改善({current_quality:.0f} < {previous_quality:.0f})，停止迭代"

        return True, "继续优化"

    def build_loop_context(self, chapter_number: int) -> str:
        """为下一个LLM调用构建Agent Loop上下文"""
        if chapter_number not in self.decision_history:
            return ""

        decisions = self.decision_history[chapter_number]
        parts = [f"【主编调度记录 — 第{chapter_number}章】"]
        for d in decisions:
            parts.append(
                f"第{d.iteration}轮: 质量{d.quality_before:.0f}→{d.quality_after:.0f} | "
                f"执行 {[a.action_type.value for a in d.actions]}"
            )
        return "\n".join(parts)


# ============================================================
# Agent Loop 执行器
# ============================================================
class AgentLoopExecutor:
    """Agent Loop 执行器 — 将主编决策转化为实际操作

    用法：
        executor = AgentLoopExecutor(workflow)
        result = executor.run_chapter_loop(chapter_number)
    """

    def __init__(self, workflow):
        self.workflow = workflow
        self.editor = EditorAgent()

    def run_chapter_loop(self, chapter_number: int) -> ChapterLoopResult:
        """执行单章的完整 Agent Loop

        这是Agent Loop的核心方法，替代原有的固定write_next_chapter流程。
        """
        result = ChapterLoopResult(chapter_number=chapter_number, iterations=0)
        llm_calls = 0
        content = ""
        quality = 0.0

        # Iteration 0: 必做操作（思考规划 + 记忆权重 + 写作 + 门禁）
        iteration = 0
        decision = LoopDecision(
            chapter_number=chapter_number,
            iteration=iteration,
            reasoning="初始写作循环",
        )

        # Phase 1: 思考 + 规划（来自reasoning_planner）
        # Phase 2: 动态记忆权重
        # Phase 3: 写作
        # Phase 4: 门禁检查
        # 这些在workflow.write_next_chapter中已经集成

        # 获取初始质量
        if content:
            from src.novel_agent.generation_gates import get_generation_gates
            gates = get_generation_gates()
            gate_report = gates.check_all(
                content=content,
                chapter_number=chapter_number,
                target_words=self.workflow.config.chapter_words,
            )
            quality = gate_report.total_score
        else:
            quality = 75  # 默认质量中上

        decision.quality_before = 0
        decision.quality_after = quality
        result.decisions.append(decision)
        result.actions_executed.extend(["reasoning_plan", "memory_reweight", "write_chapter", "gate_check"])
        llm_calls += 2  # planning + writing

        # ================================================================
        # 动态迭代循环
        # ================================================================
        previous_quality = quality

        while self.editor.should_continue(
            iteration=iteration,
            current_quality=quality,
            previous_quality=previous_quality,
            actions_taken=[ActionType(a) for a in result.actions_executed],
        )[0]:
            iteration += 1
            previous_quality = quality

            # 获取最新内容
            chapter = self._get_current_chapter(chapter_number)
            if not chapter:
                break
            content = chapter.content

            # 主编决策：下一步做什么
            gate_report = None
            if chapter.gate_report:
                gate_report = chapter.gate_report

            actions = self.editor.decide_next_actions(
                chapter_number=chapter_number,
                iteration=iteration,
                current_quality=quality,
                gate_results=gate_report,
                chapter_length=len(content),
                target_length=self.workflow.config.chapter_words,
                style_type=self.workflow.config.style_type,
            )

            if not actions:
                logger.info(f"EditorAgent: no actions needed for ch{chapter_number}")
                break

            decision = LoopDecision(
                chapter_number=chapter_number,
                iteration=iteration,
                actions=actions,
                reasoning=f"质量{quality:.0f}，需{len(actions)}个操作",
                quality_before=quality,
            )

            # 执行主编决策的每个操作
            for action in actions:
                try:
                    executed = self._execute_action(action, chapter_number, content)
                    result.actions_executed.append(action.action_type.value)
                    llm_calls += executed
                except Exception as e:
                    logger.error(f"Action {action.action_type.value} failed: {e}")

            # 重新评估质量
            chapter = self._get_current_chapter(chapter_number)
            if chapter and chapter.content:
                from src.novel_agent.generation_gates import get_generation_gates
                gates = get_generation_gates()
                new_report = gates.check_all(
                    content=chapter.content,
                    chapter_number=chapter_number,
                    target_words=self.workflow.config.chapter_words,
                )
                quality = new_report.total_score

            decision.quality_after = quality
            result.decisions.append(decision)

            if quality >= self.editor.quality_threshold + 5:
                break

        result.iterations = iteration + 1
        result.final_quality = quality
        result.total_llm_calls = llm_calls
        result.success = quality >= self.editor.quality_threshold

        logger.info(
            f"Agent Loop ch{chapter_number} complete: "
            f"{result.iterations} iterations, {len(result.actions_executed)} actions, "
            f"quality={quality:.0f}, success={result.success}, "
            f"efficiency={result.efficiency_ratio:.2f}"
        )

        return result

    def _get_current_chapter(self, chapter_number: int):
        """获取当前章节对象"""
        chapters = self.workflow.state.chapters
        for ch in chapters:
            if ch.chapter_number == chapter_number:
                return ch
        return None

    def _execute_action(self, action: Action, chapter_number: int, content: str) -> int:
        """执行单个主编操作，返回消耗的LLM调用次数"""
        wf = self.workflow

        if action.action_type == ActionType.POLISH:
            wf.polish_chapter(chapter_number)
            return 1

        elif action.action_type == ActionType.PROOFREAD:
            wf.proofread_chapter(chapter_number)
            return 1

        elif action.action_type == ActionType.AUTO_FIX:
            fix_instructions = action.params.get("fix_instructions", "")
            fix_prompt = f"""以下章节需要修正。

【修正意见】
{fix_instructions}

【原始内容】
{content[:3000]}

请输出修正后的完整章节："""
            try:
                new_content = wf.llm.generate(fix_prompt, temperature=0.7)
                chapter = self._get_current_chapter(chapter_number)
                if chapter:
                    chapter.content = new_content
                    chapter.word_count = len(new_content)
                return 1
            except Exception:
                return 0

        elif action.action_type == ActionType.REGENERATE:
            try:
                # 用更高温度重写
                new_content = wf.writer_agent.write_chapter(
                    wf.state, chapter_number, wf.config.chapter_words,
                    knowledge_context="",
                    reasoning_context="请重新构思本章，避免之前的问题。",
                    memory_context="",
                )
                chapter = self._get_current_chapter(chapter_number)
                if chapter:
                    chapter.content = new_content
                    chapter.word_count = len(new_content)
                return 1
            except Exception:
                return 0

        elif action.action_type == ActionType.EXTEND_CONTENT:
            target = action.params.get("target_words", 2000)
            extend_prompt = f"""以下章节字数不足，请续写补充到{target}字。

【当前内容】
{content}

【续写要求】
- 接着上文继续
- 增加场景描写或对话
- 推进情节
- 直接输出续写内容（不要重复上文）"""
            try:
                extension = wf.llm.generate(extend_prompt, temperature=0.8)
                new_content = content + "\n\n" + extension
                chapter = self._get_current_chapter(chapter_number)
                if chapter:
                    chapter.content = new_content
                    chapter.word_count = len(new_content)
                return 1
            except Exception:
                return 0

        elif action.action_type == ActionType.WEB_SEARCH:
            try:
                wf.knowledge_integrator.run_pipeline(
                    llm_generate=wf.llm.generate,
                    novel_title=wf.state.setting.novel_title if wf.state.setting else "",
                    chapter_number=chapter_number,
                    force_keywords=action.params.get("keywords"),
                )
                return 2  # keyword extraction + search analysis
            except Exception:
                return 0

        elif action.action_type == ActionType.WEB_FETCH:
            urls = action.params.get("urls", [])
            if urls:
                from src.novel_agent.web_fetch import get_web_fetcher
                fetcher = get_web_fetcher()
                for url in urls[:3]:
                    fetcher.fetch_and_summarize(url, llm_generate=wf.llm.generate)
                return len(urls[:3])
            return 0

        elif action.action_type == ActionType.STATE_WRITEBACK:
            from src.novel_agent.state_writeback import get_state_writeback
            wb = get_state_writeback()
            chapter = self._get_current_chapter(chapter_number)
            if chapter:
                wb.extract_and_writeback(wf.llm.generate, chapter, wf.state)
            return 1

        elif action.action_type == ActionType.CONTEXT_COMPRESS:
            from src.novel_agent.state_writeback import get_state_writeback
            wb = get_state_writeback()
            chapter = self._get_current_chapter(chapter_number)
            if chapter:
                wb.compress_chapter(wf.llm.generate, chapter)
            return 1

        elif action.action_type == ActionType.DEEP_AUDIT:
            from src.novel_agent.enhanced_audit import get_enhanced_audit
            audit = get_enhanced_audit()
            chapter = self._get_current_chapter(chapter_number)
            if chapter:
                report = audit.run_deep_audit(wf.llm.generate, chapter, wf.config.style_type)
                # 将审计结果写入章节
                if chapter:
                    chapter.quality_score = sum(
                        v.get("score", 75) if isinstance(v, dict) else 75
                        for v in report.values()
                        if isinstance(v, dict) and "score" in v
                    ) / max(1, len([v for v in report.values() if isinstance(v, dict) and "score" in v]))
            return 1

        return 0


# 全局单例
_editor: Optional[EditorAgent] = None


def get_editor_agent() -> EditorAgent:
    global _editor
    if _editor is None:
        _editor = EditorAgent()
    return _editor
