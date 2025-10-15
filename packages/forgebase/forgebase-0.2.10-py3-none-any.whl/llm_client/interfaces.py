from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List, Optional, Protocol


class ILLMClient(Protocol):
    """Interface agnóstica para clientes LLM com suporte a tool calling.

    Implementações devem prover envio síncrono, streaming e tool calling.
    O parâmetro `context` fica livre (lista de dicts) para permitir estratégias
    diversas de construção de prompt sem acoplamento.

    Esta interface permite que diferentes providers (OpenAI, Llama, Anthropic)
    sejam usados de forma intercambiável sem alterar código cliente.
    """

    @property
    def name(self) -> str:  # noqa: D401
        """Nome do provedor (ex.: 'openai', 'llama', 'anthropic')."""
        ...

    def set_api_key(self, key: str) -> bool:
        """Configura a credencial, retornando True se ficar pronto para uso."""
        ...

    def send_message(self, prompt: str, context: Optional[List[dict]] = None) -> str:
        """Envia um prompt e retorna o texto final."""
        ...

    def send_stream(self, prompt: str, context: Optional[List[dict]] = None) -> Iterable[str]:
        """Gera tokens/trechos de resposta em streaming."""
        ...

    def configure_tools(
        self,
        tools: List[Any],  # List[Tool] - evitando import circular
        tool_choice: str | dict | None = "auto",
    ) -> None:
        """Configura ferramentas disponíveis para tool calling.

        Args:
            tools: Lista de definições Tool (JSON Schema compatível)
            tool_choice: Política de escolha de ferramenta:
                - "auto": LLM decide se usa ferramenta
                - "required": LLM deve usar uma ferramenta
                - {"name": "tool_name"}: Força ferramenta específica
                - None: Desabilita tool calling
        """
        ...

    def register_tool(
        self,
        name: str,
        func: Callable[[Dict[str, Any]], Any],
    ) -> None:
        """Registra handler Python para uma ferramenta.

        Args:
            name: Nome da ferramenta (deve corresponder ao definido em configure_tools)
            func: Função Python que executa a ferramenta. Recebe dict de argumentos
                  e retorna o resultado (será serializado como JSON).

        Example:
            >>> def get_weather(args: dict) -> str:
            ...     city = args["city"]
            ...     return f"{city}, 25°C, ensolarado"
            >>> provider.register_tool("get_weather", get_weather)
        """
        ...


__all__ = ["ILLMClient"]

