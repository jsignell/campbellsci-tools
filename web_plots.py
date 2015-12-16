import os
import datetime as dt
import pandas as pd
import numpy as np
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
    
    units = UnitsLine.replace('"','').split(',')
    if len(df)>60*24*3:
        df = df.resample('1H', how='mean')
    return df, units

def select_param(datafile):
    global df
    global units
    df, units = read_campbellsci(path, datafile)

def plot_param(param):
    global df
    global units
    fig, ax = plt.subplots()
    df[param].plot(figsize=(3,2), marker='o', ax=ax)
    plt.xlabel('Time (UTC)')
    plt.ylabel(units[df.columns.get_loc(param)])
    plt.title(param + ' (time in UTC)')
    mpld3.save_html(fig, './output/{p}.html'.format(p=param))

select_param(datafile='CR1000_Table1.dat')
for paramw in ['TCroof_Avg', 'RHCroof', 'DnTot_Avg', 'UpTot_Avg', 'Rain_mm_3600_Tot', 'WindSpd_ms']:
    plot_param(param=paramw)
os.system("cp -f output/* ../../web/butler/dataplots/")