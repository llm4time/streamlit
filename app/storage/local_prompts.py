from .local_storage import LocalStorage
from typing import Dict, List
from .base import BasePromptsStorage
from .exceptions import PromptAlreadyExistsError, PromptNotFoundError
from config import logger


class LocalPromptsStorage(BasePromptsStorage):
  def __init__(self, storage_key: str = "prompts"):
    self.storage = LocalStorage()
    self.storage_key = storage_key

  def _load(self) -> List[Dict]:
    return self.storage.get_item(self.storage_key) or []

  def _save(self, prompts: List[Dict]) -> None:
    self.storage.update_items(self.storage_key, prompts)

  def insert(self, name: str, content: str, variables: dict = None) -> bool:
    variables = variables or {}
    try:
      prompts = self._load()
      if any(p["name"] == name for p in prompts):
        raise PromptAlreadyExistsError(f"Prompt '{name}' already exists.")

      self.storage.set_item(
          self.storage_key,
          {"name": name, "content": content, "variables": variables}
      )

      logger.info(f"Prompt '{name}' inserted successfully.")
      return True
    except Exception as e:
      logger.error(f"Error inserting prompt: {e}")
      raise

  def select(self, name: str) -> Dict | None:
    try:
      prompts = self._load()
      prompt = next((p for p in prompts if p["name"] == name), None)
      if not prompt:
        raise PromptNotFoundError(f"Prompt '{name}' not found.")
      return prompt
    except Exception as e:
      logger.error(f"Error selecting prompt: {e}")
      raise

  def select_all(self) -> List[Dict]:
    try:
      return self._load()
    except Exception as e:
      logger.error(f"Error selecting all prompts: {e}")
      return []

  def remove(self, name: str) -> bool:
    try:
      prompts = self._load()
      if not any(p["name"] == name for p in prompts):
        raise PromptNotFoundError(f"Prompt '{name}' not found.")
      updated = [p for p in prompts if p["name"] != name]
      self._save(updated)
      logger.info(f"Prompt '{name}' removed successfully.")
    except Exception as e:
      logger.error(f"Error removing prompt: {e}")
      raise

  def remove_many(self, names: List[str]) -> Dict[str, bool]:
    try:
      prompts = self._load()
      results = {}
      for name in names:
        if any(p["name"] == name for p in prompts):
          prompts = [p for p in prompts if p["name"] != name]
          results[name] = True
          logger.info(f"Prompt '{name}' removed successfully.")
        else:
          results[name] = False
          logger.warning(f"Prompt '{name}' not found.")
      self._save(prompts)
      return results
    except Exception as e:
      logger.error(f"Error removing prompts: {e}")
      return {name: False for name in names}

  def update(self, name: str, new_content: str, new_variables: dict) -> bool:
    try:
      prompts = self._load()
      found = False
      for p in prompts:
        if p["name"] == name:
          p["content"] = new_content
          p["variables"] = new_variables
          found = True
          break
      if not found:
        raise PromptNotFoundError(f"Prompt '{name}' not found.")
      self._save(prompts)
      logger.info(f"Prompt '{name}' updated successfully.")
    except Exception as e:
      logger.error(f"Error updating prompt: {e}")
      raise

  def rename(self, old_name: str, new_name: str) -> bool:
    try:
      prompts = self._load()
      if not any(p["name"] == old_name for p in prompts):
        raise PromptNotFoundError(f"Prompt '{old_name}' not found.")
      if any(p["name"] == new_name for p in prompts):
        raise PromptAlreadyExistsError(f"Prompt '{new_name}' already exists.")
      for p in prompts:
        if p["name"] == old_name:
          p["name"] = new_name
          break
      self._save(prompts)
      logger.info(f"Prompt '{old_name}' renamed to '{new_name}'.")
    except Exception as e:
      logger.error(f"Error renaming prompt: {e}")
      raise
