import streamlit as st
import pandas as pd
import numpy as np
import time, io, datetime
import fdnx_simulator as fx
import fdnx_scheduler as fs

st.write("# Compare Schedules Here")
st.write("Upload up to three FDNX schedule files to simulate and compare.")
to_download = 0

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
    to_download = 1
    ladles = st.session_state.ladles
    fdnx1 = st.session_state.fdnx1
    fdnx2 = st.session_state.fdnx2
    fdnx3 = st.session_state.fdnx3
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

if to_download == 1:
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
    # Write each dataframe to a different worksheet.
        fdnx1.to_excel(writer, sheet_name='FCNX1')
        fdnx2.to_excel(writer, sheet_name='FDNX2')
        fdnx3.to_excel(writer, sheet_name='FDNX3')
        ladles.to_excel(writer, sheet_name='sim_ladles')
        lanes[0].to_excel(writer, sheet_name='sim_lane1')
        lanes[1].to_excel(writer, sheet_name='sim_lane2')
        lanes[2].to_excel(writer, sheet_name='sim_lane3')
        lanes[3].to_excel(writer, sheet_name='sim_lane4')
        lanes[4].to_excel(writer, sheet_name='sim_lane5')
        lanes[5].to_excel(writer, sheet_name='sim_lane6')
        writer.close()
        # Get the current timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
       # Close the Pandas Excel writer and output the Excel file to the buffer
        selected_iron = st.session_state.selected_iron
        st.download_button(
            label= ("Download Latest Simulation File"),
            data=buffer,
            file_name= "FDNXSchedule_" + timestamp +".xlsx",
            mime="application/vnd.ms-excel"
        )
