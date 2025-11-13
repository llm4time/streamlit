from streamlit_cookies_controller import CookieController
import time

controller = CookieController()


def set_cookie(key: str, value: str, expires: int | None = None) -> None:
  controller.set(key, value, max_age=expires)
  time.sleep(1)


def get_cookie(key: str, default=None) -> str | None:
  data = controller.get(key) or default
  time.sleep(1)
  return data


def delete_cookie(key: str) -> None:
  controller.remove(key)
  time.sleep(1)


def rename_cookie(old_key: str, new_key: str) -> None:
  value = get_cookie(old_key)
  if value is not None:
    set_cookie(new_key, value)
    delete_cookie(old_key)


def clear_cookies() -> None:
  for key in controller.getAll().keys():
    delete_cookie(key)


def all_cookies() -> dict:
  data = controller.getAll()
  time.sleep(1)
  return data
