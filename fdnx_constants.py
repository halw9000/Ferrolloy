#Ferrolloy Constants
## Iron Constants
cold_pour_threshold = 2400 
hot_pour_threshold = 2550 

## FDNX Constants -- mold speeds and pattern switch times
mph_nocore = 35  # FDNX capacity per hour without core
mph_withcore = 25  # FDNX capacity per hour with core
pattern_switch_hours = .15  # Time for switching patterns on FDNX machine

## DECK Constants
deck_lanes = 6  
lane_cart_capacity = 20  # Capacity of each lane in terms of carts (not needed???)
molds_per_cart = 3  # Number of molds per cart
pour_speed_lbs_sec = 2  # Pour speed in lbs/sec
cart_pour_buffer_sec = 10  # Buffer time for pouring carts
distance_between_lanes_sec = 10  # Distance between lanes in seconds

## LADLE Constants
ladle_capacity = 650
ladle_avg_weight = 580
ladle_weight_dev = 7.5

ladle_start_temp_avg = 2650
ladle_start_temp_dev = 5
ladle_tempdrop_min = 25

ladle_refill_time = 180  # Time to refill a ladle in seconds

furnace_ready_min = 600  # Minimum time to refill a ladle in seconds
