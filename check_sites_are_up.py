#!/home/jsignell/miniconda2/envs/campbellsci-tools/bin/python

import os
import sys
import subprocess

import smtplib
from email.mime.text import MIMEText
import pandas as pd
import urllib

if sys.version_info[0] < 3:
    from StringIO.StringIO as IO
    from urllib import urlopen
else:
    from io.BytesIO as IO
    from urllib.request import urlopen

def send_email(contents, subject='Web Services', to='jsignell@gmail.com'):
    msg = MIMEText(contents)
    msg['Subject'] = subject
    msg['From'] = 'hydrometgroup@gmail.com'
    msg['To'] = to

    server = smtplib.SMTP('smtp.gmail.com',587) #port 465 or 587
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login('hydrometgroup@gmail.com','princetonhydromet')
    server.sendmail('hydrometgroup@gmail.com',to, msg.as_string())
    server.close()

# check that sites are online
sites = {"home": "http://hydrometeorology.princeton.edu",
         "thredds": "http://hydromet-thredds.princeton.edu:9000/thredds/catalog.html",
         "erddap": "http://hydromet-thredds.princeton.edu:8000/erddap/index.html"}
content = ''

for site, url in sites.items():
    try:
        status = urlopen(url).getcode()
        if status != 200:
            sendit = True
        else:
            sendit = False
    except urllib.error.URLError:
        sendit = True
    if sendit:
        content = content+"{site} is not online\n".format(site=site)
        if site != "home":
            # check if docker is running erddap and thredds
            try:
                output = subprocess.check_output("docker ps", shell=True)
                docker = True
            except subprocess.CalledProcessError:
                content = content+"docker daemon is not running\n"
                docker = False
            if docker:
                df = pd.read_csv(IO(output), delim_whitespace=True)
                print(df.columns)
                if site not in df.NAMES.values:
                    # attempt to restart docker service
                    os.system("cd /home/jsignell/{site}; "
                              "cat start.txt | bash".format(site=site))
if len(content) > 0:
    send_email(content)
            # TODO: If this doesn't work is docker running at all?

# TODO: Is cloudstation working at the server?
# this is the most likely but should trigger an email from web_plots_run_hourly

# TODO: Is the web drive mounted at the server?
# should happen at every reboot
