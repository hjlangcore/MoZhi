"""生成门禁系统 — 借鉴天命 6 道生成门禁

每章写完后必须通过质量门禁，不通过则自动修正重试。
门禁不是简单的打分，而是可以 BLOCK 低质量输出的硬性检查点。

门禁流程：
  章节生成 → Gate 1(字数) → Gate 2(钩子) → Gate 3(连贯) → Gate 4(类型) → Gate 5(重复) → Gate 6(AI痕迹)
  任何 FAIL → 自动修正 → 重新过门禁
  全 PASS → 发布
"""
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger


class GateResult(str, Enum):
    PASS = "pass"       # 通过
    WARN = "warn"       # 警告但通过（50-70分）
    FAIL = "fail"       # 不通过，需修正


@dataclass
class GateCheck:
    """单道门禁的检查结果"""
    gate_name: str
    result: GateResult
    score: float            # 0-100
    reason: str = ""
    fix_instruction: str = ""  # FAIL 时的修正指令


@dataclass
class GatesReport:
    """完整门禁报告"""
    chapter_number: int
    gates: List[GateCheck] = field(default_factory=list)
    overall: GateResult = GateResult.PASS
    total_score: float = 0.0
    fix_count: int = 0

    @property
    def passed(self) -> bool:
        return self.overall != GateResult.FAIL

    @property
    def needs_fix(self) -> bool:
        return self.overall == GateResult.FAIL

    def get_fix_instructions(self) -> str:
        """汇总所有 FAIL 门禁的修正指令"""
        failures = [g for g in self.gates if g.result == GateResult.FAIL]
        if not failures:
            return ""
        parts = ["\n【本章需修正以下问题后重新生成】\n"]
        for i, g in enumerate(failures, 1):
            parts.append(f"{i}. [{g.gate_name}] {g.fix_instruction}")
        return "\n".join(parts)


