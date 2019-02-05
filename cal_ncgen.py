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

        * .. TODO::
             concatenate multiple cdl input files
        * If infile is cdl then create nc by calling ``ncgen``.
          If no other arguments for nc then return
        * open nc file
        * determine instrument to operate on from nc or arg['instr']
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

                # .. TODO: Remove EOF closing braces and put at end of
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
            subprocess.check_call(['ncgen','-b','-k3','-o',
                                   outarg,abs_infile[0]])
        except subprocess.CalledProcessError as err:
            #print('\n',vars(err))
            if err.returncode == 127:
                print('\nCommand not found. Check that ncgen is installed.\n')
            elif err.returncode == 1:
                # Generally error in cdl
                print('\nGeneration of netCDF from cdl file failed.')
                print('Check input cdl syntax.\n')
            raise SystemExit
        except Exception as err:
            print('\nSomething went horribly wrong with the ncgen call\n')
            print('\n',err)
            pdb.set_trace()

    if os.path.splitext(abs_infile[0])[-1].lower() == '.nc' and \
       os.path.exists(abs_infile[0]):
        outarg = abs_infile[0]

    if all([v_==None for k_,v_ in args.items() if k_ != 'outfile']):
        # No arguments given so can return
        return

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
        except:
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

        pdb.set_trace()
        nc.update(updates)

        # Update the history and username attributes
        nc.update_hist(history)
        nc.update_user(user)

        # Save nc back into netCDF4 file

    # root closed
    pdb.set_trace()




# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__=='__main__':

    import argparse

    # Define commandline options
    usage = '%(prog)s files [options]'
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
                        'used to update a different parameter.'
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
                        'cal nc file. If not given then filename is '
                        'generated based on the input cdl file. If the '
                        'input is an nc file and the filename is different '
                        'from the input, then a new nc file shall be '
                        'created.'))

    parser.add_argument('--hist', action='store',
                        dest='hist', nargs='*',
                        default=None,
                        help=('Do not auto-generate the updated history '
                        'attribute of the resultant cal nc file. Instead the '
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
                        'attribute of the resultant cal nc file. Instead the '
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
    print('\t  Calibration netCDF generation script')
    print('-----------------------------------------------------\n')

    call(args_dict['files'],opts_dict)

    print('\nDone.\n')
    # EOF