"""增强版多维度审计 — 合并天命6道门禁 + 马良AI多模型评估思路

在原审计管线基础上增加：
  1. LLM驱动的深度审计（语义理解而非简单规则匹配）
  2. 章节质量趋势追踪（发现质量下滑趋势）
  3. 场景级审计（作品→卷→章→场景各层都有审计）
  4. 审计历史存档（用于Agent Loop的"回头看"决策）
"""
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from loguru import logger

from src.novel_agent.state import NovelState, ChapterModel, SceneModel
from src.novel_agent.generation_gates import GenerationGates, GateResult


# LLM深度审计 Prompt
DEEP_AUDIT_PROMPT = """你是一位资深小说审稿编辑。请对以下章节进行专业质量评估。

【章节信息】
第{chapter_number}章《{chapter_title}》
字数：{word_count}
文风：{style_type}

【章节内容（前2000字）】
{content_sample}

请从以下维度评分（每项0-100分），并给出具体理由：

1. 开篇抓人度 (hook_strength)：开头300字是否立即吸引读者
2. 冲突张力 (conflict_tension)：核心冲突的设计和执行
3. 人物塑造 (character_depth)：角色行为是否符合设定，是否有成长
4. 节奏控制 (pacing)：信息密度、张弛有度
5. 语言质感 (language_quality)：文笔是否有文学质感，避免AI腔
6. 结尾钩子 (ending_hook)：章末是否有悬念或期待感

输出JSON格式（确保是有效JSON）：
{{
    "hook_strength": {{"score": 75, "reason": "..."}},
    "conflict_tension": {{"score": 80, "reason": "..."}},
    "character_depth": {{"score": 70, "reason": "..."}},
    "pacing": {{"score": 75, "reason": "..."}},
    "language_quality": {{"score": 80, "reason": "..."}},
    "ending_hook": {{"score": 65, "reason": "..."}},
    "overall_comment": "一句话总评",
    "improvement_suggestions": ["建议1", "建议2"]
}}

只输出JSON。"""


@dataclass
class AuditDimension:
    name: str
    score: float
    reason: str = ""
    passed: bool = True


@dataclass
class ChapterAuditReport:
    chapter_number: int
    overall_score: float
    dimensions: List[AuditDimension] = field(default_factory=list)
    llm_analysis: Dict[str, Any] = field(default_factory=dict)
    gate_report: Any = None
    suggestions: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def is_quality_decline(self) -> bool:
        return self.overall_score < 60

    @property
    def critical_issues(self) -> List[str]:
        return [d.name for d in self.dimensions if d.score < 40]


