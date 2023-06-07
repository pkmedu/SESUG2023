# -*- coding: utf-8 -*-
"""
Created on Sat Feb 25 00:01:11 2023

@author: Pradip.Muhuri
"""

with open(r"c:\SESUG_2023\SESUG_rev_06052023.sas", 'r') as program:
    data = program.readlines()

with open(r"c:\SESUG_2023\SESUG_rev_06052023_LN.py", 'w') as program:
    for (number, line) in enumerate(data):
        program.write('%d  %s' % (number + 1, line))