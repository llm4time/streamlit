import streamlit as st
import llm4time as l4t
from helpers import crud
from datetime import datetime
import pandas as pd
import base64
import io
import os


def upload() -> None:
  file = st.session_state.uploaded_file

  for state in ["step"]:
    if state in st.session_state:
      del st.session_state[state]
  st.session_state.step = 1

  try:
    _, ext = os.path.splitext(file.name)

    match ext.lower():
      case ".csv":
        df = pd.read_csv(file)
      case ".xlsx":
        df = pd.read_excel(file)
      case ".json":
        df = pd.read_json(file)
      case ".parquet":
        df = pd.read_parquet(file)
      case _:
        raise ValueError("Unsupported file extension.")

    upload_dialog(df)
  except Exception as e:
    if file is not None:
      st.toast(f"Error loading file: {e}", icon="🚨")


@st.dialog("Configure Dataset")
def upload_dialog(df: pd.DataFrame) -> None:

  if st.session_state.step == 1:
    columns = df.columns.tolist()
    st.session_state.index = st.selectbox(
        "Choose the datetime column:", columns, index=0,
        help="Time reference column that indicates the datetime for each observation.")
    st.session_state.columns = st.multiselect(
        "Choose the value columns:", df.columns.drop(st.session_state.index),
        help="Columns that contain the values of the time series.")

  if st.session_state.step == 2:
    if len(st.session_state.columns) > 1:
      st.session_state.duplicates = st.radio(
          "How to handle duplicate timestamps?", options=["first", "last", "sumf", "suml"],
          format_func=lambda x: {
              "first": "Keep the first occurrence",
              "last": "Keep the last occurrence",
              "sumf": "Sum numeric values and keep first categories",
              "suml": "Sum numeric values and keep last categories",
          }[x],
          index=0,
          help=(
              "- Keep the first occurrence: keeps the first row for each timestamp.\n"
              "- Keep the last occurrence: keeps the last row for each timestamp.\n"
              "- Sum numeric values and keep first categories: sums numeric columns and keeps the first categorical value.\n"
              "- Sum numeric values and keep last categories: sums numeric columns and keeps the last categorical value."
          ))
    else:
      st.session_state.duplicates = st.radio(
          "How to handle duplicate timestamps?", options=["first", "last", "sum"],
          format_func=lambda x: {
              "first": "Keep the first occurrence",
              "last": "Keep the last occurrence",
              "sum": "Sum the values",
          }[x],
          index=0,
          help=(
              "- Keep the first occurrence: keeps the first row for each timestamp.\n"
              "- Keep the last occurrence: keeps the last row for each timestamp.\n"
              "- Sum the values: sums the values for each timestamp."
          ))

  elif st.session_state.step == 3:
    st.session_state.normalize = st.radio(
        "Do you want to normalize the dataset?", ["Yes", "No"], index=1,
        help="Ensures that all timestamps between the start and end of the dataset are present.")

    if st.session_state.normalize == "Yes":
      col1, col2 = st.columns(2)
      with col1:
        freq = st.selectbox(
            "Frequency:",
            options=["D", "W", "M", "Y", "H", "T"],
            format_func=lambda x: {
                "D": "Daily",
                "W": "Weekly",
                "M": "Monthly",
                "Y": "Yearly",
                "H": "Hourly",
                "T": "Minute"
            }[x],
            index=0,
            help="Defines the time unit of the time series.")
      with col2:
        interval = st.number_input("Interval:", min_value=1, max_value=60, value=1, step=1,
                                   help="Defines how many frequency units apart the data points will be considered.")
      st.session_state.freq = freq if interval == 1 else f"{interval}{freq}"

  elif st.session_state.step == 4:
    st.session_state.imputation = st.radio(
        "Do you want to impute missing values?", ["Yes", "No"], index=1,
        help="Fills in the missing values in the dataset according to the selected method.")

    if st.session_state.imputation == "Yes":
      st.session_state.fill_method = st.selectbox(
          "Imputation Method:",
          options=["ffill", "bfill", "linear", "spline",
                   "mean", "median", "sma", "ema"],
          format_func=lambda x: {
              "ffill": "Forward Fill",
              "bfill": "Backward Fill",
              "linear": "Linear Interpolation",
              "spline": "Spline Interpolation",
              "mean": "Mean",
              "median": "Median",
              "sma": "Simple Moving Average",
              "ema": "Exponential Moving Average",
          }[x],
          index=0,
          help=(
              "- Forward Fill (ffill): fills missing numeric and categorical values using the last known value, then backfills if needed.\n"
              "- Backward Fill (bfill): fills missing numeric and categorical values using the next known value, then forward fills if needed.\n"
              "- Linear Interpolation: estimates missing numeric values using linear interpolation, then forward/backward fills remaining gaps.\n"
              "- Spline Interpolation: estimates missing numeric values using spline interpolation, then forward/backward fills remaining gaps.\n"
              "- Mean: fills missing numeric values with the mean of the column.\n"
              "- Median: fills missing numeric values with the median of the column.\n"
              "- Simple Moving Average (SMA): fills missing numeric values using rolling mean with specified window, then ffill/bfill.\n"
              "- Exponential Moving Average (EMA): fills missing numeric values using exponential weighted mean, then ffill/bfill."
          ))

      if st.session_state.fill_method == "spline":
        st.session_state.spline_order = st.number_input(
            "Spline Order:", min_value=1, max_value=5, value=2, step=1,
            help="Specifies the order of the spline interpolation.")
      elif st.session_state.fill_method == "sma":
        st.session_state.sma_window = st.number_input(
            "Window Size:", min_value=1, max_value=30, value=3, step=1,
            help="Specifies the window size for the simple moving average.")
      elif st.session_state.fill_method == "ema":
        st.session_state.ema_span = st.number_input(
            "Span:", min_value=1, max_value=30, value=3, step=1,
            help="Specifies the span for the exponential moving average.")

  elif st.session_state.step == 5:
    file = st.session_state.uploaded_file
    st.session_state.file = st.text_input("Save file as:", value=file.name).strip()
    _, ext = os.path.splitext(st.session_state.file)

    if ext not in [".csv", ".xlsx", ".json", ".parquet"]:
      st.warning("A valid file extension is required: .csv, .xlsx, .json, or .parquet")

    if crud.crud_files().exists(st.session_state.file):
      st.warning(f"File **{st.session_state.file}** already exists.")

  def next_step() -> None:
    st.session_state.step += 1

  def prev_step() -> None:
    st.session_state.step -= 1

  def confirm(df: pd.DataFrame) -> None:
    df = df[[st.session_state.index] + st.session_state.columns]
    ts = l4t.read_file(df, index_col=st.session_state.index)
    ts = ts.agg_duplicates(method=st.session_state.duplicates)
    ts.index.name = "datetime"

    if st.session_state.normalize == "Yes":
      ts = ts.normalize(freq=st.session_state.freq)

    if st.session_state.imputation == "Yes":
      match st.session_state.fill_method:
        case "ffill":
          ts.impute_ffill(inplace=True)
        case "bfill":
          ts.impute_bfill(inplace=True)
        case "linear":
          ts.impute_interpolate(method="linear", inplace=True)
        case "spline":
          ts.impute_interpolate(
              method="spline",
              order=st.session_state.spline_order,
              inplace=True)
        case "mean":
          ts.impute_mean(inplace=True)
        case "median":
          ts.impute_median(inplace=True)
        case "sma":
          ts.impute_sma(
              window=st.session_state.sma_window,
              inplace=True)
        case "ema":
          ts.impute_ema(
              span=st.session_state.ema_span,
              inplace=True)

    csv_str = ts.to_csv()
    buffer = io.BytesIO(csv_str.encode("utf-8"))
    buffer.name = st.session_state.file
    st.session_state.buffer = buffer
    st.session_state.upload = True

  col1, col2 = st.columns(2)
  with col1:
    if st.session_state.step > 1:
      st.button("Back", on_click=prev_step, width="stretch")
  with col2:
    if st.session_state.step < 5:
      disabled = False
      if st.session_state.step == 1:
        disabled = len(st.session_state.columns) == 0
      st.button("Next", on_click=next_step, width="stretch", disabled=disabled)
    else:
      disabled = False
      _, ext = os.path.splitext(st.session_state.file)
      if ext not in [".csv", ".xlsx", ".json", ".parquet"]:
        disabled = True
      if crud.crud_files().exists(st.session_state.file):
        disabled = True
      if st.button("Confirm", type="primary", width="stretch", disabled=disabled):
        confirm(df)
        st.rerun()


