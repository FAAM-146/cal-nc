#! /usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Functions for reading, writing, and manipulating netCDF files.
"""


import datetime, pytz
import netCDF4
import xarray as xr
import pdb

#from .. import cal_proc


# Project information
__title__ = 'FAAM Calibration netCDF - nc functions'
__description__ = 'Functions for reading, writing, and manipulating netCDF files.'
__institution__ = 'FAAM - Facility for Airborne Atmospheric Measurements'
__version__ = '0.1'
__date__ = '2019 10 24'
__author__ = 'Graeme Nott'
__author_email__ = 'graeme.nott@faam.ac.uk'
__copyright__ = '2019, FAAM'


__all__ = ['read_nc','run_ncgen']


def read_nc(master,aux=[]):
    """
    Function for reading netCDF calibration files into DataSets

    .. Note::

        All nc files are left open so that the Datasets associated with each
        file can be operated on/with in the rest of the program. This is 
        required whether or not the file was opened as read-only. Thus all
        Datasets should be explicitly closed when they are finished with.

    param master: 'master' netCDF file that is opened for read/write
    type: master: Filename string of filepath object
    param aux: Any additional netCDF files that are to be added/concatenated with
        master nc file. Auxillary nc files are opened as read only. Default is
        [], ie no auxillary files.
    returns: Dataset from master netCDF and list of any auxillary Datasets.
    """

    # Open master nc file for reading/writing
    master_ds = netCDF4.Dataset(master, mode='r+', format='NETCDF4')
    # master_ds = xr.open_dataset(master,
    #                             decode_times=True)


    # Open any auxillary files as read only
    aux_ds = [netCDF4.Dataset(f_, mode='r', format='NETCDF4') for f_ in aux]
    # aux_ds = [xr.open_dataset(master,
    #                           decode_times=True) for f_ in aux]
    
    return master_ds, aux_ds



def run_ncgen(fin,fout,nc_fmt=3):
    """
    Create netCDF file, fout, from input cdl, fin

    :param fin: Filename of cdl file
    :type fin: string
    :param fout: Filename of output netCDF file
    :type fin: string
    :param nc_fmt: Integer specifying the format of the netCDF created,
        default is 3 for netCDF-4. Options are;

        1 netcdf classic file format, netcdf-3 type model
        2 netcdf 64 bit classic file format, netcdf-3 type model
        3 netcdf-4 file format, netcdf-4 type model
        4 netcdf-4 file format, netcdf-3 type model

        Note that using a netcdf-3 format will break group features.
    :type nc_fmt: integer, 1-4
    :returns: None
    """

    import subprocess

    try:
        subprocess.check_call(['ncgen','-b','-k{:d}'.format(nc_fmt),'-o',
                               fout,fin])
    except subprocess.CalledProcessError as err:
        #print('\n',vars(err))
        if err.returncode == 127:
            print('\nCommand not found. Check that ncgen is installed.\n')
        elif err.returncode == 1:
            # Generally error in cdl
            print('\nGeneration of netCDF from cdl file failed.')
            print(' {}'.format(fin))
            print('Check input cdl syntax.\n')
        raise SystemExit
    except Exception as err:
        print('\nSomething went horribly wrong with the ncgen call\n')
        print('\n',err)
        pdb.set_trace()

    return
