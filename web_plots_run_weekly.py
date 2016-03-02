#!/home/jsignell/miniconda2/bin/python
"""
Create website's weekly plots and update files for download


Julia Signell
2016-01-25
"""
from csifile import *
import os
import zipfile
import datetime as dt
import pandas as pd
import numpy as np
import xarray as xr
import matplotlib
matplotlib.use('Agg')  # run this before importing pyplot to allow running remotely
import matplotlib.pyplot as plt
import mpld3 

loggernet_path = '../../CloudStation/LoggerNet/'
data_path = '../../data/'
plot_path = './output/'

datafiles=['CR1000_Table1.dat',
           'CR1000_Table2.dat',
           'CR5000_onemin.dat',
           'CR5000_flux.dat',
           'CL06_CR1000_IP_Table1.dat',
           'Wash_Strm_CR200_IP_Table1.dat',
           'Upper WS CR200_Table1.dat'
          ]

def concat_data(path, datafile):
    csi_all = concat(grab(path, datafile))
    df = csi_all.df.resample('1D', how='mean')
    for col in df.columns:
        if col.endswith('Tot') or col.endswith('tot'):
            df[col] = csi_all.df[col].resample('1D', how='sum')
    return df, csi_all.units

def plot_param(df, path, param, units):
    fig, ax = plt.subplots(figsize=(8,6))
    df[param].plot(marker='o', ax=ax, legend=None)
    try:
        plt.ylabel(units[df.columns.get_loc(param)], labelpad=10)
    except:
        pass
    plt.xlabel('')
    plt.title(param + ' (time in UTC)')
    mpld3.save_html(fig, '{o}{p}.html'.format(o=path, p=param))
    plt.close(fig)

def zipdir(ziph, year):
    # ziph is zipfile handle
    for f in os.listdir('./'):
        if os.path.isfile(f):
            if str(year) in f and 'zip' not in f:
                ziph.write(os.path.join(f))

def update_and_plot(site, d, params, y=2016):
    update(loggernet_path, d, data_path+site)
    df, units = concat_data(data_path+site, d)
    cwd = os.getcwd()
    os.chdir(data_path+site)
    zipf = zipfile.ZipFile('{s}_{y}.zip'.format(s=site[0:-1], y=y), 'w', zipfile.ZIP_DEFLATED)
    zipdir(zipf, y)
    zipf.close()
    os.chdir(cwd)
    for param in params:
        plot_param(df, plot_path+site, param, units)
    try:
        os.system("cp -f {o}{s}* ../../web/{s}dataplots/".format(o=plot_path, s=site))
        os.system("cp -f {p}{s}*_{y}.zip ../../web/{s}datafiles/".format(p=data_path, s=site, d=d, y=2016))
    except:
        pass

def generate_nc(site):
    csi_all = concat(grab(site.data_path, site.datafiles[0]))
    csi_all.df.columns = [col.replace('(','_').replace(')','') for col in csi_all.df.columns]
    units = dict(zip(csi_all.df.columns, csi_all.units))
    method = dict(zip(csi_all.df.columns, csi_all.method))
    csi_all.df.index.name = 'time'
    csi_all.df.insert(0, 'time', csi_all.df.index)
    csi_all.df = csi_all.df.drop_duplicates(subset=['time']).drop('time', axis=1)
    ds = xr.Dataset.from_dataframe(csi_all.df)
    for var in ds.data_vars.keys():
        ds[var].attrs.update({'units': units.get(var), 'method': method.get(var)})
        if ds[var].dtype == 'int64':
            ds[var].encoding.update({'dtype': np.double})
        if site.name !='butler':
            ds[var].encoding.update({'chunksizes':(1000,),'zlib': True})
    if site.name == 'broadmead':
        s = ds.albedo_Avg.to_dataframe()
        s.albedo_Avg.replace(' ', np.nan, inplace=True)
        s.albedo_Avg = s.albedo_Avg.astype('float')
        da = xr.DataArray.from_series(s.albedo_Avg)
        ds.albedo_Avg.values = da.values

        s = ds.Tsoil_avg_2.to_dataframe()
        s.Tsoil_avg_2.replace(' ', np.nan, inplace=True)
        s.Tsoil_avg_2 = s.Tsoil_avg_2.astype('float')
        da = xr.DataArray.from_series(s.Tsoil_avg_2)
        ds.Tsoil_avg_2.values = da.values

        s = ds.del_Tsoil_1.to_dataframe()
        s.del_Tsoil_1.replace(' ', np.nan, inplace=True)
        s.del_Tsoil_1 = s.del_Tsoil_1.astype('float')
        da = xr.DataArray.from_series(s.del_Tsoil_1)
        ds.del_Tsoil_1.values = da.values

        s = ds.del_Tsoil_2.to_dataframe()
        s.del_Tsoil_2.replace(' ', np.nan, inplace=True)
        s.del_Tsoil_2 = s.del_Tsoil_2.astype('float')
        da = xr.DataArray.from_series(s.del_Tsoil_2)
        ds.del_Tsoil_2.values = da.values

    ds = ds.assign_coords(station_name=site.name)
    ds.station_name.attrs.update({'long_name': 'station name',
                            'cf_role': 'timeseries_id',
                            'strlen': '6'})
    ds = ds.assign_coords(lat=site.lat)
    ds.lat.attrs.update({'units': 'degrees_north',
                         'long_name': 'station latitude',
                         'standard_name': 'latitude'})
    ds = ds.assign_coords(lon=site.lon)
    ds.lon.attrs.update({'units': 'degrees_east',
                         'long_name': 'station longitude',
                         'standard_name': 'longitude'})
    ds.time.encoding.update({'units':'seconds since 1970-01-01', 'calendar':'gregorian', 'dtype': np.double})
    ds.attrs.update({'featureType': 'timeSeries',
                     'Conventions': 'CF-1.6',
                     'description': site.long_name,
                     'history': 'Created {now}'.format(now= pd.datetime.now())})
    ds.to_netcdf('{path}{f}.nc'.format(path=site.data_path, f=site.name), format='netCDF4', engine='h5netcdf')
    try:
        os.system("cp {path}{f}.nc ~/erddapData/MonitoringStations/".format(path=site.data_path, f=site.name))
        print("Finished generating nc file for {f}".format(f=site.name))
    except:
        print("Copy did not work for {f}".format(f=site.name))

