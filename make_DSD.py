#!/home/jsignell/miniconda2/bin/python
"""
Generate storm DSD plots


Julia Signell
2016-06-28
"""
import os
from csifile import *
import datetime as dt
import pandas as pd
import numpy as np
import xarray as xr
import matplotlib
matplotlib.use('Agg')  # run this before importing pyplot to allow running remotely
import matplotlib.pyplot as plt
import mpld3 

data_path = '../../data/broadmead/'
plot_path = './output/broadmead/DSD/'

# generate DSDs for any recent storms
cols = [u'mm062', u'mm187', u'mm312', u'mm437', u'mm562', u'mm687', u'mm812',
       u'mm937', u'mm1062', u'mm1187', u'mm1375', u'mm1625', u'mm1875',
       u'mm2125', u'mm2375', u'mm2750', u'mm3250', u'mm3750', u'mm4250',
       u'mm4750', u'mm5500', u'mm6500', u'mm7500', u'mm8500', u'mm9500',
       u'mm11000', u'mm13000', u'mm15000', u'mm17000', u'mm19000', u'mm21500',
       u'mm24']
grid = [(0,0.1245),(0.1245,0.2495),(0.2495,0.3745),(0.3745,0.4995),(0.4995,0.6245),(0.6245,0.7495),
        (0.7495,0.8745),(0.8745,0.9995),(0.9995,1.1245),(1.1245,1.25),(1.25,1.50),(1.50,1.75),
        (1.75,2.00),(2.00,2.25),(2.25,2.50),(2.50,3.00),(3.00,3.50),(3.50,4.00),(4.00,4.50),
        (4.50,5.00),(5.00,6.00),(6.00,7.00),(7.00,8.00),(8.00,9.00),(9.00,10.0),(10.0,12.0),
        (12.0,14.0),(14.0,16.0),(16.0,18.0),(18.0,20.0),(20.0,23.0),(23.0,26.0)]
grid = np.array(grid)
d = dict(zip(cols, grid.mean(axis=1)))

cmap = matplotlib.cm.get_cmap('Blues', 10)
cmap.set_under('None')

trange = pd.date_range(pd.datetime.now()-pd.DateOffset(days=30), pd.datetime.now()+pd.DateOffset(days=30), freq='1m')
ym = zip(trange.year, trange.month)

parsivel = concat([CSIFile(data_path+'CR6_SN1698_parsivel_{y}_{m:02d}.dat'.format(y=n[0], m=n[1])) for n in ym])
csi = concat([CSIFile(data_path+'CR5000_flux_{y}_{m:02d}.dat'.format(y=n[0], m=n[1])) for n in ym])
df = parsivel.df.resample('5min', label='right').mean()
#drop the first time after the parsivel has been off
tr = df[(df.rain_intensity.isnull())].index
df.loc[tr+pd.Timedelta(minutes=5)].dropna(inplace=True)
df = df[['rain_intensity']].join([csi.df[['Rain_1_mm_Tot','Rain_2_mm_Tot']]*12])
df.columns = ['Disdrometer', 'Rain gage 1', 'Rain gage 2']
rate = df.mean(axis=1)

thresh=2
dry_interval=6
wet_times = rate[rate>=thresh].index
time_until_wet = pd.TimedeltaIndex(np.diff(wet_times))

# there have to be at least dry_interval dry hours between storms
ends = rate[rate>=thresh][0:-1][time_until_wet>=(pd.Timedelta(hours=dry_interval))]
starts = rate[rate>=thresh][1:][time_until_wet>=(pd.Timedelta(hours=dry_interval))]

starts = starts[0:-1]
ends = ends[1:]

ti = [(starts.index[n]-pd.Timedelta(minutes=30), ends.index[n]+pd.Timedelta(minutes=30)) for 
      n in range(starts.shape[0]) if 
      ends.index[n] - starts.index[n] > pd.Timedelta(hours=1)]

ds = xr.open_dataset(data_path+'broadmead_dropsize.nc')
ds0 = xr.concat([xr.DataArray(ds[n].assign_coords(diameter=d[n]))for n in cols], 'diameter')

ds0.name = '10**x normalized drop count per diameter class'

for i in range(len(ti)):
    fig, ax = plt.subplots(figsize=(12,6))
    ds1 = ds0.sel(time=slice(ti[i][0], ti[i][1]))
    if ds1.shape[1] ==0:
        plt.close(fig)
        continue
    ds1.plot(cmap=cmap, vmin=0)
    plt.ylim(.25, 5)
    plt.ylabel('Drop diameter (mm)')
    plt.title('{t} Drop Size Distribution (time in UTC)'.format(t=ti[i][0].date()))

    ax2 = ax.twinx()
    ax2.patch.set_alpha(0.0)
    ax2.plot(parsivel.df.rain_intensity.loc[ti[i][0]:ti[i][1]], 'k')
    ax2.set_ylabel('rain_intensity (mm/hr)')
    mpld3.save_html(fig, '{o}{t}.html'.format(o=plot_path, t=ti[i][0].date()))
    if i == len(ti)-1:
        mpld3.save_html(fig, '{o}recent.html'.format(o=plot_path))
    plt.close(fig)

try:
    os.system("cp -f {o}* ../../web/{s}dataplots/DSD/".format(o=plot_path, s='broadmead/'))
except:
    pass
