"""联网搜索模块 — 支持多引擎搜索，为小说创作提供参考资料"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from loguru import logger
import re
import urllib.parse

from src.core.network_client import get_network_client


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str = "web"


class WebSearcher:
    """多引擎联网搜索器"""

    def __init__(self):
        self.network = get_network_client()
        self._ddgs = None  # lazy import duckduckgo_search

    def _get_ddgs(self):
        if self._ddgs is None:
            try:
                from ddgs import DDGS
                self._ddgs = DDGS()
            except ImportError:
                try:
                    from duckduckgo_search import DDGS
                    self._ddgs = DDGS()
                except ImportError:
                    logger.warning("ddgs/duckduckgo_search not installed, using HTML fallback")
                    self._ddgs = False
        return self._ddgs if self._ddgs is not False else None

    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """搜索并返回结构化结果，自动选择最佳引擎"""
        # 优先用 duckduckgo_search 库
        ddgs = self._get_ddgs()
        if ddgs:
            try:
                return self._search_ddgs_lib(ddgs, query, max_results)
            except Exception as e:
                logger.warning(f"DDGS library search failed: {e}, falling back to HTML")

        # 回退到 HTML 抓取
        return self._search_ddg_html(query, max_results)

    def _search_ddgs_lib(self, ddgs, query: str, max_results: int) -> List[SearchResult]:
        results = []
        try:
            for r in ddgs.text(query, max_results=max_results):
                results.append(SearchResult(
                    title=r.get("title", ""),
                    url=r.get("href", ""),
                    snippet=r.get("body", ""),
                ))
        except Exception as e:
            logger.error(f"DDGS error: {e}")
            raise
        logger.info(f"Web search '{query}': {len(results)} results (DDGS library)")
        return results

    def _search_ddg_html(self, query: str, max_results: int) -> List[SearchResult]:
        """通过 DuckDuckGo HTML 端点搜索（无需 API key）"""
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        results = []

        try:
            status, html, _ = self.network.get(url)
            if status != 200:
                logger.error(f"DuckDuckGo HTML search failed: HTTP {status}")
                return results

            # 解析 HTML 搜索结果
            result_blocks = re.findall(
                r'<a rel="nofollow" class="result__a" href="([^"]+)".*?>(.*?)</a>.*?<a class="result__snippet".*?>(.*?)</a>',
                html, re.DOTALL
            )

            for href, title_raw, snippet_raw in result_blocks[:max_results]:
                title = re.sub(r'<[^>]+>', '', title_raw).strip()
                snippet = re.sub(r'<[^>]+>', '', snippet_raw).strip()
                # DDG HTML 返回的链接是重定向链接，提取真实 URL
                real_url = urllib.parse.parse_qs(urllib.parse.urlparse(href).query).get("uddg", [href])[0]
                results.append(SearchResult(
                    title=title,
                    url=real_url,
                    snippet=snippet,
                ))

        except Exception as e:
            logger.error(f"DuckDuckGo HTML parse error: {e}")

        logger.info(f"Web search '{query}': {len(results)} results (DDG HTML)")
        return results

    def search_multi(self, queries: List[str], max_per_query: int = 3) -> List[SearchResult]:
        """批量搜索多个关键词并去重"""
        seen_urls = set()
        all_results = []

        for query in queries:
            try:
                results = self.search(query, max_per_query)
                for r in results:
                    if r.url not in seen_urls:
                        seen_urls.add(r.url)
                        all_results.append(r)
            except Exception as e:
                logger.warning(f"Search failed for '{query}': {e}")

        return all_results


_web_searcher: Optional[WebSearcher] = None


def get_web_searcher() -> WebSearcher:
    global _web_searcher
    if _web_searcher is None:
        _web_searcher = WebSearcher()
    return _web_searcher