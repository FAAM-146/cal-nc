#! /usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Script for creating FAAM calibration netCDF files.

.. code-block:: console

    $ python3 cal_ncgen.py SEA-WCM2000.cdl

creates a netCDF4 file, ``SEA-WCM2000.nc`` from the cdl source file. To
update variables in the netCDF directly from the command line:

.. code-block:: console

    $ python3 cal_ncgen.py SEA-WCM2000.nc -u time 700 800
      -u applies_to C150- C180- -u TWC/r100 31.4473 31.5585
      -u TWC/dtdr 33.9276 34.0387 --user 'Graeme Nott <graeme.nott@faam.ac.uk>'
      --hist \<now\>\ Artificial\ update\ 1 '<today> Artificial update 2'

where the nc file is read in and four parameters are updated. Two entries
are appended to the global variables ``time`` and ``applies_to``, and to the
TWC group variables ``TWC/r100`` and ``TWC/dtdr``. The same username is
appended to the ``username`` global attribute for both entries. Different
history strings are appended to the global ``history`` attribute however (note
the two different ways to escape history strings) with ``<now>`` and ``<today>``
being converted to the current date.

It is possible to update variables using one or more external files. This
requires a custom parser to be part of the instrument processor class so that
these files can be read and injested. A single external file may be added to an
existing calibration netCDF file with;

.. code-block:: console

    $ python3 cal_ncgen.py PCASP_faam_20170701_v001_r000_cal.nc -u time 20170919
      -u applies_to C027-C055 -u parsefile testing/data/20170919_P1_cal_results_cs.csv

Additional metadata associated with the text file
`testing/data/20170919_P1_cal_results_cs.csv` is given with `-u` arguments. The
special --update key `parsefile` indicates that the following value needs to be
parsed with the instrument-specific parser method.

It is also possible to add multiple external calibration files at the same time
as the associated metadata with an external configuration file. This file uses
the standard ascii format that is parsed with the `configparser 
<https://docs.python.org/3.7/library/configparser.html>`_ package. So if for 
example the config file `PCASP1_CLARIFY_cals.cfg` contained;

.. code-block::

    [pre-CLARIFY]
    time = 20170701
    applied_to = C027-
    user = Graeme Nott
    traceability = List of PSL lot number information
    comments = After realignment of inlet jet
    cal_flag = 0

    parsefile = testing/data/20170801_P1_cal_results_cs.csv

    [post-CLARIFY]
    time = 20170919
    applied_to = C027-C055
    user = Graeme Nott
    traceability = List of PSL lot number information
    cal_flag = 0

    parsefile = testing/data/20170919_P1_cal_results_cs.csv

this could be inserted into an existing netCDF file that has been created from
the PCASP1 template cdl file as follows;

.. code-block:: console

    $ python3 cal_ncgen.py PCASP1_cal.cdl -u parsefile PCASP1_CLARIFY_cals.cfg
      -o PCASP_faam_20170701_v001_r000_cal.nc

Note that such a config file must have a recognisable format and the `.cfg.` or
`.config` extension to ensure that the instrument parser is not invoked on the
config file directly.

