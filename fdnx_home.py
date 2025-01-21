import streamlit as st
import pandas as pd
import numpy as np
import time, io, datetime
import fdnx_simulator as fx
import fdnx_scheduler as fs


def schedule_info(df):
    info = "Pour Weight: " + str(df['pour_wt'].sum()) + ",  Total Molds: " + str(df['mold_qty'].sum()) + ",  Mold Hours: " + str(round(df['mold_hrs'].sum(),1)) + ",  Pattern Switches: " + str(len(df)-1) + "  Deck Time: " + str(round(df['total_deck_time'].sum() / 3600,1)) + " hrs"
    return info
    
st.set_page_config(
    page_title="Ferroloy Scheduler",
    page_icon="🛠",
)

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
        submit_button = st.form_submit_button(label='Generate Schedule & Simulate')
        if submit_button:
            with st.spinner('Generating schedules for: ' + selected_iron):
                schedules_made, total_attempts = fs.get_FDNX_schedule(selected_iron,df_jobs)
                fdnx1 = schedules_made[0]
                fdnx2 = schedules_made[1]
                fdnx3 = schedules_made[2]
            if total_attempts < fs.max_attempts: 
                st.success("Done! Attempts: " + str(total_attempts) + ". Schedules displayed and available for download.")
                st.write("Brett! right now these schedules are weighted by a measure I made up called 'deck time' which we will need to discuss. It's basically how long molds take to pour and sit in their jacket. I can weight by other things--we will need to find what works. Feel free to click generate/simulate as many times as you want, won't hurt anything.")
                st.header("FDNX 1 Schedule")
                st.write(schedule_info(fdnx1))
                st.dataframe(fdnx1)
                st.header("FDNX 2 Schedule")
                st.write(schedule_info(fdnx2))
                st.dataframe(fdnx2)
                st.header("FDNX 3 Schedule")
                st.write(schedule_info(fdnx3))
                st.dataframe(fdnx3)
                with st.spinner("Simulation running. Should take ~20-30s max"):
                        ladles, lanes, sim_seconds = fx.fdnx_simulator(schedules_made)    
                st.header("Simulated Ladles:")
                st.write("Brett-- This is a the simulation. Logic needs improved as well as things like column headers--for example, 'ladle weight' is really the leftover weight/pig after pouring. We may find we want to collect other data as well. Teh simulation logic right now is not treating the furnace right I do not think, and therefore we see more pours where pour weight is ~400.")
                st.dataframe(ladles)
                st.write("Brett--at the very bottom is a download button which contains each of the above tables as well as a page for each 'simulated lane' where you can see when carts were filled, by what ladle, etc. Eventually we can find ways to analyze this data better so you can make adjustments and reevaluate the schedule. The chart below this shows you the expected pour weight by ladle. We will also do another with how many molds are filled with each ladle--get an idea of where there are double-taps and or not all molds filled.")
                mold_wt_chart_data = ladles[['ladle_number', 'total_mold_wt']]
                mold_count_chart_data = ladles[['ladle_number', 'molds_filled']]
                mold_avgwt_chart_data = ladles[['ladle_number', 'avg_mold_wt']]
                st.header("Poured Amount By Ladle:")
                st.line_chart(mold_wt_chart_data, x="ladle_number",y="total_mold_wt")
                st.header("Molds Filled Per Ladle:")
                st.line_chart(mold_count_chart_data, x="ladle_number",y="molds_filled")
                st.header("Mold Filled AVG Weight:")
                st.line_chart(mold_avgwt_chart_data, x="ladle_number",y="avg_mold_wt")
                to_download = 1
            else:
                st.warning("Max attempts were reached. Results may be suboptimal. Try again, might work, who knows..")

    
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
        st.download_button(
            label= ('Download Schedule and Simulation Data for: ' + selected_iron),
            data=buffer,
            file_name= "FDNXSchedule_" + timestamp +".xlsx",
            mime="application/vnd.ms-excel"
        )
            

                








