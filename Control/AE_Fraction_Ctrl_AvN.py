# -*- coding: utf-8 -*-
"""
Created on Tue Jul 30 16:23:40 2019
@author: NINIC2

DESCRIPTION: THE FOLLOWING SCRIPT IS USED FOR TIMING THE AVN INTERMITTEND AERATION CONTROL.
IT IS SPECIFICALLY TAILORD FOR THE CO-PILOT REACTOR OF THE pilEAUTe PLANT OF THE modelEAU GROUP OF PROF. P. VANROLLEGHEM.
ALL MEASUREMENT DATA IS OBTAINED FROM THE datEAUbase. PROPER FUNCTIONING OF THE LATTER IS THEREFORE MANDATORY.

Copyright (c) 2019 by Niels Nicolaï, nicolai.niels@gmail.com, modelEAU, Université Laval. All Rights Reserved.
"""

import datetime
import pandas as pd
import numpy as np
import os
import time

from connectDatEUAbase import *

#%%  PC CHECK
#Determine on which PC the script is running
PC_name = os.environ['COMPUTERNAME']


if PC_name == 'MODELEAU':
    #Define in which folder the intermediate data is stored
    path_intermData = 'C:/Users/Admin/Documents/Python Scripts/AvN Control/Data/'
    #Define in which folder the control scripts is stored
    path_controller = 'C:/Users/Admin/Documents/Python Scripts/AvN Control/'
    #Define in which folder the final control action is stored
    path_ctrlAction = 'D:/DataReadFile/'
    #Define in which folder the user defined variables are found
    path_usrVals = 'C:/Users/Admin/Documents/Python Scripts/AvN Control/'
elif PC_name == 'GCI-MODELEAU-08':
    #Define in which folder the intermediate data is stored
    path_intermData = 'C:/Users/NINIC2/Documents/GitHub/AvN/Control/Data/'
    #Define in which folder the control scripts is stored
    path_controller = 'C:/Users/NINIC2/Documents/GitHub/AvN/Control/'
    #Define in which folder the final control action is stored
    path_ctrlAction = 'C:/Users/NINIC2/Documents/GitHub/AvN/Control/Data/'
    #Define in which folder the user defined variables are found
    path_usrVals = 'C:/Users/NINIC2/Documents/GitHub/AvN/Control/'
else:
    print('Add directories to PATH')
    exit()
    
#%% LOAD USER DEFINED PARAMETERS
with open(path_usrVals+'values_init_fAE_AvN.txt') as f:
    usr_vals = eval(f.read())
    
#%%  GET INTERMEDIATE DATA STORED LOCALLY
#Try to get previous control values saved in an existing txt file
try:    
    stored_vals = pd.read_csv(path_intermData+'intermDataAvNCtrl_fAE.csv', sep=',')
    stored_vals.set_index('datetime', drop=True, inplace=True)
    fAE_1  = stored_vals['fAE'].iloc[-1]
    error_1 = stored_vals['error_1'].iloc[-1]
    error_2 = stored_vals['error_1'].iloc[-2]
    PID_P_1 = stored_vals['Cntrb. P'].iloc[-1]
    PID_I_1 = stored_vals['Cntrb. I'].iloc[-1]
    PID_D_1 = stored_vals['Cntrb. D'].iloc[-1]
    tAE_1 = stored_vals['tAE'].iloc[-1]
    counter_1 = stored_vals['counter'].iloc[-1]

    #Prevent errors when database read communication results in NaN
    l = 2
    while (np.isnan(fAE_1) or np.isnan(error_1) or np.isnan(PID_P_1) or np.isnan(PID_I_1) or np.isnan(PID_D_1) or np.isnan(tAE_1) or np.isnan(counter_1)) and l < 10:
           fAE_1  = stored_vals['fAE'].iloc[-l]
           error_1 = stored_vals['error_1'].iloc[-l]
           error_2 = stored_vals['error_1'].iloc[-l-1]
           PID_P_1 = stored_vals['Cntrb. P'].iloc[-l]
           PID_I_1 = stored_vals['Cntrb. I'].iloc[-l]
           PID_D_1 = stored_vals['Cntrb. D'].iloc[-l]
           tAE_1 = stored_vals['tAE'].iloc[-l]
           counter_1 = stored_vals['counter'].iloc[-l]+l-1
           l += 1

