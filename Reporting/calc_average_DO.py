# -*- coding: utf-8 -*-
"""
Created on Mon Nov  4 14:05:52 2019

@author: NINIC2
"""

from connect_datEAUbase import date_to_epoch

def calc_average_DO(df_DO_column, DO_treshold=1):
    
    #Get DO values as a list
    DO_temp = df_DO_column.dropna()
    DO = DO_temp.tolist()
        
    #Get timestamp as a list
    time_temp = DO_temp.reset_index().datetime
    time = [date_to_epoch(date) for date in time_temp]
    
    #Get indexes of DO values above treshold
    DO_high_indx = [ind for ind, x in enumerate(DO) if x > DO_treshold]
    
    #Locate jumps in DO
    DO_jump = [indx_2 - indx_1 for indx_1, indx_2 in zip(DO_high_indx, DO_high_indx[1:])]
    
    #Calculate average DO when DO is higher than the specified treshold
    j = 0
    l = 0
    for i in DO_jump:
        if DO_jump[i] == 1:
            buffer[j] = DO[DO_high_indx[i]]
        else:
            DO_avg[l] = sum(buffer)/len(buffer)
            time_avg[l] = time[DO_high_indx[i]-round(len(buffer)/2)]
            j=0
            l+=1
            del buffer
            buffer[j] = DO[DO_high_indx[i]]
        j+=1

    return DO_avg, time_avg;