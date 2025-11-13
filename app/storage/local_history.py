from .local_storage import LocalStorage
from typing import Dict, List, Tuple
from .base import BaseHistoryStorage
from .exceptions import HistoryNotFoundError
from config import logger


class LocalHistoryStorage(BaseHistoryStorage):
  def __init__(self, storage_key: str = "history"):
    self.storage = LocalStorage()
    self.storage_key = storage_key

  def _load(self) -> List[Dict]:
    data = self.storage.get_item(self.storage_key)
    data = data if isinstance(data, list) else []
    return data

  def _save(self, records: List[Dict]) -> None:
    self.storage.update_items(self.storage_key, records)

  def insert(self, **kwargs) -> bool:
    try:
      self.storage.set_item(self.storage_key, kwargs)
      logger.info("Record inserted successfully.")
      return True
    except Exception as e:
      logger.error(f"Error inserting record: {e}")
      raise

  def select(self, dataset: str, prompt_types: List[str]) -> List[Tuple]:
    try:
      records = self._load()
      filtered = [
          r for r in records
          if r.get("dataset") == dataset and r.get("prompt_type") in prompt_types
      ]
      if not filtered:
        return []
      keys = list(filtered[0].keys())
      return [tuple(r[k] for k in keys) for r in filtered]
    except Exception as e:
      logger.error(f"Error selecting records: {e}")
      return []

  def group_by(self, columns: List[str]) -> List[Dict]:
    try:
      if not columns:
        raise ValueError("Columns list cannot be empty.")
      records = self._load()
      filtered = [
          r for r in records
          if all(r.get(k) is not None for k in ("smape", "mae", "rmse"))
      ]
      return sorted(filtered, key=lambda x: tuple(x[c] for c in columns))
    except Exception as e:
      logger.error(f"Error grouping records: {e}")
      return []

  def remove(self, record_id: int) -> bool:
    try:
      records = self._load()
      updated = [r for r in records if r.get("id") != record_id]
      if len(updated) == len(records):
        raise HistoryNotFoundError(f"Record with id {record_id} not found.")
      self._save(updated)
      logger.info(f"Record {record_id} removed successfully.")
      return True
    except Exception as e:
      logger.error(f"Error removing record: {e}")
      raise

  def remove_many(self, dataset: str, prompt_types: List[str]) -> bool:
    try:
      records = self._load()
      updated = [
          r for r in records
          if not (r.get("dataset") == dataset and r.get("prompt_type") in prompt_types)
      ]
      self._save(updated)
      logger.info("Records removed successfully.")
      return True
    except Exception as e:
      logger.error(f"Error removing records: {e}")
      raise

  def remove_all(self) -> bool:
    try:
      self._save([])
      logger.info("All records removed successfully.")
      return True
    except Exception as e:
      logger.error(f"Error clearing history: {e}")
      raise
