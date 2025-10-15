"""Forgebase core package.

API Pública v0.2.1:
    - Framework MVC-C: CustomBaseModel, CustomCommandBase, etc.
    - LLM Client: LLMClientFactory (recomendado), ILLMClient, Tool
    - Legacy: OpenAIProvider (deprecated - use LLMClientFactory)
"""

from importlib import metadata

from llm_client import (  # noqa: F401
    APIResponseError,
    ConfigurationError,
    ContentPart,
    ILLMClient,
    LLMClientFactory,
    LLMOpenAIClient,
    OpenAIProvider,
    OutputMessage,
    ResponseResult,
    TextFormat,
    TextOutputConfig,
    Tool,
)

from .commandbase import CustomCommandBase, guard_errors  # noqa: F401
from .controllerbase import CustomBaseController  # noqa: F401
from .exceptionbase import CommandException, ForgeBaseException  # noqa: F401
from .factories import PersistenceFactory  # noqa: F401
from .interfaces import (  # noqa: F401
    IBaseCommand,
    IBaseController,
    IBaseModel,
    IBasePersistence,
    IBaseView,
)
from .json_persistence import JSonPersistence as JsonPersistence  # noqa: F401
from .modelbase import BaseModelData, CustomBaseModel  # noqa: F401
from .viewbase import CustomBaseView  # noqa: F401

try:
    __version__ = metadata.version("forgebase")
except metadata.PackageNotFoundError:  # pragma: no cover - during dev
    __version__ = "0.0.dev0"

__all__ = [
    "__version__",
    # ============================================
    # Framework MVC-C (Core)
    # ============================================
    "BaseModelData",
    "CustomBaseModel",
    "CustomCommandBase",
    "CustomBaseController",
    "CustomBaseView",
    "PersistenceFactory",
    "JsonPersistence",
    # Interfaces
    "IBaseCommand",
    "IBaseController",
    "IBaseModel",
    "IBasePersistence",
    "IBaseView",
    # Exceptions
    "CommandException",
    "ForgeBaseException",
    "guard_errors",
    # ============================================
    # LLM Client (Public API - v0.2.1)
    # ============================================
    "LLMClientFactory",  # ✅ Factory (recomendado)
    "ILLMClient",  # ✅ Interface para type hints
    "Tool",  # ✅ Model para tool calling
    "ContentPart",
    "OutputMessage",
    "ResponseResult",
    "TextFormat",
    "TextOutputConfig",
    "APIResponseError",
    "ConfigurationError",
    # ============================================
    # LLM Client (Legacy - Deprecated)
    # ============================================
    # Mantidos para backward compatibility na v0.2.1
    # Use LLMClientFactory.create("openai") em vez disso
    "OpenAIProvider",  # ⚠️ Deprecated
    "LLMOpenAIClient",  # ⚠️ Deprecated - interno
]
