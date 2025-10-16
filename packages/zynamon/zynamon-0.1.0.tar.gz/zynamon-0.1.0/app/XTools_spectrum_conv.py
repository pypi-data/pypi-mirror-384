# -*- coding: utf-8 -*-
"""
Created on Thu Jan 19 15:49:52 2023
@author: z00176rb
"""

import re
import csv

from zdev.plot import qplot, qplotly
#from zynamon.tscore import convert_time
from zynamon.xutils import x_read_spectrum, x_write_spectrum, x_ROUTINE



#%% manual
#-----------------------------------------------------------------------------------------------

# FILE = r"C:\z\CBM_data\z\spec\OSG04 GBX AC1 SpmAcc 2023-01-19 15-15-32.360.947.000.csv"
# # FILE = r"C:\z\CBM_data\z\spec\01 GBX AC1 SpmOrdAcc 2023-01-19 15-06-40.190.312.000.csv"
# SPREAD = 0.1

# read spectrum
spectrum, orig_header = x_read_spectrum(FILE)

# modify & save file
time_span_iso = x_write_spectrum(FILE[:-4]+'_mod.csv', spectrum, orig_header, spread=SPREAD)

# show covered time span
print(f"first ~ {time_span_iso[0]}")
print(f"last  ~ {time_span_iso[1]}")  

# show spectrum
fh = qplotly(spectrum['magnitude'], spectrum['freq'])
# qplot(spectrum['phase'], spectrum['freq'], fig=fh, newplot=True)


#%% auto
#-----------------------------------------------------------------------------------------------

ROOT = r'C:/z/CBM_data/z/Spec/auto/'
# ROOT = r'C:\z\CBM_data\z\Spec\auto\'
# ROOT = r'D:\\Location\\CMS Tennet Offline CSV'

PATTERN = '.* Spm.*\.csv'
# PATTERN = '.* SpmOrdAcc.*\.csv'

print("="*96)
print("RUNNING ROUTINE")
print("="*96)

x_batch_conv_spec(ROOT, PATTERN, target_dir=None, backup_dir=None, 
                  backup=True, verbose=True)

print("="*96)
print("="*96)
print("DONE")


#-----------------------------------------------------------------------------------------------


