# -*- coding: utf-8 -*-
"""
Created on Wed Jun  7 15:51:09 2023

@author: Pradip.Muhuri
"""

import pandas as pd
df_py = pd.read_excel(f"C:\Python\Web_Scraping\output\MEPS_zip_links_2023-06-06.xlsx")
df_sas = pd.read_excel(f"C:\SESUG_2023\SAS_MEPS_zip_links_2023-06-07.xlsx")
diff = df_sas.compare(df_py, keep_equal=True, keep_shape = True)
print(diff)