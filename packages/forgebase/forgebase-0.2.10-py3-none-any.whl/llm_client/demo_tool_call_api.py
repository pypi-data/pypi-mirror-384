"""
Demo de Tool Calling via OpenAI Responses API (online), forçando o uso da
ferramenta "get_weather" e respondendo com uma previsão fixa.

Pré-requisitos:
- Definir OPENAI_API_KEY no ambiente ou em um .env na raiz

Execução (Windows PowerShell):
  $env:PYTHONPATH = "shared/src;apps/llm_client/src"
  python -m llm_client.demo_tool_call_api

Execução (Linux/WSL):
  PYTHONPATH=shared/src:apps/llm_client/src python -m llm_client.demo_tool_call_api
"""

from __future__ import annotations

import os
from typing import Any, Dict

from dotenv import load_dotenv
from forge_utils import logger

from .models import Tool
from .openai_provider import OpenAIProvider


def main() -> int:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY não definida. Defina e tente novamente.")
        return 1

    provider = OpenAIProvider()
    provider.set_api_key(api_key)

    # Debug mode: print requests/responses raw from Responses API
    if os.getenv("DEMO_DEBUG_PAYLOAD"):
        try:
            import json as _json

            from .response import OpenAIResponse

            class DebugResponse(OpenAIResponse):
                from typing import Any
                def send_response(self, request: Any) -> Any:  # noqa: D401
                    print("\n[DEBUG] request: ")
                    try:
                        # pydantic model
                        payload = request.model_dump(exclude_none=True)
                    except Exception:
                        try:
                            # dataclass/dict fallback
                            payload = dict(request)
                        except Exception:
                            payload = str(request)
                    print(_json.dumps(payload, indent=2, ensure_ascii=False))
                    resp = super().send_response(request)
                    print("[DEBUG] response.output raw: ")
                    try:
                        pretty = resp.model_dump(exclude_none=True)
                        print(
                            _json.dumps(
                                pretty,
                                indent=2,
                                ensure_ascii=False,
                            )
                        )
                    except Exception:
                        print(resp)
                    # Try to fetch input_items for this response id (helps map function_call ids)
                    try:
                        items = self.list_input_items(resp.id)
                        print("\n[DEBUG] response.input_items raw: ")
                        print(_json.dumps(items, indent=2, ensure_ascii=False))
                    except Exception as _e:
                        print(f"[DEBUG] list_input_items failed: {_e}")
                    return resp

            # swap client's response for a debug wrapper
            if getattr(provider, "_client", None):
                assert provider._client is not None
                provider._client.response = DebugResponse(api_key)
                print("[DEBUG] DEMO_DEBUG_PAYLOAD ativo: imprimindo requests/responses brutos.")
        except Exception as _exc:  # pragma: no cover
            print(f"[DEBUG] não foi possível ativar modo debug: {_exc}")

    # Ferramenta e registro local
    weather_tool = Tool(
        type="function",
        name="get_weather",
        description="Retorna a temperatura da cidade informada.",
        parameters={
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    )

    # Força o uso da ferramenta no turn 1
    # Algumas variantes da API aceitam apenas 'required' ou exigem 'function.name'
    # O cliente normaliza automaticamente ambos os formatos.
    # Força uso da ferramenta; 'required' funciona de forma ampla entre variantes da API
    provider.configure_tools([weather_tool], tool_choice="required")

    def get_weather(args: Dict[str, Any]) -> str:
        city = args.get("city", "São Paulo")
        return f"{city}, 30 graus."

    provider.register_tool("get_weather", get_weather)

    pergunta = "Qual a temperatura de hoje?"
    print("Pergunta:", pergunta)

    # Mensagem enviada; o modelo é obrigado a emitir tool_use na 1ª resposta.
    out = provider.send_message(pergunta)
    print("Resposta:", out or "(vazia)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
