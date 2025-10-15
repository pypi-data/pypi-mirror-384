from pathlib import Path

from forge_utils.paths import build_app_paths
from forge_utils.paths import ensure_dirs as ensure_dirs_util

APP_NAME = "forgebase"
_paths = build_app_paths(APP_NAME)
CONFIG_PATH: Path = _paths.config_path
HISTORY_PATH: Path = _paths.history_path


def ensure_dirs() -> None:
    ensure_dirs_util(_paths.config_dir, _paths.data_dir)
