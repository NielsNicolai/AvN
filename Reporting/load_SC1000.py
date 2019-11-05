# -*- coding: utf-8 -*-
"""
Created on Tue Nov  5 09:57:31 2019

DESCRIPTION: THE FOLLOWING DEFINITION CAN BE USED TO READ A DATA FILE GENERATED BY THE SC1000 INSTRUMENT
IT WILL AUTOMATICALLY SET THE DATATIME IN THE CORRECT FORMAT

Copyright (c) 2019 by Niels Nicolaï, nicolai.niels@gmail.com, modelEAU, Université Laval. All Rights Reserved.

@author: NINIC2
"""

import pandas as pd
import datetime

def get_SC1000_data(files):
    SC1000_df = None
    for file in files:
        temp_df = pd.read_csv(file)
        temp_df['datetime'] = temp_df.apply(lambda row: datetime.datetime.strptime(row['datetime'],"%Y/%m/%d %H:%M:%S"),axis=1)
        temp_df.set_index('datetime', inplace=True)        
        if SC1000_df is None:
            SC1000_df = temp_df
        else:
            SC1000_df = SC1000_df.join(temp_df, how='outer')
    return SC1000_df