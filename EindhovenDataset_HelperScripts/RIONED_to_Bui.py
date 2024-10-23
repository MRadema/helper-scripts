"""
Created on: 2024-05-29
Author: Mees Radema
Last updated: 2024-08-21

Description:
This script was made to isolate RIONED design precipitation from a csv & extract it into .bui files usable for Delft3D-FM.
A set amount of hours is specified to add as 'empty space' at the end of the event, to ensure the model runs for longer than there is input (& there is time for rainfall response)

NOTE: This script is provided 'as-is'. Use at your own risk.
"""
import pandas as pd
import numpy as np
from datetime import datetime

### Input files
rioned_csv = "c:/code_wd/wb-01/workbench-01/HybridurbHelpers/Rainfall_NL_RIONED.csv"

### Settings
length_addition = 3                 # amount of hours to add at the end of the event.
event_t0 = "2023 01 01 00 00 00"    # all events share this t0
out_folder = "c:/code_wd/wb-01/workbench-01/HybridurbHelpers/bui_files"


def write_preamble(filename, duration_seconds, first_record):
    creationtime = datetime.now()
    creationtime = creationtime.strftime("%Y/%m/%d %H:%M:%S")
    preamble_lines = [f"* Created: {creationtime}",
                       "* Use the default data set for other input (always 1)",
                       "1",
                       "*Aantal stations",
                        "1",
                        "*Namen van stations",
                        "'Global'",
                        "* Number of events and the period in seconds",
                        "1 300",
                        "* The first record contains the start date and time (yyyy mm dd HH mm ss), * followed by the length of the event (dd HH mm ss).",
                        "* The last part is the data for each time step.",
                        first_record]
    f = open(filename, "w")
    for line in preamble_lines:
        f.write(line)
        f.write("\n")
    f.close()
    


input_df = pd.read_csv(rioned_csv, sep=',', skiprows=2)

# Loop through input dataframe by row to grab event
for index, row in input_df.iterrows():
    eventname = row.iloc[0]
    filename = f"{out_folder}/{eventname}.bui"
    # get rid of useless columns (first few are metadata, lots of na's at end)
    row = row[3:].dropna().to_numpy()
    row = np.append(row, np.zeros(length_addition*12)) # add empty hours at end of event

    # get event length; days hours and minutes
    e_days =   row.size / 12 // 24
    e_hours = (row.size / 12) % 24 // 1
    e_mins =  (row.size / 12) % 24 % 1 * 60
    if e_days < 10:
        e_days =  f"0{int(e_days)}"
    else: 
        e_days = int(e_days)
    if e_hours < 10:
        e_hours = f"0{int(e_hours)}"
    else: 
        e_hours = int(e_hours)
    if e_mins < 10:
        e_mins = f"0{int(e_mins)}"
    else: 
        e_mins = int(e_mins)
    duration_seconds = int(row.size / 12 * 3600)

    first_record = f"{event_t0} {e_days} {e_hours} {e_mins} 00"

    write_preamble(filename, duration_seconds, first_record)

    f = open(filename, "a")
    for record in row:
        f.write(f"{record / 12}")
        f.write("\n")
    f.close()
    print(f"written file {filename}")




