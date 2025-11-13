import base64
import streamlit as st
import llm4time as l4t
import pandas as pd
from helpers import crud, API
from utils import abspath
from config import logger
import io


with st.sidebar:
  st.write(f"#### ⚙️ Model Settings")

  models = crud.crud_models().select_all()
  model_options = {f"{m[2]} / {m[1]}": m for m in models}
  _, model_name, provider = model_options.get(
      st.selectbox("Model", model_options.keys(), index=0, help="Choose the model to be used."), (None, None, None))

  temperature = st.slider(
      label="Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1,
      help="Temperature controls the randomness of the model's response. Higher values result in more creative and varied responses.")

  st.write("---")
  st.write(f"#### ⚙️ Prompt Settings")

  files = crud.crud_files().select_all()
  filenames = [file["filename"] for file in files]
  filename = st.selectbox("Dataset", filenames)

  if filename:
    selected_file = next((f for f in files if f.get("filename") == filename), None)
    content_bytes = base64.b64decode(selected_file["content"])
    ts = l4t.read_file(pd.read_csv(io.BytesIO(content_bytes)), index_col="datetime")
    ts = l4t.MultiTimeSeries(ts)

    columns = st.multiselect("Select one or more columns", ts.columns.tolist())

    min_date = ts.index.min().date()
    max_date = ts.index.max().date()
    min_end_date = min(min_date + pd.Timedelta(days=2), max_date)

    start_date = str(st.date_input(
        label="Start Date", min_value=min_date, max_value=max_date, value=min_date))
    end_date = str(st.date_input(
        label="End Date", min_value=min_end_date, max_value=max_date, value=min_end_date))

    horizon_forecast = st.slider(
        label="Forecast Periods", min_value=1, max_value=96, step=1,
        help="Number of periods to be forecasted.")

    prompt_type = st.selectbox(
        label="Prompt Type", options=list(l4t.PromptType), index=0, format_func=lambda f: f.name,
        help="Choose the type of prompt to be used.")

    prompt_name = (st.selectbox(
        label="Prompt", options=[p["name"] for p in crud.crud_prompts().select_all()], index=0,
        help="Choose the prompt to be used.")
        if prompt_type == l4t.PromptType.CUSTOM else None)

    if prompt_type in (l4t.PromptType.FEW_SHOT, l4t.PromptType.COT_FEW):
      examples = st.slider(
          label="Examples", min_value=1, max_value=5, value=1,
          help="Number of examples to be used.")
    elif prompt_type == l4t.PromptType.CUSTOM:
      examples = st.slider(
          label="Examples", min_value=0, max_value=5, value=0,
          help="Number of examples to be used.")
    else:
      examples = 0

    if examples > 0:
      sampling = st.selectbox(
          label="Sampling", options=list(l4t.Sampling), index=0, format_func=lambda f: f.name,
          help="Choose the sampling strategy to be used.")
    else:
      sampling = None

    tsformat = st.selectbox(
        label="Series Format", options=list(l4t.TSFormat), index=0, format_func=lambda f: f.name,
        help="Presentation format of the data for the model. Different formats can influence the model's performance.")

    tstype = st.radio(
        label="Series Type", options=list(l4t.TSType), index=0, format_func=lambda f: f.name,
        help="In the numeric series, the values are passed as [3.662, 3.124, 3.465, 3.609], while in the text series, the values are passed as [3 . 6 6 2, 3 . 1 2 4, 3 . 4 6 5, 3 . 6 0 9].")

    ts = ts[columns]
    train, val = ts.split(start=start_date, end=end_date, periods=horizon_forecast)

  confirm = st.button("Generate Analysis", type="primary", width="stretch")


if not confirm:
  st.write('## LLM4Time Pipeline')
  st.write('##### Follow the steps below to upload your dataset, configure the model and generate predictions.')
  st.image(abspath('assets/llm4time.svg'), width=780)

elif not model_name:
  st.toast('Model not selected. Please select one before continuing.',
           icon='⚠️')

elif not filename:
  st.toast('Dataset not selected. Please select one before continuing.',
           icon='⚠️')

elif not columns:
  st.toast('No columns selected. Please select one or more columns before continuing.',
           icon='⚠️')

elif prompt_type == l4t.PromptType.CUSTOM and prompt_name is None:
  st.toast('Prompt not selected. Please select one before continuing.',
           icon='⚠️')

elif val.shape[0] < horizon_forecast:
  st.toast('Validation set is smaller than the forecast horizon. Please adjust the date range or reduce the forecast periods.',
           icon='⚠️')

