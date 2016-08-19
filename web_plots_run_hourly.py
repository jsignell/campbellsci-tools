#!/home/jsignell/miniconda2/envs/campbellsci-tools/bin/python
"""
Create plots for website's weekly dashboard


Julia Signell
2016-01-06

2016-06-28: added email if internet goes down.
2016-08-16: reorganized and added .env file
"""

import os
import datetime as dt
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # run this before importing pyplot to allow running remotely
import matplotlib.pyplot as plt
import mpld3

from os.path import join, dirname
from dotenv import load_dotenv
load_dotenv(join(dirname(__file__), '.env'))

LOGGERNET_DIR = os.environ.get("LOGGERNET_DIR")
PLOT_DIR = os.environ.get("PLOT_DIR")
WEB_DIR = os.environ.get("WEB_DIR")

sites = {'butler':
            {'CR1000_Table1.dat':
                ['TCroof_Avg', 'RHCroof', 'DnTot_Avg',
                 'UpTot_Avg', 'Rain_mm_3_Tot', 'WindSpd_ms']},
         'broadmead':
            {'CR5000_flux.dat':
                ['Hc', 'LE_wpl', 'Rl_downwell_Avg','Rl_upwell_Avg',
                 'Rs_downwell_Avg', 'Rs_upwell_Avg', 'co2_mean', 'h2o_Avg',
                 'wnd_spd','t_hmp_mean', 'Rain_1_mm_Tot', 'Rain_2_mm_Tot']},
         'washington':
            {'Upper WS CR200_Table1.dat':
                ['Upper_Temp_C_Avg', 'Upper_Corrected_cm_Avg'],
             'Wash_Strm_CR200_IP_Table1.dat':
                ['Lower_Temp_C_Avg', 'Lower_Corrected_cm_Avg'],
             'CL06_CR1000_IP_Table1.dat':
                ['Lvl_cm_Avg', 'AirTC_Avg']}
        }

def send_email(contents, to='jsignell@gmail.com'):
    msg = MIMEText(contents)
    msg['Subject'] = 'Lidar Lab Data'
    msg['From'] = 'hydrometgroup@gmail.com'
    msg['To'] = to

    server = smtplib.SMTP('smtp.gmail.com',587) #port 465 or 587
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login('hydrometgroup@gmail.com','princetonhydromet')
    server.sendmail('hydrometgroup@gmail.com',to, msg.as_string())
    server.close()

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

def dashboard(out_path, params):
    now = pd.datetime.utcnow()
    weekago = now - pd.DateOffset(days=7)
    weekago = df.index[df.index>=weekago][0]
    for param in params:
        try:
            # make the individual plots
            fig, ax = plt.subplots(figsize=(8,6))
            df.loc[weekago::,param].plot(marker='o', ax=ax, legend=None)
            ax.set_ylabel(units[df.columns.get_loc(param)], labelpad=10)
            ax.set_xlabel('')
            ax.set_title(param + ' (time in UTC)')
            mpld3.save_html(fig, '{o}{p}_week.html'.format(o=out_path, p=param))
            plt.close(fig)
        except:
            if param not in df.columns:
                print('failed on' + param)
            elif now not in df.index or weekago not in df.index:
                print(df.index[df.index>weekago][0])
            else:
                print('unknown failure for ' + out_path.split('/')[2] +
                      ' ' + param)

def color_status_cloud(path, out_path, f):
    import time
    import smtplib
    from email.mime.text import MIMEText
    i = 0
    i = max(i, os.path.getmtime(path+f))
    t = time.time() - i
    hover_text = time.ctime(i)
    contents = ''
    # set the email content
    if t > 60*65:
        # send email if we need to
        send_email('Internet connection failed starting at {i}\n'.format(i=hover_text) +
                   'Troubleshooting: Is the lidar lab computer on?\n '+
                   'Is LoggerNet running?\n Is CloudStation running?\n' +
                   'Is CloudStation running on hydromet-thredds?\n'+
                   'Is the cronjob running on the lidar lab computer?\n')
    if 0 < t< 60*60:
        c = "#9ACD32"
    elif t < 60*60*24:
        c = "#FFFF2F"
    elif t < 60*60*24*7:
        c = "#FF7B24"
    else:
        c = "#CF1F0F"
    os.system("sed -i -e 's/#3333EE/{c}/g' {out_path}{f}".format(
              c=c, out_path=out_path, f=f))

# Logger status
try:
    os.system('cp {i}logger_status.html {o}'.format(i=LOGGERNET_DIR, o=PLOT_DIR))
    color_status_cloud(LOGGERNET_DIR, PLOT_DIR, 'logger_status.html')
    os.system("cp -f {o}logger_status.html {web}dataplots/".format(o=PLOT_DIR, web=WEB_DIR))
except:
    try:
        os.system("cp -f {i}/logger_status.html {web}dataplots/".format(
                  i=LOGGERNET_DIR, web=WEB_DIR))
    except:
        pass

for site, datafiles in sites.items():
    for datafile, params in datafiles.items():
        df, units = read_campbellsci(LOGGERNET_DIR, datafile)
        if site == 'washington':
            if datafile == 'Upper WS CR200_Table1.dat':
                df = df.resample('15min').mean().add_prefix('Upper_')
            elif datafile == 'Wash_Strm_CR200_IP_Table1.dat':
                df = df.add_prefix('Lower_')
        dashboard('{out}{site}/'.format(out=PLOT_DIR, site=site), params)
    try:
        os.system("cp -f {out}{site}/* {web}{site}/dataplots/".format(
                  out=PLOT_DIR, site=site, web=WEB_DIR))
    except:
        pass
