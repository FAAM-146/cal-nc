#! /usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
File reader/parser utilities.
"""


import datetime, pytz
import numpy as np
import os.path
import netCDF4
import csv

import pdb


# -----------------------------------------------------------------------------
def opc_calfile(cal_file, f_type='pcasp_d', reject_bins=None, invalid=-9999):
    """Parses calibration files outputted from various calibration programs.

    Currently reads in csv files from Phil's calibration programs along with
    Angela's calibration program.

    .. NOTE::

        This has been ripped straight from ``datafile_utils.py``. Probably
        can do this better.

    Args:
        cal_file (:obj:`str` or :obj:`pathlib`): Filename of calibration file to
        be read.
        f_type (:obj:`str`): Type of calibration file to read. One of;

            'pcasp_d'
                output of CDtoDConverter.exe
            'pcasp_cs'
                output of pcaspcal.exe
            'cdp_d'
                output of CDtoDConverter.exe
            'cdp_cs'
                output from ADs calibration program

        reject_bins (:obj:`list`): List of integer bin numbers that are not
            returned. Default is None.
        invalid (:obj:`int` or :obj:`str`): Value of invalid values as used by
            input file. Default is -9999.

    Returns:
        Dictionary of metadata and data masked arrays.
    """



    # List of known types for help
    valid_types = {'pcasp_d':   'output of CDtoDConverter.exe [default]',
                   'pcasp_cs':  'output of pcaspcal.exe',
                   'cdp_d':     'output of CDtoDConverter.exe [default]',
                   'cdp_cs':    'output of CDP calibration program'}


    # Initialise dictionary
    d = {'metadata': {},
         'data'    : {}}


    def read_row_with_heading(line=''):
        '''
        Read comma-delineated row that starts with a heading and return the
        heading as a string and the row of data as an array.
        '''

        # Strip off white space and extra commas
        # Split into heading and data
        row = line.strip().strip(',').split(',',1)

        if row[0].strip() is '':
            return None, None

        if len(row) == 1:
            return row[0], None

        try:
            # Try to create a list of numbers
            data = [float(v) for v in row[1].split(',') if v.strip() != '']
        except ValueError:
            # Create a list of strings
            data = [v.strip() for v in row[1].split(',') if v.strip() != '']
        else:
            # Mask invalid array entries but need to cope with float('NaN')
            data = np.ma.masked_invalid(data,invalid)
            data = np.ma.masked_values(data,invalid)

        return row[0], data


    if f_type.lower() in ['pcasp_d','cdp_d']:
        # The file formats for cdp and pcasp diameter files are identical
        # Input file is from CDtoDConverter.exe
        # Format is;
        # Line 1: Input filename
        # Line 2: Mie table filename
        # Line 4-13: Table of values, one row for each of the bins

        d['metadata']['cal file'] = os.path.abspath(cal_file)

        try:
            f = open(cal_file, 'r')
        except FileNotFoundError as err:
            print(err)
            return None

        # Read metadata at top of file
        line = f.readline()
        while line.strip() != '':
            # Read the metadata, is seperated from data table by blank line
            [k,v] = line.split(':',1)
            d['metadata'][k.strip()] = v.strip()
            line = f.readline()

        # Read the rest of the file
        line = f.readline()
        while line != '':
            # For some reason may get an extra ',' at the end thus double strip
            l = line.strip().strip(',').split(',')

            # Create masked array where masked values are invalid value
            for i in range(1,len(l)):
                # Loop through line and convert to numbers
                try:
                    l[i] = float(l[i])
                except ValueError:
                    if '-1.#IND' in l[i]:
                        # This is a C++ indeterminant. Convert to 'invalid' so
                        # is masked but print warning to user as this may
                        # signify problems with cal processing.
                        l[i] = invalid
                        print(
                    "\nWARNING: '-1.#IND' converted to {0}".format(invalid))
                        print(' File: {}\n'.format(os.path.basename(cal_file)))
                    else:
                        print('\nUnknown character encounted: {}'.format(l[i]))
                        print(' File: {}\n'.format(os.path.basename(cal_file)))
                        print(' Line: ',l)
                        print()
                        pdb.set_trace()
                except Exception as err:
                    print(err)
                    print(' File: {}\n'.format(os.path.basename(cal_file)))
                    pdb.set_trace()

            d['data'][l[0]] = np.ma.masked_equal(l[1:],invalid)

            line = f.readline()

        # Create array of bin numbers *** Starting at 1 ***
        d['data']['bin'] = np.arange(len(d['data']['Channel Centre'])) + 1

        # Close file
        f.close()


    elif f_type.lower() == 'pcasp_cs':
        # Input file is from pcaspcal.exe.

        d['metadata']['cal file'] = os.path.abspath(cal_file)
        d['data']['raw data'] = {}
        d['data']['Straight line fits'] = {}

        try:
            f = open(cal_file, 'r')
        except FileNotFoundError as err:
            print(err)
            return None

        # Read metadata at top of file
        # Read any empty/extra lines at top of file

        line = f.readline()
        while not line.strip().lower().startswith(\
                                      'data files used for calibration:'):
            #pdb.set_trace()
            line = f.readline()

        # Read through all data files used to create calibration
        d['metadata']['input files'] = []
        while line.strip() != '':
            # Read the metadata, is seperated from data table by blank line
            d['metadata']['input files'].append(line.strip())
            line = f.readline()

        # Find column headings for raw data table.
        # Problem is that currently (Sept2012) the first column heading is
        # misspelt Partricle Diameter (micron)'. So match characters 'P','D',
        # and '(' at beginning of line incase it is corrected in future.
        def find_headings(l):
            '''Put in func as need a try/except'''
            try:
                return l.split()[0].startswith('P') & \
                       l.split()[1].startswith('D') & \
                       l.split()[2].startswith('(')
            except:
                return False

        while find_headings(line) is False:
            line = f.readline()

        # Create list keys from headings. Ignore any extra ',' at end of line
        # Plus some headings seem to have an additional space at end
        headings = [h.strip() for h in line.strip().split(',') \
                    if h.strip() != '']

        for h in headings:
            d['data']['raw data'][h] = []

        # Read in the raw data table, is seperated from fits by blank line
        line = f.readline()
        while line.strip() != '':

            # 'Mode Channel (1-28)' data (row 10) may be non-integer which
            # generally means that histogram peak could not be found so was
            # not used in fitting procedure. Don't include this row in arrays
            try:
                tmp = int(line.split(',')[10])
            except:
                # Line has some non-int string so go onto next line
                pass
            else:
                for v,h in zip(line.strip().rstrip(',').split(','),headings):
                    # Columns of raw data have the following headings
                    # Partricle Diameter (micron),+/- (micron),
                    # Standard Deviation (micron),Particle Composition ,
                    # Refractive Index,
                    # Scattering Cross Section (micron squared),
                    # +/- (micron squared),Start Time (hh:mm:ss),
                    # End Time (hh:mm:ss),Date (yyyymmdd),Mode Channel (1-28),
                    # Mode Voltage (A-D counts),+/- (A-D counts)

                    d['data']['raw data'][h.strip()].append(v)
            finally:
                line = f.readline()

        # Sort out variable types in the raw data table and convert to arrays
        for h_i in [0,1,2,5,6,11,12]:
            # Convert folowing columns to arrays of floats;
            # 'Partricle Diameter (micron)', '+/- (micron)',
            # 'Standard Deviation (micron)',
            # 'Scattering Cross Section (micron squared)',
            # '+/- (micron squared)', 'Mode Voltage (A-D counts)',
            # '+/- (A-D counts)'
            d['data']['raw data'][headings[h_i]] = \
                np.array(d['data']['raw data'][headings[h_i]],dtype=float)

        for h_i in [4]:
            # Convert following columns to array of complex numbers
            # 'Refractive Index'

            # Create a 2d list of real and img parts of each number
            tmp = [c.rstrip('i').split('+') for \
                   c in d['data']['raw data'][headings[h_i]]]

            # Then convert tuples into complex numbers
            d['data']['raw data'][headings[h_i]] = \
                   np.array([complex(float(r),float(i)) for (r,i) in tmp])

        for h_i in [10]:
            # Convert the following columns to arrays of integers
            # 'Mode Channel (1-28)'
            try:
                d['data']['raw data'][headings[h_i]] = \
                np.array(d['data']['raw data'][headings[h_i]],dtype=int)
            except:
                pdb.set_trace()

        for h_i in [3,7,8,9]:
            # Convert the remaining columns to arrays of strings
            d['data']['raw data'][headings[h_i]] = \
                np.array(d['data']['raw data'][headings[h_i]],dtype=str)

        # Sort the raw data in terms of aerosol size
        sort_i = np.argsort(d['data']['raw data']\
                               ['Partricle Diameter (micron)'])

        for k in headings:
            d['data']['raw data'][k] = d['data']['raw data'][k].take(sort_i)

        # Skip any blank lines
        while line.strip() != 'Straight line fits':
            line = f.readline()

        # Read lines that contain raw input data
        # Read the straight line fit data
        line = f.readline()
        while not line.startswith('Lower Thresholds'):
            # Straight line fit data is separated from bin table by blank line
            [k,l] = read_row_with_heading(line)
            if k is not None:
                d['data']['Straight line fits'][k] = l

            line = f.readline()

        # Skip over empty lines
        while line.strip() == '': line = f.readline()

        # Read bin data and put into arrays
        while line.strip() != '':
            # Read through to the end of file
            [k,l] = read_row_with_heading(line)
            if k is not None:
                d['data'][k] = l

            line = f.readline()

        # Create array of bin numbers *** Starting at 1 ***
        d['data']['bin'] = np.arange(len(d['data']['Lower Thresholds'])) + 1

        # Close file
        f.close()

    elif f_type.lower() == 'cdp_cs':
        # Input file is from ADs CDP calibration program/s.

        d['metadata']['cal file'] = os.path.abspath(cal_file)
#        d['data']['raw data'] = {}
        d['data']['Straight line fits'] = {}

        f = open(cal_file, 'rb')

        # Read any empty/extra lines at top of file
        line = f.readline()
        while line.strip() == '':
            line = f.readline()

        # Read through metadata
        while not line.title().startswith('Straight Line Fits'):
            # Discard empty lines
            [k,l] = read_row_with_heading(line)
            if k is not None:
                d['metadata'][k] = l

            line = f.readline()

        # Read the straight line fit data
        line = f.readline()
        while not line.title().startswith('Lower Thresholds'):
            # Straight line fit data is separated from bin table by blank line
            [k,l] = read_row_with_heading(line)
            if k is not None:
                d['data']['Straight line fits'][k] = l

            line = f.readline()

        # Read bin data and put into arrays
        while line.strip() != '':
            # Read through to the end of file
            [k,l] = read_row_with_heading(line)
            if k is not None:
                d['data'][k] = l

            line = f.readline()

        # Create array of bin numbers *** Starting at 1 ***
        d['data']['bin'] = np.arange(len(d['data']['Lower Thresholds'])) + 1

        # Close file
        f.close()


    else:
        print('\nUnknown calibration file type:')
        print('{0} Valid types are;'.format(os.path.basename(cal_file)))
        for k,v in valid_types.items():
            print(' {0}\t{1}'.format(k,v))

        print()
        d = None

    # Return arrays of only bins required
    if reject_bins is not None:

        try:
            del_bins = np.asarray(reject_bins, dtype=int)
        except:
            # Something happened
            pdb.set_trace()

        # Find bins to remove
        del_bins_i = np.where(np.in1d(d['data']['bin'],del_bins))[0]
        len_bins = d['data']['bin'].shape

        # Loop through all data arrays and delete offending elements
        # Note that metadata and raw data arrays are left unmodified

        for k,v in d['data'].items():
            try:
                v.shape == len_bins
            except:
                continue
            else:
                d['data'][k] = np.delete(v,del_bins_i)

    return d

