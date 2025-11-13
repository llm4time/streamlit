import streamlit as st
import llm4time as l4t
import pandas as pd
from helpers import crud
from utils import normalize
from storage.cookies import set_cookie, rename_cookie, delete_cookie
import storage.exceptions as exceptions
from streamlit_theme import st_theme

theme = st_theme()
if theme is None:
  st.stop()

css = f"""
.st-key-api-tabs,
.st-key-custom-prompts-tabs {{
  padding: 1rem;
  border-radius: 0.5rem;
  background-color: {theme["secondaryBackgroundColor"]};
}}
"""
st.html(f"<style>{css}</style>")


def save_model(provider: str, name: str) -> None:
  try:
    crud.crud_models().insert(provider=provider, name=name)
    st.toast("Settings saved successfully!", icon="✅")
  except exceptions.ModelAlreadyExistsError:
    st.toast(f"The model **{name}** for **{provider}** already exists.", icon="❌")
    raise
  except exceptions.ModelNotFoundError:
    st.toast(f"The model **{name}** for **{provider}** was not found.", icon="❌")
    raise
  except Exception:
    st.toast("Error saving settings.", icon="❌")
    raise


def rename_model(old_name: str, new_name: str, provider: str) -> None:
  try:
    crud.crud_models().rename(old_name=old_name, new_name=new_name, provider=provider)
    st.toast("Model renamed successfully!", icon="✅")
  except exceptions.ModelAlreadyExistsError:
    st.toast(f"The model **{new_name}** for **{provider}** already exists.", icon="❌")
  except Exception:
    st.toast("Error renaming model.", icon="❌")


def delete_models(models: list[tuple]) -> None:
  try:
    crud.crud_models().remove_many(models)
    st.toast("Models deleted successfully!", icon="✅")
  except Exception:
    st.toast("Error deleting models.", icon="❌")
    raise


def delete_prompts(prompt_names: list[str]) -> None:
  try:
    n = len(prompt_names)
    crud.crud_prompts().remove_many(prompt_names)
    st.toast(f"Prompt{'s' if n > 1 else ''} deleted successfully!", icon="✅")
  except Exception:
    st.toast("Error deleting prompts.", icon="❌")
    raise


if "save_settings" in st.session_state and st.session_state.save_settings:
  if "provider" in st.session_state:
    if st.session_state.provider == str(l4t.Provider.OPENAI):
      try:
        save_model(provider=st.session_state.provider, name=st.session_state.model)
        prefix = normalize(f"{st.session_state.provider}_{st.session_state.model}")
        set_cookie(f"{prefix}:api_key", st.session_state.api_key, expires=30*24*60*60)
        set_cookie(f"{prefix}:base_url", st.session_state.base_url, expires=30*24*60*60)
      except:
        st.toast("Error saving settings.", icon="❌")
      finally:
        del st.session_state.api_key
        del st.session_state.base_url
    elif st.session_state.provider == str(l4t.Provider.AZURE):
      try:
        save_model(provider=st.session_state.provider, name=st.session_state.model)
        prefix = normalize(f"{st.session_state.provider}_{st.session_state.model}")
        set_cookie(f"{prefix}:api_key", st.session_state.api_key, expires=30*24*60*60)
        set_cookie(f"{prefix}:endpoint", st.session_state.endpoint, expires=30*24*60*60)
        set_cookie(f"{prefix}:api_version",
                   st.session_state.api_version, expires=30*24*60*60)
      except:
        st.toast("Error saving settings.", icon="❌")
      finally:
        del st.session_state.api_key
        del st.session_state.endpoint
        del st.session_state.api_version
    del st.session_state.provider
    del st.session_state.save_settings
    st.rerun()


