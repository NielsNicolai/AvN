# -*- coding: utf-8 -*-
"""
Created on Wed Aug 14 14:34:58 2019

@author: NINIC2
"""

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
ending = 6*24*60 #minutes

startDateTime = datetime.datetime.now() - datetime.timedelta(hours=0, minutes=begining, seconds=0)
stopDateTime = datetime.datetime.now() - datetime.timedelta(hours=0, minutes=ending, seconds=0)

Start = date_to_epoch(startDateTime.strftime("%Y-%m-%d %H:%M:%S"))
End = date_to_epoch(stopDateTime.strftime("%Y-%m-%d %H:%M:%S"))

#Define the requested parameters
Project = 'pilEAUte'
Location = ['Copilote reactor 4']
param_list = ['DO']
equip_list = ['AIT-341']

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

df['avg DO'] = df['DO'].rolling(10, min_periods=1).mean()

#Replace all zero values for NaNs
df = df.replace(0.0, np.nan)

# output to static HTML file
output_file("AvN_oxygen.html", title="DO copilote")

# create a new plot with a title and axis labels
fig = figure(title="AvN controller performance", x_axis_label='', y_axis_label='Concentrations [mg/L]', plot_width=1600, plot_height=300)

fig.line(df.index, df['DO'], legend="raw DO tank 5", line_width=2, line_color='#ffff66')
fig.line(df.index, df['avg DO'], legend="avg DO tank 5", line_width=2, line_color="orange")

fig.xaxis.formatter=DatetimeTickFormatter(
    days=["%m/%d"],
    hours=["%m/%d - %H:%M"],
    minutes=["%m/%d - %H:%M"]
)

fig.legend.location = 'top_left'

fig.y_range = Range1d(0, 0.5)

fig.xaxis.major_label_orientation = 3.141529/4

# show the results
show(fig)