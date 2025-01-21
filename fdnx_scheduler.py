import pandas as pd
import numpy as np
import time
import math
import fdnx_constants as fc
import streamlit as st


#IDEAS:
# change function to be ablle to take specific weights for later randomization
# allow for true/false to reverse hot/cold direction?
# sort up on one, down on another, middle the other?
# STD Dev of expected deck weight?
############################################################################################################
## Weights for balancing schedules
schd_var_threshold = .002  # Percent variance per schedule allowed between total mold hours on each FDNX machine
mold_hour_weight = 1
pour_weight_weight = 0
crt_count_weight = 0
deck_time_weight = 0
possible_schedules = []
max_attempts = 1500
############################################################################################################

##IMPORT & TRANSFORM DATA
##Weekly Order Data EXCEL 
file_path = r'C:\Users\halmc\OneDrive\Documents\Projects\Molds\Testdata1.xlsx'

def categorize_pour_temp(temp):
    if (temp < fc.cold_pour_threshold):
        return "Cold"
    elif (temp > fc.hot_pour_threshold):
        return "Hot"
    else:
        return ""
            
def import_FDNX_jobs(uploaded_file):

    dtype = {
        'order_num': str,  
        'product_id': str,
        'material': str,  
        'order_qty': float,
        'mold_wt': float,
        'pour_wt': float,
        'pour_temp_min': float,
        'jacket_min': float,
        'cores_req': float
    }
    df = pd.read_excel(uploaded_file, dtype=dtype,  header=None)
    
    # Set the column headers to match the dtype keys
    df.columns = list(dtype.keys())
    df.set_index('order_num',inplace=True)
    df['temp_flag'] = df['pour_temp_min'].apply(categorize_pour_temp)
    # Add a column for order_qty rounded up to the nearest multiple of 3 for total molds to be made
    df['mold_qty'] = df['order_qty'].apply(lambda x: math.ceil(x / 3.0) * 3.0)
    # molds per hour added to data frame
    df['mph'] = df['cores_req'].apply(lambda x: fc.mph_withcore if x == 1 else fc.mph_nocore)
    # Add a column for mold hours
    df['mold_hrs'] = df.apply(lambda row: row['mold_qty'] / row['mph'], axis=1)
    # Add a column for carts to fill as an integer
    df['carts_to_fill_order'] = (df['mold_qty'] / fc.molds_per_cart).astype(int)
    # Add a column for cart deck time
    df['cart_deck_time'] = df.apply(lambda row: row['mold_wt'] * fc.molds_per_cart * fc.pour_speed_lbs_sec + row['jacket_min'] * 60 + fc.cart_pour_buffer_sec, axis=1)
    # Add a column for total deck time
    df['total_deck_time'] = df.apply(lambda row: row['carts_to_fill_order'] * row['cart_deck_time'], axis=1)

    return df
############################################################################################################
## FUNCTIONS

## BALANCE FDNX Schedule
def balance_FDNX(df, material, total_attempts):
    ## Filter orders for iron / material
    df_material = df[df['material'] == material]
    total_attempts = 0
