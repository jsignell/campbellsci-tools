#!/home/jsignell/miniconda2/envs/campbellsci-tools/bin/python
"""
Full process for moving and split large (~2GB) 10Hz datafiles into daily files.
All files must share a unique root (in this case: CR5000_ts_data_).

This script is scheduled to run every day from a cron job

Julia Signell
2016-11-21
"""
import os
from split_ts_files import wrapper

file_root = 'CR5000_ts_data_'
outfile = "TOA5_EC_{YYYY}_{MM}_{DD}_0500.dat"  # must contain time formatters
DATA_DIR = "/home/jsignell/CloudStation/Data/"  # trailing / matters
STAGING_DIR = "/home/jsignell/agnes_staging/"  # trailing / matters


def move_files_locally(DATA_DIR, STAGING_DIR, file_root):
    status = 0
    for f in os.listdir(DATA_DIR):
        if f.startswith(file_root):
            os.rename(DATA_DIR+f, STAGING_DIR+f)
            status += 1
    return status


def move_daily_files_to_year_dir(STAGING_DIR, outfile):
    years = []
    for f in os.listdir(STAGING_DIR):
        if f.startswith(outfile.split('{')[0]):
            year = f[outfile.index('{YYYY}'): outfile.index('{YYYY}')+4]
            if not os.path.isdir(STAGING_DIR+year):
                os.mkdir(STAGING_DIR+year)
            os.rename(STAGING_DIR+f, os.path.join(STAGING_DIR, year, f))
            years.append(year)
    return set(years)


def move_other_files_to_backup(STAGING_DIR, file_root):
    files = [f for f in os.listdir(STAGING_DIR) if f.startswith(file_root)]
    files.sort()
    for f in files[:-2]:
        os.rename(STAGING_DIR+f, os.path.join(STAGING_DIR, 'backup', f))


def push_files_to_agnes(STAGING_DIR, year):
    command = ("rsync -u {path}{YYYY}/* jsignell@agnes.princeton.edu:"
               "/data/SENSOR/Broadmead/{YYYY}/Daily_TS/")
    os.system(command.format(path=STAGING_DIR, YYYY=year))


def process(DATA_DIR, STAGING_DIR, file_root, outfile):
    status = move_files_locally(DATA_DIR, STAGING_DIR, file_root)
    if status == 0:
        return
    wrapper(file_root, path=STAGING_DIR, hour=5, outfile=outfile)
    years = move_daily_files_to_year_dir(STAGING_DIR, outfile)
    for year in years:
        push_files_to_agnes(STAGING_DIR, year)
    if status > 2:
        move_other_files_to_backup(STAGING_DIR, file_root)

if __name__ == "__main__":
    process(DATA_DIR, STAGING_DIR, file_root, outfile)
