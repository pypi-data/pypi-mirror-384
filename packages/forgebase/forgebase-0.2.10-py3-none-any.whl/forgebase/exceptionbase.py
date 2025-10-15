
class ForgeBaseException(Exception):
    """Exceção base para todos os erros da aplicação."""
    def __init__(self, message: str = "Erro na aplicação", cause: Exception | None = None) -> None:
        self.message = message
        self.cause = cause
        super().__init__(self.message)

# Exceções de comando
class CommandException(ForgeBaseException):
    """Erro na execução de comandos."""
    pass

# Exceções de persistência
class PersistenceException(ForgeBaseException):
    """Erro relacionado à persistência de dados."""
    pass