if "upload" in st.session_state and st.session_state.upload:
  crud.crud_files().upload(st.session_state.buffer)
  st.toast(f"File '{st.session_state.file}' uploaded successfully!", icon="✅")
  del st.session_state.upload
  del st.session_state.buffer


@st.dialog("Confirm deletion")
def delete_dialog(filenames: list):
  n = len(filenames)

  if n == 1:
    st.write(f"Are you sure you want to delete the file **{filenames[0]}**?")
  else:
    st.write(f"Are you sure you want to delete **{n} files**?")

  st.caption("**⚠️ This action cannot be undone.**")

  col1, col2 = st.columns(2)
  with col1:
    if st.button("No", width="stretch"):
      st.rerun()
  with col2:
    if st.button("Yes, delete", width="stretch", type="primary"):
      st.session_state.delete_files = True
      st.session_state.files_to_delete = filenames
      st.rerun()


if "delete_files" in st.session_state and st.session_state.delete_files:
  n = len(st.session_state.files_to_delete)
  try:
    crud.crud_files().remove_many(st.session_state.files_to_delete)
    st.toast(f"File{'s' if n > 1 else ''} deleted successfully!", icon="✅")
  except Exception as e:
    st.warning(f"Error deleting files: {str(e)}")
  finally:
    del st.session_state.delete_files
    del st.session_state.files_to_delete
    st.rerun()