if "rename_model" in st.session_state and st.session_state.rename_model:
  try:
    rename_model(
        old_name=st.session_state.old_model,
        new_name=st.session_state.new_model,
        provider=st.session_state.provider
    )
    old_prefix = normalize(f"{st.session_state.provider}_{st.session_state.old_model}")
    new_prefix = normalize(f"{st.session_state.provider}_{st.session_state.new_model}")
    if st.session_state.provider == str(l4t.Provider.OPENAI):
      rename_cookie(f"{old_prefix}:api_key", f"{new_prefix}:api_key")
      rename_cookie(f"{old_prefix}:base_url", f"{new_prefix}:base_url")
    elif st.session_state.provider == str(l4t.Provider.AZURE):
      rename_cookie(f"{old_prefix}:api_key", f"{new_prefix}:api_key")
      rename_cookie(f"{old_prefix}:endpoint", f"{new_prefix}:endpoint")
      rename_cookie(f"{old_prefix}:api_version", f"{new_prefix}:api_version")
  except Exception:
    st.toast("Error renaming model.", icon="❌")
  finally:
    del st.session_state.rename_model
    del st.session_state.old_model
    del st.session_state.new_model
    del st.session_state.provider
    st.rerun()

if "confirm_delete" in st.session_state and st.session_state.confirm_delete:
  if "models_to_delete" in st.session_state:
    try:
      delete_models(st.session_state.models_to_delete)
      for model, provider in st.session_state.models_to_delete:
        prefix = normalize(f"{provider}_{model}")
        delete_cookie(f"{prefix}:api_key")
        delete_cookie(f"{prefix}:base_url")
    except Exception:
      st.toast("Error deleting models.", icon="❌")
    finally:
      del st.session_state.models_to_delete
      st.rerun()
  elif "prompts_to_delete" in st.session_state:
    try:
      delete_prompts(st.session_state.prompts_to_delete)
    except Exception:
      st.toast("Error deleting prompts.", icon="❌")
    finally:
      del st.session_state.prompts_to_delete
  del st.session_state.confirm_delete
  st.rerun()

# ---------------- Configure Model ----------------

if "mode" not in st.session_state:
  st.session_state.mode = l4t.Provider.LM_STUDIO

st.write(f"### API")
with st.container(key="api-tabs"):
  col1, col2, col3 = st.columns(3)
  with col1:
    selected = st.session_state.mode == l4t.Provider.LM_STUDIO
    if st.button("LM Studio", type="primary" if selected else "tertiary", width="stretch"):
      st.session_state.mode = l4t.Provider.LM_STUDIO
      st.rerun()
  with col2:
    selected = st.session_state.mode == l4t.Provider.OPENAI
    if st.button("OpenAI / Ollama", type="primary" if selected else "tertiary", width="stretch"):
      st.session_state.mode = l4t.Provider.OPENAI
      st.rerun()
  with col3:
    selected = st.session_state.mode == l4t.Provider.AZURE
    if st.button("OpenAI Azure", type="primary" if selected else "tertiary", width="stretch"):
      st.session_state.mode = l4t.Provider.AZURE
      st.rerun()

if st.session_state.mode == l4t.Provider.LM_STUDIO:
  st.write(
      "You will be redirected to LM Studio. If you do not have LM Studio installed, "
      "you can download it [here](https://lmstudio.ai)."
  )
  model = st.text_input(
      label="Model",
      placeholder="deepseek-r1",
      help="Enter the name of the model you want to use in LM Studio."
  )
  confirm = st.button(
      type="primary",
      label="💾 Save Settings",
      help="Click to save the settings."
  )

elif st.session_state.mode == l4t.Provider.OPENAI:
  st.write(
      "You will be redirected to the API. If you do not have an API key, "
      "you can obtain one [here](https://platform.openai.com/signup)."
  )
  api_key = st.text_input(
      label="API Key",
      type="password",
      help="Enter the API key you want to use.",
      placeholder="********************************"
  )
  model = st.text_input(
      label="Model",
      help="Enter the name of the model you want to use.",
      placeholder="gpt-3.5-turbo"
  )
  base_url = st.text_input(
      label="Base URL",
      help="Enter the base URL you want to use.",
      placeholder="https://api.example.com/openai/v1"
  )
  confirm = st.button(
      type="primary",
      label="💾 Save Settings",
      help="Click to save the settings."
  )
  if confirm and not (api_key and model and base_url):
    st.toast("Please fill in all fields before saving the settings.", icon="⚠️")
  elif confirm:
    st.session_state.save_settings = True
    st.session_state.api_key = api_key
    st.session_state.base_url = base_url
    st.session_state.model = model
    st.session_state.provider = str(l4t.Provider.OPENAI)
    st.rerun()

