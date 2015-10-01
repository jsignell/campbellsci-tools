'''
Create a netcdf file from a campbell sci data file

Julia Signell
2015-05-07
'''

from __init__ import *


def manage_dtypes(x):
    '''Ensure that all data columns are either intergers or floats'''
    if x.values.dtype == np.dtype('int64') or x.values.dtype == np.dtype('<M8[ns]'):
        return x
    else:
        try:
            return x.astype('float64')
        except:
            return x


def createDF(input_file, input_dict, attrs):
    '''Create a list of daily dataframes in UTC from a .dat file.'''
    kw = dict(parse_dates=True, index_col=0, iterator=True,
              chunksize=100000, low_memory=False)
    if input_dict['has_header'] is True:
        df_ = pd.read_csv(input_file, skiprows=[0, 2, 3], **kw)
    else:
        df_header = pd.read_csv(input_dict['header_file'],
                                skiprows=[0], nrows=1)
        header = list(df_header.columns.values)
        df_ = pd.read_csv(input_file, header=None, names=header, **kw)
    df = pd.concat(df_)
    df.index.name = 'time'
    df = df.apply(manage_dtypes)           # try to make all fields numeric
    df = df.tz_localize(attrs['local_timezone'])  # explain the local tz
    df = df.tz_convert('UTC')                  # convert df to UTC
    df = df.drop_duplicates()

    # group dataframe by day of the year in UTC
    DFList = []
    for group in df.groupby([df.index.year, df.index.month, df.index.day]):
        DFList.append(group[1])
    return DFList


def group_by_day(DFL):
    '''Create a list of dataframes from split datafiles.'''
    DFList = []
    if len(DFL[0]) > 1:
        for df in DFL[0][0:-1]:
            DFList.append(df)
    if DFL[0][-1].index[-1].date() == DFL[1][0].index[0].date():
        df = pd.concat([DFL[0][-1], DFL[1][0]])
        DFL[1].pop(0)
    else:
        df = DFL[0][-1]
    DFList.append(df)
    DFL.pop(0)
    print('DFL has length %s' % len(DFL))
    print('DFL[0] has length %s' % len(DFL[0]))
    if len(DFL[0]) == 0:
        DFL = []
    return DFList, DFL


def get_ncnames(DFList):
    '''Create a list of netcdf filenames correspoding to days in DFList.'''
    ncfilenames = []
    for i in range(len(DFList)):
        doy = DFList[i].index[0].dayofyear
        y = DFList[i].index[0].year
        # create the output filenames
        ncfilenames.append('raw_MpalaTower_%i_%03d.nc' % (y, doy))
    return ncfilenames


def get_attrs(header_file, attrs):
    '''Augment attributes by inspecting the header of the .dat file.'''
    # metadata needs to be CF-1.6 compliant
    # in the TOA5 datafile headers, some metadata are written in the 1st row
    meta_list = eval(open(header_file).readlines()[0])

    attrs.update({'format': meta_list[0],
                  'logger': meta_list[1],
                  'datafile': meta_list[7]})
    if ':' in  meta_list[5]:
        attrs.update({'program': meta_list[5].split(':')[1]})
    else:
        attrs.update({'program': meta_list[5]})
    source_info = (attrs['logger'], attrs['datafile'], attrs['program'],
                   meta_list[6])
    source = 'Flux tower sensor data %s_%s.dat, %s, %s' % source_info
    attrs.update({'source': source})

    # the local attributes are in the 2nd, 3rd, and 4th rows
    df_names = pd.read_csv(header_file, skiprows=[0], nrows=2, dtype='str')
    df_names = df_names.astype('str')
    df_names.index = ('units', 'comment')
    local_attrs = df_names.to_dict()

    return attrs, local_attrs


def get_depths():
    if input_dict['datafile'] in ('soil', 'Table1'):
        depths = input_dict['depths']
        coords.update({'depth': (['depth'],
                                 depths,
                                 dict(units='cm',
                                      standard_name='depth',
                                      positive='down',
                                      axis='Z'))})


def get_coords(coords_vals):
    '''Process coords input in __init__ or added later'''
    lon = coords_vals['lon']
    lat = coords_vals['lat']
    elevation = coords_vals['elevation']
    coords = {
        'lon': (['site'], lon, dict(units='degrees east',
                                     standard_name='longitude',
                                     axis='X')),
        'lat': (['site'], lat, dict(units='degrees north',
                                     standard_name='latitude',
                                     axis='Y')),
        'elevation': (['site'], elevation, dict(units='m',
                                                 standard_name='elevation',
                                                 positive='up',
                                                 axis='Z'))}
    return coords


def make_MultiIndex(df, site):
    '''Replace pre-existing time index with multidim site and time index.'''  
    indices = [site, df.index]
    new_index = pd.MultiIndex.from_product(indices, names=['site', 'time'])
    df.set_index(new_index, inplace=True)
    return df


def createDS(df, input_dict, attrs, local_attrs, site, coords_vals):
    '''Create an xray.Dataset object from dataframe and dicts of parts'''        
    if input_dict['datafile'] is 'soil':
        df = df.resample('10min')
    try:
        df = make_MultiIndex(df, site)
        ds = xray.Dataset.from_dataframe(df)
    except:
        ds = None
        print 'contains non-identical overlapping data --> throw away'
        print 'dataset is None'
        return ds
    ds.attrs.update(attrs)
    ds.coords.update(get_coords(coords_vals))
    for name in ds.data_vars.keys():
        ds[name].attrs = local_attrs[name]
        ds[name].attrs.update(dict(content_coverage_type='physicalMeasurement'))
    return ds
