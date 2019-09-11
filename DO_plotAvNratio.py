# -*- coding: utf-8 -*-
"""
Created on Thu Aug  1 18:33:22 2019

@author: NINIC2
"""

from bokeh.plotting import figure, output_file, show
from bokeh.models import DatetimeTickFormatter, Range1d
import datetime
from connectDatEUAbase import *

#Initialise connection with the datEAUbase
cursor, conn = create_connection()

#Get measurement data over a specific interval
begining = 11*24*60 #minutes
ending = 6*24*60  #minutes

startDateTime = datetime.datetime.now() - datetime.timedelta(hours=0, minutes=begining, seconds=0)
stopDateTime = datetime.datetime.now() - datetime.timedelta(hours=0, minutes=ending, seconds=0)

Start = date_to_epoch(startDateTime.strftime("%Y-%m-%d %H:%M:%S"))
End = date_to_epoch(stopDateTime.strftime("%Y-%m-%d %H:%M:%S"))

#Define the requested parameters
Project = 'pilEAUte'
Location = ['Copilote effluent','Copilote effluent']
param_list = ['NH4-N','NO3-N']
equip_list = ['Varion_001','Varion_001']

#Extract the specified parameters from the datEAUbase
extract_list={}
for i in range(len(param_list)):
    extract_list[i] = {
        'Start':Start,
        'End':End,
        'Project':Project,
        'Location':Location[i],
        'Parameter':param_list[i],
        'Equipment':equip_list[i]
    }
    
#Create a new pandas dataframe
#print('ready to extract')
df = extract_data(conn, extract_list)
df.columns = param_list
df = df*1000
#print(len(df))

#Replace all zero values for NaNs
df = df.replace(0.0, np.nan)

# output to static HTML file
output_file("AvN_nitrogen.html", title="NH4/NO3 ratio copilote")

# create a new plot with a title and axis labels
fig = figure(title="AvN controller performance", x_axis_label='', y_axis_label='Concentrations [mg/L]', plot_width=1600, plot_height=600)

# add a line renderer with legend and line thickness
fig.line(df.index, df['NO3-N'], legend="NO3-N", line_width=2, line_color="green")
#fig.line(x, df['avg NO3-N'], legend="Filtered NO3-N", line_width=2, line_color="green")

fig.line(df.index, df['NH4-N'], legend="NH4-N", line_width=2, line_color="red")
#fig.line(x, df['avg NH4-N'], legend="Filtered NH4_N", line_width=2, line_color="orange")

df['ratio'] = df['NH4-N']/df['NO3-N']

fig.line(df.index, df['ratio'], legend="Ratio NH4/NO3", line_width=2, line_color="blue")
fig.line(df.index, 1, line_width=1, line_color="black", line_dash = "dashed")

#fig.line(df.index, df['DO'], legend="DO tank 5", line_width=2, line_color="orange")

fig.xaxis.formatter=DatetimeTickFormatter(
    days=["%m/%d"],
    hours=["%m/%d - %H:%M"],
    minutes=["%m/%d - %H:%M"]
)

fig.legend.location = 'top_left'

fig.y_range = Range1d(0, 15)

fig.xaxis.major_label_orientation = 3.141529/4

# show the results
show(fig)