class GenerationGates:
    """生成门禁管线

    用法：
        gates = GenerationGates()
        report = gates.check_all(chapter_content, context, llm_generate)
        if report.needs_fix:
            # 用 report.get_fix_instructions() 修正后重试
    """

    def __init__(self, max_fix_retries: int = 2):
        self.max_fix_retries = max_fix_retries

    # ============================================================
    # Gate 1: 字数门禁
    # ============================================================
    def gate_length(self, content: str, target_words: int,
                    previous_content: str = "") -> GateCheck:
        """检查中文字数是否达标"""
        chinese_chars = len([c for c in content if '一' <= c <= '鿿'])
        min_acceptable = int(target_words * 0.6)

        if chinese_chars >= target_words:
            return GateCheck(
                gate_name="字数门禁",
                result=GateResult.PASS,
                score=100,
                reason=f"中文字数{chinese_chars}，达标"
            )
        elif chinese_chars >= min_acceptable:
            return GateCheck(
                gate_name="字数门禁",
                result=GateResult.WARN,
                score=60 + 40 * (chinese_chars - min_acceptable) / (target_words - min_acceptable),
                reason=f"中文字数{chinese_chars}/{target_words}，偏低但可接受",
                fix_instruction=f"字数不足，需从{chinese_chars}字扩展到至少{target_words}字"
            )
        else:
            return GateCheck(
                gate_name="字数门禁",
                result=GateResult.FAIL,
                score=max(0, chinese_chars / target_words * 100),
                reason=f"中文字数严重不足：{chinese_chars}/{target_words}",
                fix_instruction=f"严重字数不足！当前仅{chinese_chars}字，目标{target_words}字。请大幅扩展内容：增加场景描写、对话、心理活动、战斗细节。"
            )

    # ============================================================
    # Gate 2: 钩子门禁
    # ============================================================
    def gate_hook(self, content: str, style_type: str = "") -> GateCheck:
        """检查结尾是否有钩子/悬念"""
        ending = content[-300:] if len(content) > 300 else content

        hook_keywords = [
            "突然", "忽然", "却", "竟然", "猛然", "骤然", "陡然",
            "下一个", "然而", "不料", "谁知", "只见", "就在这",
            "未完待续", "欲知后事", "危险", "危机", "神秘", "诡异",
            "?", "！", "...", "……"
        ]

        matches = [kw for kw in hook_keywords if kw in ending]
        score = min(100, len(matches) * 25)

        if score >= 60:
            return GateCheck(
                gate_name="钩子门禁", result=GateResult.PASS, score=score,
                reason=f"结尾检测到{len(matches)}个钩子信号"
            )
        elif score >= 30:
            return GateCheck(
                gate_name="钩子门禁", result=GateResult.WARN, score=score,
                reason="结尾钩子偏弱",
                fix_instruction="请在结尾加入悬念或反转：突然事件/新线索/危机预告/人物冲突预告"
            )
        else:
            return GateCheck(
                gate_name="钩子门禁", result=GateResult.FAIL, score=score,
                reason="结尾缺少钩子",
                fix_instruction="必须在章节结尾加入钩子！选择一种：①突发事件打断当前场景 ②新角色/势力登场 ③主角做出意外决定 ④揭示一个秘密线索 ⑤预告下一章的危机"
            )

    # ============================================================
    # Gate 3: 连贯性门禁
    # ============================================================
    def gate_coherence(self, content: str, previous_ending: str = "",
                       character_names: List[str] = None) -> GateCheck:
        """检查与上一章的连贯性"""
        if not previous_ending:
            return GateCheck(
                gate_name="连贯门禁", result=GateResult.PASS, score=100,
                reason="无前文可比对"
            )

        # 检查是否有明显的跳跃
        content_start = content[:500]
        issues = []

        # 简单检查：前文结尾的关键词是否在新章节开头出现
        prev_keywords = self._extract_keywords(previous_ending[-200:])
        start_keywords = self._extract_keywords(content_start)
        overlap = prev_keywords & start_keywords
        overlap_rate = len(overlap) / max(1, len(prev_keywords))

        if overlap_rate < 0.1:
            issues.append("新章节开头与前章结尾衔接度低")

        score = min(100, overlap_rate * 100 + 50)

        if not issues:
            return GateCheck(
                gate_name="连贯门禁", result=GateResult.PASS, score=score,
                reason=f"与前文衔接良好（关键词重叠率{overlap_rate:.0%}）"
            )
        elif score >= 40:
            return GateCheck(
                gate_name="连贯门禁", result=GateResult.WARN, score=score,
                reason="; ".join(issues),
                fix_instruction="请确保本章开头与前章结尾有明确的时空/情节衔接"
            )
        else:
            return GateCheck(
                gate_name="连贯门禁", result=GateResult.FAIL, score=score,
                reason="章节严重脱离前文",
                fix_instruction=f"本章与前章严重脱节！请从前章结尾直接接续：'{previous_ending[-100:]}...'之后立即发生的事情。不要跳时间线、不要跳场景、不要引入无关新角色。"
            )

    # ============================================================
    # Gate 4: 类型一致性门禁
    # ============================================================
    def gate_genre(self, content: str, style_type: str = "",
                   expected_keywords: List[str] = None) -> GateCheck:
        """检查是否符合目标文风类型特征"""
        if not expected_keywords:
            return GateCheck(
                gate_name="类型门禁", result=GateResult.PASS, score=100,
                reason="无类型约束"
            )

        content_lower = content.lower()
        matches = [kw for kw in expected_keywords if kw.lower() in content_lower]
        match_rate = len(matches) / len(expected_keywords) if expected_keywords else 1.0

        if match_rate >= 0.4:
            return GateCheck(
                gate_name="类型门禁", result=GateResult.PASS,
                score=match_rate * 100,
                reason=f"类型关键词覆盖率{match_rate:.0%}"
            )
        elif match_rate >= 0.2:
            return GateCheck(
                gate_name="类型门禁", result=GateResult.WARN,
                score=match_rate * 100,
                reason=f"类型特征偏弱",
                fix_instruction=f"请融入更多{style_type}风格元素"
            )
        else:
            return GateCheck(
                gate_name="类型门禁", result=GateResult.FAIL,
                score=match_rate * 100,
                reason=f"类型特征缺失",
                fix_instruction=f"本章严重偏离{style_type}风格！请加入该类小说的典型元素。"
            )

    # ============================================================
    # Gate 5: 重复门禁
    # ============================================================
    def gate_repetition(self, content: str, previous_content: str = "") -> GateCheck:
        """检查是否与前章有大量重复"""
        if not previous_content:
            return GateCheck(
                gate_name="重复门禁", result=GateResult.PASS, score=100,
                reason="无前文可比对"
            )

        # 提取句子级 n-gram 比较
        prev_sentences = self._split_sentences(previous_content)
        curr_sentences = self._split_sentences(content)

        if len(prev_sentences) < 3 or len(curr_sentences) < 3:
            return GateCheck(
                gate_name="重复门禁", result=GateResult.PASS, score=100,
                reason="内容过短，跳过检查"
            )

        repeats = 0
        for cs in curr_sentences:
            if len(cs) < 10:
                continue
            for ps in prev_sentences:
                if len(ps) < 10:
                    continue
                # 简单相似度：公共子串长度
                common = self._lcs_length(cs, ps)
                if common > len(cs) * 0.7 or common > len(ps) * 0.7:
                    repeats += 1
                    break

        repeat_rate = repeats / len(curr_sentences) if curr_sentences else 0

        if repeat_rate < 0.1:
            return GateCheck(
                gate_name="重复门禁", result=GateResult.PASS,
                score=100 - repeat_rate * 100,
                reason=f"与前章重复率{repeat_rate:.0%}"
            )
        elif repeat_rate < 0.25:
            return GateCheck(
                gate_name="重复门禁", result=GateResult.WARN,
                score=60,
                reason=f"有{repeats}处与前章相似",
                fix_instruction="部分内容与前章重复，请调整表述或推进情节"
            )
        else:
            return GateCheck(
                gate_name="重复门禁", result=GateResult.FAIL,
                score=max(0, 50 - repeat_rate * 100),
                reason=f"严重重复！{repeats}处与前章雷同",
                fix_instruction="大量内容与前章重复！请完全重写这些段落的表述，推进情节发展而非重复描述。"
            )

    # ============================================================
    # Gate 6: AI 痕迹门禁
    # ============================================================
    def gate_ai_traces(self, content: str) -> GateCheck:
        """检查 AI 写作痕迹"""
        ai_patterns = [
            ("总的来说", 15), ("总而言之", 15), ("综上所述", 20),
            ("此外", 5), ("另外", 5), ("值得注意的是", 10),
            ("可以说", 5), ("毫无疑问", 10), ("显然", 8),
            ("在这个充满", 15), ("让我们", 15),
            ("通过以上", 20), ("总而言之", 15),
            ("希望这些", 20), ("以上是", 20),
            ("值得注意的是", 10), ("不可否认", 10),
            ("众所周知", 15), ("不管怎样", 10),
            ("最后但并非最不重要", 20),
        ]

        content_lower = content.lower()
        total_penalty = 0
        found_patterns = []

        for pattern, penalty in ai_patterns:
            count = content_lower.count(pattern.lower())
            if count > 0:
                total_penalty += penalty * count
                found_patterns.append(f"{pattern}(×{count})")

        score = max(0, 100 - total_penalty)

        if score >= 70:
            return GateCheck(
                gate_name="AI痕迹门禁", result=GateResult.PASS, score=score,
                reason="AI痕迹可接受"
            )
        elif score >= 40:
            return GateCheck(
                gate_name="AI痕迹门禁", result=GateResult.WARN, score=score,
                reason=f"检测到AI常用语: {', '.join(found_patterns[:5])}",
                fix_instruction="请将这些AI痕迹词替换为更自然的表达：删除总结性语句，用具体描写代替抽象概括。"
            )
        else:
            return GateCheck(
                gate_name="AI痕迹门禁", result=GateResult.FAIL, score=score,
                reason=f"AI痕迹过重: {', '.join(found_patterns[:5])}",
                fix_instruction=f"AI痕迹过重！请重写以下段落风格的问题：删除'{found_patterns[0] if found_patterns else '总结性语句'}'等AI常用语，增加具象描写、感官细节、对话。"
            )

    # ============================================================
    # 全部门禁检查
    # ============================================================
    def check_all(
        self,
        content: str,
        chapter_number: int,
        target_words: int = 2000,
        previous_content: str = "",
        style_type: str = "",
        style_keywords: List[str] = None,
    ) -> GatesReport:
        """运行全部 6 道门禁检查"""
        gates = [
            self.gate_length(content, target_words, previous_content),
            self.gate_hook(content, style_type),
            self.gate_coherence(content, previous_content[-300:] if previous_content else ""),
            self.gate_genre(content, style_type, style_keywords),
            self.gate_repetition(content, previous_content),
            self.gate_ai_traces(content),
        ]

        # 判定总结果
        has_fail = any(g.result == GateResult.FAIL for g in gates)
        has_warn = any(g.result == GateResult.WARN for g in gates)
        avg_score = sum(g.score for g in gates) / len(gates)

        if has_fail:
            overall = GateResult.FAIL
        elif has_warn:
            overall = GateResult.WARN
        else:
            overall = GateResult.PASS

        report = GatesReport(
            chapter_number=chapter_number,
            gates=gates,
            overall=overall,
            total_score=avg_score,
        )

        # 日志输出
        gate_summary = " | ".join(
            f"{g.gate_name}:{g.result.value}({g.score:.0f})" for g in gates
        )
        logger.info(f"Gate check ch{chapter_number}: [{overall.value}] avg={avg_score:.0f} | {gate_summary}")

        if has_fail:
            failed = [g.gate_name for g in gates if g.result == GateResult.FAIL]
            logger.warning(f"Chapter {chapter_number} FAILED gates: {failed}")

        return report

    # ============================================================
    # 辅助方法
    # ============================================================
    @staticmethod
    def _extract_keywords(text: str, min_len: int = 2) -> set:
        """简单提取关键词（2字以上的中文词组）"""
        import re
        words = re.findall(r'[一-鿿]{' + str(min_len) + r',}', text)
        return set(words)

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        """按句号、问号、感叹号等分割句子"""
        import re
        return [s.strip() for s in re.split(r'[。！？；\n]', text) if len(s.strip()) > 5]

    @staticmethod
    def _lcs_length(a: str, b: str) -> int:
        """最长公共子串长度"""
        m, n = len(a), len(b)
        if m == 0 or n == 0:
            return 0
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        max_len = 0
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if a[i-1] == b[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                    max_len = max(max_len, dp[i][j])
        return max_len

    @staticmethod
    def build_fix_prompt(original_content: str, fix_instructions: str, target_words: int) -> str:
        """构建修正 Prompt"""
        return f"""以下章节未能通过质量检查，请根据修正意见重写。

【修正意见】
{fix_instructions}

【原始章节（需修正）】
{original_content[:3000]}

【重写要求】
- 保留原有的情节方向和角色设定
- 针对性解决上述修正意见中的问题
- 目标字数：{target_words}字
- 确保结尾有钩子
- 避免AI写作痕迹
- 直接输出修正后的完整章节"""


_gates: Optional[GenerationGates] = None


def get_generation_gates() -> GenerationGates:
    global _gates
    if _gates is None:
        _gates = GenerationGates()
    return _gates
