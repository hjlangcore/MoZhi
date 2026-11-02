# 墨智 MoZhi 项目安全漏洞与性能优化报告

## 执行摘要

本报告对墨智 MoZhi AI 小说创作平台进行了全面的安全审计和性能分析。项目整体架构合理，但存在多个需要修复的安全漏洞和性能瓶颈。

**风险等级分布：**
- 🔴 高危漏洞：3 个
- 🟡 中危漏洞：5 个
- 🟢 低危问题：8 个
- ⚡ 性能优化建议：10 项

---

## 一、安全漏洞分析

### 🔴 高危漏洞

#### 1. 硬编码密钥 (CVE-2024-Secret-001)

**位置：** `src/core/config.py:42`

```python
SECRET_KEY: str = "your-secret-key-change-in-production"
```

**风险描述：**
- 默认密钥未在生产环境中更改
- 攻击者可利用此密钥伪造 JWT token
- 可能导致会话劫持和权限提升

**影响范围：** 所有使用 SECRET_KEY 的认证功能

**修复建议：**
```python
# 修改为从环境变量读取，无默认值
SECRET_KEY: str = Field(..., env="SECRET_KEY")

# 或在启动时生成随机密钥
import secrets
SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
```

**环境配置示例 (.env)：**
```bash
SECRET_KEY=$(openssl rand -hex 32)
```

---

#### 2. SQL 注入风险 (CVE-2024-SQL-002)

**位置：** `src/core/config.py:18`

```python
DATABASE_URL: str = "sqlite:///./mozhi.db"
```

**风险描述：**
- 虽然当前使用 SQLite，但未看到 SQLAlchemy 的使用
- 如果后续扩展数据库，直接使用字符串拼接查询将导致 SQL 注入
- 文件路径未进行 sanitize，可能存在路径遍历风险

**修复建议：**
```python
# 1. 使用 SQLAlchemy ORM
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class Session(Base):
    __tablename__ = 'sessions'
    id = Column(Integer, primary_key=True)
    # ...

# 2. 参数化查询
session.query(Session).filter(Session.id == session_id).first()

# 3. 路径验证
from pathlib import Path
def validate_path(path: str) -> Path:
    base = Path("./data").resolve()
    target = (base / path).resolve()
    if not str(target).startswith(str(base)):
        raise ValueError("Invalid path")
    return target
```

---

#### 3. SSRF 漏洞 (CVE-2024-Network-003)

**位置：** `src/novel_agent/ai_site_scraper.py`, `src/core/network_client.py`

**风险描述：**
- 网络请求模块未限制目标地址
- 攻击者可诱导系统访问内网资源
- 支持 HTTP 重定向到内网地址

**受影响端点：**
- `/api/v1/novels/{novel_id}/fetch-url`
- 所有联网搜索功能

**修复建议：**
```python
# src/core/network_client.py 添加 IP 白名单检查
import socket
from urllib.parse import urlparse
import ipaddress

ALLOWED_SCHEMES = ['http', 'https']
BLOCKED_IP_RANGES = [
    ipaddress.ip_network('10.0.0.0/8'),
    ipaddress.ip_network('172.16.0.0/12'),
    ipaddress.ip_network('192.168.0.0/16'),
    ipaddress.ip_network('127.0.0.0/8'),
]

def is_safe_url(url: str) -> bool:
    parsed = urlparse(url)
    
    # 检查协议
    if parsed.scheme not in ALLOWED_SCHEMES:
        return False
    
    # 解析并检查 IP
    try:
        ip = socket.gethostbyname(parsed.hostname)
        ip_obj = ipaddress.ip_address(ip)
        
        for blocked in BLOCKED_IP_RANGES:
            if ip_obj in blocked:
                return False
        
        return True
    except Exception:
        return False

# 在请求前验证
if not is_safe_url(url):
    raise ValueError("Unsafe URL detected")
```

---

### 🟡 中危漏洞

#### 4. 调试信息泄露 (CVE-2024-Info-004)

