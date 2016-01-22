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
    df = pd.read_csv(filename, skiprows=[0,2,3], index_col=0, parse_dates=True, 
		     na_values=["NAN", "INF", "-INF", 7999, -7999])
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
	# also make the individual plots
	figw, axw = plt.subplots(figsize=(8,6))
	df[weekago:now][param].plot(marker='o', ax=axw, legend=None)
	axw.set_ylabel(units[df.columns.get_loc(param)], labelpad=10)
	axw.set_xlabel('')
	axw.set_title(param + ' (time in UTC)')
	mpld3.save_html(figw, '{o}{p}_week.html'.format(o=out_path, p=param))
	plt.close(figw)
    mpld3.save_html(fig, '{o}{p}.html'.format(o=out_path, p='dashboard'))

# Logger status
try:
    os.system("cp -f {i}/logger_status.html ../../web/dataplots/".format(i=path))
except:
    pass
    
#CR1000 Butler Roof
out_path = './output/butler/'
df, units = read_campbellsci(path, datafile='CR1000_Table1.dat')
params = ['TCroof_Avg', 'RHCroof', 'DnTot_Avg', 'UpTot_Avg', 'Rain_mm_3_Tot', 'WindSpd_ms']
dashboard()
try:
    os.system("cp -f output/butler/* ../../web/butler/dataplots/")
except:
    pass
    
#CR5000 ECS
out_path = './output/broadmead/'
df, units = read_campbellsci(path, datafile='CR5000_flux.dat')
params = ['Hc', 'LE_wpl',
	  'Rl_downwell_Avg','Rl_upwell_Avg',
          'Rs_downwell_Avg','Rs_upwell_Avg']
dashboard()
try:
    os.system("cp -f output/broadmead/dashboard.html output/broadmead/rad_dashboard.html")
except:
    pass
params = ['co2_mean', 'h2o_Avg',
	  'wnd_spd','t_hmp_mean',
          'Rain_1_mm_Tot', 'Rain_2_mm_Tot']
dashboard()
try:
    os.system("cp -f output/broadmead/dashboard.html output/broadmead/met_dashboard.html")
    os.system("cp -f output/broadmead/* ../../web/ecs/dataplots/")
except:
    pass

#CR200 Washington
out_path='./output/washington/'
df, units = read_campbellsci(path, datafile='Upper WS CR200_Table1.dat')
df = df.resample('15min', how='mean').add_prefix('Upper_')
params = ['Upper_Temp_C_Avg', 'Upper_Corrected_cm_Avg']
dashboard()
df, units = read_campbellsci(path, datafile='Wash_Strm_CR200_IP_Table1.dat')
df = df.add_prefix('Lower_')
params = ['Lower_Temp_C_Avg', 'Lower_Corrected_cm_Avg']
dashboard()
df, units = read_campbellsci(path, datafile='CL06_CR1000_IP_Table1.dat')
params = ['Lvl_cm_Avg', 'AirTC_Avg']
dashboard()
try:
    os.system("cp -f output/washington/* ../../web/washington/dataplots/")
except:
    pass
