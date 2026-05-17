from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from loguru import logger
import re
from collections import Counter

from src.novel_agent.ai_site_scraper import get_ai_site_scraper
from src.novel_agent.continuity_checker import get_continuity_checker
from src.novel_agent.duplicate_detector import get_duplicate_detector


class TriggerManager:
    def __init__(self):
        self.ai_site_scraper = get_ai_site_scraper()
        self.continuity_checker = get_continuity_checker()
        self.duplicate_detector = get_duplicate_detector()
        self.enabled = True
        self.auto_triggers = []
        self.manual_triggers = []
        self.trigger_history = []
        
        self._register_default_triggers()

    def _register_default_triggers(self):
        self.auto_triggers.append({
            "name": "repetition_detection",
            "description": "检测内容重复",
            "check_func": self._check_repetition,
            "threshold": 0.3,
            "enabled": True
        })
        
        self.auto_triggers.append({
            "name": "continuity_issue",
            "description": "检测连贯性问题",
            "check_func": self._check_continuity,
            "threshold": 0.5,
            "enabled": True
        })
        
        self.auto_triggers.append({
            "name": "creative_block",
            "description": "检测创作瓶颈",
            "check_func": self._check_creative_block,
            "threshold": 0.6,
            "enabled": True
        })
        
        self.auto_triggers.append({
            "name": "knowledge_gap",
            "description": "检测知识缺口",
            "check_func": self._check_knowledge_gap,
            "threshold": 0.4,
            "enabled": True
        })

    def _check_repetition(self, content: str, context: Dict[str, Any]) -> float:
        result = self.duplicate_detector.check_chapter_duplicates(content, context.get('previous_content', ''))
        return result.get('similarity', 0)

    def _check_continuity(self, content: str, context: Dict[str, Any]) -> float:
        previous_content = context.get('previous_content', '')
        if not previous_content:
            return 0.0

        result = self.continuity_checker.check_chapter_continuity
        # Use similarity-based basic check since we don't have full novel state here
        from src.novel_agent.utils import calculate_text_similarity
        similarity = calculate_text_similarity(previous_content[-500:] if len(previous_content) > 500 else previous_content,
                                                content[:500] if len(content) > 500 else content)
        issues = 0.0 if similarity > 0.3 else 0.5
        return issues

    def _check_creative_block(self, content: str, context: Dict[str, Any]) -> float:
        indicators = []
        
        word_count = len(content.split())
        if word_count < 50:
            indicators.append(0.8)
        
        question_ratio = content.count('?') / max(len(content.split()), 1)
        if question_ratio > 0.1:
            indicators.append(0.7)
        
        hesitation_patterns = ['不知道', '怎么', '如何', '应该', '可能']
        hesitation_count = sum(content.count(pattern) for pattern in hesitation_patterns)
        if hesitation_count > 3:
            indicators.append(0.6)
        
        if not indicators:
            return 0.0
        
        return sum(indicators) / len(indicators)

    def _check_knowledge_gap(self, content: str, context: Dict[str, Any]) -> float:
        gap_indicators = ['需要', '查一下', '了解', '研究', '参考', '资料']
        gap_count = sum(content.count(indicator) for indicator in gap_indicators)
        
        if gap_count == 0:
            return 0.0
        
        return min(1.0, gap_count * 0.25)

    def check_all_triggers(self, content: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []

        triggered = []
        
        for trigger in self.auto_triggers:
            if not trigger['enabled']:
                continue
            
            try:
                score = trigger['check_func'](content, context)
                
                if score >= trigger['threshold']:
                    triggered.append({
                        "name": trigger['name'],
                        "description": trigger['description'],
                        "score": score,
                        "threshold": trigger['threshold'],
                        "triggered_at": datetime.now().isoformat()
                    })
                    logger.info(f"Trigger activated: {trigger['name']} (score: {score})")
            except Exception as e:
                logger.error(f"Error checking trigger {trigger['name']}: {e}")

        return triggered

    def trigger_knowledge_search(self, query: str, site: str = "deepseek") -> Dict[str, Any]:
        logger.info(f"Manual knowledge search triggered: {query}")
        
        result = self.ai_site_scraper.search_knowledge(query, site)
        
        self.trigger_history.append({
            "type": "manual",
            "query": query,
            "site": site,
            "success": result.get("success", False),
            "timestamp": datetime.now().isoformat()
        })
        
        return result

    def auto_trigger_search(self, triggers: List[Dict[str, Any]], content: str) -> List[Dict[str, Any]]:
        results = []
        
        for trigger in triggers:
            queries = self._generate_queries(trigger, content)
            
            for query in queries[:3]:
                result = self.ai_site_scraper.search_knowledge(query)
                
                self.trigger_history.append({
                    "type": "auto",
                    "trigger": trigger['name'],
                    "query": query,
                    "success": result.get("success", False),
                    "timestamp": datetime.now().isoformat()
                })
                
                results.append(result)
        
        return results

    def _generate_queries(self, trigger: Dict[str, Any], content: str) -> List[str]:
        queries = []
        
        if trigger['name'] == 'repetition_detection':
            keywords = self._extract_keywords(content)
            queries = [f"如何避免写作重复内容", f"写作技巧 避免重复描写"]
        
        elif trigger['name'] == 'continuity_issue':
            queries = [f"小说情节连贯性技巧", f"如何保持故事逻辑连贯"]
        
        elif trigger['name'] == 'creative_block':
            queries = [f"写作灵感激发方法", f"克服创作瓶颈技巧"]
        
        elif trigger['name'] == 'knowledge_gap':
            keywords = self._extract_keywords(content)
            if keywords:
                queries = [f"{keywords[0]} 相关知识", f"{keywords[0]} 专业资料"]
        
        return queries

    def _extract_keywords(self, content: str) -> List[str]:
        words = re.findall(r'[\u4e00-\u9fa5]{2,}', content)
        counter = Counter(words)
        return [word for word, _ in counter.most_common(5)]

    def enable_trigger(self, trigger_name: str):
        for trigger in self.auto_triggers:
            if trigger['name'] == trigger_name:
                trigger['enabled'] = True
                logger.info(f"Trigger enabled: {trigger_name}")
                return True
        return False

    def disable_trigger(self, trigger_name: str):
        for trigger in self.auto_triggers:
            if trigger['name'] == trigger_name:
                trigger['enabled'] = False
                logger.info(f"Trigger disabled: {trigger_name}")
                return True
        return False

    def set_trigger_threshold(self, trigger_name: str, threshold: float):
        for trigger in self.auto_triggers:
            if trigger['name'] == trigger_name:
                trigger['threshold'] = max(0.0, min(1.0, threshold))
                logger.info(f"Threshold set for {trigger_name}: {threshold}")
                return True
        return False

    def set_enabled(self, enabled: bool):
        self.enabled = enabled
        logger.info(f"Auto-trigger system {'enabled' if enabled else 'disabled'}")

    def get_trigger_status(self) -> Dict[str, Any]:
        return {
            "system_enabled": self.enabled,
            "triggers": [{
                "name": t['name'],
                "description": t['description'],
                "enabled": t['enabled'],
                "threshold": t['threshold']
            } for t in self.auto_triggers],
            "trigger_history_count": len(self.trigger_history)
        }

    def get_trigger_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self.trigger_history[-limit:]


_trigger_manager: Optional[TriggerManager] = None


def get_trigger_manager() -> TriggerManager:
    global _trigger_manager
    if _trigger_manager is None:
        _trigger_manager = TriggerManager()
    return _trigger_manager
