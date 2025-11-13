import streamlit as st
import llm4time as l4t
import pandas as pd
from helpers import crud


@st.dialog("Confirm deletion")
def delete_dialog(filename: str, prompt_types: list) -> None:
  st.write(
      f"Are you sure you want to clear the history of the dataset **{filename}** for the prompts below?")
  st.markdown("\n".join(f"- **{prompt_type}**" for prompt_type in prompt_types))
  st.caption("**⚠️ This action cannot be undone.**")

  col1, col2 = st.columns(2)
  with col1:
    if st.button("No", width="stretch"):
      st.rerun()
  with col2:
    if st.button("Yes, delete", width="stretch", type="primary"):
      try:
        st.session_state.clear_history = True
        st.session_state.filename = filename
        st.session_state.prompt_types = prompt_types
        st.rerun()
      except Exception as e:
        st.toast(f"Error clearing history: {str(e)}", icon="⚠️")


if "clear_history" in st.session_state and st.session_state.clear_history:
  try:
    crud.crud_history().remove_many(st.session_state.filename, st.session_state.prompt_types)
    st.toast("History cleared successfully.", icon="✅")
  except Exception as e:
    st.toast(f"Error clearing history: {str(e)}", icon="⚠️")
  finally:
    del st.session_state.clear_history
    del st.session_state.filename
    del st.session_state.prompt_types
    st.rerun()

with st.sidebar:
  files = crud.crud_files().select_all()
  filenames = [file["filename"] for file in files]
  filename = st.selectbox("Dataset", filenames)

  prompt_types = st.multiselect(
      label='Prompts Type',
      options=[f.name for f in l4t.PromptType],
      default=[l4t.PromptType.ZERO_SHOT.name],
      help='Select the prompt types you want to view. You can select more than one prompt type to compare results.'
  )

  if filename and prompt_types:
    st.session_state.history = crud.crud_history().select(filename, prompt_types)

  confirm_view_history = st.button(
      type="primary",
      label="View History",
      help="Click to view the prediction history of the selected prompts.",
      width="stretch"
  )

  confirm_clear_history = st.button(
      label="Clear History",
      help="Click to clear the prediction history of the selected prompts.",
      width="stretch",
  )

if confirm_view_history and prompt_types == []:
  st.warning("Please select at least one prompt type to view the predictions.")

elif confirm_clear_history and prompt_types == []:
  st.warning("Please select at least one prompt type to clear the history.")

elif confirm_clear_history:
  delete_dialog(filename, prompt_types)

elif confirm_view_history:
  history = st.session_state.history
  for i, result in enumerate(history[::-1]):
    with st.expander(f"**{i+1} • `{result[4]}` / `{result[1]}` / `{result[2]}` / `{result[3]}` / `{result[8]}` / `{result[9]}` / `{result[10]}`**", expanded=False):
      with st.expander("TRAINING SET", expanded=False):
        train = l4t.from_str(result[23], format="csv")
        train = l4t.MultiTimeSeries(train)
        col1, col2, col3, col4, col5 = st.columns([3, 3, 3, 2, 1])
        with col1:
          st.metric("Dataset", result[4])
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
            width="stretch",
            key=f"train_linechart_{i}"
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
            width="stretch",
            key=f"train_barplot_{i}"
        )
        st.dataframe(train.describe().T, width="stretch")

        st.write("##### STL DECOMPOSITION")
        stl = train.stl()
        st.dataframe(pd.DataFrame({
            "Trend Strength": [stl["t_strength"][col] for col in train.num_columns],
            "Seasonality Strength": [stl["s_strength"][col] for col in train.num_columns],
            "Noise Strength": [stl["r_strength"][col] for col in train.num_columns]
        }, index=train.num_columns), width="stretch")

      with st.expander(f"MODEL RESPONSE", expanded=False):
        with st.chat_message("user"):
          st.write("###### User")
          st.code(result[24], language="json", height=600)
        with st.chat_message("assistant"):
          st.write("###### Model")
          st.code(result[17], language="json5")

      with st.expander("FORECAST RESULTS", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
          st.metric(label="INPUT TOKENS", value=result[14])
        with col2:
          st.metric(label="OUTPUT TOKENS", value=result[15])
        with col3:
          st.metric(label="RESPONSE TIME", value=f"{result[16]:.2f} seconds")

        val = l4t.from_str(result[19], format="csv")
        pred = l4t.from_str(result[18], format="csv")
        st.plotly_chart(
            l4t.lineplot(
                val, pred,
                groups=["Real", "Predicted"],
                title="Time Series - Real vs Predicted"
            ),
            width="stretch",
            key=f"forecast_linechart_{i}"
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
            width="stretch",
            key=f"forecast_barplot_{i}"
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
            width="stretch",
            key=f"forecast_metrics_{i}"
        )
        st.dataframe(metrics, width="stretch")
