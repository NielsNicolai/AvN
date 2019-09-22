#!/usr/bin/env python
# coding: utf-8

"""
AVN DATA COLLECTION AND PLOTTING TOOL
-------------------------------------

Created on Fri Sept 20 11:45:40 2019
@author: Niels Nicolaï; Jean-David Therrien

WITH THIS NOTEBOOK, ONE MAY:
* Extract data from a matlab file and convert it into a pandas DataFrame
* Query data from the datEAUbase that are relevant to the AvN project
* Collect data from the AvN controller file
* Generate plots describing the AvN controller performance over the span of the collected data

DEPENDENCIES:
To extract data from the dateaubase, the file Dateaubase.py must be present on the user's computer and the path to it must be known.
 A VPN connection to the datEAUbase server is also required.

THE FOLLOWING THIRD-PARTY PYTHON MODULES ARE ALSO NEEDED:
* numpy
* pandas
* plotly
* plotly-orca
* scipy

Copyright (c) 2019 modelEAU, Université Laval. All Rights Reserved.
"""

import pandas as pd
import numpy as np

import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
pio.templates.default = 'plotly_white' #Set the default plot style for plotly
pio.renderers.default = "browser" #Set the default renderer (jupyter or browser)

import datetime
import scipy.io
import sys

#import functions to obtain data
datEAUbase_path = '../datEAU_win/datEAU_filtering'
sys.path.append(datEAUbase_path)
from connect_datEAUbase import *
from load_datEAUbase import *
from load_ANAPRO  import *
from load_control_files import *

#Define the period to be visualised
start_date = "25 August 2019"
end_date = "6 September 2019"

# Extract data from the control files, specify file names manually
files = ['data/DO00.csv','data/DO0.csv','data/DO1.csv', 'data/DO2.csv', 'data/DO3.csv']
ctrl_df = get_ctrl_data(files)
ctrl_df.tail()

# Extract data from the datEAUbase
#Direct connection to detEAUbase
df_db = extract_AvN_from_db(start_date, end_date)
# Save the data to a csv file for later reuse
# df_db.to_csv('dateaubase_data.csv')

# Load the data back from a .csv:
#df_db = pd.read_csv('data/dateaubase_data.csv', index_col='datetime')
#df_db.index = df_db.index.astype('datetime64[ns]')

# Bring the data sources together
df = df_db.join(ctrl_df, how='outer') # Join control files
# df = df.join(df_mat, how='outer') # Join Matlab data

df_lab = pd.read_csv('data/labData.csv', index_col='datetime')
df = df.join(df_lab, how='outer')

# Calculate the NH4-N to NH3-N ratio for the Pilote and Copilote
df['Pilote ratio'] = df['Pilote effluent NH4-N']/df['Pilote effluent NO3-N']
df['Copilote ratio'] = df['Copilote effluent NH4-N']/df['Copilote effluent NO3-N']

# Change the value of influent NH4 to get the right units
df['Primary settling tank effluent NH4-N'] /=1000
df = df.round(2)


# Visualize data
# Use markers instead of line. Lines won't work because of all the NAN's created by the different time stamps.

reactor = 'Copilote'
fig = make_subplots(
    rows=4,
    cols=1,
    shared_xaxes=True,
    row_heights=[0.2, 0.4, 0.2, 0.2],
    vertical_spacing=0.1,
    subplot_titles=(
        'Influent',
        'Effluent',
        'AvN ratio',
        'Aeration',
    ),
)

# Subplot 1 - Influent 
fig.add_trace(
    go.Scattergl(
        x=df.index,
        y=df['Primary settling tank effluent NH4-N'],
        name = 'Influent NH4-N',
        mode='markers',
        legendgroup='leg1',
        marker=dict(
            color='rgb(153, 0, 0)',
            size=3,
        )
    ),
    row=1, col=1
)
fig.add_trace(
    go.Scattergl(
        x=df.index,
        y=df['Lab Primary settling tank effluent NH4-N'],
        name = 'Lab influent NH4-N',
        mode='markers',
        legendgroup='leg1',
        marker=dict(
            color='rgb(102, 0, 0)',
            size=8,
            symbol='star-dot',
            line=dict(
                    width=1,
                    color='rgb(0,0,0)',
            )
        )
    ),
    row=1, col=1
)

