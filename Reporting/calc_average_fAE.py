# -*- coding: utf-8 -*-
"""
Created on Mon Nov  4 14:05:52 2019

@author: NINIC2
"""
import numpy as np
import pandas as pd
from connect_datEAUbase import *

def calc_average(df_column, treshold):
    
    #Get values as a list
    var_temp = df_column.dropna()
    var = var_temp.tolist()
        
    #Get timestamp as a list
    time_temp = var_temp.reset_index().datetime
    time = [date_to_epoch(date) for date in time_temp]
    
    #Get indexes of the values above treshold
    var_high_indx = [ind for ind, x in enumerate(var) if x > treshold]
    
    #Locate jumps
    var_jump = [indx_2 - indx_1 for indx_1, indx_2 in zip(var_high_indx, var_high_indx[1:])]
    
    #Calculate average of the variable when var is higher than the specified treshold
    buffer = []; var_avg = []; time_avg = []
    for i in np.arange(0, len(var_jump)-1, 1).tolist():
        if var_jump[i] == 1:
            buffer.append(var[var_high_indx[i]])
        else:
            var_avg.append(sum(buffer)/len(buffer))
            time_avg.append(time[var_high_indx[i]-round(len(buffer)/2)])
            buffer = []
            buffer.append(var[var_high_indx[i]])
    
    #Convert epoch time to datetime type
    time_avg = [epoch_to_pandas_datetime(dateTime) for dateTime in time_avg]
    
    #Create a new dataframe and return it
    df = pd.DataFrame(list(zip(time_avg,var_avg)),columns=['datetime',df_column.name+' - avg cycle'])
    df.set_index('datetime', inplace=True)
    return df