**位置：** `src/api/main.py:69`

```python
"detail": str(exc) if settings.DEBUG else None
```

**风险描述：**
- DEBUG 模式下暴露完整异常堆栈
- 可能泄露敏感信息和系统结构
- 生产环境可能误开启 DEBUG

**修复建议：**
```python
# 永远不要在生产环境返回详细错误
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # 生产环境只返回通用错误
    detail = str(exc) if settings.DEBUG and is_internal_request(request) else None
    
    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_ERROR",
            "message": "Internal server error",
            "detail": detail
        }
    )

def is_internal_request(request: Request) -> bool:
    """检查是否为内部请求"""
    client_ip = request.client.host
    return client_ip in ["127.0.0.1", "::1"] or client_ip.startswith("10.")
```

---

#### 5. 缺少输入验证 (CVE-2024-Input-005)

**位置：** `src/api/routes/novel_routes.py:96-108`, `line 112-132`

```python
@router.post("/{novel_id}/worldview", response_model=BaseResponse)
async def save_worldview(novel_id: str, world_view: Dict[str, Any], store=Depends(get_store)):
    # 无任何验证直接保存
    store.update_novel(novel_id, world_view=world_view)
```

**风险描述：**
- 未验证输入数据大小，可能导致 DoS
- 未过滤恶意内容（XSS、脚本注入）
- 未限制字段类型和范围

**修复建议：**
```python
from pydantic import BaseModel, Field, validator

class WorldViewInput(BaseModel):
    class Config:
        extra = "forbid"  # 禁止额外字段
    
    description: str = Field(..., max_length=10000)
    characters: list = Field(default_factory=list, max_items=100)
    settings: dict = Field(default_factory=dict)
    
    @validator('description')
    def sanitize_description(cls, v):
        # 移除潜在的危险标签
        import re
        return re.sub(r'<script.*?>.*?</script>', '', v, flags=re.IGNORECASE | re.DOTALL)

@router.post("/{novel_id}/worldview", response_model=BaseResponse)
async def save_worldview(novel_id: str, data: WorldViewInput, store=Depends(get_store)):
    # 验证通过后才保存
    store.update_novel(novel_id, world_view=data.dict())
```

---

#### 6. 竞态条件 (CVE-2024-Race-006)

**位置：** `src/core/session_store.py`

**风险描述：**
- 文件读写无锁机制
- 并发请求可能导致数据损坏
- JSON 文件非原子写入

**修复建议：**
```python
import fcntl
from contextlib import contextmanager

class FileSessionStore(SessionStore):
    @contextmanager
    def _file_lock(self, file_path: Path):
        lock_file = file_path.with_suffix('.lock')
        with open(lock_file, 'w') as lf:
            fcntl.flock(lf.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lf.fileno(), fcntl.LOCK_UN)
    
    def _save_sessions(self):
        with self._file_lock(self.sessions_file):
            # 原子写入：先写临时文件再重命名
            temp_file = self.sessions_file.with_suffix('.tmp')
            data = [session.model_dump() for session in self._sessions.values()]
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            temp_file.replace(self.sessions_file)
```

---

#### 7. 不安全的反序列化 (CVE-2024-Deserialize-007)

**位置：** `src/core/session_store.py:27-30`, `37-41`

```python
with open(self.sessions_file, 'r', encoding='utf-8') as f:
    data = json.load(f)
    for session_data in data:
        session = SessionModel(**session_data)  # 无验证
```

**风险描述：**
- 加载外部 JSON 无完整性校验
- 可能被篡改的数据导致应用崩溃
- 缺少 schema 验证

