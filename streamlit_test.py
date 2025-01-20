import streamlit as st
import pandas as pd
import numpy as np
import time, io

uploaded_file = st.file_uploader("Upload Raw Jobs File Here", type={"xlsx"})

buffer = io.BytesIO()
to_download = 0

if uploaded_file is not None:
   
   df = pd.ExcelFile(uploaded_file)
   df_jobs = pd.read_excel(uploaded_file)
   sheet_names = df.sheet_names
   with st.form(key='sheet_selector_form'):
      selected_sheet = st.selectbox("Select a sheet to load data", sheet_names)
      selected_iron = st.selectbox("What iron type should we schedule?",["65-45-12","G35","Other"])
      submit_button = st.form_submit_button(label='Submit')
      if submit_button:
         with st.spinner('Generating schedules for: ' + selected_iron):
            time.sleep(2)
         st.success("Done!")
         to_download = 1

   chart_data = pd.DataFrame(np.random.randn(20, 3), columns=["a", "b", "c"])
   st.line_chart(chart_data)

   if to_download == 1:
      with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
    # Write each dataframe to a different worksheet.
          df_jobs.to_excel(writer, sheet_name='Sheet1')
       # Close the Pandas Excel writer and output the Excel file to the buffer
          writer.close()
          st.download_button(
              label= ('Download Schedule for: ' + selected_iron),
              data=buffer,
              file_name="pandas_multiple.xlsx",
              mime="application/vnd.ms-excel"
          )
         
compare_file = st.file_uploader("(Optional) Upload a Comparison Schedule", type={"xlsx"})

else:
   st.warning("")


