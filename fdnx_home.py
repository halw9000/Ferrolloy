import streamlit as st
import pandas as pd
import numpy as np
import time, io, datetime
import fdnx_scheduler as fs

def schedule_info(df):
    info = "Pour Weight: " + str(df['pour_wt'].sum()) + ",  Total Molds: " + str(df['mold_qty'].sum()) + ",  Mold Hours: " + str(round(df['mold_hrs'].sum(),1)) + ",  Pattern Switches: " + str(len(df)-1)
    return info
    
st.set_page_config(
    page_title="Ferroloy Scheduler",
    page_icon="🛠",
)

st.navigation([
    st.Page('fdnx_home.py', title='FDNX Scheduler', icon='⏰'),
    st.Page('pages/simulation.py', title='Deck Simulator', icon='🧰️'),
    st.Page('streamlit_test.py', title='test page', icon='🧰️')
])




    # your content


st.write("# Ferroloy FDNX Scheduler")
st.write(
    """This scheduler will ingest the FDNX weekly job data and aim to create a balanced schedule across each machine. This project is still in development, so the scheduler may display odd behavior--for example, it may switch from balancing schedules on total molds to balancing on total pour weight."""
)

st.header("Raw Jobs Data Upload")
uploaded_file = st.file_uploader("Upload Raw Jobs File Here", type={"xlsx"})
st.write("Brett, remember you need to overwrite the 'cores required' column with 1's an 0's for now") 

buffer = io.BytesIO()
to_download = 0

if uploaded_file is not None:
    df_jobs = fs.import_FDNX_jobs(uploaded_file)
    st.dataframe(df_jobs)
    with st.form(key='sheet_selector_form'):
        selected_iron = st.selectbox("What iron type should we schedule?",["65-45-12","80-55-06","G-35"])
        submit_button = st.form_submit_button(label='Generate Schedule')
        if submit_button:
            with st.spinner('Generating schedules for: ' + selected_iron):
                schedules_made, total_attempts = fs.get_FDNX_schedule(selected_iron,df_jobs)
                fdnx1 = schedules_made[0]
                fdnx2 = schedules_made[1]
                fdnx3 = schedules_made[2]
            if total_attempts < fs.max_attempts: 
                st.success("Done! Attempts: " + str(total_attempts) + ". Schedules displayed and available for download.")
            else:
                st.warning("Max attempts were reached. Results may be suboptimal. Try again, might work, who knows..")
            st.header("FDNX 1 Schedule")
            st.write(schedule_info(fdnx1))
            st.dataframe(fdnx1)
            st.header("FDNX 2 Schedule")
            st.write(schedule_info(fdnx2))
            st.dataframe(fdnx2)
            st.header("FDNX 3 Schedule")
            st.write(schedule_info(fdnx3))
            st.dataframe(fdnx3)
            to_download = 1

    if to_download == 1:
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        # Write each dataframe to a different worksheet.
            fdnx1.to_excel(writer, sheet_name='FCNX1')
            fdnx2.to_excel(writer, sheet_name='FDNX2')
            fdnx3.to_excel(writer, sheet_name='FDNX3')
            # Get the current timestamp
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
           # Close the Pandas Excel writer and output the Excel file to the buffer
            writer.close()
            st.download_button(
                label= ('Download Schedule for: ' + selected_iron),
                data=buffer,
                file_name= "FDNXSchedule_" + timestamp +".xlsx",
                mime="application/vnd.ms-excel"
              )

   

#chart_data1 = pd.DataFrame(np.random.randn(20, 3), columns=["a", "b", "c"])
#chart1 = st.line_chart(chart_data1)

#compare_file = st.file_uploader("(Optional) Upload a Comparison Schedule", type={"xlsx"})
#chart_data2 = pd.DataFrame(np.random.randn(20, 3), columns=["a", "b", "c"])
#chart2 = st.line_chart(chart_data2)



#chart1 = st.line_chart(chart_data1)
#chart2 = st.line_chart(chart_data2)