elif st.session_state.mode == l4t.Provider.AZURE:
  st.write(
      "You will be redirected to the API. If you do not have an API key, "
      "you can obtain one [here](https://portal.azure.com)."
  )
  api_key = st.text_input(
      label="API Key",
      type="password",
      placeholder="********************************",
      help="Enter the API key you want to use."
  )
  model = st.text_input(
      label="Model",
      placeholder="gpt-3.5-turbo",
      help="Enter the name of the model you want to use.",
  )
  api_version = st.text_input(
      label="API Version",
      placeholder="Ex: 2024-05-01-preview",
      help="Enter the API version you want to use."
  )
  endpoint = st.text_input(
      label="Endpoint",
      placeholder="Ex: https://<resource-name>.services.ai.azure.com",
      help="Enter the endpoint you want to use."
  )
  confirm = st.button(
      "💾 Save Settings",
      help="Click to save the settings.",
      type="primary",
  )
  if confirm and not (api_key and model and api_version and endpoint):
    st.toast("Please fill in all fields before saving the settings.", icon="⚠️")
  elif confirm:
    st.session_state.save_settings = True
    st.session_state.api_key = api_key
    st.session_state.endpoint = endpoint
    st.session_state.api_version = api_version
    st.session_state.model = model
    st.session_state.provider = str(l4t.Provider.AZURE)
    st.rerun()


# ---------------- All models ----------------

@st.dialog("Confirm deletion")
def delete_models_dialog(models: list[tuple[str, str]]):
  n = len(models)
  if n == 1:
    model, provider = models[0]
    st.write(
        f"Are you sure you want to delete the model **{model}** from the API **{provider}**?")
  else:
    st.write(f"Are you sure you want to delete **{n} models**?")
  st.caption("**⚠️ This action cannot be undone.**")
  col1, col2 = st.columns(2)
  with col1:
    if st.button("No", width="stretch"):
      st.rerun()
  with col2:
    if st.button("Yes, delete", width="stretch", type="primary"):
      st.session_state.confirm_delete = True
      st.session_state.models_to_delete = models
      st.rerun()


st.write("---")
st.write("### Models")
st.write("This section displays the models configured in the [#api](#api) section.")

models = crud.crud_models().select_all()
if len(models) > 0:
  df_models = st.data_editor(
      pd.DataFrame([
          {"Model": f"👾 {model_name}", "API": provider, "Delete": False}
          for _, model_name, provider in models]),
      disabled=["API"],
      hide_index=True,
      width="stretch")

  for idx, row in df_models.iterrows():
    old_model = models[idx][1]
    new_model = row["Model"].replace("👾 ", "")
    provider = models[idx][2]
    if old_model != new_model:
      st.session_state.rename_model = True
      st.session_state.old_model = old_model
      st.session_state.new_model = new_model
      st.session_state.provider = provider
      st.rerun()

  models_to_delete = [
      (models[idx][1], models[idx][2])
      for idx, row in df_models.iterrows()
      if row["Delete"]]

  n = len(models_to_delete)
  if models_to_delete and st.button(label=f"🗑️ Delete {n} model{'s' if n > 1 else ''}", type="primary"):
    delete_models_dialog(models_to_delete)
else:
  st.data_editor(
      pd.DataFrame([{"Model": "", "API": "", "Delete": ""}]),
      disabled=["Model", "API", "Delete"],
      hide_index=True,
      width="stretch")


# ---------------- Create / Edit Prompts ----------------

st.write("---")
st.write("### Custom Prompts")

if "action" not in st.session_state:
  st.session_state.action = "create"

with st.container(key="custom-prompts-tabs"):
  col1, col2 = st.columns(2)
  with col1:
    selected = st.session_state.action == "create"
    if st.button("Create", type="primary" if selected else "tertiary", width="stretch"):
      st.session_state.action = "create"
      st.rerun()
  with col2:
    selected = st.session_state.action == "edit"
    if st.button("Edit", type="primary" if selected else "tertiary", width="stretch"):
      st.session_state.action = "edit"
      st.rerun()