"""

import datetime, pytz
import netCDF4
import xarray as xr
import pdb

import cal_proc
from cal_proc import *
from cal_nc import *

# Default directories where cdl file/s may be stored
# Searched in order
default_cdl_dir = ['.','cal_cdl']



def call(infile,args):
    """
    Convenience function for cal_ncgen

    :param infile: One or more cdl files. If multiple files then concat,
        if single cdl then ncgen to nc.
    :type infile: list
    :param args: Arguments for adding to cdl file
    :type args: Dictionary
    :returns: None

    :How this function works::

        * .. TODO::
             concatenate multiple cdl input files
        * If infile is cdl then create nc by calling ``ncgen``.
          If no other arguments for nc then finish
        * open nc file as ``root``
        * determine instrument to operate on from nc or args['instr']
        * Instantiate instrument class
        * Write or append data to variables
        * write nc
    """
    import subprocess
    import os.path

    # Create absolute paths for infile/s
    abs_infile_ = (os.path.abspath(os.path.join(d,f)) \
                   for d in default_cdl_dir for f in infile \
                   if os.path.isfile(os.path.join(d,f)))

    # Remove any duplicate files
    abs_infile = []
    for f_ in abs_infile_:
        if not any([os.path.samefile(a_,f_) for a_ in abs_infile]):
            abs_infile.append(f_)

    if len(abs_infile) == 0:
        # Are no valid input files
        print('\nNo valid input files have been given')
        return None

    # Split input files into nc and cdl lists
    nc_infile = [f_ for f_ in abs_infile if os.path.splitext(f_)[-1].lower() == '.nc']
    cdl_infile =[f_ for f_ in abs_infile if os.path.splitext(f_)[-1].lower() == '.cdl']

    # Find 'master' input file on which to build
    # Note that this shall always be the first netCDF file if one is provided.
    try:
        master_infile = nc_infile[0]
    except IndexError:
        # No nc files provided
        master_infile = cdl_infile[0] 

    # Determine filename of output file
    if args['outfile'] != None and type(args['outfile']) is str:
        outfile = args['outfile']
    else:
        outfile = os.path.splitext(master_infile)[0] + '.nc'

    # Read in all cdl files and convert to netCDF with temporary filenames
    tmp_outfile = []
    for i, cdl_f in enumerate(cdl_infile):
        tmp_outfile.append('{}_tmp{:003d}.nc'.format(os.path.splitext(outfile)[0],
                                                     i+1))
        # Run cal_nc.nc_func.ncgen to produce netCDF-4 format file
        run_ncgen(cdl_f,tmp_outfile[-1])

    # Make sure master is pointing to a nc file
    if os.path.splitext(master_infile)[-1] != '.nc':
        # If master_infile is a cdl then make master the corresponding nc file
        master_infile = os.path.splitext(master_infile)[0] + '.nc'
        os.replace(tmp_outfile[0],master_infile)

        _ = tmp_outfile.pop(0)

    if all([v_==None for k_,v_ in args.items() if k_ != 'outfile']) \
       and (len(abs_infile) == 1):
        # No arguments for single file so can return as outfile

        if master_infile != outfile:
            os.replace(master_infile,outfile)

        if len(outfile) < 1.1 * len(os.path.relpath(outfile)):
            print('Written: {}'.format(outfile))
        else:
            print('Written: {}'.format(os.path.relpath(outfile)))
        return



#    fred=pcasp.read_cal_file('testing/data/20170919_P1_cal_results_cs.csv',
#                                f_type='pcasp_cs')


    pdb.set_trace()

    # Take all but first nc_infile as first has been moved to master_infile
    # If empty nc_infile then nothing is done
    master_ds, aux_ds = read_nc(master_infile,nc_infile[1:] + tmp_outfile)

    pdb.set_trace()
    


    # Open nc file for reading/writing
    with netCDF4.Dataset(outarg, mode='r+', format="NETCDF4") as root:

        # Obtain intrument from nc or options
        if args['instr'] is None:
            instr = getattr(root,'instr')
        else:
            instr = args['instr']

        # Obtain appropriate instrument processing class
        instr_class = cal_proc.proc_map(instr)

        try:
            # Initialise the nc object
            nc = instr_class(root)
        except Exception as err:
            print('Instrument processing class not found: {}\n'.format(instr))
            pdb.set_trace()

        # Print out instrument processor help if required
        try:
            if 'help' in args['update_arg']:
                print(nc)
                return
        except TypeError:
            # eg if args['update_arg'] is None
            return

        # Basic check on update argument, make sure that they are all the
        # same length. If there are equal number of different lengths, the
        # first one shall be selected and the other discarded.
        update_lens = [len(v_) for v_ in args['update_arg']]
        modal_len = max(set(update_lens),key=update_lens.count) - 1

        # Restructure update args into list of dictionaries.
        # Note that this does not cope with flattened dictionaries
        updates = {l_[0]:l_[1:] for l_ in args['update_arg'] if
                   len(l_) == modal_len + 1}

        # Include some user feedback if any items discarded
        for u_arg in args['update_arg']:
            if u_arg[0] not in updates:
                print('\nUpdate argument discarded as incorrect length')
                print('  ',u_arg)
                print()

        # Want to apply history and user attributes for each update so make
        # sure are correct length.
        # The username is the same for all updates
        if args['user'] == None:
            user = None
        else:
            user = [' '.join(args['user'])] * modal_len

        if args['hist'] == None:
            history = None
        else:
            if len(args['hist']) > modal_len:
                history = args['hist'][:modal_len]
                discard_hist = args['hist'][modal_len:]
            elif len(args['hist']) != modal_len:
                history = [args['hist'][0]] * modal_len
                discard_hist = args['hist'][1:]
            else:
                history = args['hist']
                discard_hist = []

            if discard_hist != []:
                print('\nUpdate history argument is incorrect length, '
                      'discarding entries:')
                print(' ','\n  '.join(discard_hist))
                print()

        # Update the variables/attributes
        nc.update(updates)

        # Update the history and username attributes
        nc.update_hist(history)
        nc.update_user(user)

    # root closed


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__=='__main__':

    import argparse

    # Define commandline options
    usage = '%(prog)s files [options]'
    version = 'version: {v}'.format(v=cal_proc.__version__)
    description = ('Script to assist in the creation of calibration ' +\
                   'netCDF files.\n {0}'.format(version))
    epilog = __doc__

    parser = argparse.ArgumentParser(usage=usage,
                formatter_class=argparse.RawDescriptionHelpFormatter,
                description=description,
                epilog=epilog)

    # Mandatory argument
    parser.add_argument('files',
                        nargs='+',
                        help=('Input cdl or nc file/s. If one or more cdl files '
                        'then a new calibration netCDF file shall be created '
                        'using the (concatenated if possible) cdl as a template. '
                        'If an existing nc file is given then new calibration '
                        'data shall be appended to the variables in that file. '
                        'This data is provided in additional cdf/nc files or '
                        'as --update argumenmts. The first nc file, and if none '
                        'the first cdl file, is treated as the master and used '
                        'for output filename generation, root attributes, etc.'))

    # Optional arguments
    parser.add_argument('-u', '--update', action='append',
                        nargs = '*',
                        dest='update_arg', default=None,
                        help=('Space-delineated list of data parameters '
                        'as required by the specific instrument class. '
                        "'--update' can be given multiple times, each time "
                        'being used to update a different parameter.'
                        "Use '-u help' for instrument specific help."))
    parser.add_argument('-i', '--instr', action='store',
                        dest='instr', default=None,
                        help=('Instrument class is selected based on the '
                        "'instr' global attribute in the input file. "
                        'If this is none-standard or uses a different '
                        'instrument class then instr can be explicitly '
                        'given with this option.'))
    parser.add_argument('-o', '--output', action='store',
                        dest='outfile', default=None,
                        help=('Explicitly give output path/filename of '
                        'cal-nc file. If not given then the filename is '
                        'generated based on the input cdl file. If the '
                        'input is an nc file and the filename is different '
                        'from the input a new nc file shall be created.'))

    parser.add_argument('--hist', action='store',
                        dest='hist', nargs='*',
                        default=None,
                        help=('Do not auto-generate the updated history '
                        'attribute of the resultant cal-nc file. Instead the '
                        'given string is appended to the global history '
                        'attribute instead. These should be a space-delineated '
                        'series of dates and comments, spaces in each entry '
                        'must be enclosed in quotes or escaped. There should '
                        'be one history entry for each --update, if not then '
                        'the same history shall be attached to all updates.'))
    parser.add_argument('--user', action='store',
                        dest='user', nargs='*',
                        default=None,
                        help=('Do not auto-generate the updated username '
                        'attribute of the resultant cal-nc file. Instead the '
                        'given string is appended to the global username '
                        'attribute instead (should be space-seperated '
                        'user and <email>).'))
    parser.add_argument('-v', '--version', action='version',
                        version=version,
                        help='Display program version number.')


    # Process arguments and convert to dictionary ----------------------------
    args_dict = vars(parser.parse_args())
    opts_dict = {k:v for k,v in args_dict.items() if k not in ['files']}
    print()

    # Welcome splash
    print('\n-----------------------------------------------------')
    print('\tCalibration netCDF generation script')
    print('-----------------------------------------------------\n')

    call(args_dict['files'],opts_dict)

    print('\nDone.\n')
    # EOF