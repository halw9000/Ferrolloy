import pandas as pd
import streamlit as st

uploaded_file = st.file_uploader()

if uploaded_file is not None:
#read csv
df1=pd.read_csv(uploaded_file)

   #read xls or xlsx
   df1=pd.read_excel(uploaded_file)
else:
st.warning(“you need to upload a csv or excel file.”)

filename=uploaded_file.name