prompts = crud.crud_prompts().select_all()
prompt_name, prompt_content, prompt_variables = "", "", {}

if st.session_state.action == "create":
  prompt_name = st.text_input("Name", placeholder="Price Prediction")

elif st.session_state.action == "edit":
  if prompt_name := st.selectbox("Prompt", options=[p["name"] for p in prompts]):
    try:
      prompt_data = crud.crud_prompts().select(prompt_name)
      prompt_content = prompt_data["content"]
      prompt_variables = prompt_data["variables"]
    except l4t.PromptNotFoundError:
      st.error("Prompt not found.")

df_variables = st.data_editor(
    pd.DataFrame(
        [{"Key": k, "Value": v} for k, v in prompt_variables.items()]
    ) if prompt_variables else pd.DataFrame(columns=["Key", "Value"]),
    hide_index=True,
    num_rows="dynamic",
    width="stretch"
)
prompt_variables = {row["Key"]: row["Value"]
                    for _, row in df_variables.iterrows() if row["Key"]}

with st.expander("Global variables"):
  st.table(pd.DataFrame([
      {"Value": "Number of periods to be forecasted."},
      {"Value": "Number of periods in the input time series."},
      {"Value": "Statistical summary of the input time series."},
      {"Value": "Example output containing the same number of periods to be forecasted formatted."},
      {"Value": "Examples containing history and forecast, according to the sampling strategy."},
      {"Value": "Input time series formatted."},
  ], index=pd.Index(["`{horizon_forecast}`", "`{len_input}`", "`{statistics}`", "`{output_example}`", "`{forecast_examples}`", "`{input}`"], name="Key"))
      .style.set_properties(subset=["Value"], **{"color": "gray"}), border="horizontal")

col1, col2 = st.columns(2)
with col1:
  prompt_content = st.text_area(
      label="Prompt",
      value=prompt_content,
      placeholder=l4t.FEW_SHOT,
      label_visibility="collapsed",
      height=400)

with col2:
  global_variables = {
      "len_input": 30,
      "horizon_forecast": 7,
      "input": "Date,Value\n2016-07-01,38.662\n2016-07-01,37.124\n2016-07-01,36.465\n2016-07-01,33.609\n2016-07-01,31.851\n2016-07-01,30.532\n2016-07-01,30.093\n2016-07-01,29.873\n2016-07-01,29.653\n2016-07-01,29.213\n2016-07-01,27.456\n2016-07-01,27.456\n2016-07-01,27.236\n2016-07-01,26.577\n2016-07-01,26.797\n2016-07-01,26.797\n2016-07-01,26.797\n2016-07-01,26.577\n2016-07-01,26.577\n2016-07-01,26.138\n2016-07-01,26.138\n2016-07-01,25.698\n2016-07-01,25.918\n2016-07-01,25.918\n2016-07-02,25.918\n2016-07-02,26.358\n2016-07-02,26.138\n2016-07-02,25.698\n2016-07-02,25.698\n2016-07-02,25.918",
      "output_example": "Date,Value\n2016-07-01,38.662\n2016-07-01,37.124\n2016-07-01,36.465\n2016-07-01,33.609\n2016-07-01,31.851\n2016-07-01,30.532\n2016-07-01,30.093",
      "forecast_examples": (
          "Example 1:\n"
          "Period (history):\nDate,Value\n2016-07-01,38.662\n2016-07-01,37.124\n2016-07-01,36.465\n2016-07-01,33.609\n2016-07-01,31.851\n2016-07-01,30.532\n2016-07-01,30.093\n\n"
          "Period (forecast):\nDate,Value\n2016-07-01,29.873\n2016-07-01,29.653\n2016-07-01,29.213\n2016-07-01,27.456\n2016-07-01,27.456\n2016-07-01,27.236\n2016-07-01,26.577\n"
      ),
      "input_len": 30,
      "forecast_horizon": 7,
      "statistics": (
          "- Mean: 29.07\n"
          "- Median: 26.80\n"
          "- Standard Deviation: 3.45\n"
          "- Minimum Value: 25.70\n"
          "- Maximum Value: 38.66\n"
          "- First Quartile (Q1): 26.14\n"
          "- Third Quartile (Q3): 30.53\n"
          "- Trend Strength (STL): 0.82\n"
          "- Seasonality Strength (STL): 0.11"
      ),
      "examples": (
          "Example 1:\n"
          "Input (History):\nDate,Value\n2016-07-01,38.662\n2016-07-01,37.124\n2016-07-01,36.465\n2016-07-01,33.609\n2016-07-01,31.851\n2016-07-01,30.532\n2016-07-01,30.093\n\n"
          "Output (Forecast):\nDate,Value\n2016-07-01,29.873\n2016-07-01,29.653\n2016-07-01,29.213\n2016-07-01,27.456\n2016-07-01,27.456\n2016-07-01,27.236\n2016-07-01,26.577\n"
      )
  }
  try:
    global_variables.update(**prompt_variables)
    st.code(prompt_content.format(**global_variables), language="python", height=400)
  except KeyError as e:
    st.code(f"Error: key {e} not found.", language="python", height=400)
  except Exception as e:
    st.code(f"Error: {e}", language="python", height=400)


