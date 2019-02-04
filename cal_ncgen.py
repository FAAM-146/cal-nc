#! /usr/bin/env python3
r"""
Script for creating FAAM calibration netCDFs

For information see README
"""

import datetime, pytz
import netCDF4
import pdb

import cal_proc


# Default directories where cdl file/s may be stored
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

    :How this works?:

        * open nc -a
        * determine instrument
        * Instantiate instrument class
        * populate or append to data
        * write nc
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

        ########
        pdb.set_trace()

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
        except:
            print('Instrument processing class not found: {}'.format(instr))
            pdb.set_trace()

        ########
        pdb.set_trace()

        # Run any additional scripts if necessary
        try:
            if 'help' in [l[0].lower() for l in args['update_arg']]:
                print(nc)
                return
        except TypeError:
            # If args['update_arg'] is None
            pass

        nc.update(args['update_arg'])

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
    version = 'version: {v}'.format(v=cal_proc.__version__)
    description = ('Script to assist in the creation of calibration ' +\
                   'netCDF files.\n {0}'.format(version))
    epilog = 'Usage examples.\n' +\
             'Write something here'

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
    parser.add_argument('-u', '--update', action='append',
                        nargs = '*',
                        dest='update_arg', default=None,
                        help=('Space-delineated list of data parameters '
                        'as required by the specific instrument class. '
                        "'--update' can be given multiple times, each time "
                        'used to update and different parameter '
                        "Use '-d help' for instrument specific help."))
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
                        'history attribute instead (should be space-seperated '
                        'date and comment). If no string is given '
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
                        'username attribute instead (should be space-seperated '
                        'user and <email>). If no string is given '
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