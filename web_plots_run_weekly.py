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

path = '../../data/'
datafiles=['CR1000_Table1.dat',
           'CR1000_Table2.dat',
           'CR5000_onemin.dat',
           'CR5000_flux.dat',
           'CL06_CR1000_IP_Table1.dat',
           'Wash_Strm_CR200_IP_Table1.dat',
           'Upper WS CR200_Table1.dat'
          ]

def update_file(datafile, year):
	# add new values to this year's file
    df_year = pd.read_csv('../../data/'+site+'{d}_{year}.dat'.format(d=datafile, year=year), 
                          index_col=0, parse_dates=True, low_memory=False, skiprows=[1,2,3])
    df, units, method = read_campbellsci('../../CloudStation/LoggerNet/','{d}.dat'.format(d=datafile))

    if df.index[-1] == df_year.index[-1]:
        return
    df_all = pd.concat((df_year,df[df.index.difference(df_year.index)[0]:]))
    columns = pd.MultiIndex.from_tuples(zip(df_all.columns, units, method))
    df_all.set_axis(1, columns)
    df_all.insert(0, 'TIMESTAMP', df_all.index)
    df_all.to_csv('../../data/{s}{d}_{year}.dat'.format(s=site, d=datafile, year=year), index=False)

def read_campbellsci(path, datafile):
    filename = path + datafile
    df = pd.read_csv(filename, skiprows=[0,2,3], index_col=0, parse_dates=True,
                     na_values=["NAN", "INF", "-INF", 7999, -7999], low_memory=False)
    f = open(filename, 'r')
    lines = f.readlines()
    f.close()
    UnitsLine = lines[2].strip('\r\n')
    MethodLine = lines[3].strip('\r\n')
    
    units = UnitsLine.replace('"','').split(',')[1:]
    method = MethodLine.replace('"','').split(',')[1:]
    return df, units, method

def concat_data(path, datafile):
    df_all = None
    for f in os.listdir(path):
        if datafile in f and f.endswith('.dat'):
            df = pd.read_csv(path+f, header=[0,1,2], index_col=0, parse_dates=True, 
		             low_memory=False)
            df_all = pd.concat((df_all, df))
    df = df_all.resample('1D', how='mean')
    for col in df.columns.levels[0]:
        if col.endswith('Tot') or col.endswith('tot'):
            df[col] = df_all[col].resample('1D', how='sum')
    return df

def plot_param(param):
    fig, ax = plt.subplots(figsize=(8,6))
    df[param].plot(marker='o', ax=ax, legend=None)
    try:
	plt.ylabel(df[param].columns.values[0][0], labelpad=10)
    except:
	pass
    plt.xlabel('')
    plt.title(param + ' (time in UTC)')
    mpld3.save_html(fig, '{o}{p}.html'.format(o=out_path, p=param))
    plt.close(fig)
    
#CR1000 Butler Roof
site = 'butler/'
out_path = './output/butler/'
params = ['TCroof_Avg', 'RHCroof', 'DnTot_Avg', 'UpTot_Avg', 'Rain_mm_3_Tot', 'WindSpd_ms']
update_file(datafile='CR1000_Table1', year='2016')
os.system("cp -f {p}{d}_{year}.dat ../../web/butler/datafiles/".format(p=path+site, d='CR1000_Table1', year='2016'))
df = concat_data(path+site, datafile='CR1000_Table1')
for param in params:
    plot_param(param)
try:
    os.system("cp -f ./output/butler/* ../../web/butler/dataplots/")
except:
    pass
    
#CR5000 ECS
site = 'broadmead/'
out_path = './output/'+site
params = ['Hc', 'LE_wpl','Rl_downwell_Avg','Rl_upwell_Avg','Rs_downwell_Avg','Rs_upwell_Avg',
          'co2_mean','h2o_Avg','wnd_spd','t_hmp_mean','Rain_1_mm_Tot','Rain_2_mm_Tot']
update_file(datafile='CR5000_flux', year='2016')
os.system("cp -f {p}{d}_{year}.dat ../../web/ecs/datafiles/".format(p=path+site, d='CR5000_flux', year='2016'))
df = concat_data(path+site, datafile='CR5000_flux')

for param in params:
    plot_param(param)
try:
    os.system("cp -f output/broadmead/* ../../web/ecs/dataplots/")
except:
    pass

#CR6 ECS
df_all = None
for f in os.listdir('../../CloudStation/LoggerNet/'):
    if 'CR6_SN1698_rain_rate' in f and f.endswith('.csv'):
        df = pd.read_csv('../../CloudStation/LoggerNet/'+f, index_col=0, parse_dates=True)
        df_all = pd.concat((df_all, df))
df = df_all.resample('5min', how='mean', label='right')
plot_param('rain_rate')

try:
    os.system("cp -f output/broadmead/* ../../web/ecs/dataplots/")
except:
    pass


#CR200 Washington
site = 'washington/'
out_path='./output/washington/'
datafiles = ['Upper WS CR200_Table1', 'Wash_Strm_CR200_IP_Table1', 'CL06_CR1000_IP_Table1']
params = [['Upper_Temp_C_Avg', 'Upper_Corrected_cm_Avg'],
          ['Lower_Temp_C_Avg', 'Lower_Corrected_cm_Avg'],
          ['Lvl_cm_Avg', 'AirTC_Avg']]
prefixes = ['Upper_','Lower_','']
for datafile, params, prefix in zip(datafiles, params, prefixes):
    try:
        update_file(datafile, year='2016')
    except:
        pass
    os.system("cp -f '{p}{d}_{year}.dat' ../../web/washington/datafiles/".format(p=path+site, d=datafile, year='2016'))
    df = concat_data(path+site, datafile).add_prefix(prefix)
    for param in params:
        plot_param(param)
    try:
        os.system("cp -f output/washington/* ../../web/washington/dataplots/")
    except:
        pass