if st.button("💾 Save Prompt", type="primary"):
  try:
    if st.session_state.action == "create":
      crud.crud_prompts().insert(name=prompt_name, content=prompt_content, variables=prompt_variables)
      st.toast(f"Prompt **'{prompt_name}'** created successfully!", icon="✅")
      st.rerun()

    elif st.session_state.action == "edit":
      crud.crud_prompts().update(prompt_name, prompt_content, prompt_variables)
      st.toast(f"Prompt **'{prompt_name}'** updated successfully!", icon="✅")
      st.rerun()

  except exceptions.PromptAlreadyExistsError:
    st.warning(
        f"A prompt named **'{prompt_name}'** already exists. Please choose another name.")
  except exceptions.PromptNotFoundError:
    st.warning(f"Prompt **'{prompt_name}'** not found.")
  except Exception as e:
    st.error(f"An unexpected error occurred: {e}")


# ---------------- All prompts ----------------

@st.dialog("Confirm deletion")
def delete_prompts_dialog(prompt_names: list[str]):
  n = len(prompt_names)
  if n == 1:
    prompt_name = prompt_names[0]
    st.write(f"Are you sure you want to delete the prompt **'{prompt_name}'**?")
  else:
    st.write(f"Are you sure you want to delete **{n} prompts**?")
  st.caption("**⚠️ This action cannot be undone.**")
  col1, col2 = st.columns(2)
  with col1:
    if st.button("No", width="stretch"):
      st.rerun()
  with col2:
    if st.button("Yes, delete", width="stretch", type="primary"):
      st.session_state.confirm_delete = True
      st.session_state.prompts_to_delete = prompt_names
      st.rerun()


st.write("---")
st.write("### Prompts")
st.write(
    "This section displays the custom prompts created in the [#custom-prompts](#custom-prompts)."
)

if len(prompts) > 0:
  df_prompts = st.data_editor(
      pd.DataFrame([
          {"Name": f"📄 {p['name']}", "Delete": False}
          for p in prompts]),
      hide_index=True,
      width="stretch")

  try:
    for idx, row in df_prompts.iterrows():
      old_name = prompts[idx]["name"]
      new_name = row["Name"].replace("📄 ", "")
      if old_name != new_name:
        crud.crud_prompts().rename(old_name, new_name)
  except exceptions.PromptAlreadyExistsError:
    st.warning(
        f"A prompt named **'{new_name}'** already exists. Please choose another name.")
  except exceptions.PromptNotFoundError:
    st.warning(f"Prompt **'{old_name}'** not found.")
  except Exception as e:
    st.error(f"An unexpected error occurred: {e}")

  prompts_to_delete = [
      prompts[idx]["name"]
      for idx, row in df_prompts.iterrows()
      if row["Delete"]]

  n = len(prompts_to_delete)
  if prompts_to_delete and st.button(label=f"🗑️ Delete {n} prompt{'s' if n > 1 else ''}", type="primary"):
    delete_prompts_dialog(prompts_to_delete)
else:
  st.data_editor(
      pd.DataFrame([{"Name": "", "Delete": ""}]),
      disabled=["Name", "Delete"],
      hide_index=True,
      width="stretch")
