from typing import Any, Tuple

import json
import re

import backoff
import httpx
from forge_utils import logger


def log_backoff(details: Any) -> None:
    msg = (
        f"Tentativa {details['tries']} após {details['wait']:0.1f}s "
        f"por {details['target'].__name__}"
    )
    logger.warning(msg)

def is_retryable_error(exc: Exception) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in {429, 500, 502, 503, 504}
    return isinstance(exc, httpx.RequestError)

def retry_with_backoff(max_time: int | None = None) -> Any:
    """
    Decorator de retry com backoff exponencial.

    Args:
        max_time: Tempo máximo total em segundos para todas as tentativas.
                  Se None, usa apenas max_tries=4 sem limite de tempo.
    """
    return backoff.on_exception(
        backoff.expo,
        (httpx.RequestError, httpx.HTTPStatusError),
        max_tries=4,
        max_time=max_time,
        jitter=backoff.full_jitter,
        on_backoff=log_backoff,
        giveup=lambda e: not is_retryable_error(e)
    )


# --- Resilient JSON parsing for tool arguments (streaming-safe) ---
def _fix_trailing_commas(s: str) -> str:
    # Remove vírgulas antes de '}' e ']' (ex.: {"a":1,} -> {"a":1})
    return re.sub(r",\s*([}\]])", r"\1", s)


def _close_unbalanced(s: str) -> str:
    # Fecha chaves e colchetes se houver pequeno desbalanceamento (até 2)
    open_braces = s.count("{")
    close_braces = s.count("}")
    open_brackets = s.count("[")
    close_brackets = s.count("]")
    if 0 < open_braces - close_braces <= 2:
        s += "}" * (open_braces - close_braces)
    if 0 < open_brackets - close_brackets <= 2:
        s += "]" * (open_brackets - close_brackets)
    # Fecha aspas duplas se sobrar uma
    if s.count('"') % 2 == 1:
        s += '"'
    return s


def parse_json_resilient(raw: Any) -> Tuple[Any, bool]:
    """Tenta fazer json.loads(raw) com reparos leves e seguros.

    Retorna (valor, fallback_usado). Em caso de falha final, retorna
    {"_raw": <string truncada>}.
    """
    if not isinstance(raw, str):
        return raw, False
    try:
        return json.loads(raw), False
    except Exception:
        pass
    candidate = _fix_trailing_commas(raw)
    try:
        return json.loads(candidate), True
    except Exception:
        pass
    candidate = _close_unbalanced(candidate)
    try:
        return json.loads(candidate), True
    except Exception:
        # fallback seguro
        truncated = raw[:2000]
        return {"_raw": truncated}, True
