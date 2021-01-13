#! /usr/bin/env python3
# -*- coding: utf-8 -*-
r"""Script for creating FAAM calibration netCDF files.

.. code-block:: console

    $ python3 cal_ncgen.py SEA-WCM2000.cdl

creates a netCDF4 file, ``SEA-WCM2000.nc`` from the cdl source file. To
update variables in the netCDF directly from the command line;

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

An existing calibration netCDF may have values appended to to it from a cdl or
nc file with;

.. code-block:: console

    $ python3 cal_ncgen.py SEA-WCM2000_cal_20180810.nc SEA-WCM2000_20190805.cdl

Explicitly giving a different output filename with the --output argument will
leave WCM2000_cal_20180810.nc unaltered and create a new calibration netCDF;

.. code-block:: console

    $ python3 cal_ncgen.py SEA-WCM2000_cal_20180810.nc SEA-WCM2000_20190805.cdl
      --output WCM2000_cal_2018-19.nc

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
    _group = bin_cal
    time = 20170701
    applied_to = C027-
    user = Graeme Nott
    traceability = List of PSL lot number information
    comments = After realignment of inlet jet
    cal_flag = 0
    _parsefile = testing/data/20170801_P1_cal_results_cs.csv

    [post-CLARIFY]
    _group = bin_cal
    time = 20170919
    applied_to = C027-C055
    user = Graeme Nott
    traceability = List of PSL lot number information
    cal_flag = 0
    _parsefile = testing/data/20170919_P1_cal_results_cs.csv

this could be inserted into an existing netCDF file that has been created from
the PCASP1 template cdl file as follows;

.. code-block:: console

    $ python3 cal_ncgen.py PCASP1_cal.cdl -u parsefile PCASP1_CLARIFY_cals.cfg
      -o PCASP_faam_20170701_v001_r000_cal.nc

Note that such a config file must have a recognisable format and the `.cfg` or
`.config` extension to ensure that the instrument parser is not invoked on the
config file directly. The *special* options in each section that start with
an ``_`` are not treated as netCDF attributes or variables but are used to
assist in the processing of the options.

"""

import datetime, pytz
import netCDF4

import pdb

import cal_proc
from cal_proc import *
from cal_nc import *

# Default directories where cdl file/s may be stored
# Searched in order
default_cdl_dir = ['.','cal_cdl']

# Directory where temporary files are stored
default_tmp_dir = './tmp'

import warnings
warnings.filterwarnings('error')