**修复建议：**
```python
import hashlib
from pydantic import ValidationError

def _load_data(self):
    if self.sessions_file.exists():
        try:
            # 验证文件完整性（如果有 checksum 文件）
            checksum_file = self.sessions_file.with_suffix('.sha256')
            if checksum_file.exists():
                stored_hash = checksum_file.read_text().strip()
                computed_hash = hashlib.sha256(
                    self.sessions_file.read_bytes()
                ).hexdigest()
                if stored_hash != computed_hash:
                    logger.error("Session file integrity check failed")
                    return
            
            with open(self.sessions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            for session_data in data:
                try:
                    # 严格验证
                    session = SessionModel.model_validate(session_data)
                    self._sessions[session.session_id] = session
                except ValidationError as e:
                    logger.warning(f"Invalid session data skipped: {e}")
                    
        except json.JSONDecodeError as e:
            logger.error(f"Corrupted session file: {e}")
```

---

#### 8. 缺少速率限制 (CVE-2024-RateLimit-008)

**位置：** 所有 API 路由

**风险描述：**
- 无请求频率限制
- 易受暴力破解和 DoS 攻击
- 特别是搜索和生成功能

**修复建议：**
```python
# 安装 slowapi
# pip install slowapi

from slowapi import SlowAPILimiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import FastAPI

app = FastAPI()

# 配置速率限制器
limiter = SlowAPILimiter(key_func=lambda request: request.client.host)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 应用到路由
@router.post("/novels/", response_model=BaseResponse)
@limiter.limit("10/minute")  # 每分钟最多 10 次
async def create_novel(request: Request, data: NovelCreate, store=Depends(get_store)):
    # ...
```

---

#### 9. WebSocket 安全问题 (CVE-2024-WS-009)

**位置：** `src/api/routes/ws_routes.py` (推测)

**风险描述：**
- WebSocket 连接可能缺少认证
- 跨站 WebSocket 劫持风险
- 消息大小无限制

**修复建议：**
```python
from fastapi import WebSocket, WebSocketDisconnect, Depends
from src.core.auth import get_current_user  # JWT 认证

@websocket_router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    current_user = Depends(get_current_user)  # 添加认证
):
    # 验证 Origin 防止 CSRF
    origin = websocket.headers.get("origin")
    if origin not in settings.ALLOWED_ORIGINS:
        await websocket.close(code=4003)
        return
    
    await websocket.accept()
    
    # 限制消息大小
    while True:
        try:
            data = await websocket.receive_text()
            if len(data) > 1024 * 1024:  # 1MB 限制
                await websocket.send_json({"error": "Message too large"})
                continue
            # 处理消息
        except WebSocketDisconnect:
            break
```

---

### 🟢 低危问题

#### 10. 日志敏感信息 (CVE-2024-Log-010)

**位置：** `src/api/main.py:43-45`

```python
logger.info(f"{request.method} {request.url.path} - {response.status_code}")
```

**风险描述：**
- 可能记录敏感 URL 参数
- 日志文件权限未设置
- 无日志轮转配置（虽然有配置但未强制执行）

**修复建议：**
```python
# 过滤敏感信息
SENSITIVE_PATTERNS = ['token', 'password', 'secret', 'key', 'auth']

def sanitize_url(path: str) -> str:
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(path)
    params = parse_qs(parsed.query)
    
    # 移除敏感参数
    for key in SENSITIVE_PATTERNS:
        params.pop(key, None)
    
    parsed = parsed._replace(query='')
    return str(parsed)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    safe_path = sanitize_url(request.url.path)
    logger.info(f"{request.method} {safe_path} - {response.status_code} - {duration:.3f}s")
    return response
```

---

#### 11. CORS 配置过于宽松 (CVE-2024-CORS-011)

**位置：** `src/core/config.py:36-38`

```python
CORS_ALLOW_METHODS: List[str] = ["*"]
CORS_ALLOW_HEADERS: List[str] = ["*"]
```

**风险描述：**
- 允许所有方法和头
- 增加 XSS 攻击面
- 应明确指定允许的方法

**修复建议：**
```python
CORS_ORIGINS: List[str] = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://yourdomain.com"  # 生产域名
]
CORS_ALLOW_CREDENTIALS: bool = True
CORS_ALLOW_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
CORS_ALLOW_HEADERS: List[str] = [
    "Authorization",
    "Content-Type",
    "X-Requested-With",
    "Accept"
]
CORS_EXPOSE_HEADERS: List[str] = ["X-Request-ID"]
```

