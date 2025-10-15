class FgLLMError(Exception):
    """Erro base da biblioteca fgllmclient."""


class InvalidRequestError(FgLLMError):
    """Erro na formação da requisição enviada."""


class APIResponseError(FgLLMError):
    """Erro ao processar a resposta da API."""


class StreamingError(FgLLMError):
    """Erro durante o processo de streaming."""


class ConfigurationError(FgLLMError):
    """Erro de configuração interna do cliente."""
