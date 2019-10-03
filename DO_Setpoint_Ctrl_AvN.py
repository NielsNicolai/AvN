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
import time
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
    path_intermData = 'C:/Users/NINIC2/Documents/GitHub/AvNControl/'
    #Define in which folder the final control action is stored
    path_ctrlAction = 'C:/Users/NINIC2/Documents/GitHub/AvNControl/'
    #Define in which folder the user defined variables are found
    path_usrVals = 'C:/Users/NINIC2/Documents/GitHub/AvNControl/'
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

j = 1
while df.empty and j < 10:
    df = extract_data(conn, extract_list)
    time.sleep(j*0.5) #delay next reading
    j += 1

df.columns = param_list
df = df*1000 #set the units correctly to mg/L

#Replace all zero values for NaNs
df = df.replace(0.0, np.nan)
df = df.dropna()

#%%  GET INTERMEDIATE DATA STORED LOCALLY

#today = datetime.datetime.now().strftime("%Y%m%d")
#yesterdayTemp = datetime.datetime.now() - datetime.timedelta(days=1)
#yesterday = yesterdayTemp.strftime("%Y%m%d")

#Try to get previous control values saved in an existing txt file of the same day
try:    
    stored_vals = pd.read_csv(path_intermData+'intermDataAvNCtrl_'+'.csv', sep=',')
    stored_vals.set_index('datetime', drop=True, inplace=True)
    DOsp_1  = stored_vals['DOsp_1'].iloc[-1]
    error_1 = stored_vals['error_1'].iloc[-1]
    error_2 = stored_vals['error_1'].iloc[-2]
    PID_P_1 = stored_vals['Cntrb. P'].iloc[-1]
    PID_I_1 = stored_vals['Cntrb. I'].iloc[-1]
    PID_D_1 = stored_vals['Cntrb. D'].iloc[-1]

    #Prevent errors when database read communication results in NaN
    l = 2
    while (np.isnan(DOsp_1) or np.isnan(error_1) or np.isnan(PID_P_1) or np.isnan(PID_I_1) or np.isnan(PID_D_1)) and l < 10:
           DOsp_1  = stored_vals['DOsp_1'].iloc[-l]
           error_1 = stored_vals['error_1'].iloc[-l]
           error_2 = stored_vals['error_1'].iloc[-l-1]
           PID_P_1 = stored_vals['Cntrb. P'].iloc[-l]
           PID_I_1 = stored_vals['Cntrb. I'].iloc[-l]
           PID_D_1 = stored_vals['Cntrb. D'].iloc[-l]
           l += 1

