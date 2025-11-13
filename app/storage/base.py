from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple, Optional


class BaseHistoryStorage(ABC):
  @abstractmethod
  def insert(self, **kwargs) -> bool:
    pass

  @abstractmethod
  def select(self, dataset: str, prompt_types: List[str]) -> List[Dict[str, Any]]:
    pass

  @abstractmethod
  def group_by(self, columns: List[str]) -> Tuple[List[Dict[str, Any]], List[str]]:
    pass

  @abstractmethod
  def remove(self, record_id: int) -> bool:
    pass

  @abstractmethod
  def remove_many(self, dataset: str, prompt_types: List[str]) -> bool:
    pass

  @abstractmethod
  def remove_all(self) -> bool:
    pass


class BaseModelsStorage(ABC):
  @abstractmethod
  def insert(self, name: str, provider: str) -> bool:
    pass

  @abstractmethod
  def select(self, provider: str) -> List[Dict]:
    pass

  @abstractmethod
  def select_all(self) -> List[Dict]:
    pass

  @abstractmethod
  def remove_many(self, models_to_remove: List[Tuple[str, str]]) -> Dict[Tuple[str, str], bool]:
    pass

  @abstractmethod
  def rename(self, old_name: str, new_name: str, provider: str) -> bool:
    pass


class BasePromptsStorage(ABC):
  @abstractmethod
  def insert(self, name: str, content: str, variables: dict | None = None) -> bool:
    pass

  @abstractmethod
  def select(self, name: str) -> Optional[Dict]:
    pass

  @abstractmethod
  def select_all(self) -> List[Dict]:
    pass

  @abstractmethod
  def remove(self, name: str) -> bool:
    pass

  @abstractmethod
  def remove_many(self, names: List[str]) -> Dict[str, bool]:
    pass

  @abstractmethod
  def update(self, name: str, new_content: str, new_variables: dict) -> bool:
    pass

  @abstractmethod
  def rename(self, old_name: str, new_name: str) -> bool:
    pass
