import pandas as pd
import numpy as np
import time
import math
import fdnx_constants as fc
import fdnx_scheduler as fs
import streamlit as st

############################################################################################################
## FUNCTIONS: Lane Loading

## load a pattern into an FDNX machine to slowly deprecate over time
def load_FDNX(df, index, FDNX):
    FDNX = pd.DataFrame()  # Clear the FDNX DataFrame
    row_to_insert = df.loc[index].copy()  # Use .copy() to avoid SettingWithCopyWarning
    row_to_insert['carts_remaining'] = row_to_insert['carts_to_fill_order']
    FDNX = pd.concat([FDNX, row_to_insert.to_frame().T])
    return FDNX

## move a cart with 3 molds to a lane and then reduce carts remaining to be filled by FDNX
def cart_to_lane(FDNX, lane, FDNX_Schedule):
    lane = pd.concat([lane, FDNX.iloc[0:1].copy()])  # Use .copy() to avoid modifying the original DataFrame
    FDNX.at[FDNX.index[0], 'carts_remaining'] -= 1
    if FDNX.at[FDNX.index[0], 'carts_remaining'] == 0:
        FDNX = FDNX_next_pattern(FDNX, FDNX_Schedule)
    return lane, FDNX

#use an FDNX Schedule to load all scheduled lanes
def load_lanes(FDNX, lanes, FDNX_Schedule):
    for i in range(FDNX_Schedule['carts_to_fill_order'].sum()):
        lanes[i % len(lanes)], FDNX = cart_to_lane(FDNX, lanes[i % len(lanes)], FDNX_Schedule)
    return lanes

## Find the next row in schedule DataFrame after the row that shares the same index as the first row in FDNX
def FDNX_next_pattern(FDNX, FDNX_schedule):
    if not FDNX.empty:
        current_index = FDNX.index[0]
        next_index = FDNX_schedule.index.get_loc(current_index) + 1
        if next_index < len(FDNX_schedule):
            next_row = FDNX_schedule.iloc[next_index]
            FDNX = load_FDNX(FDNX_schedule, next_row.name, FDNX)
    return FDNX

## Get the top rows from lanes 1-6 where poured = False and the item is either the first item in the lane or jacket_over in the row above it is > ladle_time
def pourable_carts(lanes, ladle_time):
    top_rows = []
    current_time = ladle_time 
    for lane_number, lane in enumerate(lanes, start=1):
        if not lane.empty:
            # Find the first row where cart_completed is False
            incomplete_carts = lane[lane['cart_completed'] == False]
            if not incomplete_carts.empty:
                top_row = incomplete_carts.iloc[0].copy()  # Use .copy() to avoid SettingWithCopyWarning
                # Check if the row above has a jacket_timer less than ladle_time
                if incomplete_carts.index[0] == 0 or lane.iloc[lane.index.get_loc(top_row.name) - 1]['jacket_timer'] <= ladle_time:
                    top_row['lane'] = lane_number
                    top_rows.append(top_row)
    return pd.DataFrame(top_rows)

############################################################################################################
##LADLE FUNCTIONS

def fill_ladle(current_time, ladle_number, last_ladle_start, deck_wt):
    weight = min(np.random.normal(fc.ladle_avg_weight, fc.ladle_weight_dev), fc.ladle_capacity)
    temperature = np.random.normal(fc.ladle_start_temp_avg, fc.ladle_start_temp_dev)
    current_time = max(current_time + fc.ladle_refill_time, last_ladle_start + fc.furnace_ready_sec)
    return {'ladle_number': ladle_number, 'deck_weight': deck_wt, 'ladle_weight': weight, 'ladle_start_weight': weight, 'ladle_temp': temperature, 'ladle_start_temp': temperature, 'start_time': current_time, 'molds_filled': 0, 'total_mold_wt': 0, 'end_time': None}

def update_ladle(ladle, mold_wt, current_time):
    ladle['ladle_weight'] -= mold_wt
    ladle['molds_filled'] += 1
    ladle['total_mold_wt'] += mold_wt
    ladle['end_time'] = current_time
    return ladle

def update_ladle_temp(ladle, elapsed_time):
    ladle['ladle_temp'] -= (fc.ladle_tempdrop_min / 60) * elapsed_time
    return ladle
    
def get_deck_wt(lanes):
    deck_wt = 0
    for lane in lanes:
        if not lane.empty:
            incomplete_carts = lane[lane['cart_completed'] == False]
            if not incomplete_carts.empty:
                deck_wt += incomplete_carts.iloc[0]['mold_wt'] * fc.molds_per_cart
    return deck_wt
    
def ladle_needs_refill(ladle, min_mold_wt, min_mold_temp):
    return ladle['ladle_weight'] < min_mold_wt or ladle['ladle_temp'] < min_mold_temp

def pour_mold(ladle, row, current_time):
    mold_wt = row['mold_wt']
    pour_time = mold_wt / fc.pour_speed_lbs_sec
    ladle = update_ladle(ladle, mold_wt, current_time)
    return ladle, pour_time

