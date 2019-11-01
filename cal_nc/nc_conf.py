#! /usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Functions for parsing of configuration files.
"""


import datetime, pytz
import netCDF4
import os.path
import configparser
import shutil

import pdb

import cal_proc
from cal_proc import *



# Project information
__title__ = 'FAAM Calibration netCDF - nc configuration parsing'
__description__ = 'Functions for parsing of configuration files.'
__institution__ = 'FAAM - Facility for Airborne Atmospheric Measurements'
__version__ = '0.1'
__date__ = '2019 10 31'
__author__ = 'Graeme Nott'
__author_email__ = 'graeme.nott@faam.ac.uk'
__copyright__ = '2019, FAAM'


__all__ = ['read_config']


# Directory where temporary files are stored
default_tmp_dir = './tmp'



def read_config(cfg_file,destr=False):
    """
    Function to read in configuration file and put entries in dictionary.
    ConfigParser options used are;
        allow_no_value=True

    Input args:
        cfg_file:   configuration path/filename with the required format
        destr:      Boolean, if True then convert strings to other types

    Returns:
        cfg_dict:   dictionary with sub-dictionaries for each section
                    returns None if cfg_file cannot be found
    """


    def _ConfigSectionMap(section):
        # Read each option within the given section
        dict1 = {}
        options = cfg.options(section)
        for option in options:
            try:
                dict1[option] = cfg.get(section, option)
                if dict1[option] == -1:
                    DebugPrint('skip: {}'.format(option))
            except:
                print('exception on {}!'.format(option))
                dict1[option] = None
        return dict1

    def _destr_dict(d):
        # Walk through multi-layer dictionary and convert string values to
        # other types as appropriate
        for k, v in d.iteritems():
            if isinstance(v, dict):
                _destr_dict(v)
            else:
                if v.lower() == 'none':
                    d[k] = None
                elif v.lower() == 'true':
                    d[k] = True
                elif v.lower() == 'false':
                    d[k] = False

    # Check file validity
    if not os.path.exists(cfg_file):
        # If file as named doesn't exist then add an extension if possible
        if os.path.exists(os.path.splitext(cfg_file)[0] + '.cfg'):
            cfg_file = os.path.splitext(cfg_file)[0] + '.cfg'
        else:
            print('filename {} does not exist.'.format(cfg_file))
            return None

    cfg = configparser.ConfigParser(allow_no_value=True)

    cfg.read(cfg_file)
    cfg_dict = {}
    for l in cfg.sections():
        cfg_dict[l] = _ConfigSectionMap(l)

    if destr is True:
        _destr_dict(cfg_dict)

    if cfg_dict == {}:
        print('\ncfg_dict is empty but ' +\
              '{0} exists.'.format(os.path.basename(cfg)))
        print(' This usually occurs when the eol is set incorrectly. '+\
              'Unix eol characters are known to work.\n')
        cfg_dict = None

    return cfg_dict
