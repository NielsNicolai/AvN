# -*- coding: utf-8 -*-
"""
Created on Tue Jul 30 16:23:40 2019
@author: NINIC2

DESCRIPTION: THE FOLLOWING SCRIPT IS USED FOR AVN CONTINUOUS DO SETPOINT CONTROL.
IT IS SPECIFICALLY TAILORD FOR THE CO-PILOT REACTOR OF THE pilEAUTe PLANT OF THE modelEAU GROUP OF PROF. P. VANROLLEGHEM.
ALL MEASUREMENT DATA IS OBTAINED FROM THE datEAUbase. PROPER FUNCTIONING OF THE LATTER IS THEREFORE MANDATORY.

Copyright (c) 2019 by Niels Nicolaï, nicolai.niels@gmail.com, modelEAU, Université Laval. All Rights Reserved.
"""

import datetime
import pandas as pd
import numpy as np
import os
#import definitions_AvN 

from connectDatEUAbase import *

#%%  PC CHECK
#Determine on which PC the script is running
PC_name = os.environ['COMPUTERNAME']

if PC_name == 'MODELEAU':
    #Define in which folder the intermediate data is stored
    path_intermData = 'C:/Users/Admin/Documents/Python Scripts/AvN Control/Data/'
    #Define in which folder the final control action is stored
    path_ctrlAction = 'D:/DataReadFile/'
    #Define in which folder the user defined variables are found
    path_usrVals = 'C:/Users/Admin/Documents/Python Scripts/AvN Control/'
elif PC_name == 'GCI-MODELEAU-08':
    #Define in which folder the intermediate data is stored
    path_intermData = 'C:/Users/NINIC2/Documents/Python Scripts/'
    #Define in which folder the final control action is stored
    path_ctrlAction = 'C:/Users/NINIC2/Documents/Python Scripts/'
    #Define in which folder the user defined variables are found
    path_usrVals = 'C:/Users/NINIC2/Documents/Python Scripts/'
else:
    print('Add directories to PATH')
    exit()
    
#%% LOAD USER DEFINED PARAMETERS
with open(path_usrVals+'values_init_DOsp_AvN.txt') as f:
    usr_vals = eval(f.read())

#%%  GET DATA FROM datEAUbase
#Initialise connection with the datEAUbase
cursor, conn = create_connection()

#Get measurement data over a specific interval
intrvl = 3 #minutes
delay = 2 #minutes
stopDateTime = datetime.datetime.now() - datetime.timedelta(hours=0, minutes=delay, seconds=0)
startDateTime = stopDateTime - datetime.timedelta(hours=0, minutes=intrvl, seconds=0)
Start = date_to_epoch(startDateTime.strftime("%Y-%m-%d %H:%M:%S"))
End = date_to_epoch(stopDateTime.strftime("%Y-%m-%d %H:%M:%S"))

#Define the requested parameters
Location = 'Copilote effluent'
Project = 'pilEAUte'
param_list = ['NH4-N','NO3-N']
equip_list = ['Varion_001','Varion_001']

#Extract the specified parameters from the datEAUbase
extract_list={}
for i in range(len(param_list)):
    extract_list[i] = {
        'Start':Start,
        'End':End,
        'Project':Project,
        'Location':Location,
        'Parameter':param_list[i],
        'Equipment':equip_list[i]
    }
    
#Create a new pandas dataframe
#print('ready to extract')
df = extract_data(conn, extract_list)
df.columns = param_list
df = df*1000 #set the units correctly to mg/L

#Replace all zero values for NaNs
df = df.replace(0.0, np.nan)

#%%  GET INTERMEDIATE DATA STORED LOCALLY

today = datetime.datetime.now().strftime("%Y%m%d%H%M")
yesterdayTemp = datetime.datetime.now() - datetime.timedelta(days=1)
yesterday = yesterdayTemp.strftime("%Y%m%d%H%M")

#Try to get previous control values saved in an existing txt file of the same day
try:    
    stored_vals = pd.read_csv(path_intermData+'intermDataAvNCtrl_'+today+'.csv', sep=',')
    stored_vals.set_index('datetime', drop=True, inplace=True)
    DOsp_1  = stored_vals['DOsp_1'].iloc[-1]
    error_1 = stored_vals['error_1'].iloc[-1]
    error_2 = stored_vals['error_2'].iloc[-1]

    #Prevent errors when database read communication results in NaN
    i = 2
    if np.isnan(DOsp_1) or np.isnan(error_1):
           DOsp_1  = stored_vals['DOsp_1'].iloc[-i]
           error_1 = stored_vals['error_1'].iloc[-i]
           error_2 = stored_vals['error_2'].iloc[-i]

