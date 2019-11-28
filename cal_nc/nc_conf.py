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


__all__ = ['read_config','extract_specials']


# Directory where temporary files are stored
default_tmp_dir = './tmp'


# List of default 'special key strings' in configuration dictionary
default_special_str = ['_group',
                       '_parsefile']


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

    # Manual configuration converters
    def list_converter(s):
        """
        Convert comma-delineated string to list of numbers or strings as
        appropriate. 'none' strings are converted to None
        """
        assert ',' in s
        l = [s_.strip().replace('"','').replace('\'','') for s_ in s.split(',')]

        for conv_ in (int,float,str):
            try:
                l = [None if s_.lower()=='none' else conv_(s_) for s_ in l[:]]
            except ValueError as err:
                continue
            else:
                break
        return l

    def _ConfigSectionMap(section,rtn_str=False):
        # Read each option within the given section
        # If rtn_str is False then attempt to inteprete/convert string
        if rtn_str == True:
            getter = [cfg.get]
        else:
            getter = [cfg.getlist,
                      cfg.getint,cfg.getfloat,
                      cfg.getboolean,   # after get numbers so 0/1 are ints
                      cfg.get]

        cfg_d = {}
        options = cfg.options(section)
        for option in options:
            for getter_ in getter:
                try:
                    cfg_d[option] = getter_(section, option)
                except ValueError as err:
                    continue
                except AssertionError as err:
                    # String does not include comma so not a list
                    # Raised by list_converter()
                    continue
                except (TypeError,AttributeError) as err:
                    # Generally attempting to convert a None
                    # If None then loop through to cfg.get()
                    continue
                except Exception as err:
                    print('exception on {}!'.format(option))
                    print(err)
                    pdb.set_trace()
                    break
                else:
                    break

            # Attempt to 'none' strings to None
            if cfg_d[option] in ['none', 'None', 'NONE']:
                cfg_d[option] = None

        return cfg_d


    # Check file validity
    if not os.path.exists(cfg_file):
        # If file as named doesn't exist then add an extension if possible
        if os.path.exists(os.path.splitext(cfg_file)[0] + '.cfg'):
            cfg_file = os.path.splitext(cfg_file)[0] + '.cfg'
        else:
            print('filename {} does not exist.'.format(cfg_file))
            return None


    cfg = configparser.ConfigParser(allow_no_value=True,
                                    converters={'list': list_converter})

    cfg.read(cfg_file)
    cfg_dict = {}
    for l in cfg.sections():
        cfg_dict[l] = _ConfigSectionMap(l)

    if cfg_dict == {}:
        print('\ncfg_dict is empty but ' +\
              '{0} exists.'.format(os.path.basename(cfg)))
        print(' This usually occurs when the eol is set incorrectly. '+\
              'Unix eol characters are known to work.\n')
        cfg_dict = None

    return cfg_dict


def extract_specials(cfg_dict,specials = [],overwrite=False):
    """
    Extract special configuration keys and return

    :param cfg_dict: Configuration dictionary
    :type cfg_dict: dictionary
    :param specials: list of special strings to extract if they are present.
        Default is default_special_str. Any special strings given are appended
        to default_special_str rather than replacing it if overwrite is False.
    :type specials: list
    :params overwrite: If False [default] then any specials given in kwargs
        are appended to default_special_str. If True then only those strings
        included in specials are searched for.
    :type overwrite: boolean
    :returns: Dictionary of specials with keys of the special strings and
        input cfg_dict with special items removed. If no specials found then
        specials_dict will be {}.
    """
    #pdb.set_trace()
    if type(specials) in [str]:
        specials = [specials]

    if overwrite == False or len(specials) == 0:
        specials.extend(default_special_str)

    s_l = [s_.lower() for s_ in specials]

    specials_dict =  {k_:v_ for (k_,v_) in cfg_dict.items() if k_ in s_l}
    for k_ in specials_dict.keys():
        _ = cfg_dict.pop(k_)

    return cfg_dict, specials_dict