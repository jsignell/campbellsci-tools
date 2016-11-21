"""
Split large (~4GB) 10Hz datafiles into daily files.
All files must share a unique root (in this case: CR5000_ts_data_).

This is an example of how to run:
from split_ts_files import *
wrapper(file_root='ts_data', path="../agnes_test/2015", hour=5, outfile="TOA5_EC_{YYYY}_{MM}_{DD}_0500.dat")

Julia Signell
2016-03-11
"""
def process(filename, hour, outfile):
    import os
    get_day_ends = 'd=$(echo {f} | cut -c16-25); grep -n "{h:02d}:59:59.9" {f} > day_ends_$d.txt'
    split_files_daily = ("cat header.txt > {outfile}; " +
                         "head -n {end} {f} | tail -n {dif} >> {outfile}")
    
    os.system(get_day_ends.format(h=hour-1, f=filename))
    if "header.txt" not in os.listdir('.'):
        os.system("head -4 {filename} > header.txt".format(filename=filename))
    f = open("day_ends_{date}.txt".format(date=filename[15:25]))
    lines = f.readlines()
    count = 0
    for i in range(len(lines)-1):
        start = int(lines[count].split(':')[0])
        if hour != 24:
            date = lines[count].split(':')[1][1:11]
        if i==0:
            start0=start
        count += 1
        end = int(lines[count].split(':')[0])
        dif = end - start
        if hour != 24:
            date = lines[count].split(':')[1][1:11]
        print(date)
        out = outfile.format(YYYY=date[0:4], MM=date[5:7], DD=date[8:10])
        os.system(split_files_daily.format(f=filename, end=end, dif=dif, outfile=out))
    f.close()
    return(start0, end)

def wrapper(file_root="CR5000_ts_data_", path='./', hour=24, outfile='ts_data_{YYYY}-{MM}-{DD}.dat'):
    """
    Split aggregated files at midnight or hour given to 'hour' kwarg
    
    Parameters
    ----------
    file_root: unique 'str' contained in all raw files (default: "CR5000_ts_data_")
    path: directory in which raw ts files and shell scripts are located (default: current dir)
    outfile: a format which the files can follow such as : TOA5_EC_{YYYY}_{MM}_{DD}_0500.dat
    
    Returns
    -------
    daily files will be saved in designated path
    """
    import os              
    fix_ends = ("cat header.txt > {outfile}; " +
                "tail -{dif} {f1} >> {outfile}; " +
                "head -{start} {f2} | tail -{n} >> {outfile}")
                  
    os.chdir(path)
    files = sorted([f for f in os.listdir('./') if file_root in f])
    print(files)
    d = {}
    for f in files:
        start, end = process(f, hour, outfile)
        d[f] = {'start': start, 'end': end, 'nlines': sum(1 for line in open(f))}
    for i, filename in enumerate(files[0:-1]):
        f1 = filename
        f2 = files[i+1]
        with open(f1, 'r') as f:
            for n, line in enumerate(f):
                if n == d.get(f1)['nlines']-1:
                    date0 = line[1:11]
        with open(f2, 'r') as f:
            for n, line in enumerate(f):
                if n == 5:
                    date1 = line[1:11]
                elif n > 5:
                    break
        if date0==date1:
            out = outfile.format(YYYY=date0[0:4], MM=date0[5:7], DD=date0[8:10])
            dif = d.get(f1)['nlines']-d.get(f1)['end']
            start = d.get(f2)['start']
            os.system(fix_ends.format(dif=dif, f1=f1, start=start, f2=f2, n=start-4, outfile=out))