#Catch error if file is not existing              
except FileNotFoundError as e1:
    
    #Try to get previous control values saved in an existing txt file of the previous day
    try: 
        stored_vals = pd.read_csv(path_intermData+'intermDataAvNCtrl_'+yesterday+'.csv', sep=',')
        stored_vals.set_index('datetime', drop=True, inplace=True)
        DOsp_1  = stored_vals['DOsp_1'].iloc[-1]
        error_1 = stored_vals['error_1'].iloc[-1]
        error_2 = stored_vals['error_2'].iloc[-1]
    
    #Create a new file where the previous control values will be saved
    except FileNotFoundError as e2:
        DOsp_1 = usr_vals['DOsp_1']
        error_1 = usr_vals['error_1']
        error_2 = usr_vals['error_2']
        stored_vals = pd.DataFrame(
            data={
                'datetime':[datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                'DOsp_1':usr_vals['DOsp_1'],
                'error_1':usr_vals['error_1'],
                'error_2':usr_vals['error_2'],
                'NH4':usr_vals['NH4'],
                'NO3':usr_vals['NO3'],
                'P':usr_vals['P'],
                'I':usr_vals['I'],
                'D':usr_vals['D'],
                'Cntrb. P':0,
                'Cntrb. I':0,
                'Cntrb. D':0,
                }
            )
        stored_vals.set_index('datetime', inplace=True)
        with open(path_intermData+'intermDataAvNCtrl_'+today+'.csv', 'a') as f:
            stored_vals.to_csv(f, header=True)

#%%  FILTER DATA
#Filter the data to get a representative value for control action calculation
Fs = 6 #sample frequency in samples per minute
NFltr = round(usr_vals['lenFltr']*Fs) #filter length in minutes

NH4 = df['NH4-N'].iloc[-NFltr:].mean()
NO3 = df['NO3-N'].iloc[-NFltr:].mean()

#%%  PID CONTROL
#PID control action calculation using filtered value
error_mode = "diff" #Determines the way the AvN error is calculated: "ratio" or "diff"
operating_mode = "auto" #Determines the operating mode of the controller: "man" or "auto"

c0 = usr_vals['P'] + (usr_vals['I']*usr_vals['Ts'] + usr_vals['D']/usr_vals['Ts'])
c1 = -(usr_vals['P'] + 2*usr_vals['D']/usr_vals['Ts'])
c2 = usr_vals['D']/usr_vals['Ts']

if error_mode == "ratio":
    error = NH4/(usr_vals['alpha']*NO3)- usr_vals['beta'] - 1 #ratio should be equal to 1, therefore subtract by 1
else:
    error = NH4 - (usr_vals['alpha']*NO3) - usr_vals['beta'] #difference
  
DOsp = DOsp_1 + (error*c0 + error_1*c1 + error_2*c2) #note the positive gain of the process

#Calculate the contributions of each term in the PID control law
cntrbP = error*usr_vals['P']-error_1*usr_vals['P']
cntrbI = error*usr_vals['I']*usr_vals['Ts']
cntrbD = error*usr_vals['D']/usr_vals['Ts']-error_1*2*usr_vals['D']/usr_vals['Ts']+error_2*usr_vals['D']/usr_vals['Ts']

#Clipping of the control action according to the physical limiations system
DOsp = np.clip(DOsp, a_min=usr_vals['DOsp_min'], a_max=usr_vals['DOsp_max'])

DOsp_man = 0.1 #Manual mode setpoint
if operating_mode == "auto":
    DOsp = DOsp
else:
    DOsp = usr_vals['DOsp_man']
	
if np.isnan(DOsp): #If for some reason the calculated value is NaN
    DOsp = DOsp_1

#%% APPLY SETPOINT
#Overwrite CSV file DO setpoints continuous DO control
write_time = datetime.datetime.now() + datetime.timedelta(seconds=20) #delay at least 2 times the update rate SCADA reader.

#write_delay = 5
#write_time_red1 = datetime.datetime.now() + datetime.timedelta(seconds=write_delay)
#write_time_red2 = write_time_red1 + datetime.timedelta(seconds=write_delay)
#write_time_red3 = write_time_red2 + datetime.timedelta(seconds=write_delay)

new_DOsp = pd.DataFrame(
    data={
        'date':[datetime.datetime.now().strftime("%Y.%m.%d")], 
        'hour':[write_time.strftime("%H:%M:%S")],
        'DOsp':[round(DOsp,2)],
        }
    )

with open(path_ctrlAction+'AIC_341_Data.csv', 'w', newline='') as f:
    new_DOsp.to_csv(f, index=False, header=False)

#%% STORE INTERMEDIATE DATA LOCALLY
#Store control values
new_vals = pd.DataFrame(
    data={
        'datetime':[datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        'DOsp_1':[round(DOsp,4)],
        'error_1':[round(error,4)],
        'error_2':[round(error_1,4)],
        'NH4':[round(NH4,4)],
        'NO3':[round(NO3,4)],
        'P':[usr_vals['P']],
        'I':[usr_vals['I']],
        'D':[usr_vals['D']],
        'Cntrb. P':[round(cntrbP,4)],
        'Cntrb. I':[round(cntrbI,4)],
        'Cntrb. D':[round(cntrbD,4)],
        }
    )
new_vals.set_index('datetime', drop=True, inplace=True)    

with open(path_intermData+'intermDataAvNCtrl_'+today+'.csv', 'a', newline='') as f:
    new_vals.to_csv(f, header=False)
    