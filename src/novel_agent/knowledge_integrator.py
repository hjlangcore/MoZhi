"""知识注入器 — 联网搜索 + LLM分析 + 写入小说

完整流程：
  上下文提取 → 关键词生成 → 联网搜索 → LLM分析提炼 → 注入写作Prompt
"""
from typing import List, Dict, Any, Optional
from loguru import logger

from src.novel_agent.web_search import get_web_searcher, SearchResult


# 搜索关键词生成 Prompt
KEYWORD_EXTRACTION_PROMPT = """你是一位资深小说编辑。根据以下小说信息，生成3个值得联网搜索查资料的关键词，用于丰富小说细节。

【小说标题】{novel_title}
【世界观】{world_setting}
【修炼体系】{power_system}
【当前进度】第{chapter_number}章，已写{total_words}字
【上一章结尾】{last_ending}
【当前卷目标】{volume_goal}

请输出3个搜索关键词，每行一个。关键词要具体、可搜索，例如：
- 如果涉及炼丹 → "古代炼丹术 步骤 材料 名称"
- 如果涉及战斗 → "中国古代兵器 真实格斗技法"
- 如果涉及势力 → "古代门派制度 组织结构"
- 如果涉及境界突破 → "道家修炼 境界划分 典籍"

只输出关键词，不要编号或其他内容。"""


# 搜索结果分析提炼 Prompt
KNOWLEDGE_ANALYSIS_PROMPT = """你是一位专业的小说素材研究员。请分析以下网络搜索结果，提炼出可以用于小说写作的具体素材。

【小说背景】{novel_context}

【搜索结果】
{search_results}

请从搜索结果中提取以下内容（用中文回答）：

## 可用的细节描写
- 从搜索结果中提取的具体场景、物品、动作的描写素材（2-3条）

## 专业术语/概念
- 可以借用的专业术语或概念，让小说更真实（2-3个）

## 可融入的情节元素
- 搜索结果中提到的有趣事实，可以改编为情节元素（1-2个）

## 世界观补充
- 可以丰富小说世界观的真实参照（1-2条）

请直接输出实用素材，不要评论搜索结果的质量。如果没有找到相关内容，就如实说"无相关素材"。
"""


class KnowledgeIntegrator:
    """知识注入器：连接搜索→分析→写作的完整管线"""

    def __init__(self):
        self.searcher = get_web_searcher()

    def extract_search_keywords(
        self,
        llm_generate,
        novel_title: str = "",
        world_setting: str = "",
        power_system: str = "",
        chapter_number: int = 0,
        total_words: int = 0,
        last_ending: str = "",
        volume_goal: str = ""
    ) -> List[str]:
        """用 LLM 从小说上下文中提取搜索关键词"""
        prompt = KEYWORD_EXTRACTION_PROMPT.format(
            novel_title=novel_title,
            world_setting=world_setting[:500],
            power_system=power_system[:300],
            chapter_number=chapter_number,
            total_words=total_words,
            last_ending=last_ending[:300],
            volume_goal=volume_goal[:300],
        )

        try:
            response = llm_generate(prompt, temperature=0.3)
            keywords = [line.strip() for line in response.strip().split("\n")
                       if line.strip() and not line.strip().startswith("#")]
            # 过滤掉太短或太泛的关键词
            keywords = [k for k in keywords if len(k) >= 4]
            logger.info(f"Extracted {len(keywords)} search keywords: {keywords[:5]}")
            return keywords[:5]
        except Exception as e:
            logger.warning(f"Keyword extraction failed: {e}")
            return []

    def search_and_collect(self, keywords: List[str], max_per_keyword: int = 3) -> List[SearchResult]:
        """执行搜索并收集结果"""
        if not keywords:
            return []
        return self.searcher.search_multi(keywords, max_per_keyword)

    def analyze_results(
        self,
        llm_generate,
        search_results: List[SearchResult],
        novel_context: str
    ) -> str:
        """用 LLM 分析搜索结果，提炼可用的写作素材"""
        if not search_results:
            return ""

        # 格式化搜索结果
        results_text = "\n\n".join([
            f"[{i+1}] 标题：{r.title}\n来源：{r.url}\n摘要：{r.snippet}"
            for i, r in enumerate(search_results[:10])
        ])

        prompt = KNOWLEDGE_ANALYSIS_PROMPT.format(
            novel_context=novel_context[:1000],
            search_results=results_text[:3000],
        )

        try:
            analysis = llm_generate(prompt, temperature=0.3)
            logger.info(f"Knowledge analysis completed: {len(analysis)} chars")
            return analysis
        except Exception as e:
            logger.warning(f"Knowledge analysis failed: {e}")
            # 分析失败时直接返回原始摘要
            return self._fallback_summary(search_results)

    def _fallback_summary(self, results: List[SearchResult]) -> str:
        """LLM 分析失败时的回退：直接拼接搜索摘要"""
        lines = ["## 网络参考资料\n"]
        for r in results[:5]:
            lines.append(f"- {r.snippet[:200]}")
        return "\n".join(lines)

    def build_knowledge_injection(self, analysis: str, search_results: List[SearchResult]) -> str:
        """构建注入写作 prompt 的知识块"""
        if not analysis:
            return ""

        parts = ["\n\n【联网参考资料 — 请合理融入本章内容】\n"]
        parts.append(analysis)

        if search_results:
            parts.append("\n参考来源：")
            for r in search_results[:5]:
                parts.append(f"- {r.title}: {r.url}")

        return "\n".join(parts)

    def run_pipeline(
        self,
        llm_generate,
        novel_title: str = "",
        world_setting: str = "",
        power_system: str = "",
        chapter_number: int = 0,
        total_words: int = 0,
        last_ending: str = "",
        volume_goal: str = "",
        force_keywords: Optional[List[str]] = None,
    ) -> str:
        """执行完整管线：关键词→搜索→分析→知识块

        Returns:
            可直接追加到写作 prompt 的知识字符串，如果搜索无结果则返回空字符串
        """
        # Step 1: 提取关键词
        if force_keywords:
            keywords = force_keywords
            logger.info(f"Using forced keywords: {keywords}")
        else:
            keywords = self.extract_search_keywords(
                llm_generate=llm_generate,
                novel_title=novel_title,
                world_setting=world_setting,
                power_system=power_system,
                chapter_number=chapter_number,
                total_words=total_words,
                last_ending=last_ending,
                volume_goal=volume_goal,
            )

        if not keywords:
            return ""

        # Step 2: 搜索
        results = self.search_and_collect(keywords)
        if not results:
            logger.info("No search results found")
            return ""

        # Step 3: LLM 分析提炼
        novel_context = f"《{novel_title}》第{chapter_number}章\n世界观：{world_setting}\n修炼体系：{power_system}\n当前卷目标：{volume_goal}"
        analysis = self.analyze_results(llm_generate, results, novel_context)

        # Step 4: 构建注入块
        knowledge = self.build_knowledge_injection(analysis, results)
        logger.info(f"Knowledge pipeline complete: {len(keywords)} keywords → {len(results)} results → {len(analysis)} chars analysis")
        return knowledge


_integrator: Optional[KnowledgeIntegrator] = None


def get_knowledge_integrator() -> KnowledgeIntegrator:
    global _integrator
    if _integrator is None:
        _integrator = KnowledgeIntegrator()
    return _integrator