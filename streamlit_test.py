import pandas as pd
import streamlit as st

uploaded_file = st.file_uploader("Upload Excel Jobs File Here")

if uploaded_file is not None:
   df1=pd.read_excel(uploaded_file)
   filename=uploaded_file.name
else:
   st.warning("")

