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


if 'ladles' not in st.session_state:
    st.warn('No Schedule has been generated to compare to')
else:
    ladles = st.session_state.ladles
    mold_wt_chart_data = ladles[['ladle_number', 'total_mold_wt']]
    mold_count_chart_data = ladles[['ladle_number', 'molds_filled']]
    mold_avgwt_chart_data = ladles[['ladle_number', 'avg_mold_wt']]
    #CHARTS
    st.header("Poured Amount By Ladle:")
    st.line_chart(mold_wt_chart_data, x="ladle_number",y="total_mold_wt")
    st.header("Molds Filled Per Ladle:")
    st.line_chart(mold_count_chart_data, x="ladle_number",y="molds_filled")
    st.header("Average Pour Weight:")
    st.line_chart(mold_avgwt_chart_data, x="ladle_number",y="avg_mold_wt")
