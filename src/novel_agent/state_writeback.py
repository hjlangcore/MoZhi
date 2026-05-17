"""状态回写管线 + 上下文压缩 — T2 特性

借鉴天命的状态回写机制和 kimi-writer 的上下文压缩：

状态回写 (State Write-back Pipeline):
  每章写完后 → LLM提取状态变更 → 写回角色卡/知识库 → 记录变更日志

上下文压缩 (Context Compression):
  Token预算紧张时 → 将旧章节压缩为摘要 → 保留近期完整内容
"""
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from loguru import logger

from src.novel_agent.state import (
    NovelState, ChapterModel, StateChange, CharacterModel,
    NovelKnowledgeBase
)


# 状态变更提取 Prompt
STATE_EXTRACTION_PROMPT = """你是一位细心的故事分析师。请从以下章节中提取角色的状态变化。

【章节内容】
{chapter_content}

【已知角色及其当前状态】
{known_characters}

请以JSON格式输出本章中发生变化的角色状态：
{{
    "changes": [
        {{
            "character_name": "角色名",
            "field": "current_realm/current_location/health/alive/current_goal",
            "old_value": "变化前的值（未知则填'未知'）",
            "new_value": "变化后的值",
            "reason": "变化原因（引用章节中的具体情节）"
        }}
    ],
    "new_characters_introduced": ["新角色名"],
    "relationships_changed": [
        {{
            "character_a": "角色A",
            "character_b": "角色B",
            "change_description": "关系变化描述"
        }}
    ]
}}

只输出JSON，不要其他内容。"""


# 上下文压缩 Prompt
COMPRESSION_PROMPT = """请将以下章节内容压缩为一段简洁的摘要（100字以内），保留关键剧情点和角色状态：

【第{chapter_number}章《{chapter_title}》】
{chapter_content}

【压缩要求】
- 保留核心情节推进
- 保留角色重要行动和决定
- 保留关键对话或转折
- 保留结尾钩子
- 格式：第{chapter_number}章《{chapter_title}》：<摘要>

只输出一段摘要。"""


@dataclass
class CompressedContext:
    """压缩后的上下文"""
    chapter_number: int
    title: str
    summary: str
    original_length: int
    compressed_at: datetime = field(default_factory=datetime.now)


