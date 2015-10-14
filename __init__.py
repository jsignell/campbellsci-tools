'''
This init file should be modified for each site. 
Julia Signell
2015-10-13
'''


import os
import shutil
import sys
import time
import datetime as dt
import posixpath
import pandas as pd
import numpy as np
import xray
import matplotlib.pyplot as plt


datafiles = ['Flux']

site=['Broadmead']  # can be replaced if there are more specific sites

lat = 40.346376
lon = 74.643486
elev = 34

attrs = dict(
    title = 'Eddy Covariance Flux from Broadmead',
    summary = ('This data comes from the Broadmead eddy covariance ' +
               'flux station at Broadmead near Princeton University.'),
    license = 'MIT License',
    institution = 'Princeton University',
    acknowledgement = 'Funded by NSF and Princeton University',
    naming_authority = 'princeton.edu',
    station_name='Broadmead_EC',
    creator_name = 'Julia Signell',
    creator_email = 'jsignell@princeton.edu',
    keywords = 'eddy covariance, land surface flux',
    Conventions = 'CF-1.6',
    featureType = 'timeSeries',
    local_timezone = 'EST'
    )


coords = {
    'lon': (['site'], [lon], dict(units='degrees west',
                                     standard_name='longitude',
                                     axis='X')),
    'lat': (['site'], [lat], dict(units='degrees north',
                                     standard_name='latitude',
                                     axis='Y')),
    'elevation': (['site'], [elev], dict(units='m asl',
                                       standard_name='elevation',
                                       positive='up',
                                       axis='Z'))
    }
