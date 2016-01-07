#!/minconda/bin/python
"""
Create plots for website's weekly dashboard


Julia Signell
2016-01-06
"""

import os
import datetime as dt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mpld3 

path = 'C:/Users/Julia/work/LoggerNet/'
datafiles=['CR1000_Table1.dat',
           'CR1000_Table2.dat',
           'CR5000_onemin.dat',
           'CR5000_flux.dat',
           'CL06_CR1000_IP_Table1.dat',
           'Wash_Strm_CR200_IP_Table1.dat',
           'Upper WS CR200_Table1.dat'
          ]

def read_campbellsci(path, datafile):
    filename = path + datafile
    df = pd.read_csv(filename, skiprows=[0,2,3], index_col=0, parse_dates=True, low_memory=False)
    f = open(filename, 'r')
    lines = f.readlines()
    f.close()
    UnitsLine = lines[2]
    units = UnitsLine.replace('"','').split(',')[1:]
    return df, units

def concat_data(path, datafile):
    df_all = None
    for f in os.listdir(path):
        if datafile in f and f.endswith('.dat'):
            df, units = read_campbellsci(path, datafile=f)
            df_all = pd.concat((df_all, df))
    df = df_all.resample('1D', how='mean')
    for col in df.columns:
        if col.endswith('Tot') or col.endswith('tot'):
            df[col] = df_all[col].resample('1D', how='sum')
    return df, units

def plot_param(param):
    fig, ax = plt.subplots(figsize=(8,6))
    df[param].plot(marker='o', ax=ax)
    plt.ylabel(units[df.columns.get_loc(param)])
    plt.xlabel('')
    plt.title(param + ' (time in UTC)')
    mpld3.save_html(fig, '{o}{p}.html'.format(o=out_path, p=param))
    
#CR1000 Butler Roof
out_path = './output/butler/'
params = ['TCroof_Avg', 'RHCroof', 'DnTot_Avg', 'UpTot_Avg', 'Rain_mm_3_Tot', 'WindSpd_ms']
df, units = concat_data(path, datafile='CR1000_Table1')
for param in params:
    plot_param(param)
try:
    os.system("cp -f output/butler/* Z:/butler/dataplots/")
except:
    os.system("cp -f output/butler/* C:/Users/Julia/Desktop/test_website/dataplots/butler/")
    
#CR5000 ECS
out_path = './output/ecs/'
df, units = concat_data(path, datafile='CR5000_flux')
params = ['co2_mean','h2o_Avg','Rl_downwell_Avg','Rl_upwell_Avg','Rain_1_mm_Tot','Rain_2_mm_Tot']
for param in params:
    plot_param(param)
try:
    os.system("cp -f output/ecs/* Z:/ecs/dataplots/")
except:
    os.system("cp -f output/ecs/* C:/Users/Julia/Desktop/test_website/dataplots/")

try:
    os.system("cp -f {i}/logger_status.html Z:/dataplots/".format(i=path))
except:
    pass