class EnhancedAuditPipeline:
    """增强版审计管线

    三层审计体系：
    Layer 1 - 门禁（规则驱动，快速筛选，可阻塞）
    Layer 2 - 深度审计（LLM驱动，语义理解，6维度评分）
    Layer 3 - 趋势分析（历史追踪，预警质量下滑）
    """

    def __init__(self):
        self.gates = GenerationGates()
        self.audit_history: Dict[int, ChapterAuditReport] = {}  # chapter → report
        self.quality_trend: List[float] = []                     # 最近N章的分数
        self.trend_window = 10

    # ============================================================
    # Layer 1: 门禁检查
    # ============================================================
    def run_gates(
        self,
        content: str,
        chapter_number: int,
        target_words: int = 2000,
        previous_content: str = "",
        style_type: str = "",
    ) -> Any:
        return self.gates.check_all(
            content=content,
            chapter_number=chapter_number,
            target_words=target_words,
            previous_content=previous_content,
            style_type=style_type,
        )

    # ============================================================
    # Layer 2: LLM深度审计
    # ============================================================
    def run_deep_audit(
        self,
        llm_generate: Callable,
        chapter: ChapterModel,
        style_type: str = "",
    ) -> Dict[str, Any]:
        """LLM驱动的语义级质量评估"""
        content_sample = chapter.content[:2000]
        prompt = DEEP_AUDIT_PROMPT.format(
            chapter_number=chapter.chapter_number,
            chapter_title=chapter.title,
            word_count=chapter.word_count,
            style_type=style_type,
            content_sample=content_sample,
        )

        try:
            response = llm_generate(prompt, temperature=0.2)
            # 提取 JSON
            import re, json
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.warning(f"Deep audit JSON parse failed: {e}")

        return {}

    # ============================================================
    # 全审计 — Layer 1 + 2
    # ============================================================
    def audit(
        self,
        llm_generate: Callable,
        chapter: ChapterModel,
        novel_state: NovelState,
        previous_content: str = "",
        target_words: int = 2000,
        run_deep: bool = False,
    ) -> ChapterAuditReport:
        """执行完整审计：门禁 + 可选深度审计"""
        chapter_number = chapter.chapter_number
        style_type = novel_state.setting.style_type if novel_state.setting else ""

        # Layer 1: 门禁
        gate_report = self.run_gates(
            content=chapter.content,
            chapter_number=chapter_number,
            target_words=target_words,
            previous_content=previous_content,
            style_type=style_type,
        )

        # 转换门禁结果为审计维度
        dimensions = []
        for g in gate_report.gates:
            dimensions.append(AuditDimension(
                name=g.gate_name,
                score=g.score,
                reason=g.reason,
                passed=g.result != GateResult.FAIL,
            ))

        # Layer 2: 深度审计（每10章或低分时触发）
        llm_analysis = {}
        if run_deep or gate_report.total_score < 70 or chapter_number % 10 == 0:
            logger.info(f"Running deep audit for chapter {chapter_number}...")
            llm_analysis = self.run_deep_audit(llm_generate, chapter, style_type)

            # 将 LLM 审计维度合并进来
            if llm_analysis:
                dim_map = {
                    "hook_strength": "开篇抓人",
                    "conflict_tension": "冲突张力",
                    "character_depth": "人物塑造",
                    "pacing": "节奏控制",
                    "language_quality": "语言质感",
                    "ending_hook": "结尾钩子",
                }
                for key, cn_name in dim_map.items():
                    if key in llm_analysis:
                        dim_data = llm_analysis[key]
                        score = dim_data.get("score", 75) if isinstance(dim_data, dict) else 75
                        reason = dim_data.get("reason", "") if isinstance(dim_data, dict) else str(dim_data)
                        dimensions.append(AuditDimension(
                            name=f"LLM-{cn_name}",
                            score=float(score),
                            reason=reason,
                        ))

        # 计算综合分
        all_scores = [d.score for d in dimensions]
        overall = sum(all_scores) / len(all_scores) if all_scores else gate_report.total_score

        # 提取建议
        suggestions = []
        if isinstance(llm_analysis.get("improvement_suggestions"), list):
            suggestions = llm_analysis["improvement_suggestions"]
        for g in gate_report.gates:
            if g.result == GateResult.FAIL and g.fix_instruction:
                suggestions.append(f"[{g.gate_name}] {g.fix_instruction}")

        report = ChapterAuditReport(
            chapter_number=chapter_number,
            overall_score=overall,
            dimensions=dimensions,
            llm_analysis=llm_analysis,
            gate_report=gate_report,
            suggestions=suggestions,
        )

        # 存档
        self.audit_history[chapter_number] = report
        self.quality_trend.append(overall)
        if len(self.quality_trend) > self.trend_window:
            self.quality_trend = self.quality_trend[-self.trend_window:]

        # 趋势预警
        if len(self.quality_trend) >= 5:
            recent_avg = sum(self.quality_trend[-5:]) / 5
            older_avg = sum(self.quality_trend[:-5]) / max(1, len(self.quality_trend) - 5)
            if recent_avg < older_avg - 10:
                logger.warning(
                    f"Quality decline detected! Recent 5 chapters avg={recent_avg:.1f} "
                    f"vs older avg={older_avg:.1f}"
                )

        return report

    # ============================================================
    # Layer 3: 趋势分析
    # ============================================================
    def get_trend_report(self) -> Dict[str, Any]:
        """获取质量趋势报告"""
        if not self.quality_trend:
            return {"status": "no_data"}

        scores = self.quality_trend
        return {
            "recent_chapters": len(scores),
            "current_avg": sum(scores[-3:]) / min(3, len(scores)) if scores else 0,
            "overall_avg": sum(scores) / len(scores),
            "trend": "improving" if len(scores) >= 3 and scores[-1] > scores[0] else "declining" if len(scores) >= 3 and scores[-1] < scores[0] else "stable",
            "min_score": min(scores),
            "max_score": max(scores),
            "below_threshold_count": sum(1 for s in scores if s < 60),
        }

    # ============================================================
    # 场景级审计
    # ============================================================
    @staticmethod
    def audit_scene(scene: SceneModel) -> Dict[str, Any]:
        """场景级快速审计"""
        issues = []
        if scene.word_count < 300:
            issues.append("场景过短，建议至少300字")
        if not scene.location:
            issues.append("缺少地点设定")
        if not scene.characters_present:
            issues.append("没有出场角色")

        return {
            "scene_number": scene.scene_number,
            "score": max(0, 100 - len(issues) * 20),
            "issues": issues,
            "passed": len(issues) == 0,
        }


_enhanced_audit: Optional[EnhancedAuditPipeline] = None


def get_enhanced_audit() -> EnhancedAuditPipeline:
    global _enhanced_audit
    if _enhanced_audit is None:
        _enhanced_audit = EnhancedAuditPipeline()
    return _enhanced_audit