##split hot from cold in separate FDNX / Lines
    df_cold = df_material[df_material['temp_flag'] == 'Cold']
    df_hot = df_material[df_material['temp_flag'] == 'Hot']
    df_neutral = df_material[df_material['temp_flag'] == '']
    
    df1 = df_hot
    df3 = df_cold
    df2, df4, df5 = np.array_split(df_neutral, 3)
    
    df1 = pd.concat([df1, df4])
    df3 = pd.concat([df3, df5])
    
    i = 0
    while True:

        ## weight the individual schedules based on mold hourus and total pour weight to evaluate if they are close enogh overall
        mh1 = df1['mold_hrs'].sum() + (len(df1) - 1) * fc.pattern_switch_hours
        mh2 = df2['mold_hrs'].sum() + (len(df2) - 1) * fc.pattern_switch_hours
        mh3 = df3['mold_hrs'].sum() + (len(df3) - 1) * fc.pattern_switch_hours
        
        wt1 = df1['pour_wt'].sum() 
        wt2 = df2['pour_wt'].sum() 
        wt3 = df3['pour_wt'].sum() 

        crt1 = df1['carts_to_fill_order'].sum()
        crt2 = df2['carts_to_fill_order'].sum()
        crt3 = df3['carts_to_fill_order'].sum()

        dt1 = df1['total_deck_time'].sum()
        dt2 = df2['total_deck_time'].sum()
        dt3 = df3['total_deck_time'].sum()

        combined_wt1 = ((mh1 / df['mold_hrs'].sum()) * mold_hour_weight) + ((wt1 / df['pour_wt'].sum()) * pour_weight_weight) + ((crt1 / df['carts_to_fill_order'].sum()) * crt_count_weight) + ((dt1 / df['total_deck_time'].sum()) * deck_time_weight)
        combined_wt2 = ((mh2 / df['mold_hrs'].sum()) * mold_hour_weight) + ((wt2 / df['pour_wt'].sum()) * pour_weight_weight) + ((crt2 / df['carts_to_fill_order'].sum()) * crt_count_weight) + ((dt2 / df['total_deck_time'].sum()) * deck_time_weight)
        combined_wt3 = ((mh3 / df['mold_hrs'].sum()) * mold_hour_weight) + ((wt3 / df['pour_wt'].sum()) * pour_weight_weight) + ((crt3 / df['carts_to_fill_order'].sum()) * crt_count_weight) + ((dt3 / df['total_deck_time'].sum()) * deck_time_weight)

        if (abs(combined_wt1 - combined_wt2) <= schd_var_threshold and abs(combined_wt2 - combined_wt3) <= schd_var_threshold and abs(combined_wt1 - combined_wt3) <= schd_var_threshold) or i >= max_attempts:
            print("Attempts:", i, " mh1:", mh1, "wt1:",wt1, "crt1:",crt1, "mh2:", mh2, "wt2:",wt2, "crt2:",crt2, "mh3:", mh3, "wt3:",wt3, "crt3:",crt3)

            break
        # Randomly move items between DataFrames to balance them
        i = i + 1
        total_attempts = total_attempts + 1
        if wt1 > wt2 and not df1[df1['temp_flag'] == ''].empty:
            row_to_move = df1[df1['temp_flag'] == ''].sample(n=1)
            df2 = pd.concat([df2, row_to_move])
            df1 = df1.drop(row_to_move.index)
        elif wt2 > wt3 and not df2[df2['temp_flag'] == ''].empty:
            row_to_move = df2[df2['temp_flag'] == ''].sample(n=1)
            df3 = pd.concat([df3, row_to_move])
            df2 = df2.drop(row_to_move.index)
        elif wt3 > wt1 and not df3[df3['temp_flag'] == ''].empty:
            row_to_move = df3[df3['temp_flag'] == ''].sample(n=1)
            df1 = pd.concat([df1, row_to_move])
            df3 = df3.drop(row_to_move.index)

    return df1, df2, df3, total_attempts



############################################################################################################
## SIMULATION

# Start the timer
start_time = time.time()

# Balance the DataFrames
unique_schedules = set()

def get_FDNX_schedule(material, df):
    total_attempts = 0  # Initialize total_attempts within the function
    # Create a list of DataFrames to hold the possible schedules
    
    df1, df2, df3, total_attempts = balance_FDNX(df, material, total_attempts)


    df1 = df1.sort_values(by='mold_wt', ascending=True)
    df2 = df2.sample(frac=1).reset_index(drop=True)
    df3 = df3.sort_values(by='mold_wt', ascending=False)
    FDNX_Schedule = [df1, df2, df3]
    

    return FDNX_Schedule, total_attempts

# print(get_FDNX_schedule('65-45-12'))