#Catch error if file is not existing              
except FileNotFoundError as e1:
    
    #Try to get previous control values saved in an existing txt file of the previous day
    '''try: 
        stored_vals = pd.read_csv(path_intermData+'intermDataAvNCtrl_'+yesterday+'.csv', sep=',')
        stored_vals.set_index('datetime', drop=True, inplace=True)
        DOsp_1  = stored_vals['DOsp_1'].iloc[-1]
        error_1 = stored_vals['error_1'].iloc[-1]
    
    #Create a new file where the previous control values will be saved
    except FileNotFoundError as e2:'''
    DOsp_1 = usr_vals['DOsp']
    error_1 = usr_vals['NH4']-(usr_vals['alpha']*usr_vals['NO3'])-usr_vals['beta']
    error_2 = error_1
    PID_P_1 = 0
    PID_I_1 = 0
    PID_D_1 = 0

    
    stored_vals = pd.DataFrame(
        data={
            'datetime':[datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            'DOsp_1':usr_vals['DOsp'],
            'error_1':error_1,
            'NH4':usr_vals['NH4'],
            'NO3':usr_vals['NO3'],
            'P':usr_vals['P'],
            'I':usr_vals['I'],
            'D':usr_vals['D'],
            'Cntrb. P':PID_P_1,
            'Cntrb. I':PID_I_1,
            'Cntrb. D':PID_D_1,
            }
        )
    stored_vals.set_index('datetime', inplace=True)
    with open(path_intermData+'intermDataAvNCtrl_'+'.csv', 'a') as f:
        stored_vals.to_csv(f, header=True)



#%%  FILTER DATA
#Filter the data to get a representative value for control action calculation
Fs = 6 #sample frequency in samples per minute
NFltr = round(usr_vals['lenFltr']*Fs) #filter length in minutes

NH4 = df['NH4-N'].iloc[-NFltr:].mean()
NO3 = df['NO3-N'].iloc[-NFltr:].mean()

#%% POSITIONAL PID ALGORITHM + ANTI-RESET WINDUP
#PID controller according to K. Astrom - Control System Design - 2002 
#Forward Euler for the integral term; Backward Euler for the derivative term
#Anti-windup strategy using back-calculation
#Filtered derivative action using a low pass filter with filter coeff N
#Without setpoint weighing (reason: AvN setpoint is fixed to 0)

#Calculate the error
error = NH4 - (usr_vals['alpha']*NO3) - usr_vals['beta'] #difference

#Recalculate control parameters
#Sampling time
h = usr_vals['Ts']

#Proportional action
K = usr_vals['P']

#Integral action
if usr_vals['I'] != 0: #Make sure not to divide by 0
	Ti = usr_vals['P']/usr_vals['I'] 
else:
	Ti = 999999

#Derivative action
if usr_vals['P'] != 0:
	Td = usr_vals['D']/usr_vals['P']
else:
	Td = 0

if Td != 0: #Tracking time constant for anti-windup back-calculation
	Tt = Ti/2#(Ti*Td)**0.5
else:
	Tt = Ti/2
    
N = usr_vals['N'] #Derivative LPF filter coefficient (the higher the less filtering)

#Compute control coefficients
int_coeff_1 = K*h/Ti
int_coeff_2 = h/Tt
dif_coeff_1 = (2*Td-N*h)/(2*Td+N*h)
dif_coeff_2 = 2*K*N*Td/(2*Td+N*h)

#Control action calculation
PID_P = K*error
PID_D = (dif_coeff_1*PID_D_1)-(dif_coeff_2*(error-error_1))

if Td == 0:
    PID_D = 0

#Sanity check of the PID terms in case nan comes up (Should already be cached when reading stored values for multiple times)
if np.isnan(PID_P):
    PID_P = 0
if np.isnan(PID_I_1):
    PID_I_1 = 0  
if np.isnan(PID_D):
    PID_D = 0

#Summation of each of the PID terms
DOsp_uncstrnd = PID_P+PID_I_1+PID_D

#Limit the DO setpoint
DOsp = np.clip(DOsp_uncstrnd, a_min=usr_vals['DOsp_min'], a_max=usr_vals['DOsp_max'])

#If for some reason the calculated values are NaNs
if np.isnan(DOsp) | np.isnan(DOsp_uncstrnd): 
    DOsp = DOsp_1
    DOsp_uncstrnd = DOsp_1

#Update integral action: Forward Euler integration taking into account reset windup
PID_I = PID_I_1 + int_coeff_1*error + int_coeff_2*(DOsp-DOsp_uncstrnd)

#Sanity check of the I term in case nan comes up (Should already be cached when reading stored values for multiple times)
if np.isnan(PID_I):
    PID_I = 0

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
        'NH4':[round(NH4,4)],
        'NO3':[round(NO3,4)],
        'P':[usr_vals['P']],
        'I':[usr_vals['I']],
        'D':[usr_vals['D']],
        'Cntrb. P':[round(PID_P,4)],
        'Cntrb. I':[round(PID_I,4)],
        'Cntrb. D':[round(PID_D,4)],
        }
    )
new_vals.set_index('datetime', drop=True, inplace=True)  

with open(path_intermData+'intermDataAvNCtrl_'+'.csv', 'a', newline='') as f:
    new_vals.to_csv(f, header=False)
    