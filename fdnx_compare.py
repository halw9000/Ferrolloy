import streamlit as st
import pandas as pd
import numpy as np
import time, io, datetime
import fdnx_simulator as fx
import fdnx_scheduler as fs

st.write("# Compare Schedules Here")
st.write("Upload up to three FDNX schedule files to simulate and compare.")


col1, col2, col3 = st.columns(3)
with col1:
  com_file1 = st.file_uploader("Upload FDNX Schedule 1", type={"xlsx"})

with col2:
  com_file1 = st.file_uploader("Upload FDNX Schedule 2", type={"xlsx"})

with col3:
  com_file1 = st.file_uploader("Upload FDNX Schedule 3", type={"xlsx"})
