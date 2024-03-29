#! /usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Functions for reading, writing, and manipulating netCDF files.
"""


import datetime, pytz
import netCDF4
import os.path
import shutil

import pdb

import cal_proc
from cal_proc import *
from .nc_conf import *
from . import utils

__all__ = ['read_nc',
           'process_nc',
           'run_ncgen',
           'create_ceda_files']


# Directory where temporary files are stored by default
default_tmp_dir = './tmp'


def read_nc(master,aux=[]):
    """Function for reading netCDF calibration files into DataSets.

    .. Note::

        All nc files are left open so that the Datasets associated with each
        file can be operated on/with in the rest of the program. This is
        required whether or not the file was opened as read-only. Thus all
        Datasets should be explicitly closed when they are finished with.

    Args:
        master (:obj:`str` or :obj:`pathlib`): 'master' netCDF filename that is
            opened for read/write.
        aux (:obj:`list`): List of any additional netCDF filenames that are to
            be added/concatenated with master nc file. Auxillary nc files are
            opened as read only. Default is [], ie no auxillary files.

    Returns:
        Tuple of dataset from master netCDF and list of any auxillary Datasets.
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


def process_nc(master_nc, aux_nc=[], anc_files=[],
               out_nc=None, instr=None, updates={}):
    """Processes all netCDF and auxillary files.

    The master netCDF is copied to a temporary file which is opened for read/
    write while any auxilary files are opened as read-only datasets.
    Modifications, concatenations, etc are done on the temporary dataset and
    once complete it is closed and moved to the output file which may be either
    the master file or `out_nc`.

    Updates are applied to the master dataset *after* any concatenation etc.

    Args:
        master_nc (:obj:`str`): Filename string of 'master' netCDF file.
        aux_nc (:obj:`list`, optional): List of any additional filename/s of
            netCDF files that are to be added/concatenated with master nc file.
            Default is [], ie no auxillary files.
        anc_files (:obj:`list`, optional): List of any ancillary files that are
            not netCDF and so need to be parsed before being injested into the
            dataset. Default is [], ie no ancillary files.
        out_nc (:obj:`str`, optional): Filename string of netCDF to be written.
            If None (default) or the same as `master_nc`, `master_nc` is
            overwritten.
        instr (:obj:`str`, optional): Identifying string of instrument which
            determines processor class. If `None` (default) then instrument is
            identified from `master_nc`.
        updates (:obj:`dict`, optional): All other updates to be applied to
            the final dataset. Default is {}.

    """

    # Create a temporary copy of the master
    # Note that all 'master' operations are done on this temporary copy
    tmp_nc = '{}_tmp.nc'.format(os.path.splitext(master_nc)[0])
    try:
        shutil.copy(master_nc,tmp_nc)
    except Exception as err:
        # This always seems to give an error but does work
        pdb.set_trace()
        pass

    # Create a instrument processor from the master nc file. This file remains
    # open until explicitly closed.
    master_ds = netCDF4.Dataset(tmp_nc, mode='r+', format='NETCDF4')
                                #diskless=True, persist=True)

    # If instrument name has not explicitly been given then obtain intrument
    # from master dataset
    if instr is None:
        try:
            instr = master_ds.getncattr('instrument')
        except AttributeError:
            print('No instrument name given in master file.')
            return 1, 'Use --update instr instrument argument.'


    # Obtain appropriate instrument processing class
    instr_class = cal_proc.proc_map(instr)

    try:
        # Initialise the nc object
        master = instr_class(master_ds)
    except Exception as err:
        print('Instrument processing class not found: {}\n'.format(instr))
        return 1, ''

    # Print out instrument processor help if required
    try:
        if ['help'] in updates.values():
            print(master)

            # TODO(gn): Change this to a Raise

            return 1, ''
    except TypeError:
        # eg if args['update_arg'] is None
        pass


    # Extract any ancillary files from updates with key '_parsefile'
    try:
        anc_files.extend(updates.pop('_parsefile'))
    except KeyError:
        pass

    # Read in all additional nc files and add/append to master
    aux_ds = []
    for aux in aux_nc:
        try:
            aux_ds.append(netCDF4.Dataset(aux, mode='r', format='NETCDF4'))
        except FileNotFoundError:
            continue
        else:
            master.append_dataset(aux_ds[-1])

    # Read in any ancillary files
    for i,anc in enumerate(anc_files):

        if os.path.splitext(anc)[-1].lower() in ['.cfg','.config']:
            # Read in any configuration files.
            # Currently this code assumes that all information is included
            # within the config file.
            cfg_dict = read_config(anc)

            # Separate file to parse and associated variables
            (v_dicts,
             s_dicts) = zip(*[extract_specials(d_) for d_ in cfg_dict.values()])

            # Obtain list of files to parse and variable groups
            p_files = []
            var_dicts = []
            grps = []
            for i,s in enumerate(s_dicts):
                try:
                    p_file = s.pop('_parsefile')
                except KeyError as err:
                    p_files.append(None)
                else:
                    # Attempt to find correct path
                    p_files.append(utils.filepath(p_file,os.path.dirname(anc)))

                try:
                    grp = s.pop('_group')
                except KeyError as err:
                    grp = ''
                else:
                    # If not given or given explicitly then is root group
                    if grp in [None,'/']:
                        grp = ''

                # 'Correct' variable names to include group path
                var_dicts.append({os.path.join(grp,k_):v_
                                 for (k_,v_) in v_dicts[i].items()})

        else:
            # If ancillary files are not config's then need to be parsed
            # directly.
            # Any attributes that are included in updates are associated with
            # the ancillary file. Thus if there are more than one anc file
            # then there should be the same number of identicaly update
            # parameters (unless they are to be broadcast to all updates.

            # Create a dictionary of variables/attributes associated with
            # the ancillary file, anc.
            # This comprehension pseudo broadcasts the last value if not enough
            # have been given in updates.
            # Note that if too many attributes have been given (compared to
            # the number of anc files) then these shall be lost!
            var_dicts = [{k_:(v_[i] if len(v_)>=i else v_[-1])
                         for (k_,v_) in updates.items()}]
            p_files = [anc]

        for p_,v_ in zip(p_files, var_dicts):
            # The zip obj will be as short as the shortest input, ie empty if var_dicts==[]
            if p_ == None:
                master.append_dict(v_)
            else:
                master.update_bincal_from_file(p_,v_)

    # Append any updates that are attributes rather than variables.
    # Attributes are skipped in cal_proc.generic.append_dict()

    # Every update must include a username and a history that are appended
    # to the root attributes 'username' and 'history'. If these are not
    # given then creation is dealt with in cal_proc.generic()

    try:
        update_by = updates.pop('username')
    except KeyError as err:
        update_by = None
    master.update_user(update_by)

    try:
        update_when = updates.pop('history')
    except KeyError as err:
        update_when = None
    master.update_hist(update_when)

    for attr,update in updates.items():
        grp_, attr_ = os.path.split(attr)
        if grp_ == '' and attr not in master.ds.ncattrs():
            # Update not a root attribute so skip
            continue
        elif attr_ not in master.ds[grp_].ncattrs():
            # Update not a group attribute so skip
            continue

        master.update_attr(attr,update)

    # Close nc datasets
    for ds_ in [master_ds] + aux_ds:
        if ds_.isopen():
            ds_.close()

    try:
        if out_nc == None:
            # Write back over existing master nc file
            shutil.move(tmp_nc, master_nc)
        else:
            shutil.move(tmp_nc, out_nc)
    except:
        pdb.post_mortem()
    return 0, ''


