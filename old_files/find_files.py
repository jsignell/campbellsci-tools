'''
Find files of interest and rangle them into a list of input_dicts

Julia Signell
2015-05-07
'''

from __init__ import *
from process_files import *


def already_processed(path, f):
    '''Return True if a file has already been processed to netcdf.'''
    try:
        processed_file = posixpath.join(path, 'processed2netCDF.txt')
        processed = open(processed_file, 'r').read()
    except:
        processed = []
    if f in processed or f.strip('.zip') in processed:
        return True
    else:
        return False


def fresh_processed(path):
    '''Open and clear the processed to netcdf file in each input_dir.'''
    processed_file = posixpath.join(path, 'processed2netCDF.txt')
    if os.path.isfile(processed_file):
        processed = open(processed_file, 'w')
        processed.write('')
        processed.close


def unzip(path, f):
    '''Write unzipped file to path and redefine f'''
    archive = zipfile.ZipFile(posixpath.join(path, f), 'r')
    f = f.partition('.zip')[0]
    proper_path = posixpath.join(path, 'share')
    try:
        if os.path.isfile(posixpath.join(path, 'share', f)):
            print proper_path, f
            return proper_path, f
        else:
            archive.extract(posixpath.join('share', f), path)
            return proper_path, f
    except:
        try:
            archive.extract(f, path)
            return path, f
        except:
            try:
                archive.extract(posixpath.join('sn4709_ts_5_min_data', f), path)
                return posixpath.join(path, 'sn4709_ts_5_min_data'), f
            except:
                print('cannot unzip', f)
                return


def has_header(input_dict):
    '''Update input_dict to reflect whether or not a file has a header.'''
    input_file = posixpath.join(input_dict['path'], input_dict['filename'])
    header = list(pd.read_csv(input_file, nrows=1).columns.values)
    if header[0] == 'TOA5':
        return input_dict.update({'has_header': True,
                                  'header_file': input_file})
    else:
        header_file = posixpath.join(input_dict['path'], 'header.txt')
        if os.path.isfile(header_file):
            pass
        elif input_dict['datafile'] is 'ts_data':
            try: 
                TSDIR = os.getenv('TSDIR')
                header_file = posixpath.join(TSDIR, 'header.txt')
            except:
                print 'cannot find header in TSDIR'
        else:
            print('cannot find header file')
            header_file = None
        return input_dict.update({'has_header': False,
                                  'header_file': header_file})


def split_file(k, input_dict):
    d = input_dict['datafile']
    f = input_dict['filename']
    path = input_dict['path']
    split_path = posixpath.join(path, 'split')
    if not os.path.exists(split_path):
        os.mkdir(split_path)
    in_f = '%s' % posixpath.join(path, f)
    out_f = '%s_%02d' % (posixpath.join(split_path, d), k)

    os.system(r'''C:\cygwin\bin\bash.exe --login -c "split -C 180M -d '%s' '%s'"''' %
              (in_f, out_f))
    print('split %s' % in_f)
    splits = [x for x in os.listdir(split_path) if x.startswith('%s_%02d' %
                                                                (d, k))]
    input_dict.update(dict(splits=splits))
    k += 1
    return k, input_dict


def rangle(path, f, d, k):
    '''Rangle file into input_dict.'''
    if '.zip' in f:
        path, f = unzip(path, f)
    input_dict = ({'path': path,
                   'filename': f,
                   'datafile': d})
    has_header(input_dict)
    big = 210000000

    if os.stat(posixpath.join(path, f)).st_size >= big:
        k, input_dict = split_file(k, input_dict)
    return k, input_dict


def get_files(attrs, input_dir, output_dir, **kwargs):
    '''Return list of data dicts containing path, filename, datafile'''
    input_dicts = []
    for path, dirs, files in os.walk(input_dir):
        if 'share' in path or 'split' in path:
            continue
        k = 0
        path = path.replace('\\', '/')
        print(path)
        if kwargs['rerun'] is True:
            fresh_processed(path)
        for f in files:
            if f.startswith('.'):
                continue
            if kwargs['rerun'] is False:
                if kwargs['archive'] is True or 'ts_data' in f:
                    if already_processed(path, f) is True:
                        continue
            for d in datafiles:
                if d in f and '.dat' in f:
                    try:
                        k, input_dict = rangle(path, f, d, k)
                    except:
                        print('could not rangle {path}/{f}'.format(path=path, f=f))
                        continue
                    if kwargs['run_as_we_go'] is True:
                        if 'splits' in input_dict.keys():
                            run_splits(input_dict, output_dir, attrs,
                                       **kwargs)
                        else:
                            run_wholes(input_dict, output_dir, attrs,
                                       **kwargs)
                        continue
                    else:
                        input_dicts.append(input_dict)
    return input_dicts
