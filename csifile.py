import os
import datetime as dt
import pandas as pd
import numpy as np

class CSIFile:
    
    def __init__(self, path=None, df=None):
        if path is not None:
            self.path = path
            self.read_campbellsci()
        if df is not None:
            self.df = df

    def read_campbellsci(self):
        df = pd.read_csv(self.path, skiprows=[0,2,3], index_col=0, parse_dates=True,
                         na_values=["NAN", "INF", "-INF", 7999, -7999], low_memory=False)
        f = open(self.path, 'r')
        lines = f.readlines()
        f.close()
        self.GenLine = lines[0]
        self.ParamLine = lines[1]
        self.UnitsLine = lines[2]
        self.MethodLine = lines[3]
        self.header = ''.join(lines[0:4])

        self.units = self.UnitsLine.strip('\r\n').replace('"','').split(',')[1:]
        self.method = self.MethodLine.strip('\r\n').replace('"','').split(',')[1:]
        self.df = df
    
    def split(self, how='yearly'):
        out_file = '{o}{d}'.format(o=self.output_path, d=self.datafile) + '_{date}.dat'
        if how == 'daily':
            gb = self.df.groupby(self.df.index.date)
            for d in gb.groups.keys():
                df = gb.get_group(d)
                date = '{y}_{m:02d}_{d:02d}'
                date = date.format(y=d.year, m=d.month, d=d.day)
                self.save_file(df, out_file.format(date=date))
            return
        gb = self.df.groupby(self.df.index.year)
        for y in gb.groups.keys():
            df = gb.get_group(y)
            if how == 'yearly':
                self.save_file(df, out_file.format(date=y))
            else:
                gb_m = df.groupby(df.index.month)
                for m in gb_m.groups.keys():
                    df_m = gb_m.get_group(m)
                    date = '{y}_{m:02d}'.format(y=y, m=m)
                    self.save_file(df_m, out_file.format(date=date))

    def save_file(self, df=None, out_file=None):
        if df is None:
            df = self.df
        f = open(out_file, 'w')
        f.write(self.header)
        f.close()
        df.to_csv(out_file, mode='a', header=False, index=True)
        
    def fix_broadmead_tz(self):
        df_all = self.df
        new = df_all[:'2008-06-13 00:00'].index
        new = new.append(df_all['2008-06-13 00:00':'2008-11-03 00:00'].index + pd.DateOffset(hours=5))
        new = new.append(df_all['2008-11-03 00:00':].index)
        self.df = df_all.set_index(new)
        
    def fix_butler_tz(self):
        # This is for Butler
        df_all = self.df
        new = df_all[:'2013-03-26 07:00'].index + pd.DateOffset(hours=5)
        new = new.append(df_all['2013-03-26 08:00':'2014-01-28'].index + pd.DateOffset(hours=4))
        new = new.append(df_all['2014-01-29':'2014-06-27 05:00'].index + pd.DateOffset(hours=5))
        new = new.append(df_all['2014-06-27 06:00':'2014-12-01'].index + pd.DateOffset(hours=4))
        new = new.append(df_all['2014-12-02':'2015-05-09 04:00'].index + pd.DateOffset(hours=5))
        new = new.append(df_all['2015-05-09 05:00':'2015-10-14 14:00'].index + pd.DateOffset(hours=4))
        new = new.append(df_all['2015-10-14 15:00':].index) 
        self.df = df_all.set_index(new)
    
    def fix_washington_tz(self):
        df_all = self.df
        new = df_all[:'2015-10-14 14:00'].index + pd.DateOffset(hours=4)
        new = new.append(df_all['2015-10-14 15:00':].index)
        self.df = df_all.set_index(new)

def grab(path, datafile='CR1000_Table1'):
    csi_all = []
    for f in os.listdir(path):
        if datafile in f and f.endswith('.dat'):
            csi = CSIFile(path+f)
            csi.datafile = datafile
            csi_all.append(csi)
    return csi_all

def concat(csi_list):
    df_all = None
    for csi in csi_list:
        df_all = pd.concat((df_all,csi.df))
    df_all = df_all.sort_index()
    df_all = df_all.drop_duplicates()
    for csi in csi_list:
        if set(df_all.columns) <= set(csi.df.columns):
            csi_all = CSIFile(df=df_all[csi.df.columns])
            csi_all.header = csi.header
            csi_all.units = csi.units
            csi_all.method = csi.method
            if hasattr(csi, 'datafile'):
                csi_all.datafile = csi.datafile
            return csi_all
    return CSIFile(df_all)

def update(path, datafile='CR1000_Table1', out_path='../../data/butler/'):
    csi = CSIFile(path+datafile+'.dat')
    y = csi.df.index[0].year
    m = csi.df.index[0].month
    if os.path.isfile(out_path+datafile+'_{y}_{m:02d}.dat'.format(y=y, m=m)):
        csi_old = CSIFile(out_path+datafile+'_{y}_{m:02d}.dat'.format(y=y, m=m))
        csi_old.datafile = datafile
        csi_all = concat([csi_old, csi])
        csi_all.output_path = out_path
        csi_all.split('monthly')
    else:
        csi_old = CSIFile(out_path+datafile+'_{y}.dat'.format(y=y))
        csi_old.datafile = datafile
        csi_all = concat([csi_old, csi])
        csi_all.output_path = out_path
        csi_all.split('yearly')