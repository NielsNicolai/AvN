# -*- coding: utf-8 -*-
"""
Created on Fri Oct 18 09:12:22 2019
@author: NINIC2

DESCRIPTION: THE FOLLOWING SCRIPT CAN BE USED TO READ A DATA FILE GENERATED BY THE TRESCON INSTRUMENT
IT WILL AUTOMATICALLY SET THE DATATIME IN THE CORRECT FORMAT

Copyright (c) 2019 by Niels Nicolaï, nicolai.niels@gmail.com, modelEAU, Université Laval. All Rights Reserved.
"""

import pandas as pd
import datetime

#%% USER INPUTS
path = 'October/' #relative path where file can be found
file = 'teraterm_raw.log' #.log file obtained from TeraTerm (make sure to remove the header)

#%% EXTRACT DATA
# Read the raw .log file generated by teraterm
with open(path+'teraterm_raw.log', 'r') as file:
    raw = file.read()

# Parse string and replace where needed
temp = raw.replace(' mg/l NH4-N ',',')
temp = temp.replace(' mg/l NOx-N ',',')
temp = temp.replace(' mg/l NO2-N','')
temp = temp.replace('  ',',')
temp = temp.replace('stop','')

# Add column names at the top
temp = 'date,time,TresCon NH4-N,TresCon NOx-N,TresCon NO2-N\n' + temp

# Save the result in a .CSV file
file_name = path+'TresCon_'+datetime.datetime.now().strftime('%Y%m%d')+'.csv'
with open(file_name, 'w') as file:
    file.write(temp)

# Specify the file path. Either relative to this python script or absolute
df_tres = pd.read_csv(file_name, sep=',')

# Make one column with the date and time
df_tres['datetime'] = df_tres.apply(lambda row: row['date']+' '+row['time'], axis = 1)
df_tres.drop(columns=['date','time'],inplace=True)

# Adjust formatting of datetime column to match the formatting of the datEAUbase
df_tres['datetime'] = pd.to_datetime(df_tres['datetime'],dayfirst = True)

# Make datetime the index column
df_tres.set_index('datetime', drop=True, inplace=True)

# Save the result in a .CSV file
df_tres.to_csv(file_name)


#%% COMBINE DATA
##Merge this dataframe with another one
#df_final = df.join(df_tres, how='outer')
#
##Saves the final dataset in a CSV file
#df_final.to_csv('October/alldata_20191018.csv')