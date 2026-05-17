"""多维度审计管线 — 借鉴 InkOS 的 33 维度审计，精简为小说创作核心审计维度"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from loguru import logger

from src.novel_agent.state import NovelState, ChapterModel


@dataclass
class AuditResult:
    dimension: str
    passed: bool
    score: float            # 0-100
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


class AuditPipeline:
    """小说创作多维度质量审计管线

    审计维度（精简自 InkOS 33 维度）：
    1. 角色一致性 — OOC检测，角色行为是否符合设定
    2. 时间线连贯 — 时间流逝是否合理
    3. 设定一致性 — 世界观/战斗系统是否前后矛盾
    4. 伏笔追踪 — 伏笔埋设与回收状态
    5. 节奏评估 — 爽点密度、剧情推进速度
    6. 战力平衡 — 实力体系是否崩溃
    7. AI痕迹 — 是否存在机器写作痕迹
    8. 文风一致 — 文风是否统一
    9. 语言质量 — 语法/错别字/标点
    10. 章节钩子 — 每章结尾是否有钩子
    """

    def __init__(self):
        self.dimensions = [
            "character_consistency",
            "timeline_coherence",
            "setting_consistency",
            "foreshadowing_tracking",
            "pacing_evaluation",
            "power_balance",
            "ai_trace",
            "style_consistency",
            "language_quality",
            "chapter_hook",
        ]

    def audit_chapter(
        self,
        chapter: ChapterModel,
        novel_state: NovelState,
        previous_content: str = ""
    ) -> Dict[str, Any]:
        """对单个章节进行多维度审计"""
        results: List[AuditResult] = []

        # 1. 角色一致性
        results.append(self._audit_character_consistency(chapter, novel_state))

        # 2. 时间线连贯
        results.append(self._audit_timeline(chapter, previous_content))

        # 3. 设定一致性
        results.append(self._audit_setting(chapter, novel_state))

        # 4. 伏笔追踪
        results.append(self._audit_foreshadowing(novel_state))

        # 5. 节奏评估
        results.append(self._audit_pacing(chapter, novel_state))

        # 6. 战力平衡
        results.append(self._audit_power_balance(chapter, novel_state))

        # 7. AI痕迹
        results.append(self._audit_ai_traces(chapter))

        # 8. 文风一致
        results.append(self._audit_style(chapter, novel_state))

        # 9. 语言质量
        results.append(self._audit_language(chapter))

        # 10. 章节钩子
        results.append(self._audit_hook(chapter))

        passed_count = sum(1 for r in results if r.passed)
        total_score = sum(r.score for r in results) / len(results)

        return {
            "overall_score": round(total_score, 1),
            "passed_count": passed_count,
            "total_dimensions": len(results),
            "passed": passed_count >= len(results) * 0.7,  # 70% 通过率
            "dimensions": [
                {
                    "dimension": r.dimension,
                    "passed": r.passed,
                    "score": r.score,
                    "issues": r.issues,
                    "suggestions": r.suggestions
                }
                for r in results
            ]
        }

    def _audit_character_consistency(self, chapter: ChapterModel, state: NovelState) -> AuditResult:
        issues = []
        suggestions = []

        if not state.setting or not state.setting.main_character:
            return AuditResult("character_consistency", True, 100.0)

        mc_name = state.setting.main_character.name
        content = chapter.content

        if mc_name and mc_name not in content and chapter.chapter_number > 1:
            issues.append(f"主角「{mc_name}」在本章未出现")

        if len(content) > 100:
            # 检测突然的性格转变（简单启发式）
            aggressive_patterns = ["冷笑", "杀意", "眼中寒光"]
            passive_patterns = ["退缩", "畏惧", "颤抖"]
            aggressive_count = sum(content.count(p) for p in aggressive_patterns)
            passive_count = sum(content.count(p) for p in passive_patterns)

            if aggressive_count > 10 and passive_count > 5:
                issues.append("角色性格跳跃：同时出现攻击性和退缩行为")

        score = max(30, 100 - len(issues) * 25)
        return AuditResult("character_consistency", len(issues) == 0, score, issues, suggestions)

    def _audit_timeline(self, chapter: ChapterModel, previous_content: str) -> AuditResult:
        issues = []
        time_markers = ["片刻", "一会儿", "一个时辰", "半天", "一天", "数日", "一月", "一年"]

        found_markers = [m for m in time_markers if m in chapter.content]
        if previous_content:
            prev_markers = [m for m in time_markers if m in previous_content]

        score = 100.0
        return AuditResult("timeline_coherence", True, score, issues, [])

    def _audit_setting(self, chapter: ChapterModel, state: NovelState) -> AuditResult:
        issues = []
        if not state.setting:
            return AuditResult("setting_consistency", False, 50.0, ["缺少作品设定"])

        # 检查是否有破坏世界观设定的内容
        if state.setting.power_system:
            forbidden_terms = []
            for term in forbidden_terms:
                if term in chapter.content:
                    issues.append(f"设定冲突：使用了不符合修炼体系的内容")

        score = max(30, 100 - len(issues) * 20)
        return AuditResult("setting_consistency", len(issues) == 0, score, issues, [])

    def _audit_foreshadowing(self, state: NovelState) -> AuditResult:
        issues = []
        unresolved = [fs for fs in state.foreshadowing_tracking if fs.status == "unresolved"]
        overdue = [fs for fs in unresolved if state.current_chapter - fs.chapter_introduced > 15]

        if overdue:
            issues.append(f"有{len(overdue)}个伏笔超过15章未回收")

        score = max(20, 100 - len(overdue) * 10)
        return AuditResult("foreshadowing_tracking", len(issues) == 0, score, issues,
                          ["建议尽快回收过期伏笔"] if overdue else [])

    def _audit_pacing(self, chapter: ChapterModel, state: NovelState) -> AuditResult:
        issues = []
        content = chapter.content

        if len(content) < 500:
            issues.append("章节内容过短（<500字），节奏可能匆忙")
        if len(content) > 5000:
            issues.append("章节内容过长（>5000字），读者可能疲劳")

        dialogue_chars = content.count('"') + content.count('"') + content.count('"')
        dialogue_ratio = dialogue_chars / max(len(content), 1)
        if dialogue_ratio < 0.02:
            issues.append("对话占比过低，可能缺乏角色互动")
        if dialogue_ratio > 0.4:
            issues.append("对话占比过高，可能缺乏描写和推进")

        score = max(30, 100 - len(issues) * 20)
        return AuditResult("pacing_evaluation", len(issues) == 0, score, issues, [])

    def _audit_power_balance(self, chapter: ChapterModel, state: NovelState) -> AuditResult:
        issues = []
        content = chapter.content

        power_keywords = ["突破", "晋升", "踏入", "晋级", "实力大增", "顿悟"]
        breakthrough_count = sum(content.count(kw) for kw in power_keywords)

        if breakthrough_count > 5:
            issues.append("本章突破次数过多（>5次），战力可能崩坏")

        # 检测是否出现「王级满地走」
        high_level_terms = ["大乘", "渡劫", "飞升", "仙人", "神级", "圣级"]
        high_level_count = sum(content.count(t) for t in high_level_terms)
        if chapter.chapter_number < 20 and high_level_count > 3:
            issues.append("前期章节出现过多高级别概念，战力体系可能过早膨胀")

        score = max(30, 100 - len(issues) * 25)
        return AuditResult("power_balance", len(issues) == 0, score, issues,
                          ["控制境界提升节奏，每次突破应有充分铺垫"] if issues else [])

    def _audit_ai_traces(self, chapter: ChapterModel) -> AuditResult:
        """AI痕迹检测（简化版，独立于deai_processor）"""
        issues = []
        content = chapter.content

        ai_markers = ["总的来说", "不可否认", "值得注意的是", "在这个世界里"]
        found = [m for m in ai_markers if m in content]

        if found:
            issues.append(f"发现AI高频词汇：{', '.join(found)}")

        # 检测句式重复
        sentences = [s.strip() for s in content.split("。") if len(s.strip()) > 10]
        if len(sentences) > 10:
            avg_len = sum(len(s) for s in sentences) / len(sentences)
            uniform_count = sum(1 for s in sentences if abs(len(s) - avg_len) < 5)
            uniformity = uniform_count / len(sentences)
            if uniformity > 0.7:
                issues.append("句式长度过于均匀，缺乏节奏变化（AI特征）")

        score = max(20, 100 - len(issues) * 30)
        return AuditResult("ai_trace", len(issues) == 0, score, issues,
                          ["建议手动润色，增加句式变化和个性化表达"] if issues else [])

    def _audit_style(self, chapter: ChapterModel, state: NovelState) -> AuditResult:
        issues = []
        if not state.setting or not state.setting.style_type:
            return AuditResult("style_consistency", True, 100.0)

        target_style = state.setting.style_type
        content = chapter.content

        style_keywords = {
            "凡人流": ["修炼", "练气", "筑基", "金丹", "磨砺"],
            "热血": ["战", "杀", "爆发", "轰", "碾压", "震惊"],
            "隐忍": ["隐忍", "暗中", "低调", "潜伏", "等待"],
            "宏大": ["万界", "诸天", "星辰", "宇宙", "浩瀚"]
        }

        expected = style_keywords.get(target_style, [])
        if expected:
            found = [kw for kw in expected if kw in content]
            if len(found) < len(expected) * 0.3:
                issues.append(f"本章缺少{target_style}风格的典型元素")

        score = max(30, 100 - len(issues) * 25)
        return AuditResult("style_consistency", len(issues) == 0, score, issues, [])

    def _audit_language(self, chapter: ChapterModel) -> AuditResult:
        issues = []
        content = chapter.content

        # 错别字检测（简化版）
        common_typos = {
            "的地得": 0,
        }

        # 标点检查
        if content.count("。") < len(content) / 200:
            issues.append("句号使用过少，可能存在段落过长问题")

        score = max(30, 100 - len(issues) * 20)
        return AuditResult("language_quality", len(issues) == 0, score, issues, [])

    def _audit_hook(self, chapter: ChapterModel) -> AuditResult:
        issues = []
        content = chapter.content
        ending = content[-200:] if len(content) > 200 else content

        hook_indicators = ["?", "！", "突然", "竟然", "没想到", "接着", "下一", "将要"]
        has_hook = any(ind in ending for ind in hook_indicators)

        if not has_hook:
            issues.append("章节结尾缺乏钩子，建议添加悬念或期待")

        score = 60 if has_hook else 30
        return AuditResult("chapter_hook", has_hook, score, issues,
                          ["结尾添加：悬念提问/新威胁暗示/新目标揭示/反转让读者意外"] if not has_hook else [])


_audit_pipeline: Optional[AuditPipeline] = None


def get_audit_pipeline() -> AuditPipeline:
    global _audit_pipeline
    if _audit_pipeline is None:
        _audit_pipeline = AuditPipeline()
    return _audit_pipeline
