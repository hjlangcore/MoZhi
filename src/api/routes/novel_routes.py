from fastapi import APIRouter, HTTPException, Depends
from typing import List, Any, Dict
from loguru import logger

from src.api.schemas import (
    NovelCreate, NovelResponse, NovelSettingResponse,
    BaseResponse, ChapterResponse, WorkflowStatusResponse
)
from src.core.session_store import get_session_store
from src.novel_agent.state import NovelState, ChapterModel
from src.core.exceptions import SessionNotFoundError, NovelNotFoundError
from src.novel_agent.knowledge_integrator import get_knowledge_integrator
from src.novel_agent.web_search import get_web_searcher
from src.core.config import settings

router = APIRouter(prefix="/novels", tags=["novels"])


def get_store():
    return get_session_store()


@router.post("/", response_model=BaseResponse)
async def create_novel(data: NovelCreate, store=Depends(get_store)):
    logger.info(f"Creating novel for session: {data.session_id}")

    novel = store.create_novel(data.session_id, data.theme, data.style_type)
    if not novel:
        raise HTTPException(status_code=404, detail="Session not found")

    return BaseResponse(
        code=200,
        message="Novel created successfully",
        data={
            "novel_id": novel.novel_id,
            "title": novel.setting.novel_title if novel.setting else "待定",
            "theme": novel.setting.novel_title if novel.setting else data.theme,
            "status": novel.status,
            "total_words": novel.total_words,
            "current_chapter": novel.current_chapter,
            "style_type": novel.setting.style_type if novel.setting else data.style_type
        }
    )


@router.get("/{novel_id}", response_model=BaseResponse)
async def get_novel(novel_id: str, store=Depends(get_store)):
    novel = store.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")

    return BaseResponse(
        code=200,
        message="success",
        data={
            "novel_id": novel.novel_id,
            "title": novel.setting.novel_title if novel.setting else "待定",
            "theme": novel.setting.novel_title if novel.setting else "",
            "status": novel.status,
            "total_words": novel.total_words,
            "current_chapter": novel.current_chapter,
            "style_type": novel.setting.style_type if novel.setting else ""
        }
    )


@router.get("/{novel_id}/setting", response_model=BaseResponse)
async def get_novel_setting(novel_id: str, store=Depends(get_store)):
    novel = store.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")

    if not novel.setting:
        raise HTTPException(status_code=404, detail="Novel setting not initialized")

    setting = novel.setting
    return BaseResponse(
        code=200,
        message="success",
        data={
            "novel_title": setting.novel_title,
            "world_framework": setting.world_framework,
            "power_system": setting.power_system,
            "major_factions": setting.major_factions,
            "main_character": setting.main_character.model_dump() if setting.main_character else None,
            "supporting_characters": [c.model_dump() for c in setting.supporting_characters],
            "antagonists": [c.model_dump() for c in setting.antagonists],
            "main_plot_thread": setting.main_plot_thread,
            "core_conflicts": setting.core_conflicts,
            "style_type": setting.style_type
        }
    )


@router.post("/{novel_id}/worldview", response_model=BaseResponse)
async def save_worldview(novel_id: str, world_view: Dict[str, Any], store=Depends(get_store)):
    novel = store.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")

    store.update_novel(novel_id, world_view=world_view)
    logger.info(f"Worldview saved for novel {novel_id}")

    return BaseResponse(
        code=200,
        message="Worldview saved successfully",
        data=world_view,
    )


@router.post("/{novel_id}/characters", response_model=BaseResponse)
async def save_character(novel_id: str, body: Dict[str, Any], store=Depends(get_store)):
    novel = store.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")

    character = body.get("character", {})
    is_main = body.get("is_main", False)

    characters_list = novel.world_view.get("characters", []) if novel.world_view else []
    if is_main:
        character["_is_main"] = True
        characters_list.insert(0, character)
    else:
        characters_list.append(character)

    world_view = novel.world_view or {}
    world_view["characters"] = characters_list
    store.update_novel(novel_id, world_view=world_view)

    logger.info(f"Character saved for novel {novel_id}: {character.get('name', '?')}")
    return BaseResponse(code=200, message="Character saved successfully", data=character)


