#!/home/jsignell/miniconda2/bin/python
"""
Create plots for website's weekly dashboard


Julia Signell
2016-01-06
"""

import os
import datetime as dt
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # run this before importing pyplot to allow running remotely
import matplotlib.pyplot as plt
import mpld3 

path = '../../CloudStation/LoggerNet/'
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
    df = pd.read_csv(filename, skiprows=[0,2,3], index_col=0, parse_dates=True)
    f = open(filename, 'r')
    lines = f.readlines()
    f.close()
    UnitsLine = lines[2]
    
    units = UnitsLine.replace('"','').split(',')[1:]
    return df, units

def dashboard():
    fig, axes = plt.subplots(nrows=3, ncols=2, figsize=(8,6), sharex=True)
    plt.subplots_adjust(hspace=.4)
    now = pd.datetime.utcnow()
    weekago = now - pd.DateOffset(days=7)
    for param, ax in zip(params, axes.flat):
        df[weekago:now][param].plot(marker='o', ax=ax)
        ax.set_ylabel(units[df.columns.get_loc(param)], labelpad=10)
        ax.set_xlabel('')
        ax.set_title(param)
    mpld3.save_html(fig, '{o}{p}.html'.format(o=out_path, p='dashboard'))
    
#CR1000 Butler Roof
out_path = './output/butler/'
df, units = read_campbellsci(path, datafile='CR1000_Table1.dat')
params = ['TCroof_Avg', 'RHCroof', 'DnTot_Avg', 'UpTot_Avg', 'Rain_mm_3_Tot', 'WindSpd_ms']
dashboard()
try:
    os.system("cp -f output/butler/dashboard.html ../../web/butler/dataplots/")
except:
    os.system("cp -f output/butler/dashboard.html C:/Users/Julia/Desktop/test_website/dataplots/butler/")
    
#CR5000 ECS
out_path = './output/ecs/'
df, units = read_campbellsci(path, datafile='CR5000_flux.dat')
params = ['co2_mean','h2o_Avg','Rl_downwell_Avg','Rl_upwell_Avg','Rain_1_mm_Tot','Rain_2_mm_Tot']
dashboard()
try:
    os.system("cp -f output/ecs/dashboard.html ../../web/ecs/dataplots/")
except:
    os.system("cp -f output/ecs/dashboard.html C:/Users/Julia/Desktop/test_website/dataplots/")

try:
    os.system("cp -f {i}/logger_status.html ../../web/dataplots/".format(i=path))
except:
    pass
