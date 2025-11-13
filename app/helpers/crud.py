import storage
# from utils import abspath


def crud_history():
  return storage.LocalHistoryStorage()
  # return storage.SQLiteHistoryStorage(abspath("storage/database.db"))


def crud_models():
  return storage.LocalModelsStorage()
  # return storage.SQLiteModelsStorage(abspath("storage/database.db"))


def crud_prompts():
  return storage.LocalPromptsStorage()
  # return storage.SQLitePromptsStorage(abspath("storage/database.db"))


def crud_files():
  return storage.LocalFilesStorage()
  # return storage.SQLiteFilesStorage(abspath("storage/database.db"))
