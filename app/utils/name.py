import unicodedata
import re


def normalize(string: str) -> str:
  string = unicodedata.normalize('NFKD', string).encode(
      'ASCII', 'ignore').decode('utf-8')
  string = re.sub(r'[^a-zA-Z0-9]', '_', string)
  string = re.sub(r'_+', '_', string)
  return string.strip('_').lower()
