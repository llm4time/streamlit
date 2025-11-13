import streamlit as st
import llm4time as l4t
from helpers import crud
import pandas as pd
import base64
import io


with st.sidebar:
  files = crud.crud_files().select_all()
  filenames = [file["filename"] for file in files]
  filename = st.selectbox("Dataset", filenames)
  selected_file = next((f for f in files if f.get("filename") == filename), None)

  if selected_file is not None:
    content_bytes = base64.b64decode(selected_file["content"])
    df = l4t.read_file(pd.read_csv(io.BytesIO(content_bytes)), index_col="datetime")
    df = l4t.MultiTimeSeries(df)
    columns = st.multiselect("Select one or more columns", df.num_columns)

  confirm = st.button("Generate Statistics", type="primary", width="stretch")

if not confirm:
  pass

elif not filename:
  st.toast("Dataset not selected. Please select one before continuing.", icon="⚠️")

elif not columns:
  st.toast("No columns selected. Please select one or more columns before continuing.", icon="⚠️")

else:
  ts = df.copy()
  ts = ts[columns]

  st.write("### Time Series")
  col1, col2, col3, col4, col5 = st.columns([3, 3, 3, 2, 1])
  with col1:
    st.metric(label="Dataset", value=filename)
  with col2:
    st.metric("Start Date", ts.index.min().strftime("%Y-%m-%d"))
  with col3:
    st.metric("End Date", ts.index.max().strftime("%Y-%m-%d"))
  with col4:
    st.metric("Rows", ts.shape[0])
  with col5:
    st.metric("Columns", ts.shape[1])

  st.plotly_chart(
      ts.linechart(title="Time Series"),
      config={"responsive": True}
  )
  st.dataframe(ts, width="stretch")

  st.write("### STL Decomposition")
  try:
    st.plotly_chart(
        ts.stlplot(title="Time Series Decomposition (STL)"),
        config={"responsive": True}
    )
    stl = ts.stl()
    st.dataframe(pd.DataFrame({
        "Trend Strength": [stl["t_strength"][col] for col in ts.num_columns],
        "Seasonality Strength": [stl["s_strength"][col] for col in ts.num_columns],
        "Noise Strength": [stl["r_strength"][col] for col in ts.num_columns]
    }, index=ts.num_columns), width="stretch")
  except Exception:
    st.info("Could not compute STL strengths.")

  st.write("### Descriptive Statistics")
  st.plotly_chart(
      ts.barplot(title="Descriptive Statistics"),
      config={"responsive": True}
  )
  st.dataframe(ts.describe().T, width="stretch")
