""" Bodge script to manually adjust an existing netCDF file

"""

import os.path
import warnings
import netCDF4
from netCDF4 import Dataset
import cftime
import datetime, pytz

import re
import glob
import pdb



file = '/home/graeme/Documents/work/gdrive/Instruments/PCASP/calibrations/PCASP-2_20221214_postMPHASE/PCASP2_M-PHASE_calnc.nc'

with netCDF4.Dataset(file, 'r+', clobber=True) as nc:
	nc.history = "2022-12-16T16:00:45+0000 cal_ncgen.py v1.0 Initial creation. " +\
				 "2023-01-02T06:45:29+0000 cal_ncgen.py v1.0 Corrected ARCT mixture error."
	nc.revision_number = '1'



