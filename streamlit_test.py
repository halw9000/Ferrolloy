
uploaded_file = st.file_uploader("Upload Excel Jobs File Here", type={"xlsx"})

if uploaded_file is not None:
   xls = pd.ExcelFile(uploaded_file)
   sheet_names = xls.sheet_names
   with st.form(key='sheet_selector_form'):
        selected_sheet = st.selectbox("Select a sheet to load data", sheet_names)
        selected_skip_lines = st.text_input("Number of lines to skip (including header if present)")
        submit_button = st.form_submit_button(label='Submit')
else:
   st.warning("")

