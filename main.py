import argparse
import sys
import logging

from src.core.logging_config import setup_logging
from src.core.config import NovelConfig
from src.novel_agent.workflow import NovelWorkflow


def main():
    parser = argparse.ArgumentParser(description="Fusion Project - 集成代码生成和小说创作")
    parser.add_argument(
        "--mode",
        choices=["novel", "api"],
        default="novel",
        help="运行模式: novel(小说创作) 或 api(API服务)"
    )
    parser.add_argument(
        "--theme",
        type=str,
        default="玄幻修仙，主角天生废柴，逆袭成仙，世界观庞大，剧情热血",
        help="小说主题描述"
    )
    parser.add_argument(
        "--chapter-words",
        type=int,
        default=2000,
        help="每章字数"
    )
    parser.add_argument(
        "--length",
        choices=["short", "mid", "long"],
        default="short",
        help="小说长度类型"
    )
    parser.add_argument(
        "--style",
        choices=["凡人流", "热血", "隐忍", "宏大"],
        default="凡人流",
        help="文风类型"
    )
    
    args = parser.parse_args()
    
    setup_logging()
    logger = logging.getLogger("fusion_project")
    
    if args.mode == "novel":
        logger.info("启动小说创作模式")
        config = NovelConfig(
            novel_theme=args.theme,
            chapter_words=args.chapter_words,
            length_type=args.length,
            style_type=args.style
        )
        workflow = NovelWorkflow(config)
        workflow.run()
    elif args.mode == "api":
        logger.info("启动API服务模式")
        from src.api.main import app
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()