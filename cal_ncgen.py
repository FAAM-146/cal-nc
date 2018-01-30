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


Script summary:
---------------

Mandatory script argument is either cdl or nc file.
- If cdl a new nc file will be created using the cdl as a template
- If nc then new data is appended into the file

If more than one cdl file is given then they shall be concatenated,
there is little error checking besides removing the start and end braces. It
is up to the user to ensure no conflicts etc.

If the input is cdl then ncgen is run to create an nc file
[#fnote-direct_ncgen_call].

This nc file is then read in with the netCDF4 module. The instrument
nickname is extracted from the resulting datasets global 'instr' attribute
amd this is used to instantiate the appropriate class for that instrument.
The simplest class is 'generic' which has methods for appending history
and username information and that is all. All other classes inherit from
generic and may include other methods to parse from ancillary files and
and write this data into the nc file. This parsing will be highly specific
to an instrument, thus the individual classes.


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

.. rubic::

..[#fnote-direct_ncgen_call] This means that a user can completely by-pass
the use of this script and call ncgen directly on a user-generated cdl file.
This is by design as it allows greater flexibility.

"""

import datetime, pytz
import netCDF4
import pdb

import cal_class

# Version of this script
cal_ncgen_ver = 0.1

# Default directories where cdl file/s may be stored
default_cdl_dir = ['.','cal_cdl']


def call(infile,args):
    """
    If multiple cdl then concat
    If cdl then ncgen to nc

    open nc -a
    determine instrument
    Instantiate instrument class
        populate or append to data
    write nc
    """
    import subprocess
    import os.path

    # Create absolute paths for infile/s
    # Note that this may create multiple copies of the same file with
    # different paths.
    ### TODO: Create set to look for multiple copies of same file
    abs_infile = [os.path.abspath(os.path.join(d,f)) \
                  for d in default_cdl_dir for f in infile \
                  if os.path.isfile(os.path.join(d,f))]

    if len(abs_infile) == 0:
        # Are no valid input files
        print('\nNo valid input files have been given')
        return None

    with open(abs_infile[0], 'r+') as outfile:
        for fname in (f_ for f_ in abs_infile[1:]):

            print('\nConcatenation of multiple cdl files is not implemented.')
            break
            with open(fname) as infile_:
                instring = infile_.read()

                # TODO: Remove EOF closing braces and put at end of
                # concatenated files
                outfile.write()

    if os.path.splitext(abs_infile[0])[-1].lower() == '.cdl':
        # Convert cdl to nc
        if args['outfile'] != None and type(args['outfile']) is str:
            outarg = args['outfile']
        else:
            outarg = os.path.splitext(abs_infile[0])[0] + '.nc'

        # Run ncgen to produce netCDF-4 format file
        try:
            subprocess.check_call('ncgen -b -k 2 -o {} {}'.format(outarg,
                                                            abs_infile[0]),
                                  shell=True)
        except Exception as err:
            print('\nSomething when horribly wrong with the ncgen call')
            print('\n',err)
            pdb.set_trace()

    # Open nc file for reading/writing
    with netCDF4.Dataset(outarg, mode='r+', format="NETCDF4") as root:

        instr = getattr(root,'instr')

        # Check that instr is a valid cal_class class
        instr_class = [ic for ic in cal_class.__all__ \
                       if ic.lower() == instr.lower()]

        try:
            nc_class = getattr(cal_class,instr_class[0])
        except:
            pdb.set_trace()

        nc = nc_class(root)

        # Update the history and username attributes
        nc.update_hist(args['hist'])
        nc.update_user(args['user'])

    # root closed
    pdb.set_trace()




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
                        help=('Input cdl or nc file. If cdl then a new '
                        'calibration netCDF file shall be created '
                        'using the cdl as a template. More than one '
                        'cdl can be given and basic concatenation '
                        'shall be done to create the template. If an '
                        'existing nc file is given then new '
                        'calibration data shall be appended to the '
                        'variables in that file.'))

    # Optional arguments
    parser.add_argument('-d', '--data', action='store',
                        nargs = '+',
                        dest='datafiles', default=None,
                        help=('Space-delineated list of data file path/'
                        'filenames as required by the specific '
                        'instrument class.'))
    parser.add_argument('-i', '--instr', action='store',
                        dest='instr', default='generic',
                        help=('Instrument class is selected based on the '
                        "'instr' global attribute in the input file. "
                        'If this is none-standard or uses a different '
                        'instrument class then instr can be explicitly '
                        'given with this option.'))
    parser.add_argument('-o', '--output', action='store',
                        dest='outfile', default=None,
                        help=('Explicitly give output path/filename of '
                        'cal nc file. If not given then filename is '
                        'generated based on the input cdl file. If the '
                        'input is an nc file and the filename is different '
                        'from the input, then a new nc file shall be '
                        'created.'))

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
    parser.add_argument('-u', '--user', action='store',
                        dest='user', nargs='?',
                        default='NA',
                        const=None,
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
    opts_dict = {k:v for k,v in args_dict.items() if k not in ['files']}
    print()

    # Welcome splash
    print('\n-----------------------------------------------------')
    print('\t  Calibration netCDF generation script')
    print('-----------------------------------------------------\n')

    pdb.set_trace()
    call(args_dict['files'],opts_dict)

    print('\nDone.\n')
    # EOF