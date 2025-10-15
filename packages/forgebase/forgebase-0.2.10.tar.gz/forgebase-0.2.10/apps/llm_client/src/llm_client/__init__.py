from .factory import LLMClientFactory
from .interfaces import ILLMClient
from .llm_exceptions import APIResponseError, ConfigurationError
from .models import (
    ContentPart,
    OutputMessage,
    ResponseResult,
    TextFormat,
    TextOutputConfig,
    Tool,
)
from .openai_client import LLMOpenAIClient, OpenAIResponse
from .openai_provider import OpenAIProvider

__all__ = [
    # ============================================
    # PUBLIC API (Recommended)
    # ============================================
    "LLMClientFactory",  # ✅ Factory para criar providers (use este!)
    "ILLMClient",  # ✅ Interface para type hints
    # Models (shared)
    "Tool",
    "ContentPart",
    "OutputMessage",
    "ResponseResult",
    "TextFormat",
    "TextOutputConfig",
    # Exceptions
    "APIResponseError",
    "ConfigurationError",
    # ============================================
    # LEGACY (Deprecated - use LLMClientFactory)
    # ============================================
    # Mantidos para backward compatibility na v0.2.1
    # Serão removidos em versão futura
    "OpenAIProvider",  # ⚠️ Use LLMClientFactory.create("openai")
    "LLMOpenAIClient",  # ⚠️ Interno - não usar diretamente
    "OpenAIResponse",  # ⚠️ Interno - não usar diretamente
]
