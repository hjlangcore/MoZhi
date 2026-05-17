"""Web Fetch 模块 — 网页内容抓取 + 正文提取 + LLM摘要

借鉴 Claude Code 的 WebFetch 功能设计：
  1. 抓取网页 HTML
  2. 提取正文内容（去广告/导航/脚本）
  3. 可选 LLM 摘要分析
  4. 集成到知识管线
"""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from loguru import logger
import re
import urllib.parse

from src.core.network_client import get_network_client


@dataclass
class FetchedPage:
    url: str
    title: str = ""
    content: str = ""           # 提取后的纯文本
    raw_length: int = 0         # 原始HTML长度
    content_length: int = 0     # 提取后文本长度
    fetch_time: datetime = field(default_factory=datetime.now)
    success: bool = False
    error: str = ""


class WebFetcher:
    """网页内容抓取器"""

    def __init__(self):
        self.network = get_network_client()
        self.cache: Dict[str, FetchedPage] = {}
        self.cache_max_age = 3600  # 1小时缓存

    def fetch(self, url: str, use_cache: bool = True) -> FetchedPage:
        """抓取并提取网页正文

        Args:
            url: 目标URL
            use_cache: 是否使用缓存
        """
        # 检查缓存
        if use_cache and url in self.cache:
            cached = self.cache[url]
            age = (datetime.now() - cached.fetch_time).total_seconds()
            if age < self.cache_max_age:
                logger.debug(f"Using cached page: {url}")
                return cached

        logger.info(f"Fetching: {url[:80]}...")
        try:
            status, html, headers = self.network.get(url)
            if status != 200:
                return FetchedPage(url=url, success=False, error=f"HTTP {status}")

            title = self._extract_title(html)
            content = self._extract_content(html)

            page = FetchedPage(
                url=url,
                title=title,
                content=content,
                raw_length=len(html),
                content_length=len(content),
                success=True,
            )

            self.cache[url] = page
            logger.info(f"Fetched: {title[:40]} ({len(content)} chars extracted)")
            return page

        except Exception as e:
            logger.error(f"Fetch failed for {url[:60]}: {e}")
            return FetchedPage(url=url, success=False, error=str(e))

    def fetch_and_summarize(
        self,
        url: str,
        llm_generate=None,
        max_summary_chars: int = 500,
    ) -> Dict[str, Any]:
        """抓取网页并用LLM生成摘要"""
        page = self.fetch(url)
        if not page.success:
            return {"success": False, "error": page.error, "url": url}

        result = {
            "success": True,
            "url": url,
            "title": page.title,
            "content_length": page.content_length,
            "content_preview": page.content[:1000],
        }

        if llm_generate and page.content_length > 200:
            try:
                summary_prompt = f"""请阅读以下网页内容，用3-5句话总结对小说创作有用的关键信息（200字以内）：

网页标题：{page.title}
网页内容：
{page.content[:3000]}

只输出摘要。"""
                summary = llm_generate(summary_prompt, temperature=0.3)
                result["summary"] = summary.strip()
            except Exception as e:
                logger.warning(f"Summarization failed: {e}")
                result["summary"] = page.content[:max_summary_chars]

        return result

    def batch_fetch(self, urls: List[str], max_concurrent: int = 3) -> List[FetchedPage]:
        """批量抓取（顺序执行，限速）"""
        results = []
        for url in urls[:max_concurrent]:
            page = self.fetch(url)
            results.append(page)
        return results

    # ============================================================
    # HTML 正文提取
    # ============================================================
    @staticmethod
    def _extract_title(html: str) -> str:
        match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        if match:
            title = re.sub(r'<[^>]+>', '', match.group(1)).strip()
            # 去除站点后缀
            title = re.sub(r'\s*[-|]\s*[^|]*$', '', title)
            return title[:150]
        return ""

    @staticmethod
    def _extract_content(html: str) -> str:
        """从HTML中提取正文内容"""
        # 移除不需要的元素
        for tag in ['script', 'style', 'nav', 'header', 'footer', 'aside',
                     'noscript', 'iframe', 'form', 'button']:
            html = re.sub(f'<{tag}[^>]*>.*?</{tag}>', '', html, flags=re.DOTALL | re.IGNORECASE)

        # 移除注释
        html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)

        # 提取 body 内容
        body_match = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL | re.IGNORECASE)
        if body_match:
            html = body_match.group(1)

        # 移除所有HTML标签
        text = re.sub(r'<[^>]+>', ' ', html)

        # 清理空白
        text = re.sub(r'&nbsp;', ' ', text)
        text = re.sub(r'&amp;', '&', text)
        text = re.sub(r'&lt;', '<', text)
        text = re.sub(r'&gt;', '>', text)
        text = re.sub(r'&quot;', '"', text)
        text = re.sub(r'&#?\w+;', ' ', text)

        # 合并空白行
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'\n{3,}', '\n\n', text)

        # 去除过短的行（通常是导航残留）
        lines = [line.strip() for line in text.split('\n')]
        lines = [line for line in lines if len(line) > 20 or line.endswith(('。', '！', '？', '」'))]

        return '\n'.join(lines).strip()

    def clear_cache(self):
        self.cache.clear()


_fetcher: Optional[WebFetcher] = None


def get_web_fetcher() -> WebFetcher:
    global _fetcher
    if _fetcher is None:
        _fetcher = WebFetcher()
    return _fetcher
