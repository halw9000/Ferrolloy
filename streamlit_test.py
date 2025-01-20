import streamlit as st
import pandas as pd
import numpy as np
import time, io
import fdnx_scheduler as fs

st.set_page_config(
    page_title="Ferroloy Scheduler",
    page_icon="🛠",
)

st.sidebar.header("Ferroloy Scheduler App")

st.write("# Schedule File Upload")
st.write(
    """This scheduler is based on..."""
)

chart_container = st.container()
uploaded_file = st.file_uploader("Upload Raw Jobs File Here", type={"xlsx"})

buffer = io.BytesIO()
to_download = 0

if uploaded_file is not None:
   
   df_jobs = fs.import_FDNX_jobs(uploaded_file)
   
   with st.form(key='sheet_selector_form'):
      selected_iron = st.selectbox("What iron type should we schedule?",["65-45-12","G35","Other"])
      submit_button = st.form_submit_button(label='Submit')
      if submit_button:
         with st.spinner('Generating schedules for: ' + selected_iron):
            time.sleep(2)
         st.success("Done!")
         to_download = 1

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

    st.dataframe(df_jobs)

#chart_data1 = pd.DataFrame(np.random.randn(20, 3), columns=["a", "b", "c"])
#chart1 = st.line_chart(chart_data1)

#compare_file = st.file_uploader("(Optional) Upload a Comparison Schedule", type={"xlsx"})
#chart_data2 = pd.DataFrame(np.random.randn(20, 3), columns=["a", "b", "c"])
#chart2 = st.line_chart(chart_data2)



#chart1 = st.line_chart(chart_data1)
#chart2 = st.line_chart(chart_data2)