@router.post("/{novel_id}/style", response_model=BaseResponse)
async def save_style(novel_id: str, style_settings: Dict[str, Any], store=Depends(get_store)):
    novel = store.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")

    world_view = novel.world_view or {}
    world_view["style_settings"] = style_settings
    store.update_novel(novel_id, world_view=world_view)

    logger.info(f"Style settings saved for novel {novel_id}")
    return BaseResponse(code=200, message="Style saved successfully", data=style_settings)


@router.get("/{novel_id}/chapters", response_model=BaseResponse)
async def get_chapters(novel_id: str, store=Depends(get_store)):
    novel = store.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")

    chapters = [
        {
            "chapter_number": ch.chapter_number,
            "title": ch.title,
            "status": ch.status,
            "word_count": ch.word_count
        }
        for ch in novel.chapters
    ]
    return BaseResponse(code=200, message="success", data=chapters)


@router.get("/{novel_id}/chapters/{chapter_number}", response_model=BaseResponse)
async def get_chapter(novel_id: str, chapter_number: int, store=Depends(get_store)):
    chapter = store.get_chapter(novel_id, chapter_number)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    return BaseResponse(
        code=200,
        message="success",
        data={
            "chapter_number": chapter.chapter_number,
            "title": chapter.title,
            "content": chapter.content,
            "status": chapter.status,
            "word_count": chapter.word_count
        }
    )


@router.get("/{novel_id}/status", response_model=BaseResponse)
async def get_workflow_status(novel_id: str, store=Depends(get_store)):
    novel = store.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")

    target_words = 300000
    progress = min(100, (novel.total_words / target_words) * 100) if target_words > 0 else 0

    return BaseResponse(
        code=200,
        message="success",
        data={
            "status": novel.status,
            "current_chapter": novel.current_chapter,
            "total_words": novel.total_words,
            "target_words": target_words,
            "progress_percent": progress
        }
    )


@router.post("/{novel_id}/search", response_model=BaseResponse)
async def search_knowledge_for_novel(
    novel_id: str,
    query: str = "",
    keywords: str = "",
    store=Depends(get_store)
):
    """为小说创作搜索网络参考资料

    Args:
        query: 自然语言查询，由 LLM 分析后搜索
        keywords: 直接指定的搜索关键词，用逗号分隔（优先级高于 query）
    """
    novel = store.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")

    if not query and not keywords:
        raise HTTPException(status_code=400, detail="需要提供 query 或 keywords 参数")

    integrator = get_knowledge_integrator()

    # 搜索
    if keywords:
        kw_list = [k.strip() for k in keywords.split(",") if k.strip()]
        results = integrator.search_and_collect(kw_list, max_per_keyword=3)
    else:
        searcher = get_web_searcher()
        results = searcher.search(query, max_results=5)

    if not results:
        return BaseResponse(
            code=200,
            message="No results found",
            data={"query": query or keywords, "results": [], "count": 0}
        )

    # 构建小说上下文用于分析
    setting = novel.setting
    novel_context = f"《{setting.novel_title if setting else '待定'}》"
    if setting:
        novel_context += f"\n世界观：{setting.world_framework[:300]}"
        novel_context += f"\n修炼体系：{setting.power_system[:200]}"
        novel_context += f"\n当前进度：第{novel.current_chapter}章，{novel.total_words}字"

    # 用 LLM 分析搜索结果
    analysis = ""
    if hasattr(integrator, 'analyze_results'):
        try:
            from src.novel_agent.workflow import LLMClient
            llm = LLMClient(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.OLLAMA_MODEL,
                timeout=settings.OLLAMA_TIMEOUT
            )
            analysis = integrator.analyze_results(llm.generate, results, novel_context)
        except Exception as e:
            logger.warning(f"LLM analysis skipped: {e}")

    return BaseResponse(
        code=200,
        message="success",
        data={
            "query": query or keywords,
            "results": [
                {
                    "title": r.title,
                    "url": r.url,
                    "snippet": r.snippet,
                    "source": r.source
                }
                for r in results
            ],
            "analysis": analysis,
            "count": len(results)
        }
    )