class StateWritebackPipeline:
    """状态回写管线

    每章写完后自动运行，将故事中发生的变化同步到知识库。
    """

    def __init__(self):
        self.compressed_chapters: Dict[int, CompressedContext] = {}

    # ============================================================
    # 状态回写
    # ============================================================
    def extract_and_writeback(
        self,
        llm_generate: Callable,
        chapter: ChapterModel,
        novel_state: NovelState,
    ) -> List[StateChange]:
        """从章节内容提取状态变更，写回知识库

        Returns:
            提取到的 StateChange 列表
        """
        kb = novel_state.knowledge_base

        # 构建已知角色列表
        known_chars_str = "\n".join([
            kb.get_character_context(name)
            for name in kb.characters.keys()
        ]) or "暂无已知角色"

        prompt = STATE_EXTRACTION_PROMPT.format(
            chapter_content=chapter.content[:3000],
            known_characters=known_chars_str[:1000],
        )

        changes: List[StateChange] = []
        try:
            import json, re
            response = llm_generate(prompt, temperature=0.2)
            json_match = re.search(r'\{[\s\S]*\}', response)
            if not json_match:
                logger.warning("State extraction: no JSON found in LLM response")
                return changes

            data = json.loads(json_match.group())

            # 处理状态变更
            for change_data in data.get("changes", []):
                name = change_data.get("character_name", "")
                field = change_data.get("field", "")
                old_val = str(change_data.get("old_value", ""))
                new_val = str(change_data.get("new_value", ""))
                reason = change_data.get("reason", "")

                if not name or not field:
                    continue

                # 写回知识库
                sc = kb.update_character_state(name, **{field: new_val})
                if sc:
                    sc.chapter_number = chapter.chapter_number
                    sc.old_value = old_val
                    sc.reason = reason
                    changes.append(sc)
                    novel_state.state_changes.append(sc)
                    logger.info(f"State writeback: {name}.{field} = {new_val} (was: {old_val})")

            # 处理新角色
            for new_name in data.get("new_characters_introduced", []):
                if new_name and new_name not in kb.characters:
                    kb.characters[new_name] = CharacterModel(
                        name=new_name,
                        role="待确认",
                        description="",
                        first_appearance_chapter=chapter.chapter_number,
                        last_appearance_chapter=chapter.chapter_number,
                        total_appearances=1,
                    )
                    logger.info(f"New character added to KB: {new_name}")

            # 更新出场角色
            kb.add_character_appearance(
                novel_state.setting.main_character.name if novel_state.setting and novel_state.setting.main_character else "",
                chapter.chapter_number
            )

        except Exception as e:
            logger.warning(f"State writeback failed: {e}")

        return changes

    # ============================================================
    # 上下文压缩
    # ============================================================
    def compress_chapter(
        self,
        llm_generate: Callable,
        chapter: ChapterModel,
    ) -> CompressedContext:
        """将单章压缩为摘要"""
        prompt = COMPRESSION_PROMPT.format(
            chapter_number=chapter.chapter_number,
            chapter_title=chapter.title,
            chapter_content=chapter.content[:2000],
        )

        try:
            summary = llm_generate(prompt, temperature=0.3).strip()
        except Exception as e:
            logger.warning(f"Compression failed for ch{chapter.chapter_number}: {e}")
            summary = f"第{chapter.chapter_number}章《{chapter.title}》：{chapter.content[:200]}..."

        cc = CompressedContext(
            chapter_number=chapter.chapter_number,
            title=chapter.title,
            summary=summary,
            original_length=len(chapter.content),
        )

        self.compressed_chapters[chapter.chapter_number] = cc
        logger.info(f"Compressed ch{chapter.chapter_number}: {len(chapter.content)} → {len(summary)} chars")
        return cc

    def build_compressed_context(
        self,
        current_chapter: int,
        novel_state: NovelState,
        recent_chapters_full: int = 3,
        max_compressed_chars: int = 3000,
    ) -> str:
        """构建压缩后的上下文

        策略：
        - 最近 N 章保留完整内容
        - 更早的章节用压缩摘要
        - 总长度控制在 max_compressed_chars 限制内

        Returns:
            可注入 Prompt 的压缩上下文字符串
        """
        parts = []
        char_count = 0

        # 最近章节：完整内容
        for ch in novel_state.chapters[-recent_chapters_full:]:
            if ch.chapter_number >= current_chapter:
                continue
            snippet = f"第{ch.chapter_number}章「{ch.title}」：{ch.content[-500:]}"
            parts.append(("recent", snippet, len(snippet)))

        # 更早章节：压缩摘要
        for ch_num, cc in sorted(self.compressed_chapters.items()):
            if ch_num >= current_chapter - recent_chapters_full:
                continue
            parts.append(("compressed", cc.summary, len(cc.summary)))

        # 按 token 预算截断
        result_parts = []
        for ptype, text, length in parts:
            if char_count + length > max_compressed_chars:
                break
            if ptype == "compressed":
                result_parts.append(text)
            else:
                result_parts.append(text)
            char_count += length

        context = "\n\n".join(result_parts)
        logger.info(
            f"Built compressed context for ch{current_chapter}: "
            f"{len(result_parts)} entries, {len(context)} chars"
        )
        return context

    # ============================================================
    # 完整 T2 管线
    # ============================================================
    def run_pipeline(
        self,
        llm_generate: Callable,
        chapter: ChapterModel,
        novel_state: NovelState,
        compress: bool = True,
    ) -> Dict[str, Any]:
        """执行完整的 T2 管线：状态回写 + 上下文压缩

        Returns:
            {"changes": [...], "compressed": CompressedContext或None}
        """
        # 状态回写
        changes = self.extract_and_writeback(llm_generate, chapter, novel_state)

        # 上下文压缩（每10章或字数过多时触发）
        compressed = None
        if compress and (
            chapter.chapter_number % 10 == 0
            or novel_state.total_words > 100000
        ):
            compressed = self.compress_chapter(llm_generate, chapter)

        return {
            "changes": changes,
            "compressed": compressed,
            "total_changes_tracked": len(novel_state.state_changes),
            "compressed_chapters": len(self.compressed_chapters),
        }


_pipeline: Optional[StateWritebackPipeline] = None


def get_state_writeback() -> StateWritebackPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = StateWritebackPipeline()
    return _pipeline
