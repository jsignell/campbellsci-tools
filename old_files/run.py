# -*- coding: utf-8 -*-
"""
Created on Wed May 20 08:17:49 2015

@author: Julia
"""
# Read in all the app config settings stored in .env
# Do this before anything else!
import os
if os.path.exists('.env'):
    print('Importing environment from .env...')
    for line in open('.env'):
        var = line.strip().split('=')
        if len(var) == 2:
            os.environ[var[0]] = var[1]

#input_dir = os.getenv('ARCHIVEDIR')
input_dir = os.getenv('DATADIR')
#input_dir = 'G:/TowerDataArchive/'
output_dir = os.getenv('NETCDFDIR')

kwargs = dict(archive=False,
              rerun=False,
              run_as_we_go=True)

from __init__ import *
from find_files import get_files

get_files(attrs, input_dir, output_dir, **kwargs)
