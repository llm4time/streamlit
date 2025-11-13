class HistoryNotFoundError(Exception):
  """
  Exception raised when a record is not found in the history table.

  This exception is used when operations attempt to access records
  that do not exist in the database.
  """
  pass


class ModelNotFoundError(Exception):
  """
  Exception raised when a model is not found in the models table.

  This exception is used when operations attempt to access models
  that do not exist in the database.
  """
  pass


class ModelAlreadyExistsError(Exception):
  """
  Exception raised when trying to insert a model that already exists.

  This exception is used when there is an attempt to create duplicates
  in the unique combination of name and provider.
  """
  pass


class PromptNotFoundError(Exception):
  """Exception raised when a prompt is not found in the prompts table."""
  pass


class PromptAlreadyExistsError(Exception):
  """Exception raised when trying to insert a prompt that already exists."""
  pass
