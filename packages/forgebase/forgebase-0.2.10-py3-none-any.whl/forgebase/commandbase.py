from __future__ import annotations

from functools import wraps
from typing import Any, Callable, final

from forge_utils.log_service import logger

from .exceptionbase import CommandException, ForgeBaseException
from .interfaces import IBaseCommand, IBaseModel


def guard_errors(fn: Callable[..., Any]) -> Callable[..., Any]:
    """
    Envolve exec_command/execute e converte qualquer falha em CommandException.
    Mantém nome/doc/assinatura originais via @wraps.
    """
    @wraps(fn)
    def _wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        try:
            return fn(self, *args, **kwargs)
        except CommandException:
            raise                                    # já está no “formato certo”
        except ForgeBaseException as err:
            # erro de camada inferior (persistence, etc.)
            raise CommandException(str(err)) from err
        except Exception as err:                     # bug cru
            logger.error("Unhandled error", exc_info=err)
            raise CommandException("Erro inesperado") from err
    return _wrapper


class CustomCommandBase(IBaseCommand):
    def __init__(self, command_name: str, model: IBaseModel | None = None):
        self.command_name = command_name
        self._model = model

    def get_model(self)-> IBaseModel | None:
        return self._model

    @final
    @guard_errors
    def execute(self, **params: Any) -> Any:
        logger.debug(f'inicio: {params}')
        result = self.exec_command(self.command_name, **params)
        logger.debug(f'fim: {result}')
        return result
