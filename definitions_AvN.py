# -*- coding: utf-8 -*-
"""
Created on Wed Aug 28 14:22:01 2019

@author: NINIC2
"""

def readValuesInit(file):
    import re
    
    infile = open(file, 'r')
    lines = infile.readlines()
    
    for line in lines:
        exec(line)
    
    del infile, lines, line

         
    globals().update(locals())

#file = "values_init_DOsp_AvN.txt"
#readValuesInit(file)