from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from loguru import logger
import json
import re
from collections import namedtuple

from src.novel_agent.ai_site_scraper import get_ai_site_scraper
from src.novel_agent.memory import get_memory_manager


KnowledgeItem = namedtuple('KnowledgeItem', ['id', 'content', 'source', 'relevance', 'category', 'added_at'])


class KnowledgeProcessor:
    def __init__(self):
        self.ai_site_scraper = get_ai_site_scraper()
        self.memory_manager = get_memory_manager()
        self.knowledge_base: Dict[str, KnowledgeItem] = {}
        self.processed_queries = set()

    def search_and_process(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        if query in self.processed_queries:
            logger.info(f"Query already processed: {query}")
            return self._get_cached_results(query)

        logger.info(f"Processing knowledge query: {query}")
        
        results = []
        sites = ["deepseek", "grok"]
        
        for site in sites:
            try:
                result = self.ai_site_scraper.search_knowledge(query, site)
                
                if result.get("success"):
                    processed = self._process_search_result(result, query)
                    results.extend(processed)
                    
                    for item in processed:
                        self._store_knowledge(item)
            except Exception as e:
                logger.error(f"Error processing {site}: {e}")

        self.processed_queries.add(query)
        
        return sorted(results, key=lambda x: x['relevance'], reverse=True)[:max_results]

    def _process_search_result(self, result: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
        processed = []
        
        if 'results' in result:
            for i, item in enumerate(result['results'][:3]):
                processed.append({
                    "id": f"{result['site']}_{i}",
                    "content": self._extract_key_content(item),
                    "source": result['site'],
                    "relevance": self._calculate_relevance(item, query),
                    "category": self._determine_category(query),
                    "raw_data": item,
                    "added_at": datetime.now().isoformat()
                })
        elif 'raw_content' in result:
            processed.append({
                "id": f"{result['site']}_0",
                "content": result['raw_content'],
                "source": result['site'],
                "relevance": 0.7,
                "category": self._determine_category(query),
                "added_at": datetime.now().isoformat()
            })
        
        return processed

    def _extract_key_content(self, item: Dict[str, Any]) -> str:
        if isinstance(item, dict):
            content = item.get('content', '') or item.get('text', '') or item.get('summary', '')
        else:
            content = str(item)
        
        return content[:500] if len(content) > 500 else content

    def _calculate_relevance(self, item: Dict[str, Any], query: str) -> float:
        content = self._extract_key_content(item).lower()
        query_terms = query.lower().split()
        
        match_count = sum(1 for term in query_terms if term in content)
        return min(1.0, match_count / len(query_terms))

    def _determine_category(self, query: str) -> str:
        categories = {
            '写作技巧': ['写作', '技巧', '方法', '如何', '怎么'],
            '情节构思': ['情节', '故事', '剧情', '构思', '人物'],
            '知识查询': ['什么是', '定义', '解释', '资料', '研究'],
            '创意灵感': ['灵感', '创意', '想法', '点子'],
            '历史文化': ['历史', '文化', '古代', '传统'],
            '科学技术': ['科学', '技术', '原理', '机制']
        }
        
        for category, keywords in categories.items():
            if any(keyword in query for keyword in keywords):
                return category
        
        return '其他'

    def _store_knowledge(self, item: Dict[str, Any]):
        knowledge_item = KnowledgeItem(
            id=item['id'],
            content=item['content'],
            source=item['source'],
            relevance=item['relevance'],
            category=item['category'],
            added_at=datetime.now()
        )
        self.knowledge_base[item['id']] = knowledge_item
        
        self.memory_manager.add_knowledge(
            item['content'],
            item['category'],
            item['source']
        )

    def _get_cached_results(self, query: str) -> List[Dict[str, Any]]:
        results = []
        for item in self.knowledge_base.values():
            if query.lower() in item.content.lower():
                results.append({
                    "id": item.id,
                    "content": item.content,
                    "source": item.source,
                    "relevance": item.relevance,
                    "category": item.category,
                    "added_at": item.added_at.isoformat()
                })
        return results

    def integrate_into_novel(self, knowledge_items: List[Dict[str, Any]], context: str) -> str:
        if not knowledge_items:
            return context

        integrated = context + "\n\n【参考资料】\n"
        
        for item in knowledge_items:
            source_label = {"deepseek": "DeepSeek", "grok": "Grok"}.get(item['source'], item['source'])
            integrated += f"- [{source_label}] {item['content'][:200]}...\n"
        
        return integrated

    def get_knowledge_by_category(self, category: str) -> List[Dict[str, Any]]:
        results = []
        for item in self.knowledge_base.values():
            if item.category == category:
                results.append({
                    "id": item.id,
                    "content": item.content,
                    "source": item.source,
                    "relevance": item.relevance,
                    "category": item.category,
                    "added_at": item.added_at.isoformat()
                })
        return sorted(results, key=lambda x: x['relevance'], reverse=True)

    def get_all_knowledge(self) -> List[Dict[str, Any]]:
        results = []
        for item in self.knowledge_base.values():
            results.append({
                "id": item.id,
                "content": item.content,
                "source": item.source,
                "relevance": item.relevance,
                "category": item.category,
                "added_at": item.added_at.isoformat()
            })
        return sorted(results, key=lambda x: x['added_at'], reverse=True)

    def delete_knowledge(self, knowledge_id: str) -> bool:
        if knowledge_id in self.knowledge_base:
            del self.knowledge_base[knowledge_id]
            logger.info(f"Deleted knowledge: {knowledge_id}")
            return True
        return False

    def clear_knowledge(self):
        self.knowledge_base.clear()
        self.processed_queries.clear()
        logger.info("Knowledge base cleared")

    def get_knowledge_stats(self) -> Dict[str, Any]:
        category_counts = {}
        for item in self.knowledge_base.values():
            category_counts[item.category] = category_counts.get(item.category, 0) + 1
        
        return {
            "total_items": len(self.knowledge_base),
            "categories": category_counts,
            "processed_queries": len(self.processed_queries)
        }


_knowledge_processor: Optional[KnowledgeProcessor] = None


def get_knowledge_processor() -> KnowledgeProcessor:
    global _knowledge_processor
    if _knowledge_processor is None:
        _knowledge_processor = KnowledgeProcessor()
    return _knowledge_processor