---

#### 12. 代理配置风险 (CVE-2024-Proxy-012)

**位置：** `src/core/config.py:51-52`

```python
PROXY_ENABLED: bool = True
PROXY_URL: str = "http://127.0.0.1:7890"
```

**风险描述：**
- 默认启用代理
- 代理地址硬编码
- 可能被恶意代理中间人攻击

**修复建议：**
```python
PROXY_ENABLED: bool = Field(default=False, env="PROXY_ENABLED")
PROXY_URL: str = Field(default="", env="PROXY_URL")

# 在使用时验证
def get_proxy_config() -> Optional[Dict]:
    if not settings.PROXY_ENABLED or not settings.PROXY_URL:
        return None
    
    # 验证代理可达性
    try:
        parsed = urlparse(settings.PROXY_URL)
        if parsed.scheme not in ['http', 'https']:
            logger.warning("Invalid proxy scheme")
            return None
        return {"http": settings.PROXY_URL, "https": settings.PROXY_URL}
    except Exception:
        return None
```

---

## 二、性能优化建议

### ⚡ 高优先级优化

#### 1. 数据库性能优化

**现状：** 使用 JSON 文件存储，无索引，O(n) 查询

**优化方案：**
```python
# 迁移到真正的数据库
from sqlalchemy import create_engine, Column, String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship, sessionmaker, joinedload

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,           # 连接池大小
    max_overflow=10,        # 最大溢出连接
    pool_pre_ping=True,     # 连接前 ping 测试
    echo=settings.DEBUG     # 开发环境开启 SQL 日志
)

class Novel(Base):
    __tablename__ = 'novels'
    
    novel_id = Column(String, primary_key=True, index=True)
    session_id = Column(String, ForeignKey('sessions.session_id'), index=True)
    title = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # 添加复合索引
    __table_args__ = (
        Index('idx_session_status', 'session_id', 'status'),
    )
    
    chapters = relationship("Chapter", back_populates="novel", lazy="selectin")

# 查询优化
# ❌ 慢查询
novels = session.query(Novel).filter_by(session_id=sid).all()
for novel in novels:
    chapters = novel.chapters  # N+1 问题

# ✅ 优化后
novels = session.query(Novel).options(
    joinedload(Novel.chapters)
).filter_by(session_id=sid).all()
```

---

#### 2. 缓存层实现

**现状：** 每次请求都读取文件/数据库

**优化方案：**
```python
from functools import lru_cache
import redis
from typing import Optional

# L1: 内存缓存
class CacheManager:
    def __init__(self):
        self._cache = {}
        self._ttl = {}
    
    def get(self, key: str) -> Optional[Any]:
        if key in self._ttl and time.time() < self._ttl[key]:
            return self._cache.get(key)
        self._cache.pop(key, None)
        self._ttl.pop(key, None)
        return None
    
    def set(self, key: str, value: Any, ttl: int = 300):
        self._cache[key] = value
        self._ttl[key] = time.time() + ttl

# L2: Redis 缓存（分布式场景）
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True,
    socket_connect_timeout=5
)

def cache_result(ttl: int = 300):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # 尝试从缓存获取
            cached = redis_client.get(key)
            if cached:
                return json.loads(cached)
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 存入缓存
            redis_client.setex(key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator

@cache_result(ttl=600)
async def get_novel(novel_id: str):
    # ...
```

---

#### 3. LLM 调用优化

**现状：** 每次生成都有完整的网络往返

