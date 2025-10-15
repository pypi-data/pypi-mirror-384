from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

try:
    from appdirs import user_config_dir, user_data_dir
except Exception:  # pragma: no cover - fallback leve
    def user_config_dir(app_name: str) -> str:
        return str(Path.home() / f".{app_name}" / "config")

    def user_data_dir(app_name: str) -> str:
        return str(Path.home() / f".{app_name}" / "data")


@dataclass(frozen=True)
class AppPaths:
    app_name: str
    config_dir: Path
    data_dir: Path
    config_path: Path
    history_path: Path


def build_app_paths(app_name: str,
                    config_filename: str = "config.json",
                    history_filename: str = "history.json") -> AppPaths:
    """Build standard config/data paths for an application name.

    Uses appdirs if available, otherwise defaults to ~/.<app_name> structure.
    """
    cdir = Path(user_config_dir(app_name))
    ddir = Path(user_data_dir(app_name))
    return AppPaths(
        app_name=app_name,
        config_dir=cdir,
        data_dir=ddir,
        config_path=cdir / config_filename,
        history_path=ddir / history_filename,
    )


def ensure_dirs(*paths: Path) -> None:
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)
