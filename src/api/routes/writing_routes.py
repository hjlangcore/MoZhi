import threading
from typing import Dict
from fastapi import APIRouter, HTTPException
from loguru import logger

from src.novel_agent.workflow import NovelWorkflow
from src.core.config import NovelConfig, settings
from src.core.session_store import get_session_store
from src.novel_agent.state import NovelStatus
from src.novel_agent.novel_exporter import get_exporter
from src.novel_agent.coherence_manager import get_coherence_manager
from src.api.routes.ws_routes import broadcast_to_novel

router = APIRouter(prefix="/writing", tags=["writing"])

_running_workflows: Dict[str, threading.Event] = {}


def _get_style_description(style_type: str) -> str:
    descriptions = {
        "凡人流": "贴近现实，修仙路艰难险阻，主角需要一步一个脚印地修炼",
        "热血": "激情澎湃，战斗场面宏大，主角成长迅速",
        "隐忍": "低调内敛，主角前期受尽屈辱，后期爆发",
        "宏大": "世界观庞大，涉及多界、多域，势力纷杂",
        "番茄模式": "快节奏爽文，每章必有钩子，300字内出冲突，金手指要明确，打脸要频繁，适合番茄小说平台读者口味"
    }
    return descriptions.get(style_type, "")


def _run_writing(novel_id: str, config: NovelConfig, stop_event: threading.Event):
    store = get_session_store()
    novel = store.get_novel(novel_id)
    if not novel:
        return

    try:
        workflow = NovelWorkflow(config, stop_event=stop_event)
        workflow.state = novel
        novel.status = NovelStatus.WRITING

        if not novel.setting or not novel.setting.world_framework:
            logger.info("Generating novel setting...")
            workflow.initialize_novel()
            if stop_event.is_set():
                novel.status = NovelStatus.ABANDONED
                store._save_novels()
                return
            store._save_novels()
            store._save_sessions()

        logger.info(f"Starting auto-writing for novel {novel_id}: {config.max_words} words target")

        while novel.total_words < config.max_words:
            if stop_event.is_set():
                novel.status = NovelStatus.ABANDONED
                store._save_novels()
                logger.info(f"Writing stopped for novel {novel_id}")
                return

            chapter = workflow.write_chapter_with_agent_loop()
            if chapter is None:
                novel.status = NovelStatus.ABANDONED
                store._save_novels()
                logger.info(f"Writing stopped for novel {novel_id}")
                return
            store._save_novels()

            # WebSocket 推送章节更新
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                ch = novel.chapters[-1] if novel.chapters else None
                loop.run_until_complete(broadcast_to_novel(novel_id, {
                    "type": "chapter_update",
                    "novel_id": novel_id,
                    "current_chapter": novel.current_chapter,
                    "total_words": novel.total_words,
                    "status": novel.status,
                    "chapter": {
                        "chapter_number": ch.chapter_number if ch else 0,
                        "title": ch.title if ch else "",
                        "content": ch.content if ch else "",
                        "status": ch.status if ch else "",
                        "word_count": ch.word_count if ch else 0,
                    } if ch else None
                }))
                loop.close()
            except Exception:
                pass

            # 章后再次检查停止信号
            if stop_event.is_set():
                novel.status = NovelStatus.ABANDONED
                store._save_novels()
                return

            if novel.current_chapter % 3 == 0:
                try:
                    chapter = workflow.polish_chapter(chapter.chapter_number)
                    chapter = workflow.proofread_chapter(chapter.chapter_number)
                    store._save_novels()
                    # 润色校对后重新保存章节文件
                    workflow.display.save_chapter(chapter.chapter_number, chapter.title, chapter.content, chapter.word_count)
                except Exception as e:
                    logger.warning(f"Polish/proofread skipped: {e}")

            logger.info(f"Novel {novel_id}: ch{novel.current_chapter} {novel.total_words}/{config.max_words} words")

        novel.status = NovelStatus.COMPLETED
        store._save_novels()
        logger.info(f"Novel {novel_id} completed: {novel.total_words} words")

        # 自动导出（使用终端展示的小说目录）
        try:
            exporter = get_exporter()
            target = str(workflow.display.novel_dir) if workflow.display and workflow.display.novel_dir else ""
            export_path = exporter.export_all(novel, target_dir=target)
            logger.info(f"Novel exported to: {export_path}")
        except Exception as e:
            logger.error(f"Auto-export failed: {e}")

    except Exception as e:
        logger.error(f"Writing failed for novel {novel_id}: {e}")
        novel.status = NovelStatus.ABANDONED
        store._save_novels()
    finally:
        _running_workflows.pop(novel_id, None)



