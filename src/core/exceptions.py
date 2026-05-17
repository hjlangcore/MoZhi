from typing import Optional


class FusionException(Exception):
    def __init__(self, message: str, code: str = "FUSION_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class NovelNotFoundError(FusionException):
    def __init__(self, novel_id: str):
        super().__init__(f"Novel not found: {novel_id}", "NOVEL_NOT_FOUND")


class ChapterNotFoundError(FusionException):
    def __init__(self, novel_id: str, chapter_number: int):
        super().__init__(
            f"Chapter {chapter_number} not found in novel {novel_id}",
            "CHAPTER_NOT_FOUND"
        )


class SessionNotFoundError(FusionException):
    def __init__(self, session_id: str):
        super().__init__(f"Session not found: {session_id}", "SESSION_NOT_FOUND")


class InvalidOperationError(FusionException):
    def __init__(self, message: str):
        super().__init__(message, "INVALID_OPERATION")


class LLMConnectionError(FusionException):
    def __init__(self, message: str = "Failed to connect to LLM service"):
        super().__init__(message, "LLM_CONNECTION_ERROR")


class LLMResponseError(FusionException):
    def __init__(self, message: str = "LLM returned an invalid response"):
        super().__init__(message, "LLM_RESPONSE_ERROR")


class ValidationError(FusionException):
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR")


class AuthenticationError(FusionException):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTHENTICATION_ERROR")


class AuthorizationError(FusionException):
    def __init__(self, message: str = "Not authorized to perform this action"):
        super().__init__(message, "AUTHORIZATION_ERROR")


class RateLimitError(FusionException):
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, "RATE_LIMIT_ERROR")


class ConfigurationError(FusionException):
    def __init__(self, message: str):
        super().__init__(message, "CONFIGURATION_ERROR")
