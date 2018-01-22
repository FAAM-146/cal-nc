#! /usr/bin/env python3
r"""
Calibration netCDF
==================

Introduction:
-------------
To present calibration data in a consistant manner, to facilitate archiving of the data, and include traceability information and references, data is stored in a netCDF file of a specified structure. netCDF has been chosen as, although it is perhaps unnecessarily complicated for this application, it is commonly used for instrument data and is self-describing. The structure is flexible enough to hold many different types of instrument calibration information. The quantity of calibration information stored within the files will almost certainly be quite small so size and read/write speed are not a priority.

A full specification can be found in FAAM technical document FAAM000003, "Calibration netCDF Structure".

The proposed structure has been set with several central tenets in mind;
#. There is a single calibration file for each instrument,
#. A single instrument may require several different calibrations in order to
produce calibrated data. These different aspects of the calibration are
contained within separate groups within the same netCDF file,
#. A single file holds a time series of comparable calibrations,
#. The calibration and measurement data files each are contain references to
the other. The data file should contain a boolean variable indicating whether
the calibration has already been applied,
#. Calibrations are traceable by the inclusion of calibration metadata,
#. Future expansion and instruments can be accommodated.

File Structure:
---------------
The file is divided into groups, the top level being the root and containing
attributes that apply to contents of the entire file. This metadata contains
information about the institution as well as the instrument covered by the
file.

Global attributes
    Attributes that apply to the entire file contents, these are defined by
    the conventions. Contains information about where the data was produced,
    references, instrument information, dates of calibrations, and a
    history of file versions.

Calibration groups
    Separate calibration information are placed in different groups.

Array dimensions for calibration data are organised so that with each new calibration that is added to the file, the datetime dimension increases by one. Second and tertiary dimensions are set by the requirements of the instrument calibration parameters.

First dimension - time
    This is the unlimited dimension. This dimension is expanded each time a
    calibration is added to the file, which may be once a year or numerous
    times a flight.

Second dimension - cal
    This is a fixed dimension for the calibration information. For example,
    this may be a list of three parameters for a cubic fit or a list of
    thirty bin threshold values.

Further dimensions - vector
    These are fixed dimensions for any additional information. For example
    if the thirty bin thresholds have two parameters that describe a straight
    line fit.


Script Description
==================

Templates for calibration netCDF files are done by hand in cdl. This is a
text equivalent of the binary netCDF. Given the small amount of data in the
variables this should be reasonably convenient although it may be useful to
include functionality in this or other scripts to ingest larger datasets
and write them into variables of the calibration netCDF that is created with
the cdl template.

CDL templates:
--------------
There are at least two cdl files required. These and any others are combined
to produce the final calibration netCDF.

Institution cdl
    The top level cdl contains information on the institution only. This is
    used for all calibration netCDFs from that institution to provide
    universal information and consistency. Only global attributes are
    included in this cdl.

Instrument cdl 1
    The instrument cdl has instrument information. Global attributes and
    coordinates may be included. The primary global coordinate is *time*.
    Groups for each type of calibration for the instrument are included
    along with the group attributes, dimensions, and variables.

Instrument cdl *n*
    Subsequent instrument cdl files can be written. These may be used if the
    quantity of data becomes unwieldy for a single file.

.. highlights::
    name:
        cal_ncgen.py

    description:
        Script to assist in the creation of calibration netCDF files.

    version:
        0.1

    python version:
        3.4

    author:
        Graeme Nott <graeme.nott@faam.ac.uk>

    created:
        Jan 2018

"""

import sys
import datetime, pytz
import netCDF4

# Version of this script
cal_ncgen_ver = 0.1

default_org_cdl = "FAAM_cal.cdl"







# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__=='__main__':

    import argparse

    # Define commandline options
    usage = '%(prog)s filename [options]'
    version = 'version: {v}'.format(v=cal_ncgen_ver)
    description = ('Script to assist in the creation of calibration ' +\
                   'netCDF files.\n {0}'.format(version))
    epilog = 'Usage examples.\n' +\
             'Write something here'
####
    parser = argparse.ArgumentParser(usage=usage,
                formatter_class=argparse.RawDescriptionHelpFormatter,
                description=description,
                epilog=epilog)

    # Mandatory argument
    parser.add_argument('files',
                        nargs='+',
                        help=('White-space delineated path/filename '
                        'of input cdl file/s. Glob or list of globs '
                        'may be used.'))

    # Optional arguments
    parser.add_argument('-b', '--base', action='store',
                        dest='base_cdl', default=default_org_cdl,
                        help=("Organisation's base cdl file for this cal nc. "
                        "If --base='' then none is used. If not given then "
                        "default is '{}'.".format(default_org_cdl)))
    parser.add_argument('-o', '--output', action='store',
                        dest='outfile', default=None,
                        help=('Explicitly give output path/filename of '
                        'cal nc file. If not given then filename is '
                        'generated based on the input file/s.'))

    parser.add_argument('--hist', action='store',
                        dest='hist', nargs='?',
                        default=None,
                        const='NA',
                        help=('Do not auto-generate the updated history '
                        'attribute of the resultant cal nc file. If a string '
                        'is given then this string is appended to the '
                        'history attribute instead. If no string is given '
                        'then assume history updates have been handled in '
                        'the cdl file/s. This option should be used with '
                        'care.'))
    parser.add_argument('--user', action='store',
                        dest='user', nargs='?',
                        default=None,
                        const='NA',
                        help=('Do not auto-generate the updated username '
                        'attribute of the resultant cal nc file. If a string '
                        'is given then this string is appended to the '
                        'username attribute instead. If no string is given '
                        'then assume username updates have been handled in '
                        'the cdl file/s. This option should be used with '
                        'care.'))
    parser.add_argument('-v', '--version', action='version',
                        version=version,
                        help='Display program version number.')


    # Process arguments and convert to dictionary ----------------------------
    args_dict = vars(parser.parse_args())
    print()

    # Welcome splash
    print('\n-----------------------------------------------------')
    print('\t  Calibration netCDF generation script')
    print('-----------------------------------------------------\n')

    call(**args_dict)

    print('\nDone.\n')
    # EOF