"""思考-规划-写作管线 — 借鉴 kimi-writer 的 k2-thinking 深度推理

两阶段写作流程：
  Phase 1 - REASONING (temperature=0.3): 深度分析当前剧情位置，规划本章结构
  Phase 2 - WRITING (temperature=0.8): 基于规划执行创作

这与简单地往 prompt 里加指令不同——REASONING 阶段的输出是结构化的
章节蓝图，会作为 WRITING 阶段的明确约束。
"""
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from loguru import logger


# 章节推理规划 Prompt
CHAPTER_REASONING_PROMPT = """你是一位资深小说主编。在动笔写第{chapter_number}章之前，请先做深度分析。

【小说】《{novel_title}》
【当前进度】第{chapter_number}章，已写{total_words}字
【文风】{style_guide}
【节奏要求】{rhythm_guidance}

【上一章结尾】
{previous_ending}

【待处理伏笔】
{foreshadowing_list}

【当前卷目标】
{volume_goal}

【主要角色状态】
{character_states}

请按以下格式输出本章规划（简洁精炼，每项不超过3行）：

## 本章定位
- 本章在整体故事中的作用（过渡章/爽点章/高潮章/铺垫章）
- 必须推进的剧情线

## 冲突设计
- 核心冲突是什么
- 冲突的激烈程度（1-10）

## 角色行动
- 主角本章的目标和行动
- 其他关键角色的行动

## 情绪曲线
- 开篇情绪 → 中段情绪 → 结尾情绪
- 是否有情绪转折点

## 场景节拍
- 列出3-5个关键场景/节拍
- 每个节拍一句话概括

## 钩子设计
- 本章结尾钩子类型（悬念/反转/新线索/危机预告）
- 钩子具体内容

## 字数分配
- 预估各场景字数占比

只输出规划，不要写正文。"""


@dataclass
class ChapterPlan:
    """章节规划结果"""
    chapter_number: int
    positioning: str = ""        # 本章定位
    conflict_design: str = ""    # 冲突设计
    character_actions: str = ""  # 角色行动
    emotion_curve: str = ""      # 情绪曲线
    scene_beats: str = ""        # 场景节拍
    hook_design: str = ""        # 钩子设计
    word_allocation: str = ""    # 字数分配
    raw_plan: str = ""           # 原始规划文本

    def to_prompt_context(self) -> str:
        """将规划转为可注入写作 prompt 的上下文"""
        parts = [
            "\n\n【主编规划 — 请严格遵循本章蓝图写作】\n",
        ]
        if self.positioning:
            parts.append(f"## 本章定位\n{self.positioning}\n")
        if self.conflict_design:
            parts.append(f"## 冲突设计\n{self.conflict_design}\n")
        if self.character_actions:
            parts.append(f"## 角色行动\n{self.character_actions}\n")
        if self.emotion_curve:
            parts.append(f"## 情绪曲线\n{self.emotion_curve}\n")
        if self.scene_beats:
            parts.append(f"## 场景节拍（请按此结构展开）\n{self.scene_beats}\n")
        if self.hook_design:
            parts.append(f"## 钩子要求\n{self.hook_design}\n")
        if self.word_allocation:
            parts.append(f"## 字数分配参考\n{self.word_allocation}\n")

        parts.append("\n请基于以上规划开始写作，确保每个场景节拍都得到充分展开。")
        return "\n".join(parts)


