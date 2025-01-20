import streamlit as st
import pandas as pd
import time, io

uploaded_file = st.file_uploader("Upload Excel Jobs File Here", type={"xlsx"})
buffer = io.BytesIO()

if uploaded_file is not None:
   xls = pd.ExcelFile(uploaded_file)
   sheet_names = xls.sheet_names
   with st.form(key='sheet_selector_form'):
      selected_sheet = st.selectbox("Select a sheet to load data", sheet_names)
      selected_iron = st.selectbox("What iron type should we schedule?",["65-45-12","G35","Other"])
      submit_button = st.form_submit_button(label='Submit')
      if submit_button:
         with st.spinner('Generating schedules for: ' + selected_iron):
            time.sleep(5)
         st.success("Done!")
      # display the dataframe on streamlit app
         st.write(df)


else:
   st.warning("")