def update_lane(lane, index, row, current_time, pour_time, current_ladle):
    
    if lane.iloc[index, lane.columns.get_loc('molds_remaining')] == 3:
        lane.iloc[index, lane.columns.get_loc('pour_start_time')] = current_time 
    
    lane.iloc[index, lane.columns.get_loc('molds_remaining')] -= 1

    if lane.iloc[index, lane.columns.get_loc('molds_remaining')] == 0:
        lane.iloc[index, lane.columns.get_loc('cart_completed')] = True
        lane.iloc[index, lane.columns.get_loc('jacket_timer')] = current_time + row['jacket_min'] * 60
        lane.iloc[index, lane.columns.get_loc('pour_complete_time')] = current_time + pour_time
        lane.iloc[index, lane.columns.get_loc('ladle')] = current_ladle['ladle_number']
        lane.iloc[index, lane.columns.get_loc('pour_temp')] = current_ladle['ladle_temp']
        return True
    return False

############################################################################################################
## SIMULATION
def fdnx_simulator(test_schedule):


    # Start the timer
    start_time = time.time()
    ############################################################################################################
    ## Building the Floor

    ## FDNX 1-3
    # Initialize FDNX 1-3 as empty DataFrames
    FDNX_1 = pd.DataFrame()
    FDNX_2 = pd.DataFrame()
    FDNX_3 = pd.DataFrame()
    ## Create Deck Lanes
    lane_1 = pd.DataFrame()
    lane_2 = pd.DataFrame()
    lane_3 = pd.DataFrame()
    lane_4 = pd.DataFrame()
    lane_5 = pd.DataFrame()
    lane_6 = pd.DataFrame()

    # Load each FDNX with first item on their schedule
    FDNX_1 = load_FDNX(test_schedule[0], test_schedule[0].index[0], FDNX_1)
    FDNX_2 = load_FDNX(test_schedule[1], test_schedule[1].index[0], FDNX_2)
    FDNX_3 = load_FDNX(test_schedule[2], test_schedule[2].index[0], FDNX_3)



    ## Assign default lanes to each FDNX
    FDNX_1_lanes = [lane_1, lane_2]
    FDNX_2_lanes = [lane_3, lane_4]
    FDNX_3_lanes = [lane_5, lane_6]

    ## Assign schedules to FDNX Machine
    FDNX_Schedule_1 = test_schedule[0]
    FDNX_Schedule_2 = test_schedule[1]
    FDNX_Schedule_3 = test_schedule[2]

    # Load all lanes with the entire schedule
    FDNX_1_lanes = load_lanes(FDNX_1, FDNX_1_lanes, FDNX_Schedule_1)
    FDNX_2_lanes = load_lanes(FDNX_2, FDNX_2_lanes, FDNX_Schedule_2)
    FDNX_3_lanes = load_lanes(FDNX_3, FDNX_3_lanes, FDNX_Schedule_3)

    # Reset indexes to ensure they are unique
    for lane in [FDNX_1_lanes, FDNX_2_lanes, FDNX_3_lanes]:
        for l in lane:
            l.reset_index(drop=True, inplace=True)

    # Add new columns to lanes 1-6
    for lane in [FDNX_1_lanes, FDNX_2_lanes, FDNX_3_lanes]:
        for l in lane:
            l['molds_remaining'] = fc.molds_per_cart
            l['ladle'] = 0
            l['pour_time'] = 0.0
            l['cart_completed'] = False
            l['jacket_timer'] = 0.0
            l['pour_start_time'] = None
            l['pour_complete_time'] = None
            l['pour_temp'] = 0.0  # Add column for pour temperature

    lane_1 = FDNX_1_lanes[0]
    lane_2 = FDNX_1_lanes[1]
    lane_3 = FDNX_2_lanes[0]
    lane_4 = FDNX_2_lanes[1]
    lane_5 = FDNX_3_lanes[0]
    lane_6 = FDNX_3_lanes[1]

    # Initialize ladles DataFrame
    ladles = pd.DataFrame({
        'ladle_number': pd.Series(dtype='int'),
        'deck_weight': pd.Series(dtype='float'),
        'ladle_weight': pd.Series(dtype='float'),
        'ladle_start_weight': pd.Series(dtype='float'),
        'ladle_temp': pd.Series(dtype='float'),
        'ladle_start_temp': pd.Series(dtype='float'),
        'start_time': pd.Series(dtype='float'),
        'molds_filled': pd.Series(dtype='float'),
        'total_mold_wt': pd.Series(dtype='float'),
        'end_time': pd.Series(dtype='float'),
        'top_mold_wt': pd.Series(dtype='float')  # Add column for top mold weight
    })
    #ladles = pd.DataFrame(dtype=ladle_dtype)
    current_time = 0
    ladle_number = 1
    # Create the first ladle
    current_ladle = fill_ladle(current_time, ladle_number, 0, get_deck_wt([lane_1, lane_2, lane_3, lane_4, lane_5, lane_6]) )
    
    def get_top_mold_wt(lanes):
        top_mold_wt = 0
        for lane in lanes:
            if not lane.empty:
                incomplete_carts = lane[lane['cart_completed'] == False]
                if not incomplete_carts.empty:
                    top_mold_wt += incomplete_carts.iloc[0]['mold_wt']
        return top_mold_wt

    # Simulation loop
    while True:
        # Get the top rows from lanes 1-6
        top_rows_df = pourable_carts([lane_1, lane_2, lane_3, lane_4, lane_5, lane_6], current_time)
        while top_rows_df.empty and pd.concat([lane_1, lane_2, lane_3, lane_4, lane_5, lane_6])['molds_remaining'].sum() > 0:
            # Increment the current time and check for pourable carts again
            current_time += 60
            top_rows_df = pourable_carts([lane_1, lane_2, lane_3, lane_4, lane_5, lane_6], current_time)
            current_ladle = update_ladle_temp(current_ladle, 60)
            continue
        while not top_rows_df.empty and top_rows_df['molds_remaining'].sum() > 0:
            for index, row in top_rows_df.iterrows():
                lane_number = row['lane']
                lane = [lane_1, lane_2, lane_3, lane_4, lane_5, lane_6][lane_number - 1]
                lane_index = lane.index.get_loc(row.name)  # Get the correct index of the row in the lane
                while lane.iloc[lane_index]['molds_remaining'] > 0:
                    mold_wt = row['mold_wt']
                    pour_temp_min = row['pour_temp_min']
                    pour_time = mold_wt / fc.pour_speed_lbs_sec
                    # Check if the ladle can pour the mold
                    if current_ladle['ladle_temp'] > pour_temp_min and current_ladle['ladle_weight'] >= mold_wt:
                        # Call pour_mold to update the ladle and calculate pour time
                        current_ladle, pour_time = pour_mold(current_ladle, row, current_time)
                        # Update the ladle temperature after pouring
                        current_ladle = update_ladle_temp(current_ladle, pour_time)
                        # Update the lane
                        if update_lane(lane, lane_index, row, current_time, pour_time, current_ladle):
                            current_time += pour_time
                            current_ladle = update_ladle_temp(current_ladle, pour_time)
                        else:
                            current_time += pour_time + fc.cart_pour_buffer_sec
                            current_ladle = update_ladle_temp(current_ladle, pour_time + fc.cart_pour_buffer_sec)
                    else:
                        other_pourable_carts = pourable_carts([lane_1, lane_2, lane_3, lane_4, lane_5, lane_6], current_time + fc.ladle_doubletap_delay)   
                        if not other_pourable_carts.empty:
                            other_min_mold_wt = other_pourable_carts['mold_wt'].min()
                            other_min_temp = other_pourable_carts[other_pourable_carts['mold_wt'] == other_min_mold_wt]['pour_temp_min'].min()
                            delay_ladle_temp_drop = fc.ladle_tempdrop_min / 60 * fc.ladle_doubletap_delay
                            if current_ladle['ladle_temp'] - delay_ladle_temp_drop > other_min_temp and current_ladle['ladle_weight'] >= other_min_mold_wt:
                                row = other_pourable_carts.iloc[0]
                                lane_number = row['lane']
                                lane = [lane_1, lane_2, lane_3, lane_4, lane_5, lane_6][lane_number - 1]
                                lane_index = lane.index.get_loc(row.name)
                                current_time += fc.ladle_doubletap_delay
                                current_ladle['ladle_temp']  -=  delay_ladle_temp_drop
                                continue               
                        current_ladle['top_mold_wt'] = get_top_mold_wt([lane_1, lane_2, lane_3, lane_4, lane_5, lane_6])
                        ladles = pd.concat([ladles, pd.DataFrame([current_ladle])])
                        ladle_number += 1
                        last_ladle_start = current_ladle['start_time']
                        current_ladle = fill_ladle(current_time, ladle_number, last_ladle_start, get_deck_wt([lane_1, lane_2, lane_3, lane_4, lane_5, lane_6]))
                        current_time += fc.ladle_refill_time
                        # Ensure the ladle starts in the same lane it ran out on
                        lane_index -= 1
                        continue
                # Re-check the top rows after refilling the ladle
                top_rows_df = pourable_carts([lane_1, lane_2, lane_3, lane_4, lane_5, lane_6], current_time)
                # Add buffer time when moving to the next lane
                current_time += fc.cart_pour_buffer_sec
                current_ladle = update_ladle_temp(current_ladle, fc.cart_pour_buffer_sec)
        if pd.concat([lane_1, lane_2, lane_3, lane_4, lane_5, lane_6])['molds_remaining'].sum() == 0:
            break

    current_ladle['top_mold_wt'] = get_top_mold_wt([lane_1, lane_2, lane_3, lane_4, lane_5, lane_6])
    ladles = pd.concat([ladles, pd.DataFrame([current_ladle])])
    ladles['avg_mold_wt'] = ladles.apply(lambda row: row['total_mold_wt'] / row['molds_filled'], axis=1)
    lanes = [lane_1, lane_2, lane_3, lane_4, lane_5, lane_6]
    # End the timer and print the elapsed time
    end_time = time.time()
    #elapsed_time = end_time - start_time
    return ladles, lanes, current_time