class ReasoningPlanner:
    """深度推理规划器 — 在写作前进行结构化章节规划

    用法：
        planner = ReasoningPlanner()
        plan = planner.plan_chapter(llm_generate, context)
        # 然后将 plan.to_prompt_context() 注入写作 prompt
    """

    def __init__(self, enabled: bool = True, skip_on_golden_chapters: bool = True):
        self.enabled = enabled
        self.skip_on_golden_chapters = skip_on_golden_chapters  # 黄金三章跳过规划（已有专用 Prompt）
        self.plans: Dict[int, ChapterPlan] = {}

    def should_plan(self, chapter_number: int, chapter_type: str = "regular") -> bool:
        """判断当前章节是否需要规划"""
        if not self.enabled:
            return False

        # 黄金三章有专用 Prompt，跳过规划
        if self.skip_on_golden_chapters and chapter_number <= 3:
            return False

        return True

    def plan_chapter(
        self,
        llm_generate: Callable[[str, float], str],
        chapter_number: int,
        novel_title: str = "",
        total_words: int = 0,
        style_guide: str = "",
        rhythm_guidance: str = "",
        previous_ending: str = "",
        foreshadowing_list: str = "",
        volume_goal: str = "",
        character_states: str = "",
    ) -> ChapterPlan:
        """执行章节规划推理

        Args:
            llm_generate: LLM 生成函数 (prompt, temperature) -> str
            其他: 小说上下文信息

        Returns:
            ChapterPlan 包含结构化规划结果
        """
        prompt = CHAPTER_REASONING_PROMPT.format(
            chapter_number=chapter_number,
            novel_title=novel_title,
            total_words=total_words,
            style_guide=style_guide[:500],
            rhythm_guidance=rhythm_guidance[:500],
            previous_ending=previous_ending[:500],
            foreshadowing_list=foreshadowing_list[:300] or "无",
            volume_goal=volume_goal[:300] or "常规推进",
            character_states=character_states[:500] or "暂未记录",
        )

        logger.info(f"Reasoning planner: analyzing chapter {chapter_number}...")
        try:
            reasoning = llm_generate(prompt, temperature=0.3)
            plan = self._parse_plan(chapter_number, reasoning)
            self.plans[chapter_number] = plan
            logger.info(f"Chapter {chapter_number} plan created: {len(reasoning)} chars")
            return plan
        except Exception as e:
            logger.warning(f"Reasoning planner failed for ch{chapter_number}: {e}, skipping")
            return ChapterPlan(chapter_number=chapter_number)

    def _parse_plan(self, chapter_number: int, raw: str) -> ChapterPlan:
        """从 LLM 输出中解析结构化规划"""
        plan = ChapterPlan(chapter_number=chapter_number, raw_plan=raw)

        sections = {
            "本章定位": "positioning",
            "冲突设计": "conflict_design",
            "角色行动": "character_actions",
            "情绪曲线": "emotion_curve",
            "场景节拍": "scene_beats",
            "钩子设计": "hook_design",
            "字数分配": "word_allocation",
        }

        current_section = None
        current_content: List[str] = []

        for line in raw.split("\n"):
            line_stripped = line.strip()
            if not line_stripped:
                continue

            # 检测段落标题
            found_section = None
            for title, attr in sections.items():
                if f"## {title}" in line_stripped or f"#{title}" in line_stripped or line_stripped.startswith(f"**{title}**"):
                    found_section = (title, attr)
                    break

            if found_section:
                # 保存上一段
                if current_section:
                    setattr(plan, current_section[1], "\n".join(current_content))
                current_section = found_section
                current_content = []
            elif current_section:
                # 清理列表标记
                clean = line_stripped.lstrip("- *").strip()
                if clean:
                    current_content.append(clean)

        # 保存最后一段
        if current_section:
            setattr(plan, current_section[1], "\n".join(current_content))

        return plan

    def get_plan_context(self, chapter_number: int) -> str:
        """获取指定章节的规划上下文"""
        plan = self.plans.get(chapter_number)
        if plan:
            return plan.to_prompt_context()
        return ""

    def get_last_plan(self) -> Optional[ChapterPlan]:
        """获取最近一次规划"""
        if not self.plans:
            return None
        return self.plans[max(self.plans.keys())]


_planner: Optional[ReasoningPlanner] = None


def get_reasoning_planner() -> ReasoningPlanner:
    global _planner
    if _planner is None:
        _planner = ReasoningPlanner()
    return _planner