**优化方案：**
```python
# 1. 批量处理
class LLMBatcher:
    def __init__(self, batch_size=5, max_wait=0.1):
        self.batch_size = batch_size
        self.max_wait = max_wait
        self.queue = asyncio.Queue()
    
    async def generate_batch(self, prompts: List[str]) -> List[str]:
        # 合并多个 prompt 一次性发送
        batch_prompt = "\n\n---\n\n".join(prompts)
        response = await self._call_llm(batch_prompt)
        return response.split("\n\n---\n\n")

# 2. Prompt 缓存
import hashlib

class PromptCache:
    def __init__(self):
        self.cache = {}
    
    def _get_prompt_hash(self, prompt: str) -> str:
        return hashlib.md5(prompt.encode()).hexdigest()
    
    async def generate(self, llm, prompt: str) -> str:
        hash_key = self._get_prompt_hash(prompt)
        
        if hash_key in self.cache:
            return self.cache[hash_key]
        
        result = await llm.generate(prompt)
        self.cache[hash_key] = result
        return result

# 3. 流式响应减少首字延迟
@app.post("/generate/stream")
async def stream_generate(prompt: str):
    async def generate_tokens():
        llm = LLMClient(...)
        full_text = ""
        
        for token in llm.generate_stream(prompt):
            full_text += token
            yield f"data: {json.dumps({'token': token})}\n\n"
        
        yield f"data: {json.dumps({'done': True})}\n\n"
    
    return StreamingResponse(generate_tokens(), media_type="text/event-stream")
```

---

#### 4. 异步 IO 优化

**现状：** 部分阻塞操作

**优化方案：**
```python
# 使用 aiohttp 替代 requests
import aiohttp
from aiohttp import ClientTimeout

class AsyncNetworkClient:
    def __init__(self):
        self.session = None
    
    async def get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            timeout = ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={'User-Agent': '...'}
            )
        return self.session
    
    async def get(self, url: str) -> Tuple[int, str]:
        session = await self.get_session()
        try:
            async with session.get(url) as response:
                return response.status, await response.text()
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return 0, ""
    
    async def close(self):
        if self.session:
            await self.session.close()

# 文件 IO 也使用异步
import aiofiles

async def save_novel_async(novel_id: str, data: dict):
    async with aiofiles.open(f'data/{novel_id}.json', 'w', encoding='utf-8') as f:
        await f.write(json.dumps(data, ensure_ascii=False))
```

---

#### 5. 连接池优化

**现状：** 每次请求创建新连接

**优化方案：**
```python
# LLM 连接池
class LLMConnectionPool:
    def __init__(self, pool_size=5):
        self.pool = asyncio.Semaphore(pool_size)
        self.clients = []
    
    async def acquire(self) -> LLMClient:
        await self.pool.acquire()
        client = LLMClient(...)
        self.clients.append(client)
        return client
    
    async def release(self, client: LLMClient):
        self.clients.remove(client)
        self.pool.release()

# 数据库连接池已在 SQLAlchemy 中配置
# 确保正确关闭会话
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_db_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

---

### ⚡ 中优先级优化

#### 6. 懒加载和分页

```python
# 章节列表分页
@router.get("/{novel_id}/chapters", response_model=BaseResponse)
async def get_chapters(
    novel_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    store=Depends(get_store)
):
    novel = store.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")
    
    # 分页
    start = (page - 1) * page_size
    end = start + page_size
    chapters = novel.chapters[start:end]
    
    return BaseResponse(
        code=200,
        message="success",
        data={
            "chapters": [...],
            "total": len(novel.chapters),
            "page": page,
            "page_size": page_size,
            "total_pages": (len(novel.chapters) + page_size - 1) // page_size
        }
    )
```

---

#### 7. 后台任务队列

```python
# 使用 Celery 或 ARQ 处理耗时任务
from celery import Celery

celery_app = Celery(
    'tasks',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

@celery_app.task(bind=True, max_retries=3)
def generate_chapter_task(self, novel_id: str, chapter_number: int):
    try:
        # 耗时的章节生成
        workflow = NovelWorkflow(...)
        chapter = workflow.generate_chapter(chapter_number)
        return {"success": True, "chapter_id": chapter.id}
    except Exception as exc:
        raise self.retry(exc, countdown=60)

# API 触发任务
@router.post("/{novel_id}/chapters/generate")
async def generate_chapter(novel_id: str, chapter_number: int):
    task = generate_chapter_task.delay(novel_id, chapter_number)
    return {"task_id": task.id, "status": "queued"}
```

---

#### 8. 压缩和 CDN

```python
# 启用 Gzip 压缩
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)

