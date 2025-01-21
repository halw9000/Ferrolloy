import streamlit as st

fdnx_upload = st.Page("fdnx_upload.py", title="Upload and Simulate", icon=":material/add_circle:")
fdnx_compare = st.Page("fdnx_compare.py", title="Compare Schedules", icon=":material/delete:")

pg = st.navigation([fdnx_upload, fdnx_compare])

st.set_page_config(page_title="Ferroloy Scheduler", page_icon="🛠")

pg.run()