def run_ncgen(fin,fout,nc_fmt=3):
    """Create netCDF file from input cdl by calling external program, `ncgen`.

    Args:
        fin (:obj:`str` or :obj:`pathlib`): Filename of cdl file.
        fout (:obj:`str`): Filename of output netCDF file.
        nc_fmt (:obj:`int`): Integer specifying the format of the netCDF
            created, default is 3 for netCDF-4. Options are;

                1. netcdf classic file format, netcdf-3 type model
                2. netcdf 64 bit classic file format, netcdf-3 type model
                3. netcdf-4 file format, netcdf-4 type model
                4. netcdf-4 file format, netcdf-3 type model

            Note that using a netcdf-3 format will break group features and thus
            the entire `cal-nc` structure.
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


def create_ceda_files(ncfile, flights, revision=0, version=None, instr=None):
    """ Copies single cal-nc file into a series of files for upload to CEDA

    The CEDA filesnames include the flight number and date of the flight.
    Thus for placement into the correct directory of the archive by the
    automatic system the filename must have the correct structure. The
    idea is that the same calnc file will be placed in all CEDA flight
    directories to which it applies so the same calnc file will have multiple
    copies with different filenames.

    ..TODO::
        The filenames are generated based on the contents of ``ncfile``,
        specifically the ``applies_to`` attribute. Note that the date of the
        flight may not be given inside ``ncfile`` so this has to be determined
        either from the dictionary arg given or from CEDA...

    Args:
        ncfile (:obj: `str` or `pathlib`): Filename of calibration nc file.
        flights (:obj: `list`): List of 2-element list. Each list has a flight
            number string and the associated flight date. The date may be
            a string or a datetime object
        revision (:obj: `int`): Revision number of file. Should be incremented
            by one from previous file revision.
        version (:obj: `float`): Version of software used to produce
            ``ncfile``. If ``None`` [default] then is extracted from
            'software_version' attribute of ``ncfile``. This extracted version
            is multiplied by 10 so that if ``'software_version' == 1.1``
            then version = 011.
        instr (:obj: `str`): Name of instrument. If ``None`` [default] then
            is extracted from 'instr' attribute of ``ncfile``.
    """

    from dateutil.parser import isoparse
    import re

    FLIGHTNUM_PREFIXES = ['B', 'C']

    # CEDA filename format
    def CEDA_fmt(date, ver, rev, flt, instr):
        f = f"core-cloud-phy_faam_{date}_v{round(ver):03d}" + \
            f"_r{rev:d}_{flt.lower()}_{instr.lower()}_cal.nc"
        return f

    # Create separate flight number and date lists
    try:
        (flts, fltdates) = list(zip(*flights))
    except ValueError as err:
        print(err)
        print('Incorrect flight number and date list')
        return

    # Check that flight number strings are correct
    fltnums = []
    fltnum_letters = '['+''.join(FLIGHTNUM_PREFIXES)+']'
    for flt in flts:
        try:
            fltnums.append(re.search(fltnum_letters+'\d{3}',
                                     str(flt), re.I).group().lower())
        except AttributeError as err:
            print(err)
            print('Unable to parse flight number')
            print(flt)
            return

    # Check that date strings can be identified and format into %Y%m%d
    dates = []
    for fltdate in fltdates:
        try:
            _ = datetime.datetime.strftime(fltdate,'%Y%m%d')
        except TypeError as err:
            try:
                _d = isoparse(str(fltdate))
            except TypeError as err:
                print(err)
                print('Unable to parse flight date')
                print(fltdate)
                return
        else:
            _d = fltdate
        finally:
            dates.append(datetime.datetime.strftime(_d,'%Y%m%d'))

    ds = read_nc(ncfile)[0]

    if version == None:
        try:
            _ver = float(ds.getncattr('software_version'))*10.
        except AttributeError as err:
            print("\nNo 'software_version' found in nc file")
            print(os.path.basename(ncfile))
            return
        except ValueError as err:
            print('Software version must be a number')
            print(err)
            return

        version = round(_ver)

        if version != _ver:
            print('Integer only versions are allowed in filename. '
                  f"Filename version used is {version}")

    if instr == None:
        try:
            instr = ds.getncattr('instr')
        except AttributeError as err:
            print("\nNo 'instr' found in nc file")
            print(os.path.basename(ncfile))
            return

    for flt, date in zip(fltnums, dates):

        path = os.path.dirname(ncfile)

        fname = CEDA_fmt(date, version, revision, flt, instr)
        shutil.copy2(ncfile, os.path.join(path, fname))
