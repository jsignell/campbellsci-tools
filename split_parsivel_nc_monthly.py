#!/home/jsignell/miniconda2/envs/campbellsci-tools/bin/python
import pandas as pd
import numpy as np
import xarray as xr
import numpy as np


last_month = str(pd.Timestamp.now()-np.timedelta64(1, 'M'))[:7]

data_url = '/home/jsignell/erddapData/MonitoringStations/'

dsd_cols = [u'mm062', u'mm187', u'mm312', u'mm437', u'mm562', u'mm687', u'mm812',
       u'mm937', u'mm1062', u'mm1187', u'mm1375', u'mm1625', u'mm1875',
       u'mm2125', u'mm2375', u'mm2750', u'mm3250', u'mm3750', u'mm4250',
       u'mm4750', u'mm5500', u'mm6500', u'mm7500', u'mm8500', u'mm9500',
       u'mm11000', u'mm13000', u'mm15000', u'mm17000', u'mm19000', u'mm21500',
       u'mm24']
vel_cols = ["ms50","ms150","ms250","ms350","ms450","ms550","ms650","ms750",
        "ms850","ms950","ms1100","ms1300","ms1500","ms1700","ms1900",
        "ms2200","ms2600","ms3000","ms3400","ms3800","ms4400","ms5200",
        "ms6000","ms6800","ms7600","ms8800","ms10400","ms12000","ms13600",
        "ms15200","ms17600","ms20800"]

ds_parsivel = xr.open_dataset(data_url+'broadmead_parsivel.nc')
ds_parsivel = ds_parsivel.sel(time=last_month)

ds = xr.open_dataset(data_url+'broadmead_velocity.nc')
ds = ds.sel(time=last_month)

ds_vel = xr.concat([xr.DataArray(ds[n].assign_coords(
                    velocity=int(ds[n].name[2:])/1000))for n in vel_cols], 'velocity')

ds_vel.name = 'drop_velocity_distribution'

ds = xr.open_dataset(data_url+'broadmead_dropsize.nc')
ds = ds.sel(time=last_month)

ds_dsd = xr.concat([xr.DataArray(ds[n].assign_coords(
                diameter=int(ds[n].name[2:])/1000)) for n in dsd_cols], 'diameter')

ds_dsd.name = 'drop_size_distribution'

ds_dsd = ds_dsd.drop('station_name')
ds_vel = ds_vel.drop('station_name')

ds_all = xr.merge([ds_dsd, ds_vel, ds_parsivel], join='inner')
ds_all.attrs.update(ds_parsivel.attrs)

ds_all['wcode_metar_4678'] = ds_all['wcode_metar_4678'].astype(bytes)
ds_all['wcode_nws'] = ds_all['wcode_nws'].astype(bytes)

for var in ds_all.data_vars.keys():
    ds_all[var].encoding.update({'zlib': True})

ds_all.time.encoding.update({'units':'seconds since 1970-01-01', 'calendar':'gregorian', 'dtype': np.double})
ds_all.attrs.update({'featureType': 'timeSeries',
                 'Conventions': 'CF-1.6',
                 'history': 'Created {now}'.format(now= pd.datetime.now())})

ds_all.to_netcdf('{path}/parsivel_{t}.nc'.format(path=data_url+'broadmead_disdrometer',
                                                 t=last_month.replace('-', '_')),
                 format='netCDF4', engine='h5netcdf')
