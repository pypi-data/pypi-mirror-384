"""Factory para criação de providers LLM agnósticos.

Este módulo implementa o padrão Factory para encapsular a criação de providers
LLM, permitindo que código cliente dependa apenas de abstrações (ILLMClient)
sem conhecer implementações específicas (OpenAIProvider, LlamaProvider, etc.).

Example:
    >>> from llm_client import LLMClientFactory
    >>> provider = LLMClientFactory.create("openai", api_key="sk-...")
    >>> provider.send_message("Hello")

    >>> # Auto-configuração via variável de ambiente
    >>> provider = LLMClientFactory.create_from_env("openai")

    >>> # Trocar provider transparentemente
    >>> provider = LLMClientFactory.create("llama")  # Mesma interface!
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, Dict, Optional, Type

from .llm_exceptions import ConfigurationError

if TYPE_CHECKING:
    from .interfaces import ILLMClient


class LLMClientFactory:
    """Factory para criação de providers LLM sem expor implementações específicas.

    Esta factory permite:
    - Criar providers por nome sem conhecer classe concreta
    - Carregar configuração de variáveis de ambiente
    - Registrar providers customizados sem alterar código da biblioteca
    - Trocar providers mudando apenas uma string de configuração

    Attributes:
        _providers: Mapeamento de nome -> classe de provider
    """

    _providers: Dict[str, Type[ILLMClient]] = {}

    @classmethod
    def _ensure_providers_loaded(cls) -> None:
        """Carrega providers disponíveis sob demanda (lazy loading).

        Evita imports circulares e carrega providers apenas quando necessário.
        """
        if cls._providers:
            return

        # Import apenas quando necessário
        from .openai_provider import OpenAIProvider

        cls._providers = {
            "openai": OpenAIProvider,
            # Futuros providers serão adicionados aqui:
            # "llama": LlamaProvider,
            # "anthropic": AnthropicProvider,
        }

    @classmethod
    def create(
        cls,
        provider: str = "openai",
        api_key: Optional[str] = None,
        **kwargs: Any,
    ) -> ILLMClient:
        """Cria uma instância de provider LLM por nome.

        Args:
            provider: Nome do provider ("openai", "llama", "anthropic", etc.)
            api_key: Chave de API (opcional, pode ser configurada depois com set_api_key)
            **kwargs: Parâmetros específicos do provider:
                - timeout: Timeout em segundos (padrão: 120)
                - model: Nome do modelo (ex: "gpt-4o", "llama-3")
                - temperature: Temperatura de sampling (0.0-2.0)
                - max_tokens: Máximo de tokens na resposta

        Returns:
            Instância implementando ILLMClient

        Raises:
            ConfigurationError: Se provider não existe ou não está registrado

        Example:
            >>> provider = LLMClientFactory.create(
            ...     provider="openai",
            ...     api_key="sk-...",
            ...     timeout=60,
            ...     model="gpt-4o-mini"
            ... )
            >>> result = provider.send_message("Hello!")
        """
        cls._ensure_providers_loaded()

        if provider not in cls._providers:
            available = ", ".join(sorted(cls._providers.keys()))
            raise ConfigurationError(
                f"Provider '{provider}' não suportado. "
                f"Disponíveis: {available}"
            )

        provider_class = cls._providers[provider]
        instance = provider_class(**kwargs)

        if api_key:
            instance.set_api_key(api_key)

        return instance

    @classmethod
    def create_from_env(
        cls,
        provider: str = "openai",
        **kwargs: Any,
    ) -> ILLMClient:
        """Cria provider carregando API key de variável de ambiente.

        Busca por variáveis de ambiente no formato:
        - OPENAI_API_KEY (para provider="openai")
        - LLAMA_API_KEY (para provider="llama")
        - ANTHROPIC_API_KEY (para provider="anthropic")
        - {PROVIDER_UPPER}_API_KEY (genérico)

        Args:
            provider: Nome do provider
            **kwargs: Parâmetros adicionais (timeout, model, etc.)

        Returns:
            Provider configurado com API key do ambiente

        Raises:
            ConfigurationError: Se variável de ambiente não existe

        Example:
            >>> # Com OPENAI_API_KEY definido no ambiente
            >>> provider = LLMClientFactory.create_from_env("openai")
            >>> provider.send_message("Hello!")
        """
        env_key_map = {
            "openai": "OPENAI_API_KEY",
            "llama": "LLAMA_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
        }

        env_var = env_key_map.get(provider, f"{provider.upper()}_API_KEY")
        api_key = os.environ.get(env_var)

        if not api_key:
            raise ConfigurationError(
                f"Variável de ambiente '{env_var}' não encontrada para "
                f"provider '{provider}'. Configure a variável ou use "
                f"LLMClientFactory.create() com api_key explícito."
            )

        return cls.create(provider=provider, api_key=api_key, **kwargs)

    @classmethod
    def register_provider(
        cls,
        name: str,
        provider_class: Type[ILLMClient],
    ) -> None:
        """Registra um novo provider customizado.

        Permite extensão da factory sem modificar código da biblioteca.
        Útil para providers customizados, experimentais ou proprietários.

        Args:
            name: Nome identificador do provider (usado em create())
            provider_class: Classe que implementa ILLMClient Protocol

        Example:
            >>> class MyCustomProvider:
            ...     name = "custom"
            ...     def set_api_key(self, key): ...
            ...     def send_message(self, prompt): ...
            ...     # ... resto da interface ILLMClient
            >>>
            >>> LLMClientFactory.register_provider("custom", MyCustomProvider)
            >>> provider = LLMClientFactory.create("custom")
        """
        cls._ensure_providers_loaded()
        cls._providers[name] = provider_class

    @classmethod
    def list_providers(cls) -> list[str]:
        """Lista todos os providers disponíveis.

        Returns:
            Lista de nomes de providers registrados

        Example:
            >>> LLMClientFactory.list_providers()
            ['anthropic', 'llama', 'openai']
        """
        cls._ensure_providers_loaded()
        return sorted(cls._providers.keys())


__all__ = ["LLMClientFactory"]
