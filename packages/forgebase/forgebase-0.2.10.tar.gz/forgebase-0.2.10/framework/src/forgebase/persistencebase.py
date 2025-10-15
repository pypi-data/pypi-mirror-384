from __future__ import annotations

from typing import Any, Optional

from forge_utils import logger
from pydantic import BaseModel

from .interfaces import IBasePersistence


class PersistenceBase(IBasePersistence):
    """Base class for persistence backends.

    Provides a stable place to share cross-cutting concerns (logging, timing,
    retries) while keeping the interface minimal. Subclasses should override
    `load_data` and `save_data`.
    """

    def __init__(self, name: Optional[str] = None):
        self._name = name or self.__class__.__name__

    def load_data(self, model: BaseModel) -> bool:  # pragma: no cover - abstract
        logger.debug(f"{self._name}: load_data not implemented")
        raise NotImplementedError

    def save_data(self, model: BaseModel) -> Any:  # pragma: no cover - abstract
        logger.debug(f"{self._name}: save_data not implemented")
        raise NotImplementedError


__all__ = [
    "IBasePersistence",
    "PersistenceBase",
]
