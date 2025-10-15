from typing import Any, Callable, Dict, List, Set

from forge_utils.log_service import logger
from pydantic import BaseModel, PrivateAttr

from .commandbase import IBaseCommand
from .interfaces import IBaseModel
from .persistencebase import IBasePersistence

Observer = Callable[[str, Any, Any], None]  # campo, valor antigo, novo valor

class BaseModelData(BaseModel):
    _field_observers: Dict[str, List[Observer]] = PrivateAttr(default_factory=dict)
    _model_observers: List[Observer] = PrivateAttr(default_factory=list)
    _modified_fields: Set[str] = PrivateAttr(default_factory=set)
    _original_data: Dict[str, Any] = PrivateAttr(default_factory=dict)

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self._original_data = self.dict()
        self._modified_fields = set()
        self._field_observers = {}
        self._model_observers = []

    def __setattr__(self, name: str, value: Any) -> None:
        if name in self.__fields__:
            current_value = getattr(self, name, None)
            if current_value != value:
                self._notify_observers(name, current_value, value)
                self._modified_fields.add(name)
        super().__setattr__(name, value)

    def _notify_observers(self, field: str, old_value: Any, new_value: Any) -> None:
        # Observadores específicos de campo
        for observer in self._field_observers.get(field, []):
            observer(field, old_value, new_value)

        # Observadores do modelo inteiro
        for observer in self._model_observers:
            observer(field, old_value, new_value)

        # Callback genérico
        self._on_field_change(field, old_value, new_value)

    def _on_field_change(self, field: str, old_value: Any, new_value: Any) -> None:
        """Sobrescreva este método em subclasses se quiser agir sobre qualquer mudança."""
        pass

    def _add_field_observer(self, field: str, callback: Observer) -> None:
        if field not in self._field_observers:
            self._field_observers[field] = []
        self._field_observers[field].append(callback)

    def _add_model_observer(self, callback: Observer) -> None:
        self._model_observers.append(callback)

    def modified_fields(self) -> Set[str]:
        return self._modified_fields

    def was_modified(self, field_name: str) -> bool:
        return field_name in self._modified_fields

    @property
    def is_dirty(self) -> bool:
        return bool(self._modified_fields)

    def reset_dirty_state(self) -> None:
        self._original_data = self.dict()
        self._modified_fields.clear()

class CustomBaseModel(IBaseModel):
    _commands: Dict[str, IBaseCommand]
    _persistence: IBasePersistence | None
    _datamodel: BaseModelData | None

    def __init__(self, persistence: IBasePersistence | None = None, data: BaseModelData | None = None) -> None:
        self._persistence = persistence
        self._datamodel = data
        self._commands = {}
        self._messages: List[Any] = []

    def get_value(self, field_name: str) -> Any:
        assert self._datamodel is not None
        return getattr(self._datamodel, field_name)

    def set_value(self, field_name: str, value: Any) -> Any:
        assert self._datamodel is not None
        setattr(self._datamodel, field_name, value)


    def on_field_change(self, field: str, old_value: Any, new_value: Any) -> None:
        """Sobrescreva este método em subclasses se quiser agir sobre qualquer mudança."""
        pass

    def add_field_observer(self, field: str, callback: Observer) -> None:
        assert self._datamodel is not None
        self._datamodel._add_field_observer(field, callback)

    def add_model_observer(self, callback: Observer) -> None:
        assert self._datamodel is not None
        self._datamodel._add_model_observer(callback)

    def load_data(self) -> bool:
        assert self._persistence is not None
        assert self._datamodel is not None
        loaded = self._persistence.load_data(self._datamodel)
        self._datamodel.reset_dirty_state()
        return loaded

    def save_data(self) -> Any:
        assert self._persistence is not None
        assert self._datamodel is not None
        result = self._persistence.save_data(self._datamodel)
        self._datamodel.reset_dirty_state()
        return result

    def get_data(self) -> BaseModelData:
        assert self._datamodel is not None
        return self._datamodel

    def add_command(self, name: str, command: IBaseCommand) -> None:
        """Registra um novo comando pelo nome."""
        if name in self._commands:
            logger.warning(f"Comando '{name}' já existe e será sobrescrito.")
        self._commands[name] = command  # ← Novo método

    def remove_command(self, name: str) -> None:
        """Remove um comando registrado."""
        self._commands.pop(name, None)  # ← Novo método

    def exec_command(self, command_name: str, **params: Any) -> Any:
        """Executa um comando registrado com parâmetros."""
        command = self._commands.get(command_name)
        if not command:
            raise ValueError(f"Comando '{command_name}' não registrado.")  # ← Tratamento de erro
        return command.execute(**params)  # ← Execução dinâmica
