##
# Script to run D-Flow outside of GUI
# Base runs (length, timestep etc) on input bui files
# 
# This script is provided as-is. Use at your own risk. 

import netCDF4 as nc
import numpy as np
import pandas as pd
import os
import xml.etree.ElementTree as ET
import shutil
import subprocess
from datetime import datetime

# Function to set the dimr's control XML file's time to a new length (in sec)
def updateXML(operational_xml, length_sec):
    with open(operational_xml, 'r') as file:
        data = file.readlines()
    data[34] = "        <time>0 300 "+str(length_sec)+"</time>"+'\n'
    with open(operational_xml, 'w') as file:
        file.writelines(data)

def updateMDU(mdu, length_sec):
    with open(mdu, 'r') as file:
        data = file.readlines()
    data[170] = "TStop             = "+str(length_sec)+" \n"
    with open(mdu, 'w') as file:
        file.writelines(data)

def updateDelft3Bini(inifile, length_hour, length_min):
    number_days = (length_hour // 24) + 1
    remainder_hours = int(length_hour % 24)
    remainder_min = int(length_min % 60)
    if remainder_hours < 10:
        remainder_hours = "0" + str(remainder_hours)
    if remainder_min < 10:
        remainder_min = "0" + str(remainder_min)

    endtime_str = "EndTime='2023/01/0"+str(number_days)+";"+str(remainder_hours)+":"+str(remainder_min)+":00'\n"
    with open(inifile, 'r') as file:
        data = file.readlines()
    data[50] = "TimestepSize=300\n"
    data[52] = endtime_str
    with open(inifile, 'w') as file:
        file.writelines(data)

#
def runDIMR(dimrpath, cwd, timeout=300):
    """run dimr for the fews model to generate mesh2d needed (will be killed after timeout)"""
    #logger.info(f'Running dimr in {cwd}, timeout = {timeout}')
    proc = subprocess.Popen(dimrpath, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            cwd=cwd,
                            universal_newlines=True)
    try:
        outs, errs = proc.communicate(timeout=timeout)
    except:
        pass

# Basic logging function. Takes current event, the file to log to, and message
def addToLog(logfile, bui, logmessage):
    f = open(logfile, 'a')
    currenttime = datetime.now().strftime("%Y-%m-%d %H:%M:%S:  ")
    full_log_message = currenttime + logmessage + bui + '\n'
    f.write(full_log_message)
    f.close()

def endLogPart(logfile):
    f = open(logfile, 'a')
    f.write("\n\n")
    f.close()

def endLog(logfile):
    f = open(logfile, 'a')
    currenttime = datetime.now().strftime("%Y-%m-%d %H:%M:%S:  ")
    full_log_message = "Task finished at " + currenttime
    f.write(full_log_message)
    f.close()


def saveOutput(bui, output_folder, output_storage_folder):
    output_file_his = output_folder + "FlowFM_his.nc"
    output_file_map = output_folder + "FlowFM_map.nc"
    output_file_dia = output_folder + "FlowFM.dia"

    output_storage_his = output_storage_folder + bui + '_his_output.nc'
    output_storage_map = output_storage_folder + bui + '_map_output.nc'
    output_storage_dia = output_storage_folder + bui + '_dia.dia'

    shutil.copy(output_file_his, output_storage_his)
    shutil.copy(output_file_map, output_storage_map)
    shutil.copy(output_file_dia, output_storage_dia)


## Directory definitions. This is a mess and should be cleaned up if anyone else uses this, because I don't know what
#             exactly I was thinking when I wrote this.  -MR 20-1-2022
#   As always, one is too lazy to clean up, because even if it's ugly, it works. -MR 29-05-2024

quit_on_except = True

base_path = "c:/wd/3dfm_test/"
BUI_path = base_path + "bui_files/"
default_BUI = base_path + "rr/default.bui"
mdu_path = base_path + "dflowfm/" + "FlowFM.mdu"
main_dimr_bat = base_path + "run_delft3dfm_2024.03.bat"
logfile = base_path + "run_log.txt"
output_folder = base_path + "dflowfm/output/"
output_storage_folder = "p:/11209195-012-urban-forecasting/Models/Delft3DFM/Output/"
operational_xml = base_path + "dimr_config.xml"
inifile = base_path + "rr/DELFT_3B.INI"

BUI_list = os.listdir(BUI_path)


for bui in BUI_list:
    # Feature extraction
    addToLog(logfile, bui, "Preparing data for: ")
    try:
        # read the current bui
        currentbui = BUI_path + bui
        f = open(currentbui, "r")
        data = f.readlines()
        f.close()

        # get the header with info on event duration & tear it down into a list
        info_line_list = data[11].strip().split()

        # get event duration in seconds
        c_days  = int(info_line_list[6])
        c_hours = int(info_line_list[7])
        c_min   = int(info_line_list[8])

        length_sec = (c_days * 86400) + (c_hours * 3600) + (c_min * 60)
        
        length_hour = length_sec // 3600
        length_min = length_sec / 60

        # Update dimr XML
        updateXML(operational_xml, length_sec)

        # update RR bui
        os.remove(default_BUI)
        shutil.copy(currentbui, default_BUI)

         #update rr 3Bini
        updateDelft3Bini(inifile, length_hour, length_min)

        # update MDU
        updateMDU(mdu_path, length_sec)
        addToLog(logfile, bui, "Successfully prepared ")
    except Exception as Argument:
        addToLog(logfile, bui, "Error preparing ")
        addToLog(logfile, bui, str(Argument))
        
        if quit_on_except:
            endLog(logfile)
            exit()

    # Model running
    addToLog(logfile, bui, 'Running D-Flow for: ')

    try:
        saveOutput(bui, output_folder, output_storage_folder)
        runDIMR(main_dimr_bat, base_path, timeout=36000)
        addToLog(logfile, bui, 'Delft3D ran successfully for ')
        saveOutput(bui, output_folder, output_storage_folder)
        addToLog(logfile, bui, 'Saved output successfully')

    except Exception as Argument:
        addToLog(logfile, bui, 'Failed running D-flow for ')
        addToLog(logfile, bui, str(Argument))
        if quit_on_except:
            endLog(logfile)
            exit()
            
    endLogPart(logfile)
endLog(logfile)

