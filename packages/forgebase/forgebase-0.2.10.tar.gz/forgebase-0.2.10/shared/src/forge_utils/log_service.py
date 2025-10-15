import logging
import sys
from enum import Enum
from logging import Filter, Handler, StreamHandler
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Optional

try:  # appdirs é opcional; fallback para ~/.<app_name>
    from appdirs import user_data_dir
except Exception:  # pragma: no cover - fallback leve
    def user_data_dir(app_name: str) -> str:
        return str(Path.home() / f".{app_name}")


class LogOutput(Enum):
    CONSOLE = "console"
    FILE = "file"
    ALL = "all"
    NONE = "none"


class DenyAllFilter(Filter):
    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D401
        return False


class ModuleFilter(Filter):
    def __init__(self, module_name: str):
        super().__init__()
        self.module_name = module_name

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D401
        return record.module == self.module_name


class LogService:
    """Configura logging com console e arquivos rotativos.

    Caminhos de log podem ser injetados; caso contrário, são derivados de
    `app_name` usando `appdirs.user_data_dir`.
    """

    def __init__(
        self,
        name: str = "forgebase",
        level: int = logging.INFO,
        default_output: LogOutput = LogOutput.CONSOLE,
        *,
        app_name: str = "forgebase",
        app_log_path: Optional[Path] = None,
        error_log_path: Optional[Path] = None,
        max_bytes: int = 5 * 1024 * 1024,
        backup_count: int = 10,
    ):
        # Resolve caminhos de log
        if app_log_path is None or error_log_path is None:
            base_dir = Path(user_data_dir(app_name))
            app_log_path = app_log_path or (base_dir / "app.log")
            error_log_path = error_log_path or (base_dir / "error.log")

        app_log_path.parent.mkdir(parents=True, exist_ok=True)
        error_log_path.parent.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.propagate = True
        self.logger.disabled = False
        self._active_module: Optional[str] = None

        # formatter comum
        self._formatter = logging.Formatter(
            fmt="%(asctime)s | %(module)-20s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Console
        console_h = StreamHandler(sys.stdout)
        console_h.setFormatter(self._formatter)

        # App log (todos os níveis >= logger.level)
        app_h = RotatingFileHandler(
            filename=str(app_log_path),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        app_h.setFormatter(self._formatter)
        app_h.setLevel(logging.NOTSET)  # herda do logger

        # Error log (apenas ERROR+)
        err_h = RotatingFileHandler(
            filename=str(error_log_path),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        err_h.setFormatter(self._formatter)
        err_h.setLevel(logging.ERROR)

        self._handlers: dict[LogOutput | str, Handler] = {
            LogOutput.CONSOLE: console_h,
            LogOutput.FILE: app_h,
            "error_file": err_h,
        }

        # primeira configuração
        self._output: Optional[LogOutput] = None
        self.output = default_output

    @property
    def output(self) -> LogOutput:
        return self._output  # type: ignore[return-value]

    @output.setter
    def output(self, value: LogOutput) -> None:
        # Limpa handlers atuais (mas não altera filtros nem disabled)
        self.logger.handlers.clear()
        self._output = value

        if value in (LogOutput.CONSOLE, LogOutput.ALL):
            self.logger.addHandler(self._handlers[LogOutput.CONSOLE])
        if value in (LogOutput.FILE, LogOutput.ALL):
            # adiciona app_log e error_log
            self.logger.addHandler(self._handlers[LogOutput.FILE])
            self.logger.addHandler(self._handlers["error_file"])

        # reaplica filtro de módulo, se existir
        if self._active_module:
            self.activate(self._active_module)

    def set_level(self, level: int) -> None:
        self.logger.setLevel(level)

    def mute_all(self) -> None:
        # Nega tudo (handlers ficam, mas filtram tudo)
        for h in self.logger.handlers:
            h.filters.clear()
            h.addFilter(DenyAllFilter())
        self.logger.setLevel(logging.CRITICAL + 1)
        self.logger.propagate = False
        self.logger.disabled = True

    def activate(self, module_name: str) -> None:
        self._active_module = module_name
        self.logger.disabled = False
        self.logger.propagate = True
        for h in self.logger.handlers:
            h.filters.clear()
            h.addFilter(ModuleFilter(module_name))

    def activate_all(self) -> None:
        self._active_module = None
        self.logger.disabled = False
        for h in self.logger.handlers:
            h.filters.clear()

    # Wrappers com stacklevel
    def debug(self, msg: str, *args: Any, stacklevel: int = 2, **kwargs: Any) -> None:
        self.logger.debug(msg, *args, stacklevel=stacklevel, **kwargs)

    def info(self, msg: str, *args: Any, stacklevel: int = 2, **kwargs: Any) -> None:
        self.logger.info(msg, *args, stacklevel=stacklevel, **kwargs)

    def warning(self, msg: str, *args: Any, stacklevel: int = 2, **kwargs: Any) -> None:
        self.logger.warning(msg, *args, stacklevel=stacklevel, **kwargs)

    def warn(self, msg: str, *args: Any, stacklevel: int = 2, **kwargs: Any) -> None:
        self.logger.warning(msg, *args, stacklevel=stacklevel, **kwargs)

    def error(self, msg: str, *args: Any, stacklevel: int = 2, **kwargs: Any) -> None:
        self.logger.error(msg, *args, stacklevel=stacklevel, **kwargs)

    def critical(self, msg: str, *args: Any, stacklevel: int = 2, **kwargs: Any) -> None:
        self.logger.critical(msg, *args, stacklevel=stacklevel, **kwargs)


# Instância global padrão
logger = LogService("root", logging.INFO, default_output=LogOutput.ALL, app_name="forgebase")