@router.post("/{novel_id}/resume")
async def resume_writing_endpoint(novel_id: str):
    store = get_session_store()
    novel = store.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")
    if novel.status != NovelStatus.WRITING:
        raise HTTPException(status_code=400, detail="Novel is not in writing status")
    if novel_id in _running_workflows:
        return {"success": False, "message": "Already writing", "novel_id": novel_id}

    style_type = novel.setting.style_type if novel.setting else "fanren"
    theme = novel.setting.novel_title if novel.setting else ""

    config = NovelConfig(
        novel_theme=theme,
        chapter_words=2200,
        length_type="custom",
        style_type=style_type,
        style_description=_get_style_description(style_type),
        custom_target_words=max(novel.total_words + 100000, 500000),
    )

    stop_event = threading.Event()
    _running_workflows[novel_id] = stop_event

    thread = threading.Thread(
        target=_run_writing,
        args=(novel_id, config, stop_event),
        daemon=True
    )
    thread.start()

    return {
        "success": True,
        "message": f"Resumed from chapter {novel.current_chapter}, {novel.total_words} words",
        "novel_id": novel_id,
        "current_chapter": novel.current_chapter,
        "total_words": novel.total_words,
    }
@router.post("/{novel_id}/start")
async def start_writing_endpoint(
    novel_id: str,
    chapter_words: int = 2000,
    length_type: str = "tomato",
    custom_target_words: int = 0
):
    store = get_session_store()
    novel = store.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")

    if novel_id in _running_workflows:
        return {"success": False, "message": "Already writing", "novel_id": novel_id}

    if not novel.setting or not novel.setting.world_framework:
        theme = "玄幻修仙"
        style_type = "番茄模式"
    else:
        theme = novel.setting.novel_title
        style_type = novel.setting.style_type

    config = NovelConfig(
        novel_theme=theme,
        chapter_words=chapter_words,
        length_type=length_type,
        style_type=style_type,
        style_description=_get_style_description(style_type),
        custom_target_words=custom_target_words
    )

    stop_event = threading.Event()
    _running_workflows[novel_id] = stop_event

    thread = threading.Thread(
        target=_run_writing,
        args=(novel_id, config, stop_event),
        daemon=True
    )
    thread.start()

    return {
        "success": True,
        "message": f"Writing started — {length_type} mode, {config.estimated_chapters} chapters",
        "novel_id": novel_id,
        "target_chapters": config.estimated_chapters,
        "target_words": config.max_words,
        "chapter_words": chapter_words,
        "length_type": length_type
    }


@router.post("/{novel_id}/stop")
async def stop_writing_endpoint(novel_id: str):
    event = _running_workflows.get(novel_id)
    if event:
        event.set()
        return {"success": True, "message": "Stop signal sent", "novel_id": novel_id}
    return {"success": False, "message": "Not currently writing", "novel_id": novel_id}


@router.get("/{novel_id}/status")
async def get_writing_status_endpoint(novel_id: str):
    store = get_session_store()
    novel = store.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")

    target_words = 500000  # default to tomato 50万字
    style = novel.setting.style_type if novel.setting else ""
    if "番茄" in style:
        target_words = 500000

    return {
        "is_writing": novel_id in _running_workflows,
        "novel_id": novel_id,
        "status": novel.status,
        "current_chapter": novel.current_chapter,
        "total_words": novel.total_words,
        "target_words": target_words,
        "progress_percent": min(100, round((novel.total_words / target_words) * 100, 1)) if target_words > 0 else 0
    }