@router.post("/{novel_id}/fetch-url", response_model=BaseResponse)
async def fetch_url_for_novel(
    novel_id: str,
    url: str,
    store=Depends(get_store)
):
    """抓取网页内容并生成摘要，用于小说参考"""
    novel = store.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")

    from src.novel_agent.web_fetch import get_web_fetcher
    from src.novel_agent.workflow import LLMClient

    fetcher = get_web_fetcher()
    llm = LLMClient(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL,
        timeout=settings.OLLAMA_TIMEOUT
    )

    result = fetcher.fetch_and_summarize(url, llm_generate=llm.generate)

    return BaseResponse(code=200, message="success", data=result)


@router.get("/{novel_id}/audit-report", response_model=BaseResponse)
async def get_audit_report(novel_id: str, store=Depends(get_store)):
    """获取小说质量审计趋势报告"""
    novel = store.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")

    from src.novel_agent.enhanced_audit import get_enhanced_audit
    audit = get_enhanced_audit()

    trend = audit.get_trend_report()

    # 最近几章的审计详情
    recent_audits = {}
    for ch_num, report in sorted(audit.audit_history.items(), reverse=True)[:5]:
        recent_audits[ch_num] = {
            "score": report.overall_score,
            "passed": not report.is_quality_decline,
            "critical_issues": report.critical_issues,
            "suggestions": report.suggestions[:3],
        }

    return BaseResponse(
        code=200,
        message="success",
        data={
            "trend": trend,
            "recent_audits": recent_audits,
            "knowledge_base_stats": {
                "characters": len(novel.knowledge_base.characters),
                "world_facts": len(novel.knowledge_base.world_facts),
                "foreshadowing": len(novel.knowledge_base.foreshadowing_registry),
                "state_changes_tracked": len(novel.state_changes),
            }
        }
    )


@router.delete("/{novel_id}", response_model=BaseResponse)
async def delete_novel(novel_id: str, store=Depends(get_store)):
    novel = store.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")

    session_id = novel.session_id
    title = novel.setting.novel_title if novel.setting else "未知"

    success = store.delete_novel(novel_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete novel")

    # 如果会话的 current_novel_id 指向被删除的小说，则清除
    if session_id:
        session = store.get_session(session_id)
        if session and session.current_novel_id == novel_id:
            store.update_session(session_id, current_novel_id=None)

    logger.info(f"Deleted novel: {title} ({novel_id})")
    return BaseResponse(code=200, message=f"Novel '{title}' deleted successfully")


@router.post("/{novel_id}/state-writeback", response_model=BaseResponse)
async def trigger_state_writeback(novel_id: str, store=Depends(get_store)):
    """手动触发状态回写"""
    novel = store.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")

    if not novel.chapters:
        raise HTTPException(status_code=400, detail="No chapters to analyze")

    from src.novel_agent.state_writeback import get_state_writeback
    from src.novel_agent.workflow import LLMClient

    wb = get_state_writeback()
    llm = LLMClient(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL,
        timeout=settings.OLLAMA_TIMEOUT
    )

    last_chapter = novel.chapters[-1]
    changes = wb.extract_and_writeback(llm.generate, last_chapter, novel)

    return BaseResponse(
        code=200,
        message="success",
        data={
            "changes_detected": len(changes),
            "changes": [
                {
                    "character": c.character_name,
                    "field": c.field_changed,
                    "old": c.old_value,
                    "new": c.new_value,
                    "reason": c.reason,
                }
                for c in changes
            ],
            "total_changes_tracked": len(novel.state_changes),
        }
    )
