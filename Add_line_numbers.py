# -*- coding: utf-8 -*-
"""
Created on Sat Feb 25 00:01:11 2023

@author: Pradip.Muhuri
"""
with open(r"c:\Python\Web_Scraping\Python_Solution_WS.py", 'r') as program:
    data = program.readlines()

with open(r"c:\SESUG_2023\Python_Solution_WS_LN.py", 'w') as program:
    for (number, line) in enumerate(data):
        program.write('%d  %s' % (number + 1, line))