def rename_file(old_name: str, new_name: str) -> None:
  try:
    # Validate file name.
    if not new_name.strip():
      st.warning("File name cannot be empty.")
      return

    _, ext = os.path.splitext(new_name)
    if ext not in [".csv", ".xlsx", ".json", ".parquet"]:
      st.warning("A valid file extension is required: .csv, .xlsx, .json, or .parquet")
      return

    # Check if the original file exists.
    if not crud.crud_files().exists(old_name):
      st.warning(f"File not found: {old_name}")
      return

    # Check if the new name already exists.
    if crud.crud_files().exists(new_name) and old_name != new_name:
      st.warning(f"A file with the name '{new_name}' already exists.")
      return

    # Invalid characters for file names.
    invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
    if any(char in new_name for char in invalid_chars):
      st.warning(f"File name contains invalid characters.")
      return

    st.session_state.rename_file = True
    st.session_state.old_name = old_name
    st.session_state.new_name = new_name
    st.rerun()
  except Exception as e:
    st.warning(f"Error renaming {old_name}: {str(e)}")


if "rename_file" in st.session_state and st.session_state.rename_file:
  try:
    renamed = crud.crud_files().rename(
        st.session_state.old_name,
        st.session_state.new_name)
    if renamed:
      st.toast(f"File renamed to '{st.session_state.new_name}' successfully!", icon="✅")
    else:
      st.warning(f"Failed to rename file '{st.session_state.old_name}'.")
  except Exception as e:
    st.warning(f"Error renaming file: {str(e)}")
  finally:
    del st.session_state.rename_file
    del st.session_state.old_name
    del st.session_state.new_name
    st.rerun()


st.write("### Upload your time series dataset file")
st.file_uploader(
    "Select a file",
    on_change=upload,
    key="uploaded_file",
    type=["csv", "xlsx", "json", "parquet"]
)

files_info = []
files = crud.crud_files().select_all()
if files:
  for file in files:
    filename = file.get("filename", "Unknown")
    content = file.get("content")

    if not content:
      files_info.append({
          "File": f"📁 {filename}",
          "Extension": "N/A",
          "Rows": "N/A",
          "Columns": "N/A",
          "Size (MB)": "N/A",
          "Modification": "N/A",
          "Delete": False
      })
      continue

    try:
      content_bytes = base64.b64decode(content)
      file_size_mb = round(len(content_bytes) / (1024 * 1024), 2)
      mod_date = datetime.now().strftime("%d/%m/%Y %H:%M")
      file_extension = f".{filename.split('.')[-1].upper()}" if "." in filename else "CSV"
      df = pd.read_csv(io.BytesIO(content_bytes))
      row_count, col_count = df.shape
    except Exception:
      file_size_mb = "N/A"
      mod_date = "N/A"
      file_extension = "N/A"
      row_count = "N/A"
      col_count = "N/A"

    files_info.append({
        "File": f"📁 {filename}",
        "Extension": file_extension,
        "Rows": row_count,
        "Columns": col_count,
        "Size (MB)": file_size_mb,
        "Modification": mod_date,
        "Delete": False
    })

  files_info = st.data_editor(
      pd.DataFrame(files_info),
      disabled=["Rows", "Columns", "Extension", "Size (MB)", "Modification"],
      hide_index=True,
      width="stretch"
  )

  for idx, row in files_info.iterrows():
    old_name = files[idx]["filename"]
    new_name = row["File"].replace("📁 ", "")
    if old_name != new_name:
      rename_file(old_name, new_name)

  files_to_delete = []
  for idx, row in files_info.iterrows():
    if row["Delete"]:
      files_to_delete.append(files[idx]["filename"])

  n = len(files_to_delete)
  if files_to_delete and st.button(label=f"🗑️ Delete {n} file{'s' if n > 1 else ''}", type="primary"):
    delete_dialog(files_to_delete)