#CR1000 Butler Roof
site = 'butler/'
d = 'CR1000_Table1'
params = ['TCroof_Avg', 'RHCroof', 'DnTot_Avg', 'UpTot_Avg', 'Rain_mm_3_Tot', 'WindSpd_ms']
update_and_plot(site, d, params)

#CR5000 ECS
site = 'broadmead/'
d = 'CR5000_flux'
params = ['Hc', 'LE_wpl','Rl_downwell_Avg','Rl_upwell_Avg','Rs_downwell_Avg','Rs_upwell_Avg',
          'co2_mean','h2o_Avg','wnd_spd','t_hmp_mean','Rain_1_mm_Tot','Rain_2_mm_Tot']
update_and_plot(site, d, params)

#CR200 Washington
y=2016
site = 'washington/'
datafiles = ['Upper WS CR200_Table1', 'Wash_Strm_CR200_IP_Table1', 'CL06_CR1000_IP_Table1']
params_list = [['Upper_Temp_C_Avg', 'Upper_Corrected_cm_Avg'],
          ['Lower_Temp_C_Avg', 'Lower_Corrected_cm_Avg'],
          ['Lvl_cm_Avg', 'AirTC_Avg']]
prefixes = ['Upper_','Lower_','']
for d, params, prefix in zip(datafiles, params_list, prefixes):
    try:
        update(loggernet_path, d, data_path+site)
        zipf = zipfile.ZipFile(data_path+site+'{s}_{y}.zip'.format(s=site[0:-1], y=y), 'w', zipfile.ZIP_DEFLATED)
        zipdir(data_path+site, zipf, y)
        zipf.close()
    except:
        pass
    df, units = concat_data(data_path+site, d)
    df = df.add_prefix(prefix)
    for param in params:
        plot_param(df, plot_path+site, param, units)
    try:
        os.system("cp -f {o}{s}* ../../web/{s}dataplots/".format(o=plot_path, s=site))
        os.system("cp -f {p}{s}*_{y}.zip ../../web/{s}datafiles/".format(p=data_path, s=site, d=d, y=y))
    except:
        pass

    import os

# generate netcdf files
path = '../../data/'
sites= {'broadmead': {'data_path': path+'broadmead/',
                      'datafiles': ['CR5000_flux', 'CR5000_onemin'],
                      'lat': 40.34637, 
                      'lon':-74.64347,
                      'long_name': 'Broadmead Eddy Covariance Station'},
        'butler': {'data_path': path+'butler/',
                   'datafiles': ['CR1000_Table1', 'CR1000_Table2'],
                   'lat': 40.34421,
                   'lon':-74.65586,
                   'long_name': 'Butler Green Roof Station'},
        'washington_up': {'data_path': path+'washington/',
                          'datafiles': ['Upper WS CR200_Table1'],
                          'lat': 40.3426,
                          'lon':-74.6495,
                          'long_name': 'Washington Upstream Station'},
        'washington_down': {'data_path': path+'washington/',
                            'datafiles': ['Wash_Strm_CR200_IP_Table1'],
                            'lat': 40.34202, 
                            'lon':-74.64883,
                            'long_name': 'Washington Downstream Station'},
        'washington_lake': {'data_path': path+'washington/',
                           'datafiles': ['CL06_CR1000_IP_Table1'],
                           'lat': 40.34193,
                           'lon':-74.64795,
                           'long_name': 'Washington Stream Met Station'},        
       }

sites_df = pd.DataFrame(sites)

for col in sites_df.columns:
    generate_nc(sites_df[col])
