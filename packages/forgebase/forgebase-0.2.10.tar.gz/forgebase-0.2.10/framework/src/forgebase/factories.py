from typing import Any, Dict, Optional, Type

from .interfaces import IBasePersistence


class PersistenceFactory:
    _services: Dict[str, Type[IBasePersistence]] = {}  # Armazena classes, não instâncias

    @classmethod
    def register(cls, service_name: str, service_class: Type[IBasePersistence]) -> None:
        """Registra uma classe de serviço pelo nome"""
        cls._services[service_name] = service_class

    @classmethod
    def create(cls, service_name: str, **kwargs: Any) -> Optional[IBasePersistence]:  # renomeado e alterado
        """
        Cria uma nova instância do serviço registrado, passando argumentos para o construtor.
        """
        service_class = cls._services.get(service_name)
        if not service_class:
            return None

        return service_class(**kwargs)  # sempre cria nova instância
