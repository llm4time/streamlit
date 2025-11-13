import llm4time as l4t
from helpers import crud
from utils import normalize
from storage.cookies import get_cookie
from config import logger
import numpy as np
import random


class API:
  def __init__(self, model: str, provider: l4t.Provider):
    self.model = model
    self.provider = provider

  def response(self, content: str, temperature: float, **kwargs) -> l4t.ModelResponse:
    if str(self.provider) == str(l4t.Provider.LM_STUDIO):
      return self._lmstudio(content, temperature, **kwargs)
    elif str(self.provider) == str(l4t.Provider.OPENAI):
      return self._openai(content, temperature, **kwargs)
    elif str(self.provider) == str(l4t.Provider.AZURE):
      return self._azure_openai(content, temperature, **kwargs)
    else:
      logger.error(f"Unknown provider: {self.provider}")
      return l4t.ModelResponse(
          raw=f"Unknown provider: {self.provider}",
          predicted=None,
          input_tokens=None,
          output_tokens=None,
          time=None
      )

  def _lmstudio(self, content: str, temperature: float, **kwargs):
    return self._call_client(lambda model: l4t.LMStudio(model),
                             content, temperature, **kwargs)

  def _openai(self, content: str, temperature: float, **kwargs):
    prefix = normalize(f"{self.provider}_{self.model}")
    api_key = get_cookie(f"{prefix}:api_key")
    base_url = get_cookie(f"{prefix}:base_url")
    logger.info(f"BASE_URL: {base_url}")
    return self._call_client(
        lambda model: l4t.OpenAI(api_key=api_key, base_url=base_url, model=model),
        content, temperature, **kwargs
    )

  def _azure_openai(self, content: str, temperature: float, **kwargs):
    prefix = normalize(f"{self.provider}_{self.model}")
    api_key = get_cookie(f"{prefix}:api_key")
    endpoint = get_cookie(f"{prefix}:endpoint")
    api_version = get_cookie(f"{prefix}:api_version")
    logger.info(f"ENDPOINT: {endpoint}")
    logger.info(f"API_VERSION: {api_version}")
    return self._call_client(
        lambda model: l4t.AzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version=api_version,
            model=model
        ),
        content, temperature, **kwargs
    )

  def _get_model_data(self) -> dict:
    models_crud = crud.crud_models()
    all_models = models_crud._load()

    for m in all_models:
      if m["name"] == self.model and m["provider"] == self.provider:
        return m

    logger.warning(f"Model data not found for {self.model} ({self.provider})")
    return {}

  def _call_client(self, client_class, content: str, temperature: float, **kwargs) -> l4t.ModelResponse:
    try:
      client = client_class(self.model)
      response = client.predict(content, temperature=temperature, **kwargs)
      logger.info(f"Response: {response.predicted}")
      logger.info(f"Input Tokens: {response.input_tokens}")
      logger.info(f"Output Tokens: {response.output_tokens}")
      logger.info(f"Time: {response.time:.2f} seconds")
      return response
    except Exception as e:
      logger.error(f"Error generating response: {e}")
      return l4t.ModelResponse(
          raw=str(e),
          predicted=None,
          input_tokens=None,
          output_tokens=None,
          time=None
      )

  @staticmethod
  def _mock(ts: l4t.TimeSeries, tsformat: l4t.TSFormat, tstype: l4t.TSType) -> l4t.ModelResponse:
    pred = ts.copy()
    for column in pred.columns:
      pred[column] = pred[column] + np.random.normal(0, 0.5, size=len(pred))

    response = pred.to_str(format=tsformat, type=tstype)
    response_time = round(random.uniform(0.5, 2.5), 2)
    input_tokens = random.randint(10, 500)
    output_tokens = random.randint(10, 500)
    logger.info(f"Input Tokens: {input_tokens}")
    logger.info(f"Output Tokens: {output_tokens}")
    logger.info(f"Time: {response_time:.2f} seconds")

    return l4t.ModelResponse(
        raw=response,
        predicted=response,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        time=response_time
    )
