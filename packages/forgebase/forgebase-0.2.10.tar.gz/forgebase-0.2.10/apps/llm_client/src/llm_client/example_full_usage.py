r"""
Demo completo do cliente LLM (Responses API) e recursos disponíveis.

Inclui:
- Resposta direta (Responses API)
- Streaming de resposta
- Entrada multimodal (imagens e áudio)
- Parâmetros dinâmicos (temperature/max_tokens)
- Tratamento de exceções
- Logging estruturado
- Provider agnóstico (ILLMClient) + Tool Calling (definição e orquestração local)
- Tool Calling em streaming
- Paths de configuração/dados via forge_utils.paths

Como executar:
1) Ative seu venv e instale dependências (pip ou poetry), por ex:
   - Windows PowerShell:
       .venv\Scripts\Activate.ps1
       python -m pip install pydantic>=2.5 httpx>=0.24 backoff appdirs python-dotenv
   - Linux/macOS/WSL:
       source .venv/bin/activate
       python -m pip install pydantic>=2.5 httpx>=0.24 backoff appdirs python-dotenv

2) Configure a variável OPENAI_API_KEY (ou um arquivo .env na raiz):
   - Windows PowerShell:
       $env:OPENAI_API_KEY = "sk-..."
   - Linux/macOS/WSL:
       export OPENAI_API_KEY="sk-..."

3) Execute:
   - PYTHONPATH=shared/src:apps/llm_client/src python -m llm_client.example_full_usage
   - No Windows PowerShell:
       $env:PYTHONPATH = "shared/src;apps/llm_client/src"; python -m llm_client.example_full_usage

4) Tool Calling (opcional):
   - Para executar a seção de Tool Calling real, defina:
       Linux/macOS/WSL:   export DEMO_TOOL_CALLING=1
       PowerShell:        $env:DEMO_TOOL_CALLING = "1"
   - Observação: modelos e formato de ferramentas evoluem; erros 4xx podem ocorrer.
"""

from __future__ import annotations

import os
from typing import Any, Dict

from dotenv import load_dotenv
from forge_utils import logger
from forge_utils.paths import build_app_paths, ensure_dirs
from forgebase import (
    APIResponseError,
    ConfigurationError,
    ContentPart,
    LLMOpenAIClient,
    OpenAIProvider,
    OutputMessage,
    ResponseResult,
    TextFormat,
    TextOutputConfig,
    Tool,
)


def section(title: str) -> None:
    print(f"\n=== {title} ===")


def demo_paths() -> None:
    section("Paths de configuração e dados")
    ap = build_app_paths("forgebase")
    ensure_dirs(ap.config_dir, ap.data_dir)
    print("CONFIG:", ap.config_path)
    print("DATA:", ap.history_path)


def demo_client_basic(api_key: str) -> None:
    client = LLMOpenAIClient(
        api_key=api_key,
        model="gpt-4o",
        temperature=0.7,
        max_tokens=300,
        user="demo",
        store_local=True,
    )

    # 1) Resposta direta
    section("[1] Resposta direta")
    try:
        response = client.send_prompt(
            "Explique em três frases o conceito de 'emergência' em sistemas complexos."
        )
        print(response.output[0].content[0].text)
    except APIResponseError as e:
        print("[Erro de API]:", e)
    except Exception as e:
        print("[Erro inesperado]:", e)

    # 2) Streaming
    section("[2] Resposta com streaming")
    try:
        for delta in client.send_prompt(
            "Conte uma história curta sobre um robô e uma criança.", streamed=True
        ):
            print(delta, end="", flush=True)
        print()
    except APIResponseError as e:
        print("[Erro de API no streaming]:", e)

    # 3) Parâmetros dinâmicos
    section("[3] Resposta com nova temperatura")
    client.temperature = 0.2
    client.max_tokens = 100
    try:
        resposta = client.send_prompt("Explique o que é entropia.")
        print(resposta.output[0].content[0].text)
    except Exception as e:
        print("[Erro na terceira requisição]:", e)

    # 4) Exceção forçada
    section("[4] Teste de exceção com prompt inválido")
    try:
        client.send_prompt(None)  # type: ignore[arg-type]
    except ConfigurationError as e:
        print("[Erro de configuração capturado corretamente]:", e)


    # 5) Entrada multimodal (texto + imagem + áudio)
    section("[5] Entrada multimodal (imagem + áudio)")
    try:
        multimodal = client.send_prompt(
            "Descreva a imagem enviada e comente o áudio.",
            images=["https://upload.wikimedia.org/wikipedia/commons/9/99/Colorful_sunset.jpg"],
            audio={"base64": "ZGF0YQ==", "mime_type": "audio/wav"},
        )
        print(multimodal)
    except APIResponseError as e:
        print("[Erro na chamada multimodal]:", e)
    except Exception as e:
        print("[Multimodal inesperado]:", e)


