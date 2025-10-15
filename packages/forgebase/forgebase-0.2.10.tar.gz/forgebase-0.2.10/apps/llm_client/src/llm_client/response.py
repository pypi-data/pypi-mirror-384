import json
import os
from typing import Any, Dict, Generator, Optional

import httpx
from forge_utils import logger

from .llm_exceptions import APIResponseError, ConfigurationError
from .llm_utils import retry_with_backoff
from .models import ResponseRequest, ResponseResult

OPENAI_API_URL = "https://api.openai.com/v1/responses"

class OpenAIResponse:
    def __init__(
        self,
        api_key: str,
        organization: Optional[str] = None,
        project: Optional[str] = None,
        store_local: bool = False,
        timeout: int = 120
    ):
        self.api_key = api_key
        self.organization = organization
        self.project = project
        self.store_local = store_local
        self.timeout = timeout

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        if organization:
            self.headers["OpenAI-Organization"] = organization
        if project:
            self.headers["OpenAI-Project"] = project

        # Optional: enable Responses API beta header if configured
        # OFF by default. Enable by setting OPENAI_BETA_RESPONSES=1|true
        beta_env = os.getenv("OPENAI_BETA_RESPONSES", "").strip().lower()
        if beta_env in {"1", "true", "yes"}:
            self.headers["OpenAI-Beta"] = "responses=v1"

        # Persistent HTTP client (keep-alive, optional HTTP/2)
        http2_env = os.getenv("FORGEBASE_HTTP2", "").strip().lower() in {"1", "true", "yes"}
        try:
            self._client = httpx.Client(
                headers=self.headers,
                timeout=self.timeout,
                http2=http2_env,
            )
        except Exception:
            # Fallback: no http2 flag
            self._client = httpx.Client(headers=self.headers, timeout=self.timeout)

    def send_response(self, request: ResponseRequest) -> ResponseResult:
        """Envia requisição com retry e timeout configurado."""
        return self._send_response_with_retry(request)

    @retry_with_backoff()
    def _send_response_with_retry(self, request: ResponseRequest) -> ResponseResult:
        payload = request.dict(exclude_none=True)
        logger.debug("Payload enviado à OpenAI:")
        logger.debug(json.dumps(payload, indent=2))

        try:
            response = self._client.post(
                OPENAI_API_URL,
                json=payload,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise APIResponseError(f"Erro HTTP {e.response.status_code}: {e.response.text}") from e

        data = response.json()
        logger.debug("Resposta recebida da OpenAI:")
        logger.debug(json.dumps(data, indent=2))

        return ResponseResult(**data)

    def get_response(self, response_id: str) -> ResponseResult:
        url = f"{OPENAI_API_URL}/{response_id}"
        response = self._client.get(url)
        response.raise_for_status()
        return ResponseResult(**response.json())

    def delete_response(self, response_id: str) -> bool:
        url = f"{OPENAI_API_URL}/{response_id}"
        response = self._client.delete(url)
        response.raise_for_status()
        return response.json().get("deleted", False)

    def list_input_items(self, response_id: str) -> dict:
        url = f"{OPENAI_API_URL}/{response_id}/input_items"
        response = self._client.get(url)
        response.raise_for_status()
        return response.json()

    def send_streaming_response(self, request: ResponseRequest) -> Generator[Dict[str, Any], None, None]:
        """Envia requisição streaming com retry e timeout configurado."""
        return self._send_streaming_response_with_retry(request)

    @retry_with_backoff()
    def _send_streaming_response_with_retry(self, request: ResponseRequest) -> Generator[Dict[str, Any], None, None]:
        if not request.stream:
            raise ConfigurationError("O campo 'stream' deve ser True para uso do streaming.")

        payload = request.dict(exclude_none=True)
        logger.debug("Streaming Payload enviado à OpenAI:")
        logger.debug(json.dumps(payload, indent=2))

        # Build headers specific for SSE streaming
        stream_headers = dict(self.headers)
        stream_headers["Accept"] = "text/event-stream"

        # Use granular timeouts better suited for SSE (no read timeout)
        timeout_obj: httpx.Timeout | int
        try:
            timeout_obj = httpx.Timeout(connect=30.0, read=None, write=30.0)
        except Exception:
            timeout_obj = self.timeout

        with self._client.stream(
            "POST",
            OPENAI_API_URL,
            headers=stream_headers,
            json=payload,
            timeout=timeout_obj,
        ) as response:
            # Handle HTTP errors explicitly for streaming responses by draining the body
            if response.status_code >= 400:
                try:
                    body = response.read()
                except Exception:
                    body = b""
                try:
                    body_text = body.decode("utf-8", errors="replace") if isinstance(body, (bytes, bytearray)) else str(body)
                except Exception:
                    body_text = ""
                raise APIResponseError(f"Erro HTTP {response.status_code}: {body_text}")
            for line in response.iter_lines():
                if not line:
                    continue
                decoded = line if isinstance(line, str) else line.decode("utf-8")
                if decoded.startswith("data: "):
                    content = decoded[len("data: "):]
                    if content.strip() != "[DONE]":
                        try:
                            yield json.loads(content)
                        except json.JSONDecodeError:
                            continue

    def list_models(self) -> Dict[str, Any]:
        url = "https://api.openai.com/v1/models"
        response = self._client.get(url)
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        try:
            self._client.close()
        except Exception:
            pass
