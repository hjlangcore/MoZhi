"""节奏控制器 — 保持小说张弛有度的节奏，确保阅读体验流畅"""
from typing import Dict, Any, Optional
from enum import Enum
from loguru import logger


class ChapterType(str, Enum):
    GOLDEN_OPENING = "golden_opening"  # 黄金三章（第1-3章）
    REGULAR = "regular"                # 常规章节
    SMALL_CLIMAX = "small_climax"      # 小爽点（每3章）
    BIG_CLIMAX = "big_climax"          # 大爽点（每10章）
    VOLUME_CLIMAX = "volume_climax"    # 卷高潮


class RhythmController:
    """控制小说节奏，确保张弛有度、阅读体验流畅"""

    def __init__(self):
        self.small_climax_interval = 3   # 小爽点间隔
        self.big_climax_interval = 10    # 大爽点间隔

    def get_chapter_type(self, chapter_number: int) -> ChapterType:
        if chapter_number <= 3:
            return ChapterType.GOLDEN_OPENING
        elif chapter_number % self.big_climax_interval == 0:
            return ChapterType.BIG_CLIMAX
        elif chapter_number % self.small_climax_interval == 0:
            return ChapterType.SMALL_CLIMAX
        return ChapterType.REGULAR

    def get_chapter_guidance(self, chapter_number: int, style_type: str = "凡人流") -> str:
        """返回对应章节类型的写作指导"""
        chapter_type = self.get_chapter_type(chapter_number)

        if chapter_type == ChapterType.GOLDEN_OPENING:
            return self._golden_opening_guidance(chapter_number, style_type)

        elif chapter_type == ChapterType.BIG_CLIMAX:
            return self._big_climax_guidance(chapter_number, style_type)

        elif chapter_type == ChapterType.SMALL_CLIMAX:
            return self._small_climax_guidance(chapter_number, style_type)

        return self._regular_guidance(chapter_number)

    def _golden_opening_guidance(self, chapter_number: int, style_type: str) -> str:
        guides = {
            1: """【黄金三章·第一章 — 抓人】
写作目标：开局即冲突，300字内必须出事儿。
- 禁止：世界观介绍、背景铺垫、风景描写、回忆
- 必须：直接切入冲突 — 被羞辱/被追杀/被退婚/修为被废
- 主角触底：让读者心疼、代入
- 结尾钩子：金手指即将出现
- Show, don't tell：通过动作和结果展示情绪，不用形容词定性""",

            2: """【黄金三章·第二章 — 留人】
写作目标：金手指亮出，解决小危机，延续紧张。
- 金手指亮相：让读者知道它的能力范围，但不要全开
- 解决一个小危机：第一次尝到甜头
- 反派继续施压：制造持续紧张感
- 与主角建立情感共鸣
- 结尾钩子：更大的麻烦正在逼近""",

            3: """【黄金三章·第三章 — 锁人】
写作目标：第一次爽点交付，确立长期目标。
- 第一次打脸/升级/让反派吃惊 — 必须是实质性的
- 读者忍了两章，这章必须给足够的甜头
- 建立世界观核心矛盾
- 确立主线目标
- 结尾钩子：真正的大秘密/大威胁刚刚露头""",
        }
        return guides.get(chapter_number, guides[1])

    def _small_climax_guidance(self, chapter_number: int, style_type: str) -> str:
        return f"""【第{chapter_number}章 — 小爽点章节】
写作目标：解决一个阶段性问题，让读者获得满足感。
- 收掉1-2个前面埋的小伏笔
- 主角实力或地位有小幅提升
- 打脸：让曾经看不起主角的人吃瘪
- 结尾：暗示更大的挑战即将来临
- 节奏：前紧后松，结尾留钩"""

    def _big_climax_guidance(self, chapter_number: int, style_type: str) -> str:
        return f"""【第{chapter_number}章 — 大高潮章节！！！】
写作目标：全篇最爽的章节之一，读者拍案叫绝。
- 收掉前面埋的主要伏笔
- 主角实力跨越式提升（突破大境界/获得至宝/击败强敌）
- 群像震惊：多角度描写旁观者的震撼反应
- 世界观拓展：揭示更深层的秘密
- 场面要宏大，情绪要饱满
- 适当虐后再爽：先抑后扬
- 结尾：为下一个大篇章埋下新伏笔"""

    def _regular_guidance(self, chapter_number: int) -> str:
        return f"""【第{chapter_number}章 — 常规推进章节】
写作目标：推动剧情、铺垫伏笔、丰富角色。
- 单章五步法：抛出矛盾 → 拉高仇恨 → 主角出手 → 全场反应 → 结尾留钩
- 至少推进一条支线剧情
- 至少展示一个角色侧面
- 语言简洁有力，避免流水账
- 结尾必须有钩子"""

    def get_satisfaction_tracking_prompt(self, recent_chapters_summary: str, chapter_number: int) -> str:
        return f"""检查最近几章是否满足小说节奏要求：
- 第{chapter_number}章是{self.get_chapter_type(chapter_number).value}章节
- 判断爽点密度是否足够
- 检查是否有连续压抑超过3章的情况
- 检查钩子是否每章都有

最近章节摘要：
{recent_chapters_summary}

请给出节奏评估和改进建议。"""


_rhythm_controller: Optional[RhythmController] = None


def get_rhythm_controller() -> RhythmController:
    global _rhythm_controller
    if _rhythm_controller is None:
        _rhythm_controller = RhythmController()
    return _rhythm_controller