#Catch error if file is not existing              
except FileNotFoundError as e:
    DOsp_1 = 0
    fAE_1 = usr_vals['fAE']
    error_1 = usr_vals['NH4']-(usr_vals['alpha']*usr_vals['NO3'])-usr_vals['beta']
    error_2 = error_1
    PID_P_1 = 0
    PID_I_1 = usr_vals['fAE_man']
    PID_D_1 = 0
    tAE_1 = 0
    counter_1 = usr_vals['Tc']-2*usr_vals['Ts']
    
    stored_vals = pd.DataFrame(
        data={
            'datetime':[datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            'DOsp':DOsp_1,
            'fAE':usr_vals['fAE'],
            'error_1':error_1,
            'NH4':usr_vals['NH4'],
            'NO3':usr_vals['NO3'],
            'P':usr_vals['P'],
            'I':usr_vals['I'],
            'D':usr_vals['D'],
            'Cntrb. P':PID_P_1,
            'Cntrb. I':PID_I_1,
            'Cntrb. D':PID_D_1,
            'tAE':tAE_1,
            'counter':counter_1,
            }
        )
    stored_vals.set_index('datetime', inplace=True)
    with open(path_intermData+'intermDataAvNCtrl_fAE.csv', 'a') as f:
        stored_vals.to_csv(f, header=True)


#%% GET CURRENT COUNTER VALUE THAT KEEPS TRACK OF THE AvN CYCLE
#Increment the counter with 1 time step    
counter = counter_1 + 1*usr_vals['Ts']

# Reset counter whenever the cycle time is reached
if counter >= usr_vals['Tc']:
    counter = 0

#%% APPLY THE CORRECT DO SETPOINT DEPENDING ON THE PHASE WITHIN THE CYCLE
#Aerobic phase
if counter >= tAE_1:
    DOsp = 0

#Anoxic phase
elif counter < tAE_1:
    DOsp = usr_vals['DOsp']
    
write_time_1 = datetime.datetime.now() + datetime.timedelta(seconds=20)

new_fAE = pd.DataFrame(
    data={
        'DOsp':[round(DOsp,2)],
        }
    )

with open(path_ctrlAction+'AIC_241_Data_V2.csv', 'w', newline='') as f:
    new_fAE.to_csv(f, index=False, header=False)

with open(path_ctrlAction+'AIC_251_Data_V2.csv', 'w', newline='') as f:
    new_fAE.to_csv(f, index=False, header=False)

#%%  GET DATA FROM datEAUbase
error_conn = False
error_import = False

try:
    #Initialise connection with the datEAUbase
    cursor, connection = create_connection()
    NH4, NH4_timestamp = get_last_value(connection, 49) #metadata_ID = 49 : NH4 pilote
    NH4 = NH4*1000
    NO3, NO3_timestamp = get_last_value(connection, 51) #metadata_ID = 51 : NO3 pilote
    NO3 = NO3*1000
    current_time = date_to_epoch(datetime.datetime.now())

    # Import of data into the datEAUbase ceased for some reason
    max_delay = 10*60
    if  current_time - NH4_timestamp > max_delay or current_time - NO3_timestamp > max_delay:
        NH4 = 55
        NO3 = 55
        error_import = True

# Connection to the datEAUbase failed
except:
    NH4 = 99
    NO3 = 99
    error_conn = True

#%% WHEN THE PREVIOUS CYCLE IS ALMOST FINISHED --> CALCULATE THE NEW AEROBIC FRACTION USING A PID CONTOLLER 

#Calculate the error
error = NH4 - (usr_vals['alpha']*NO3) - usr_vals['beta'] #difference

if counter == usr_vals['Tc']-1*usr_vals['Ts'] and not error_conn and not error_import:
    #PID controller according to K. Astrom - Control System Design - 2002
    #Forward Euler for the integral term; Backward Euler for the derivative term
    #Anti-windup strategy using back-calculation
    #Filtered derivative action using a low pass filter with filter coeff N
    #Without setpoint weighing (reason: AvN setpoint is fixed to 0)
    
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
    	Tt = (Ti*Td)**0.5
    else:
    	Tt = Ti
        
    N = usr_vals['N'] #Derivative LPF filter coefficient (the higher the less filtering)
    
    #Compute control coefficients
    int_coeff_1 = K*h/Ti
    int_coeff_2 = h/Tt
	#According to book Astrom: (gives problems)
	#dif_coeff_1 = (2*Td-N*h)/(2*Td+N*h)
	#dif_coeff_2 = 2*K*N*Td/(2*Td+N*h)
	#According to scilab:
    dif_coeff_1 = Td/(Td+h*N) #scilab
    dif_coeff_2 = -Td*K*N/(Td+N*h)
    
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
    fAE_uncstrnd = PID_P+PID_I_1+PID_D
    
    #Limit the DO setpoint
    fAE = np.clip(fAE_uncstrnd, a_min=usr_vals['fAE_min'], a_max=usr_vals['fAE_max'])
    
    #If for some reason the calculated values are NaNs
    if np.isnan(fAE) or np.isnan(fAE_uncstrnd): 
        fAE = fAE_1
        fAE_uncstrnd = fAE_1
        
    #Convert aerobic fraction to time
    tAE = round(fAE*usr_vals['Tc'])
    
    #Update integral action: Forward Euler integration taking into account reset windup
    PID_I = PID_I_1 + int_coeff_1*error + int_coeff_2*(fAE-fAE_uncstrnd)
    
    #Sanity check of the I term in case nan comes up (Should already be cached when reading stored values for multiple times)
    if np.isnan(PID_I):
        PID_I = 0

else:
    fAE = fAE_1
    tAE = tAE_1    
    PID_P = PID_P_1
    PID_I = PID_I_1
    PID_D = PID_D_1
    
    
#%% STORE INTERMEDIATE DATA LOCALLY
#Store control values
new_vals = pd.DataFrame(
    data={
        'datetime':[datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        'DOsp':[DOsp],
        'fAE_1':[round(fAE,4)],
        'error_1':[round(error,4)],
        'NH4':[round(NH4,4)],
        'NO3':[round(NO3,4)],
        'P': [usr_vals['P']],
        'I': [usr_vals['I']],
        'D': [usr_vals['D']],
        'Cntrb. P':[round(PID_P,5)],
        'Cntrb. I':[round(PID_I,5)],
        'Cntrb. D':[round(PID_D,5)],
        'tAE':[tAE],
        'counter':[counter],
        }
    )
new_vals.set_index('datetime', drop=True, inplace=True)    

with open(path_intermData+'intermDataAvNCtrl_fAE.csv', 'a', newline='') as f:
    new_vals.to_csv(f, header=False)





















