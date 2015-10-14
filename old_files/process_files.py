'''
Process datafiles from input_dicts and write daily netcdf files.

Julia Signell
2015-05-07
'''

from __init__ import *
import TOA5_to_netcdf as t2n
from parse_campbellsci import parse_program


def try_run(i, DFList, input_dict, nc_path, **kwargs):
    if not os.path.exists(nc_path):
        return True
    if input_dict['datafile'] is 'soil':
        return True
    # only rerun files processed more than 12 hours ago
    old_file = os.path.getmtime(nc_path) < time.time()-60*60*12
    if kwargs['rerun'] and old_file is True:
        return True
    if i in (0, len(DFList)-1) and old_file is False:
        return True
    return False


def merge_partial(ds, nc_path, merge_old=False, **kwargs):
    '''If a file already exists, try to knit the files together.'''
    old_file = os.path.getmtime(nc_path) < time.time()-60*60*24*7
    if merge_old is False and old_file is True:
        print 'old dataset was run more than a week ago..'
        if kwargs['rerun'] is False:
            return None
        else:
            print 'overwriting old dataset'
            return ds
    ds_old = xray.open_dataset(nc_path)
    if ds.broadcast_equals(ds_old):
        print 'datasets contains the same data'
        return None
    p_no_match = ds.attrs['program'] != ds_old.attrs['program']
    l_no_match = ds.attrs['logger'] != ds_old.attrs['logger']
    if l_no_match or p_no_match:
        print 'datasets don\'t have matching metadata'
        return None
    v_old, v = ds_old.data_vars.keys(), ds.data_vars.keys()
    v_old.sort(), v.sort()
    if v_old != v:
        print 'datasets don\'t have the same variables'
        return None
    if ds['site'] != ds_old['site']:
            print ds['site'], ds_old['site']
            print 'datasets don\'t occur at the same site'
            return None
    ind = xray.concat([ds_old.time, ds.time], dim='time')
    use, index = np.unique(ind.values, return_index=True)
    if len(ds_old.time) not in index:
        print 'all available data are in the old dataset'
        return None
    ds_new1 = ds_old.isel(time=[i for i in index if i < len(ds_old.time)])
    ds_new2 = ds.isel(time=[i for i in index-len(ds_old.time) if i >= 0])
    if ds_new2.time[0].values < ds_new1.time[0].values:
        ds_new = xray.concat((ds_new2, ds_new1), dim='time',
                             mode='different')
    else:
        ds_new = xray.concat((ds_new1, ds_new2), dim='time',
                             mode='different')
    return ds_new


def merge_sites(ds, nc_path):
    '''Merge variables from different sites contained in separate files.'''
    ds0 = xray.open_dataset(nc_path)
    ds1 = ds
    if ds1.site.values in ds0.site.values:
        ds = None
        return ds
    ind = np.unique(xray.concat([ds0.time, ds1.time], dim='time').values)
    ds0 = ds0.reindex({'time': ind}, copy=False)
    ds1 = ds1.reindex({'time': ind}, copy=False)
    print ds1.RECORD
    try:
        ds = xray.auto_combine(datasets=(ds0, ds1), concat_dim='site')
    except:
        ds = None        
    return ds


def done_processing(input_dict, **kwargs):
    if input_dict['datafile'] is 'ts_data':
        os.remove(posixpath.join(input_dict['path'], input_dict['filename']))
        start = ''
        for i in input_dict['path'].split('/')[0:-1]:
            start = posixpath.join(start, i)
        processed_file = posixpath.join(start, 'processed2netCDF.txt')
    elif kwargs.get('archive') is True:
        processed_file = posixpath.join(input_dict['path'],
                                        'processed2netCDF.txt')
    else:
        return
    processed = open(processed_file, 'a')
    processed.write(input_dict['filename']+'\n')
    return


def run(DFList, input_dict, output_dir, attrs, **kwargs):
    '''Process .dat file and write daily netcdf files.'''
    ncfilenames = t2n.get_ncnames(DFList)
    out_path = posixpath.join(output_dir, input_dict['datafile'])
    attrs, local_attrs = t2n.get_attrs(input_dict['header_file'], attrs)
    site, coords_vals = parse_program(output_dir, attrs)
    print site, coords_vals
    for i in range(len(DFList)):
        df = DFList[i]
        nc = ncfilenames[i]
        nc_path = posixpath.join(out_path, nc)
        print nc_path
        if not try_run(i, DFList, input_dict, nc_path, **kwargs):
            continue
        print 'gonna run'
        ds = t2n.createDS(df, input_dict, attrs, local_attrs,
                          site, coords_vals)
        if ds is not None:
            if input_dict['datafile'] is 'soil' and os.path.exists(nc_path):
                ds = merge_sites(ds, nc_path)
            elif i in (0, len(DFList)-1) and os.path.exists(nc_path):
                print 'gonna merge'
                ds = merge_partial(ds, nc_path, **kwargs)
        if ds is None:
            print 'got ds = None'
            continue
        ds.to_netcdf(path=nc_path, mode='w', format='NETCDF3_64BIT')
    coords_vals = None
    if ncfilenames in os.listdir(out_path):
        print 'done with', input_dict['filename']
        done_processing(input_dict, **kwargs)


def run_splits(input_dict, output_dir, attrs, **kwargs):
    '''Run split files so that they append for each day.'''
    DFL = []
    for f in input_dict['splits']:
        input_file = posixpath.join(input_dict['path'], 'split', f)
        if f.endswith('00'):
            pass
        else:
            input_dict.pop('has_header')
            input_dict.update({'has_header': False})
        DFList = t2n.createDF(input_file, input_dict, attrs)
        DFL.append(DFList)
        if len(DFL) > 1:
            DFList, DFL = t2n.group_by_day(DFL)
            run(DFList, input_dict, output_dir, attrs, **kwargs)
    try:
        shutil.rmtree(path_join(input_dir, 'split/'))
    except:
        pass


def run_wholes(input_dict, output_dir, attrs, **kwargs):
    '''Run whole files'''
    input_file = posixpath.join(input_dict['path'], input_dict['filename'])
    DFList = t2n.createDF(input_file, input_dict, attrs)
    run(DFList, input_dict, output_dir, attrs, **kwargs)
