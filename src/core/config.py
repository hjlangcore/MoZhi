from typing import List
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    APP_NAME: str = "墨智 MoZhi"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    DATABASE_URL: str = "sqlite:///./mozhi.db"

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama2"
    OLLAMA_TIMEOUT: int = 120

    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    LOG_ROTATION: str = "100 MB"
    LOG_RETENTION: str = "7 days"

    MAX_CHAPTER_WORDS: int = 5000
    MIN_CHAPTER_WORDS: int = 1000
    DEFAULT_CHAPTER_WORDS: int = 2000

    SESSION_EXPIRE_HOURS: int = 72

    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    API_PREFIX: str = "/api/v1"

    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    NETWORK_TIMEOUT: int = 30
    NETWORK_MAX_RETRIES: int = 3
    NETWORK_REQUEST_INTERVAL: int = 5
    NETWORK_VERIFY_SSL: bool = True

    PROXY_ENABLED: bool = True
    PROXY_URL: str = "http://127.0.0.1:7890"


class NovelConfig(BaseModel):
    novel_theme: str = "玄幻修仙，主角天生废柴，逆袭成仙，世界观庞大，剧情热血"
    chapter_words: int = Field(default=2000, ge=500, le=10000)
    length_type: str = Field(default="short", pattern="^(short|mid|long|tomato|custom)$")
    style_type: str = Field(default="凡人流")
    style_description: str = ""

    custom_target_words: int = Field(default=0, ge=0, le=5000000)

    @field_validator("custom_target_words")
    @classmethod
    def validate_custom_target_words(cls, v: int) -> int:
        if v > 0 and v < 10000:
            raise ValueError("custom_target_words must be 0 (not set) or at least 10000")
        return v

    @property
    def max_words(self) -> int:
        multipliers = {"short": 30000, "mid": 100000, "long": 300000, "tomato": 500000}
        if self.length_type == "custom" and self.custom_target_words > 0:
            return self.custom_target_words
        return multipliers.get(self.length_type, 30000)

    @property
    def estimated_chapters(self) -> int:
        return max(1, self.max_words // self.chapter_words)


def get_settings() -> Settings:
    return Settings()


_settings = None


def _get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = get_settings()
    return _settings


settings = _get_settings()