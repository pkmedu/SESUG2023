#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')
df_sas = pd.read_excel(r"C:\SESUG_2023\SAS_Solution_WS_2023-08-12.xlsx")
df_py = pd.read_excel(r"C:\SESUG_2023\Python_Solution_WS_2023-08-12.xlsx")
diff = df_sas.compare(df_py, keep_equal=True, keep_shape = True)
print(diff)



