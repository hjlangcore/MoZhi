from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from loguru import logger
import time

from src.core.config import settings
from src.core.logging_config import setup_logging
from src.core.exceptions import FusionException
from src.api.routes import session_routes, novel_routes, chat_routes, network_routes, writing_routes, ws_routes, ai_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Starting 墨智 MoZhi API...")
    yield
    logger.info("Shutting down 墨智 MoZhi API...")


app = FastAPI(
    title="墨智 MoZhi API",
    description="AI-powered novel creation platform",
    version=settings.APP_VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    # 过滤敏感信息，避免记录到日志中
    safe_path = request.url.path
    sensitive_patterns = ['token', 'password', 'secret', 'key', 'auth']
    
    # 简单检查 URL 是否包含敏感参数（如果有 query string）
    if request.url.query:
        for pattern in sensitive_patterns:
            if pattern in request.url.query.lower():
                safe_path = f"{request.url.path}?[REDACTED]"
                break
    
    logger.info(f"{request.method} {safe_path} - {response.status_code} - {duration:.3f}s")
    return response


@app.exception_handler(FusionException)
async def fusion_exception_handler(request: Request, exc: FusionException):
    return JSONResponse(
        status_code=400,
        content={
            "code": exc.code,
            "message": exc.message,
            "detail": str(exc)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # 检查是否为内部请求（允许显示详细信息）
    client_ip = request.client.host if request.client else ""
    is_internal = client_ip in ["127.0.0.1", "::1"] or client_ip.startswith("10.") or client_ip.startswith("192.168.")
    
    # 只在 DEBUG 模式且为内部请求时显示详细信息
    detail = str(exc) if settings.DEBUG and is_internal else None
    
    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_ERROR",
            "message": "Internal server error",
            "detail": detail
        }
    )


app.include_router(session_routes.router, prefix=settings.API_PREFIX)
app.include_router(novel_routes.router, prefix=settings.API_PREFIX)
app.include_router(network_routes.router, prefix=settings.API_PREFIX)
app.include_router(writing_routes.router, prefix=settings.API_PREFIX)
app.include_router(chat_routes.router, prefix=settings.API_PREFIX)
app.include_router(ws_routes.router, prefix=settings.API_PREFIX)
app.include_router(ai_routes.router, prefix=settings.API_PREFIX)


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    llm_connected = False
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        llm_connected = response.status_code == 200
    except:
        pass

    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "llm_connected": llm_connected
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