else:
  try:
    prompt_content, prompt_variables = None, {}
    if prompt_type == l4t.PromptType.CUSTOM:
      prompt_data = crud.crud_prompts().select(prompt_name)
      prompt_content = prompt_data['content']
      prompt_variables = prompt_data['variables']

    prompt = l4t.prompt(
        ts=train,
        periods=horizon_forecast,
        type=prompt_type,
        tsformat=tsformat,
        tstype=tstype,
        examples=examples,
        sampling=sampling,
        template=prompt_content,
        **prompt_variables
    )
  except Exception as e:
    st.toast(e, icon='⚠️')
    st.stop()

  st.write("#### OVERVIEW")
  col1, col2, col3, col4, col5, col6 = st.columns([3, 3, 2, 4, 3, 2])
  with col1:
    st.metric("Model", model_name.upper())
  with col2:
    st.metric("API", provider.upper())
  with col3:
    st.metric("Temperature", temperature)
  with col4:
    st.metric("Prompt Type", prompt_type.name)
  with col5:
    st.metric("Series Type", tstype.name)
  with col6:
    st.metric("Series Format", tsformat.name)

  st.write("---")
  st.write("#### TRAINING SET")
  col1, col2, col3, col4, col5 = st.columns([3, 3, 3, 2, 1])
  with col1:
    st.metric("Dataset", filename)
  with col2:
    st.metric("Start Date", train.index.min().strftime("%Y-%m-%d"))
  with col3:
    st.metric("End Date", train.index.max().strftime("%Y-%m-%d"))
  with col4:
    st.metric("Rows", train.shape[0])
  with col5:
    st.metric("Columns", train.shape[1])

  st.plotly_chart(
      l4t.linechart(
          train,
          title="Time Series - Training Set",
          lightness=0.7
      ),
      width="stretch"
  )
  st.dataframe(train, width="stretch")

  st.write("##### DESCRIPTIVE STATISTICS")
  st.plotly_chart(
      l4t.barplot(
          train,
          title="Descriptive Statistics - Training Set",
          yaxis_type="log",
          lightness=0.7
      ),
      width="stretch"
  )
  st.dataframe(train.describe().T, width="stretch")

  st.write("##### STL DECOMPOSITION")
  stl = train.stl()
  st.dataframe(pd.DataFrame({
      "Trend Strength": [stl["t_strength"][col] for col in train.num_columns],
      "Seasonality Strength": [stl["s_strength"][col] for col in train.num_columns],
      "Noise Strength": [stl["r_strength"][col] for col in train.num_columns]
  }, index=train.num_columns), width="stretch")

  st.write("---")
  st.write("#### FORECAST RESULTS")
  try:
    api = API(model_name, provider)
    response = api.response(content=prompt, temperature=temperature)
    # response = API._mock(val, tsformat, tstype)
    pred = l4t.from_str(response.predicted, format=tsformat)
    pred = l4t.MultiTimeSeries(pred)
    pred.columns = val.columns
    pred.index = val.index

    col1, col2, col3 = st.columns(3)
    with col1:
      st.metric(label="INPUT TOKENS", value=response.input_tokens)
    with col2:
      st.metric(label="OUTPUT TOKENS", value=response.output_tokens)
    with col3:
      st.metric(label="RESPONSE TIME", value=f"{response.time:.2f} seconds")

    with st.expander("MODEL RESPONSE", expanded=True):
      with st.chat_message("user"):
        st.write("###### User")
        st.code(prompt, language="json", height=600)
      with st.chat_message("assistant"):
        st.write("###### Model")
        st.code(response.raw, language="json5")

    st.plotly_chart(
        l4t.lineplot(
            val, pred,
            groups=["Real", "Predicted"],
            title="Time Series - Real vs Predicted"
        ),
        width="stretch"
    )
    col1, col2 = st.columns(2)
    with col1:
      st.write("##### REAL")
      st.dataframe(val, width="stretch")
    with col2:
      st.write("##### PREDICTED")
      st.dataframe(pred, width="stretch")

    st.plotly_chart(
        l4t.barplot(
            val, pred,
            groups=["Real", "Predicted"],
            title="Descriptive Statistics - Real vs Predicted",
            yaxis_type="log"
        ),
        width="stretch"
    )
    col1, col2 = st.columns(2)
    with col1:
      st.write("##### REAL")
      st.dataframe(val.describe().drop("count"), width="stretch")
    with col2:
      st.write("##### PREDICTED")
      st.dataframe(pred.describe().drop("count"), width="stretch")

    metrics = val.metrics(pred)
    st.plotly_chart(
        l4t.barplot(
            metrics,
            x=["sMAPE", "MAE", "RMSE"],
            title="Forecast Metrics",
            yaxis_type="log"
        ),
        width="stretch"
    )
    st.dataframe(metrics, width="stretch")

    crud.crud_history().insert(
        model=model_name,
        provider=provider,
        temperature=temperature,
        dataset=filename,
        columns=columns,
        start_date=start_date,
        end_date=end_date,
        prompt_type=prompt_type.name,
        tsformat=tsformat.name,
        tstype=tstype.name,
        examples=examples,
        sampling=sampling.name if sampling else None,
        horizon_forecast=horizon_forecast,
        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
        response_time=response.time,
        response_raw=response.raw,
        response_predicted=pred.to_str(format="csv"),
        validation=val.to_str(format="csv"),
        metrics=metrics.to_dict(orient="records"),
        statistics_val=val.describe().to_dict(orient="records"),
        statistics_pred=pred.describe().to_dict(orient="records"),
        training=train.to_str(format="csv"),
        prompt=prompt
    )
    st.toast('Forecast generated and saved to history successfully!', icon='✅')
  except Exception as e:
    logger.error(f"Error during forecast generation: {e}")
    with st.expander("MODEL RESPONSE", expanded=True):
      with st.chat_message("user"):
        st.write("###### User")
        st.code(prompt, language="json", height=600)
      with st.chat_message("assistant"):
        st.write("###### Model")
        st.code(response.raw, language="json5")
      st.info("Notice: An error occurred while generating the forecast. Please check the model response above for details.")
