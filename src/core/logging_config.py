from loguru import logger
import sys
from pathlib import Path

from src.core.config import settings


def setup_logging():
    logger.remove()

    log_format = settings.LOG_FORMAT

    # 控制台输出
    logger.add(
        sys.stderr,
        format=log_format,
        level=settings.LOG_LEVEL,
        colorize=True
    )

    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # 通用日志 — 每日午夜轮转，避免 Windows seek 错误
    logger.add(
        log_dir / "mozhi_{time:YYYY-MM-DD}.log",
        format=log_format,
        level=settings.LOG_LEVEL,
        rotation="00:00",
        retention="7 days",
        compression="zip",
        encoding="utf-8",
        enqueue=True,
        catch=True,
    )

    # 错误日志 — 每日午夜轮转
    logger.add(
        log_dir / "error_{time:YYYY-MM-DD}.log",
        format=log_format,
        level="ERROR",
        rotation="00:00",
        retention="7 days",
        compression="zip",
        encoding="utf-8",
        enqueue=True,
        catch=True,
        filter=lambda record: record["level"].name == "ERROR"
    )

    logger.info(f"墨智 MoZhi v{settings.APP_VERSION} starting...")
    logger.info(f"Log level: {settings.LOG_LEVEL}")