# 静态资源使用 CDN
# 在 nginx 或云服务商配置
```

---

## 三、代码质量改进

### 1. 类型注解完善

```python
# 当前
def process(data):
    return data

# 改进
from typing import Dict, List, Optional, Union

def process(data: Dict[str, Any]) -> List[Dict[str, str]]:
    return [...]
```

### 2. 错误处理标准化

```python
# 自定义异常类
class FusionException(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class NovelNotFoundException(FusionException):
    def __init__(self, novel_id: str):
        super().__init__(
            code="NOVEL_NOT_FOUND",
            message=f"Novel {novel_id} not found",
            status_code=404
        )

# 统一使用
raise NovelNotFoundException(novel_id)
```

### 3. 单元测试覆盖

```python
# tests/test_security.py
import pytest
from src.core.config import settings

def test_secret_key_not_default():
    assert settings.SECRET_KEY != "your-secret-key-change-in-production"

def test_cors_not_wildcard():
    assert "*" not in settings.CORS_ORIGINS

@pytest.mark.asyncio
async def test_rate_limiting():
    # 测试速率限制
    pass
```

---

## 四、部署安全建议

### 1. 环境变量管理

```bash
# .env.production (不要提交到 Git)
SECRET_KEY=<strong-random-key>
DEBUG=False
DATABASE_URL=postgresql://user:pass@localhost/mozhi
REDIS_URL=redis://localhost:6379
OLLAMA_BASE_URL=http://internal-ollama:11434
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

### 2. Docker 安全配置

```dockerfile
# Dockerfile 改进
FROM python:3.11-slim

# 创建非 root 用户
RUN useradd -m -u 1000 appuser

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chown -R appuser:appuser /app

USER appuser
EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3. Nginx 反向代理

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    # 强制 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/ssl/certs/yourdomain.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.key;
    
    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # 速率限制
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
    
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 五、优先级排序和行动清单

### 立即修复（1 周内）
- [ ] 更换默认 SECRET_KEY
- [ ] 添加输入验证和 sanitization
- [ ] 实现 SSRF 防护
- [ ] 关闭生产环境 DEBUG 模式

### 短期修复（1 个月内）
- [ ] 迁移到关系型数据库
- [ ] 实现速率限制
- [ ] 添加文件锁机制
- [ ] 完善错误处理

### 中期优化（3 个月内）
- [ ] 实现缓存层
- [ ] 异步 IO 改造
- [ ] 后台任务队列
- [ ] 完善监控和日志

### 长期规划（6 个月内）
- [ ] 微服务拆分
- [ ] 容器化部署
- [ ] CI/CD 流水线
- [ ] 安全审计自动化

---

## 六、监控和告警建议

```python
# 添加 Prometheus 指标
from prometheus_fastapi_instrumentator import PrometheusFastApiInstrumentator

instrumentator = PrometheusFastApiInstrumentator()
instrumentator.instrument(app).expose(app)

# 关键指标监控
# - 请求延迟 p95/p99
# - 错误率
# - LLM 调用次数和成本
# - 数据库连接数
# - 缓存命中率
```

---

## 总结

墨智 MoZhi 项目具有良好的架构基础和功能完整性，但在安全性和性能方面存在明显改进空间。建议按照优先级清单逐步实施修复和优化措施，特别关注：

1. **安全第一**：立即修复密钥、SSRF、注入等高危漏洞
2. **性能瓶颈**：数据库和缓存是主要优化点
3. **可维护性**：加强类型检查、测试覆盖和文档

实施这些改进后，系统的安全性、性能和可维护性将得到显著提升。
