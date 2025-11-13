from .local_storage import LocalStorage
from typing import Dict, List, Tuple
from .base import BaseModelsStorage
from .exceptions import ModelAlreadyExistsError, ModelNotFoundError
from config import logger


class LocalModelsStorage(BaseModelsStorage):
  def __init__(self, storage_key: str = "models"):
    self.storage = LocalStorage()
    self.storage_key = storage_key

  def _load(self) -> List[Dict]:
    data = self.storage.get_item(self.storage_key)
    data = data if isinstance(data, list) else []
    return data

  def _save(self, models: List[Dict]) -> None:
    self.storage.update_items(self.storage_key, models)

  def insert(self, name: str, provider: str) -> bool:
    try:
      models = self._load()
      if any(m["name"] == name and m["provider"] == provider for m in models):
        raise ModelAlreadyExistsError(
            f"Model '{name}' already exists for provider '{provider}'."
        )

      self.storage.set_item(self.storage_key, {
          "name": name,
          "provider": provider
      })

      logger.info(f"Model '{name}' inserted successfully (Local).")
      return True
    except Exception as e:
      logger.error(f"Error inserting model: {e}")
      raise

  def select(self, provider: str) -> List[Tuple[int, str, str]]:
    try:
      models = self._load()
      filtered = [m for m in models if m["provider"] == provider]
      return [(m["id"], m["name"], m["provider"]) for m in filtered]
    except Exception as e:
      logger.error(f"Error selecting models: {e}")
      return []

  def select_all(self) -> List[Tuple[int, str, str]]:
    try:
      models = self._load()
      return [(m["id"], m["name"], m["provider"]) for m in models]
    except Exception as e:
      logger.error(f"Error selecting all models: {e}")
      return []

  def remove_many(self, models_to_remove: List[Tuple[str, str]]) -> Dict[Tuple[str, str], bool]:
    try:
      models = self._load()
      results = {}
      for name, provider in models_to_remove:
        found = any(m["name"] == name and m["provider"] == provider for m in models)
        if not found:
          logger.warning(f"Model '{name}' ({provider}) not found.")
          results[(name, provider)] = False
          continue
        models = [m for m in models if not (
            m["name"] == name and m["provider"] == provider)]
        logger.info(f"Model '{name}' ({provider}) removed successfully.")
        results[(name, provider)] = True

      self._save(models)
      return results
    except Exception as e:
      logger.error(f"Error removing models: {e}")
      return {k: False for k in models_to_remove}

  def rename(self, old_name: str, new_name: str, provider: str) -> bool:
    try:
      models = self._load()
      if not any(m["name"] == old_name and m["provider"] == provider for m in models):
        raise ModelNotFoundError(
            f"Model '{old_name}' not found for provider '{provider}'."
        )

      if any(m["name"] == new_name and m["provider"] == provider for m in models):
        raise ModelAlreadyExistsError(
            f"Model '{new_name}' already exists for provider '{provider}'."
        )

      for m in models:
        if m["name"] == old_name and m["provider"] == provider:
          m["name"] = new_name
          break

      self._save(models)
      logger.info(f"Model '{old_name}' renamed to '{new_name}'.")
      return True
    except Exception as e:
      logger.error(f"Error renaming model: {e}")
      raise
