from streamlit_local_storage import LocalStorage as StreamlitLS
from typing import Any, List, Dict
import time


class LocalStorage:
  def __init__(self):
    self._storage = StreamlitLS()

  def _load(self, key: str) -> List[Dict[str, Any]]:
    data = self._storage.getItem(key)
    data = data if isinstance(data, list) else []
    time.sleep(1)
    return data

  def _next_id(self, records: List[Dict[str, Any]]) -> int:
    return max((r.get("id", 0) for r in records), default=0) + 1

  def set_item(self, key: str, value: Dict[str, Any]) -> None:
    records = self._load(key)
    next_id = self._next_id(records)
    value_with_id = {"id": next_id, **value}
    records.append(value_with_id)
    self._storage.setItem(key, records)
    time.sleep(1)

  def get_item(self, key: str) -> Any:
    data = self._load(key)
    return data

  def update_items(self, key: str, records: List[Dict[str, Any]]) -> None:
    self._storage.setItem(key, records)
    time.sleep(1)

  def remove_item(self, key: str) -> None:
    self._storage.eraseItem(key)
    time.sleep(1)

  def clear(self) -> None:
    self._storage.deleteAll()
    time.sleep(1)
