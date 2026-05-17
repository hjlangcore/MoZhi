from typing import Optional, Dict, Any, List
from datetime import datetime
from loguru import logger
import json
import re
from urllib.parse import urljoin

from src.core.network_client import get_network_client
from src.core.proxy_manager import get_proxy_manager


class AISiteScraper:
    def __init__(self):
        self.network_client = get_network_client()
        self.proxy_manager = get_proxy_manager()
        self.visited_urls = set()
        self.last_access_time = {}
        self.request_interval = 5

    def _check_rate_limit(self, base_url: str) -> bool:
        now = datetime.now().timestamp()
        last_access = self.last_access_time.get(base_url, 0)
        
        if now - last_access < self.request_interval:
            return False
        
        self.last_access_time[base_url] = now
        return True

    def _get_proxy(self) -> Optional[str]:
        return self.proxy_manager.get_current_proxy()

    def _extract_text_content(self, html: str) -> str:
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def access_deepseek(self) -> Dict[str, Any]:
        url = "https://chat.deepseek.com/"
        
        if not self._check_rate_limit(url):
            logger.warning("Rate limit hit for deepseek")
            return {"success": False, "error": "Rate limit exceeded"}

        logger.info(f"Accessing DeepSeek: {url}")
        
        proxy = self._get_proxy()
        status_code, content, headers = self.network_client.get(url, proxy=proxy)
        
        if status_code != 200:
            logger.error(f"Failed to access DeepSeek: {status_code}")
            return {"success": False, "status_code": status_code, "error": "Failed to access"}

        self.visited_urls.add(url)
        
        return {
            "success": True,
            "url": url,
            "status_code": status_code,
            "content_length": len(content),
            "headers": dict(headers),
            "accessed_at": datetime.now().isoformat()
        }

    def access_grok(self) -> Dict[str, Any]:
        url = "https://grok.com/"
        
        if not self._check_rate_limit(url):
            logger.warning("Rate limit hit for grok")
            return {"success": False, "error": "Rate limit exceeded"}

        logger.info(f"Accessing Grok: {url}")
        
        proxy = self._get_proxy()
        status_code, content, headers = self.network_client.get(url, proxy=proxy)
        
        if status_code != 200:
            logger.error(f"Failed to access Grok: {status_code}")
            return {"success": False, "status_code": status_code, "error": "Failed to access"}

        self.visited_urls.add(url)
        
        return {
            "success": True,
            "url": url,
            "status_code": status_code,
            "content_length": len(content),
            "headers": dict(headers),
            "accessed_at": datetime.now().isoformat()
        }

    def search_knowledge(self, query: str, site: str = "deepseek") -> Dict[str, Any]:
        logger.info(f"Searching knowledge: {query} on {site}")
        
        if site == "deepseek":
            return self._search_deepseek(query)
        elif site == "grok":
            return self._search_grok(query)
        else:
            return {"success": False, "error": "Unknown site"}

    def _search_deepseek(self, query: str) -> Dict[str, Any]:
        url = "https://chat.deepseek.com/api/search"
        
        if not self._check_rate_limit("https://chat.deepseek.com/"):
            return {"success": False, "error": "Rate limit exceeded"}

        proxy = self._get_proxy()
        
        try:
            payload = {
                "query": query,
                "limit": 5
            }
            
            status_code, content, headers = self.network_client.post(
                url,
                json=payload,
                proxy=proxy
            )
            
            if status_code == 200:
                try:
                    data = json.loads(content)
                    return {
                        "success": True,
                        "query": query,
                        "site": "deepseek",
                        "results": data,
                        "accessed_at": datetime.now().isoformat()
                    }
                except json.JSONDecodeError:
                    return {
                        "success": True,
                        "query": query,
                        "site": "deepseek",
                        "raw_content": content[:500],
                        "accessed_at": datetime.now().isoformat()
                    }
            else:
                return {"success": False, "status_code": status_code}
                
        except Exception as e:
            logger.error(f"DeepSeek search error: {e}")
            return {"success": False, "error": str(e)}

    def _search_grok(self, query: str) -> Dict[str, Any]:
        url = "https://grok.com/search"
        
        if not self._check_rate_limit("https://grok.com/"):
            return {"success": False, "error": "Rate limit exceeded"}

        proxy = self._get_proxy()
        
        try:
            params = {
                "q": query,
                "limit": 5
            }
            
            status_code, content, headers = self.network_client.get(
                url,
                params=params,
                proxy=proxy
            )
            
            if status_code == 200:
                return {
                    "success": True,
                    "query": query,
                    "site": "grok",
                    "content_length": len(content),
                    "accessed_at": datetime.now().isoformat()
                }
            else:
                return {"success": False, "status_code": status_code}
                
        except Exception as e:
            logger.error(f"Grok search error: {e}")
            return {"success": False, "error": str(e)}

    def get_visited_urls(self) -> List[str]:
        return list(self.visited_urls)

    def get_access_stats(self) -> Dict[str, Any]:
        return {
            "visited_urls_count": len(self.visited_urls),
            "last_access_times": self.last_access_time,
            "request_interval": self.request_interval
        }

    def set_request_interval(self, seconds: int):
        self.request_interval = max(1, seconds)
        logger.info(f"Request interval set to {seconds} seconds")


_ai_site_scraper: Optional[AISiteScraper] = None


def get_ai_site_scraper() -> AISiteScraper:
    global _ai_site_scraper
    if _ai_site_scraper is None:
        _ai_site_scraper = AISiteScraper()
    return _ai_site_scraper