def call(infile,args):
    """Convenience function for cal_ncgen.py.

    The main grunt work is actually done in ``nc_func.process_nc()``.

    How this works:

        * Creates separate lists of `nc` and `cdl` files. Determines 'master'
            file based on list order with `nc` files having priority over `cdl`.
        * netCDF files are created for any `cdl` files by calling ``ncgen``.
          If no other arguments for nc then finish
        * Determine output filename
        * If no changes to master `nc` file required then exit.
        * Consolidate any arguments into an ``updates`` dictionary
        * Pass to ``nc_func.process_nc()`` for creation of complete cal-nc file.

    Args:
        infile (:obj:`list`): List of one or more cdl filesnames. If multiple
            files are given than these will be concatenated.
        if single cdl then ncgen to nc.
        args (:obj:`dict`): Arguments for adding to resultant nc file.
    """

    import os.path

    # Create absolute paths for infile/s
    # temporarily create a set to get rid of dups
    abs_infile_ = list(set([os.path.abspath(os.path.join(d,f)) \
                   for f in infile for d in default_cdl_dir\
                   if os.path.isfile(os.path.join(d,f))]))

    if len(abs_infile_) != len(infile):
        print('Given input file not found:')
        for f_ in infile:
            if os.path.basename(f_) not in (os.path.basename(f__) for f__ in abs_infile_):
                print(' {}'.format(os.path.basename(f_)))
        print()

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
    nc_infile = [f_ for f_ in abs_infile
                 if os.path.splitext(f_)[-1].lower() == '.nc']
    cdl_infile =[f_ for f_ in abs_infile
                 if os.path.splitext(f_)[-1].lower() == '.cdl']

    # Find 'master' input file on which to build
    # Note that this shall always be the first netCDF file if one is provided.
    try:
        master_infile = nc_infile.pop(0)
    except IndexError:
        # No nc files provided
        master_infile = os.path.splitext(cdl_infile[0])[0] + '.nc'
        run_ncgen(cdl_infile[0],
                  master_infile)
        _ = cdl_infile.pop(0)

    # Determine filename of output file
    if args['outfile'] != None and type(args['outfile']) is str:
        outfile = args['outfile']
    else:
        outfile = master_infile

    # Read in all cdl files and convert to netCDF with temporary filenames
    tmpfile = []
    for i, f_ in enumerate(cdl_infile):
        #tmpfile.append(tempfile.TemporaryFile(dir=os.path.dirname(f_)))
        tmpfile.append('{}_tmp.nc'.format(os.path.join(default_tmp_dir,
                                                       os.path.splitext(f_)[0]),
                       i+1))
        # Run cal_nc.nc_func.ncgen to produce netCDF-4 format file
        run_ncgen(f_,tmpfile[-1])

    # Make sure master is pointing to a nc file
    if os.path.splitext(master_infile)[-1] != '.nc':
        # If master_infile is a cdl then make master the corresponding nc file
        master_infile = os.path.splitext(master_infile)[0] + '.nc'
        os.replace(tmpfile[0],master_infile)

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

    # Restructure update args into list of dictionaries.
    # If the same update key called multiple times then make value a list
    updates = {}
    for u_ in args['update_arg']:
        if u_[0] in updates:
            updates[u_[0]].extend(u_[1:])
        else:
            updates[u_[0]] = u_[1:]

    # Add user and history attributes and make terms consistant
    # eg program options --user=Fred and -u username Fred are equivalent

    ## TODO: Consolidate with specials in nc_conf.py
    for u_,k_ in zip([args['user'],args['hist']],['username','history']):
        try:
            if u_ != updates[k_]:
                # Conflict in argument. Get user to select.
                print('\nConflict in argument {}'.format(k_))
                print('[1]* {}'.format(u_))
                print('[2]  {}'.format(updates[k_]))
                sel = input('Select input [1/2]: ')
                if sel != 2:
                    updates[k_] = u_
        except KeyError as err:
            # Attribute not included in dic so put it in
            updates[k_] = u_


    ### Process ########################################################
    proc_rtn, proc_err = process_nc(master_infile,
                                    nc_infile + tmpfile,
                                    out_nc = outfile,
                                    instr=args['instr'],
                                    updates=updates)

    # Delete any temporary files
    for file in tmpfile:
        os.remove(file)

    if proc_rtn != 0:
        # Error occured in process_nc
        print(proc_err)
        return

    return


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
                        help=('Input cdl or nc file/s. If one or more cdl '
                        'files then a new calibration netCDF file shall be '
                        'created using the (concatenated if possible) cdl as '
                        'a template. If an existing nc file is given then '
                        'new calibration data shall be appended to the '
                        'variables in that file. This data is provided in '
                        'additional cdf/nc files or as --update argumenmts. '
                        'The first nc file, and if none the first cdl file, '
                        'is treated as the master and used for output '
                        'filename generation, root attributes, etc.'))

    # Optional arguments
    parser.add_argument('-u', '--update', action='append',
                        nargs ='*',
                        dest='update_arg', default=[],
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

    parser.add_argument('--ceda', action='append',
                        nargs='+',
                        dest='ceda_flts', default=None,
                        help=('Generate CEDA-standard filenames from a single '
                        'existing cal-nc file. The option values are a '
                        'space-delineated list of flight number and flight '
                        "date that match the CEDA structure. '--ceda' can be"
                        'given multiple times if creating multiple flight '
                        'files.'))
    parser.add_argument('--ceda_ver', action='store',
                        dest='ceda_ver', default=None,
                        help=('Version of software used to generate the '
                        'cal-nc file. If not given then is read from the '
                        'cal-nc file.'))
    parser.add_argument('--ceda_rev', action='store',
                        dest='ceda_rev', default=0,
                        help=('Revision of cal-nc file to be produced. If '
                        'not specified then is assumed to be 0. The revision '
                        'should be incremented by 1 from revision already '
                        'on CEDA.'))
    parser.add_argument('--ceda_instr', action='store',
                        dest='ceda_instr', default=None,
                        help=('Instrument name for the cal-nc file to be '
                        'produced. If not given then is read from the cal-nc '
                        'file.'))
    parser.add_argument('-v', '--version', action='version',
                        version=version,
                        help='Display program version number.')


    # Process arguments and convert to dictionary ----------------------------
    args_dict = vars(parser.parse_args())
    opts_dict = {k:v for k,v in args_dict.items() if k not in ['files']}

    pdb.set_trace()

    if args_dict['ceda_flts'] != None:
        if len(args_dict['files']) > 1:
            raise ValueError('Only a single cal-nc file can be converted.')

        create_ceda_files(args_dict['files'][0],
                          args_dict['ceda_flts'],
                          args_dict['ceda_rev'],
                          args_dict['ceda_ver'],
                          args_dict['ceda_instr'])

    else:
        for i,l in enumerate(opts_dict['update_arg']):
            # Replace special option arguments strings with those recognised
            opts_dict['update_arg'][i][0] = \
                        opts_dict['update_arg'][i][0].replace('parsefile',
                                                              '_parsefile')

        print()

        # Welcome splash
        print('\n-----------------------------------------------------')
        print('\tCalibration netCDF generation script')
        print('-----------------------------------------------------\n')

        call(args_dict['files'],opts_dict)

    print('\nDone.\n')
    # EOF