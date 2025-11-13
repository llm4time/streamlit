import os


def abspath(path: str) -> str:
  """Get the absolute path relative to the project root."""
  root = os.path.dirname(os.path.dirname(__file__))
  return os.path.normpath(os.path.join(root, path))
