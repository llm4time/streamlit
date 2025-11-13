from .local_storage import LocalStorage
from typing import Any, List, Dict
import base64


class LocalFilesStorage:
  def __init__(self, store_name: str = "uploads"):
    self.store_name = store_name
    self.storage = LocalStorage()
    self._init_store()

  def _init_store(self) -> None:
    data = self.storage.get_item(self.store_name)
    if not isinstance(data, list):
      self.storage._storage.setItem(self.store_name, [])

  def upload(self, file) -> None:
    content = base64.b64encode(file.read()).decode("utf-8")
    self.storage.set_item(self.store_name, {"filename": file.name, "content": content})

  def select_all(self) -> List[Dict[str, Any]]:
    data = self.storage.get_item(self.store_name)
    data = data if isinstance(data, list) else []
    return data

  def exists(self, name: str) -> bool:
    files = self.select_all()
    file_exists = any(f.get("filename") == name for f in files)
    return file_exists

  def rename(self, old_name: str, new_name: str) -> bool:
    files = self.select_all()
    renamed = False
    for f in files:
      if f.get("filename") == old_name:
        f["filename"] = new_name
        renamed = True
    if renamed:
      self.storage.update_items(self.store_name, files)
    return renamed

  def remove(self, name: str) -> None:
    records = self.select_all()
    updated = [r for r in records if r.get("filename") != name]
    self.storage.update_items(self.store_name, updated)

  def remove_many(self, names: List[str]) -> None:
    records = self.select_all()
    updated = [r for r in records if r.get("filename") not in names]
    self.storage.update_items(self.store_name, updated)

  def clear(self) -> None:
    self.storage.remove_item(self.store_name)
