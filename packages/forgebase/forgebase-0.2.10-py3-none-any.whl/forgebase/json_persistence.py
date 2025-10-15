import json
from pathlib import Path

from forge_utils.log_service import logger
from pydantic import BaseModel

from .interfaces import IBasePersistence


class JSonPersistence(IBasePersistence):
    def __init__(self, file_name: str):
        self.file_name = Path(file_name)

    def load_data(self, model: BaseModel) -> bool:
        logger.info(f"Carregando dados de {self.file_name}")

        if not self.file_name.exists():
            logger.warning("Arquivo JSON não encontrado.")
            return False

        try:
            with self.file_name.open('r', encoding='utf-8') as file:
                data = json.load(file)

                # ✅ Substitui a instância atual por uma validada
                validated_model = model.__class__.model_validate(data)
                model.__dict__.update(validated_model.__dict__)

                logger.info("Dados carregados com sucesso.")
            return True

        except Exception as e:
            logger.error(f"Erro ao carregar dados: {e}")
            return False

    def save_data(self, model: BaseModel) -> None:
        try:
            logger.info(f"Salvando dados em {self.file_name}")
            with self.file_name.open('w', encoding='utf-8') as file:
                json.dump(
                    model.model_dump(mode="json"),  # Pydantic v2
                    file,
                    ensure_ascii=False,
                    indent=4
                )
            logger.info("Dados salvos com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao salvar dados: {e}")
