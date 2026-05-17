from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, Dict, Any, List

from src.core.network_client import get_network_client
from src.core.proxy_manager import get_proxy_manager
from src.novel_agent.ai_site_scraper import get_ai_site_scraper
from src.novel_agent.trigger_manager import get_trigger_manager
from src.novel_agent.knowledge_processor import get_knowledge_processor

router = APIRouter(prefix="/network", tags=["network"])


@router.get("/status")
async def get_network_status():
    network_client = get_network_client()
    proxy_manager = get_proxy_manager()
    
    return {
        "network_enabled": True,
        "proxy_active": proxy_manager.is_proxy_active(),
        "current_proxy": proxy_manager.get_current_proxy(),
        "request_count": network_client.request_count
    }


@router.post("/proxy/set")
async def set_proxy(proxy_url: Optional[str] = None):
    proxy_manager = get_proxy_manager()
    proxy_manager.set_proxy(proxy_url)
    
    return {
        "success": True,
        "message": f"Proxy {'set' if proxy_url else 'disabled'}",
        "current_proxy": proxy_manager.get_current_proxy()
    }


@router.post("/proxy/system")
async def use_system_proxy():
    proxy_manager = get_proxy_manager()
    proxy_manager.use_system_proxy()
    
    return {
        "success": True,
        "message": "Using system proxy",
        "current_proxy": proxy_manager.get_current_proxy()
    }


@router.get("/proxy/list")
async def get_proxy_list():
    proxy_manager = get_proxy_manager()
    
    return {
        "success": True,
        "proxies": proxy_manager.get_proxy_list(),
        "current_proxy": proxy_manager.get_current_proxy()
    }


@router.post("/proxy/add")
async def add_proxy(name: str, proxy_url: str):
    proxy_manager = get_proxy_manager()
    proxy_manager.add_proxy_to_list(name, proxy_url)
    
    return {"success": True, "message": f"Proxy '{name}' added"}


@router.delete("/proxy/remove/{name}")
async def remove_proxy(name: str):
    proxy_manager = get_proxy_manager()
    success = proxy_manager.remove_proxy_from_list(name)
    
    if success:
        return {"success": True, "message": f"Proxy '{name}' removed"}
    raise HTTPException(status_code=404, detail="Proxy not found")


@router.post("/proxy/select/{name}")
async def select_proxy(name: str):
    proxy_manager = get_proxy_manager()
    success = proxy_manager.select_proxy_by_name(name)
    
    if success:
        return {"success": True, "message": f"Proxy '{name}' selected"}
    raise HTTPException(status_code=404, detail="Proxy not found")


@router.post("/ai/access/{site}")
async def access_ai_site(site: str):
    scraper = get_ai_site_scraper()
    
    if site == "deepseek":
        result = scraper.access_deepseek()
    elif site == "grok":
        result = scraper.access_grok()
    else:
        raise HTTPException(status_code=400, detail="Unknown site")
    
    return result


@router.post("/ai/search")
async def ai_search(
    query: str,
    site: Optional[str] = Query("deepseek", enum=["deepseek", "grok", "both"])
):
    scraper = get_ai_site_scraper()
    
    if site == "both":
        results = {
            "deepseek": scraper.search_knowledge(query, "deepseek"),
            "grok": scraper.search_knowledge(query, "grok")
        }
    else:
        results = {site: scraper.search_knowledge(query, site)}
    
    return {"success": True, "query": query, "results": results}


@router.get("/triggers/status")
async def get_trigger_status():
    trigger_manager = get_trigger_manager()
    return trigger_manager.get_trigger_status()


@router.post("/triggers/toggle")
async def toggle_triggers(enabled: bool):
    trigger_manager = get_trigger_manager()
    trigger_manager.set_enabled(enabled)
    
    return {"success": True, "enabled": enabled}


@router.post("/triggers/{name}/toggle")
async def toggle_trigger(name: str, enabled: bool):
    trigger_manager = get_trigger_manager()
    
    if enabled:
        success = trigger_manager.enable_trigger(name)
    else:
        success = trigger_manager.disable_trigger(name)
    
    if success:
        return {"success": True, "name": name, "enabled": enabled}
    raise HTTPException(status_code=404, detail="Trigger not found")


@router.post("/triggers/{name}/threshold")
async def set_trigger_threshold(name: str, threshold: float):
    trigger_manager = get_trigger_manager()
    success = trigger_manager.set_trigger_threshold(name, threshold)
    
    if success:
        return {"success": True, "name": name, "threshold": threshold}
    raise HTTPException(status_code=404, detail="Trigger not found")


@router.post("/triggers/check")
async def check_triggers(content: str, previous_content: Optional[str] = ""):
    trigger_manager = get_trigger_manager()
    
    context = {"previous_content": previous_content}
    triggered = trigger_manager.check_all_triggers(content, context)
    
    if triggered:
        search_results = trigger_manager.auto_trigger_search(triggered, content)
        return {
            "success": True,
            "triggered": triggered,
            "search_results": search_results
        }
    
    return {"success": True, "triggered": [], "message": "No triggers activated"}


@router.get("/knowledge")
async def get_knowledge(
    category: Optional[str] = None,
    limit: int = Query(10, ge=1, le=50)
):
    processor = get_knowledge_processor()
    
    if category:
        items = processor.get_knowledge_by_category(category)[:limit]
    else:
        items = processor.get_all_knowledge()[:limit]
    
    return {"success": True, "knowledge": items}


@router.post("/knowledge/search")
async def search_knowledge(query: str, max_results: int = Query(5, ge=1, le=20)):
    processor = get_knowledge_processor()
    results = processor.search_and_process(query, max_results)
    
    return {"success": True, "query": query, "results": results}


@router.delete("/knowledge/{knowledge_id}")
async def delete_knowledge_item(knowledge_id: str):
    processor = get_knowledge_processor()
    success = processor.delete_knowledge(knowledge_id)
    
    if success:
        return {"success": True, "message": "Knowledge deleted"}
    raise HTTPException(status_code=404, detail="Knowledge not found")


@router.delete("/knowledge/clear")
async def clear_all_knowledge():
    processor = get_knowledge_processor()
    processor.clear_knowledge()
    
    return {"success": True, "message": "All knowledge cleared"}


@router.get("/knowledge/stats")
async def get_knowledge_stats():
    processor = get_knowledge_processor()
    return {"success": True, "stats": processor.get_knowledge_stats()}


@router.post("/knowledge/integrate")
async def integrate_knowledge(content: str, previous_content: Optional[str] = ""):
    processor = get_knowledge_processor()
    trigger_manager = get_trigger_manager()
    
    context = {"previous_content": previous_content}
    triggered = trigger_manager.check_all_triggers(content, context)
    
    if triggered:
        search_results = trigger_manager.auto_trigger_search(triggered, content)
        integrated_content = processor.integrate_into_novel(search_results, content)
        
        return {
            "success": True,
            "integrated_content": integrated_content,
            "triggers_activated": len(triggered),
            "knowledge_items_found": len(search_results)
        }
    
    return {"success": True, "integrated_content": content, "message": "No knowledge integration needed"}