def demo_provider_with_tools(api_key: str) -> None:
    section("[6] Provider agnóstico + Tool Calling (orquestração local)")

    provider = OpenAIProvider()
    provider.set_api_key(api_key)

    # Definição de uma ferramenta (esquema JSON compatível com Responses API)
    tool = Tool(
        type="function",
        name="say_hello",
        description="Retorna uma saudação simples",
        parameters={
            "type": "object",
            "properties": {"who": {"type": "string"}},
            "required": ["who"],
        },
    )
    provider.configure_tools([tool], tool_choice="auto")

    # Função Python local registrada para executar quando houver tool_use
    def say_hello(args: Dict[str, Any]) -> str:
        return f"Olá, {args.get('who', 'mundo')}!"

    provider.register_tool("say_hello", say_hello)

    # Prompt orientando o uso da ferramenta (tool calling síncrono)
    prompt = (
        "Se precisar, chame a ferramenta say_hello com who='Forgebase'. "
        "Em seguida, finalize a resposta."
    )
    try:
        out = provider.send_message(prompt)
        print(out or "(resposta vazia)")
    except Exception as e:
        print("[Tool Calling desabilitado ou não suportado pelo modelo atual]:", e)

    section("[6.1] Tool Calling com streaming")
    try:
        stream = provider.send_stream(
            "Se precisar, use a ferramenta say_hello e em seguida descreva o resultado.",
            images=None,
            audio=None,
        )
        for chunk in stream:
            print(chunk, end="", flush=True)
        print()
    except Exception as e:
        print("[Tool Calling streaming falhou]:", e)


def demo_local_tool_forecast() -> None:
    section("[7] Tool Calling OFFLINE (previsão fixa)")

    class LocalDummyResponse:
        def __init__(self) -> None:
            self.calls = 0

        def send_response(self, request: Any) -> ResponseResult:
            self.calls += 1
            if self.calls == 1:
                # Primeira resposta: solicita uso da ferramenta get_weather
                part = ContentPart(
                    type="tool_use",
                    id="tu_local_1",
                    name="get_weather",
                    input={"city": "São Paulo"},
                )
                return ResponseResult(
                    id="local_r1",
                    object="response",
                    created_at=0,
                    status="in_progress",
                    error=None,
                    incomplete_details=None,
                    instructions=None,
                    max_output_tokens=None,
                    model="gpt-4o",
                    output=[part],
                    parallel_tool_calls=None,
                    previous_response_id=None,
                    reasoning=None,
                    store=None,
                    temperature=1.0,
                    text=TextOutputConfig(format=TextFormat(type="text")),
                    tool_choice=None,
                    tools=None,
                    top_p=1.0,
                    truncation="disabled",
                    usage=None,
                    user=None,
                    metadata=None,
                )

            # Segunda resposta: texto final
            msg = OutputMessage(
                type="message",
                id="m_local",
                status="completed",
                role="assistant",
                content=[ContentPart(type="output_text", text="São Paulo, 30 graus.")],
            )
            return ResponseResult(
                id="local_r2",
                object="response",
                created_at=1,
                status="completed",
                error=None,
                incomplete_details=None,
                instructions=None,
                max_output_tokens=None,
                model="gpt-4o",
                output=[msg],
                parallel_tool_calls=None,
                previous_response_id="local_r1",
                reasoning=None,
                store=None,
                temperature=1.0,
                text=TextOutputConfig(format=TextFormat(type="text")),
                tool_choice=None,
                tools=None,
                top_p=1.0,
                truncation="disabled",
                usage=None,
                user=None,
                metadata=None,
            )

        from typing import Any, Dict, Generator
        def send_streaming_response(  # pragma: no cover
            self,
            request: Any,
        ) -> Generator[Dict[str, Any], None, None]:
            yield {"delta": "not used"}

    offline_client = LLMOpenAIClient(api_key="local", response=LocalDummyResponse())
    offline_provider = OpenAIProvider(client=offline_client)

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
    # força uso da ferramenta para demo offline
    offline_provider.configure_tools(
        [weather_tool],
        tool_choice={"type": "tool", "name": "get_weather"},
    )

    def get_weather(args: Dict[str, Any]) -> str:
        city = args.get("city", "São Paulo")
        return f"{city}, 30 graus."

    offline_provider.register_tool("get_weather", get_weather)

    pergunta = "Qual a temperatura de hoje?"
    print("Pergunta:", pergunta)
    resposta = offline_provider.send_message(pergunta)
    print("Resposta:", resposta or "(vazia)")


def main() -> None:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

    demo_paths()

    if not api_key:
        logger.warning("OPENAI_API_KEY não definida; seções online serão ignoradas.")
        print("Dica: defina sua chave e execute novamente para ver as chamadas reais.")
        # Executa demo offline de Tool Calling mesmo sem chave
        demo_local_tool_forecast()
        return

    demo_client_basic(api_key)
    if os.getenv("DEMO_TOOL_CALLING"):
        demo_provider_with_tools(api_key)
    else:
        section("[5] Provider + Tool Calling (exemplo opcional)")
        print("Defina DEMO_TOOL_CALLING=1 para tentar a seção de Tool Calling.")
    # Sempre exibe também a versão offline da demo de ferramenta
    demo_local_tool_forecast()


if __name__ == "__main__":
    main()