# Subplot 2 - Effluent
fig.add_trace(
    go.Scattergl(
        x=df.index,
        y=df[reactor+' effluent NH4-N'],
        name = 'Effluent NH4-N',
        mode='markers',
        legendgroup='leg2',
        marker=dict(
            color='rgb(255, 0, 0)',
            size=3,
        )
    ),
    row=2, col=1
)
fig.add_trace(
    go.Scattergl(
        x=df.index,
        y=df['Lab '+reactor+' effluent NH4-N'],
        name = 'Lab effluent NH4-N',
        mode='markers',
        legendgroup='leg2',
        marker=dict(
            color='rgb(255, 0, 0)',
            size=8,
            symbol='star-dot',
            line=dict(
                    width=1,
                    color='rgb(0,0,0)',
            )
        )
    ),
    row=2, col=1
)
fig.add_trace(
    go.Scattergl(
        x=df.index,
        y=df[reactor+' effluent NO3-N'],
        name = 'Effluent NO3-N',
        mode='markers',
        legendgroup='leg2',
        marker=dict(
            color='rgb(46, 184, 80)',
            size=3,
        )
    ),
    row=2, col=1
)
fig.add_trace(
    go.Scattergl(
        x=df.index,
        y=df['Lab '+reactor+' effluent NO3-N'],
        name = 'Lab effluent NO3-N',
        mode='markers',
        legendgroup='leg2',
        marker=dict(
            color='rgb(46, 184, 80)',
            size=8,
            symbol='star-dot',
            line=dict(
                    width=1,
                    color='rgb(0,0,0)',
            )
        )
    ),
    row=2, col=1
)

# Subplot 3 - AvN ratio
fig.add_trace(
    go.Scattergl(
        x=df.index,
        y=[1]*len(df.index),
        name = 'AvN setpoint',
        mode='lines',
        legendgroup='leg3',
        line=dict(
            color='rgb(0, 0, 0)',
            width=2,
            dash="dash",
            
        )
    ),
    row=3, col=1
)
fig.add_trace(
    go.Scattergl(
        x=df.index,
        y=df[reactor+' ratio'],
        name = 'Ratio NH4-N/NO3-N',
        mode='markers',
        legendgroup='leg3',
        marker=dict(
            color='rgb(51, 102, 255)',
            size=3,
        )
    ),
    row=3, col=1
)

# Subplot 4 - Aeration
fig.add_trace(
    go.Scattergl(
        x=df.index,
        y=df['DOsp_1'],
        name = 'DO setpoint',
        mode='lines+markers',
        legendgroup='leg4',
        connectgaps=True,
        marker=dict(
            color='rgb(204, 51, 0)',
            size=3,
        ),
        line=dict(
            shape='hv'
        )
    ),
    row=4, col=1
)
fig.add_trace(
    go.Scattergl(
        x=df.index,
        y=df[reactor+' reactor 4 DO'],
        name = 'DO tank 5',
        mode='markers',
        legendgroup='leg4',
        opacity=0.3,
        marker=dict(
            color='rgb(255, 153, 0)',
            size=3,
        )
    ),
    row=4, col=1
)

# Layout figure
showgrid=True
gridcolor = 'rgb(204, 204, 204)'
gridwidth=1

showline=True
linecolor='rgb(153, 153, 153)'
linewidth=2

fig.update_xaxes(
    showgrid=showgrid,
    gridwidth=gridwidth,
    gridcolor=gridcolor,
    showline=showline,
    linewidth=linewidth,
    linecolor=linecolor,
)
fig.update_yaxes(
    showgrid=showgrid,
    gridwidth=gridwidth,
    gridcolor=gridcolor,
    showline=showline,
    linewidth=linewidth,
    linecolor=linecolor,
)

fig.update_layout(
	# Change dimensions according to desired screen resolution
    #height=1030,
    #width=1660,
    height=740,
    width=1340,
    title_text="AvN performance: <b>"+reactor,
    legend_orientation="h",
    font=dict(size=10),
)

# Add the modelEAU logo
fig.layout.images = [dict(
        source="https://pbs.twimg.com/profile_images/723538279644147712/JnZh9k7P.jpg",
        xref="paper", yref="paper",
        x=0.9, y=-0.2,
        sizex=0.175, sizey=0.175,
        xanchor="left", yanchor="bottom"
      )]

# Sbplot specific layouts
fig.update_yaxes(title_text="[mg/L]", title_font=dict(size=10), range=[10.0, 51.0], row=1, col=1)
fig.update_yaxes(title_text="[mg/L]", title_font=dict(size=10), row=2, col=1)
fig.update_yaxes(title_text="[-]", title_font=dict(size=10), row=3, col=1)
fig.update_yaxes(title_text="[mg/L]", title_font=dict(size=10), range=[0.0, 0.52], nticks=6, row=4, col=1)

# Add annotations to keep track of events
'''
fig.update_layout(
    annotations=[
        go.layout.Annotation(
            x="2019-09-03 10:30:00",
            y=40,
            xref="x1",↨
            yref="y1",
            text="Cleaning<br>NN<br>18.19%",
            showarrow=False,
            arrowhead=0,
            arrowcolor="rgb(153, 153, 153)",
            ax=0,
            ay=10,
            font = dict(size=9,color="rgb(153, 153, 153)"),
        )
    ],
)
'''

# Save figure to HTML file
#pio.write_html(fig, file='AvNdata_Meeting190918_small.html', auto_open=True)

#Show figure in default renderer
fig.show()




