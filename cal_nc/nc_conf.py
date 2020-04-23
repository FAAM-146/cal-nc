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


def read_config(cfg_file, de_str=True):
    """Read in configuration file and return entries in dictionary.

    ConfigParser options used are;

        * allow_no_value=True

    Args:
        cfg_file (:obj:`str` or :obj:`pathlib`): Configuration path/filename
            with the required format.
        de_str (:obj:`bool`): If True [default] then attempt to de-string string
            entries.

    Returns:
        Dictionary with sub-dictionaries for each section or None if
            ``cfg_file`` cannot be found.
    """

    # Manual configuration converters
    def _list_converter(s):
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

    def _convert_time(s):
        """ Converts a datetime string into a datetime object

        """
        from dateutil import parser

        try:
            return parser.parse(s, dayfirst=True)
        except ValueError as err:
            raise err


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
            if option.lower() in ['time']:
                # Make sure time entries stay as strings
                cfg_d[option] = cfg.get(section, option)
                continue
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

            # Attempt to convert 'none' strings to None
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
                                    converters={'list': _list_converter,
                                                'datetime': _convert_time})
    cfg.read(cfg_file)
    cfg_dict = {}
    for l in cfg.sections():
        cfg_dict[l] = _ConfigSectionMap(l,not(de_str))

    if cfg_dict == {}:
        print('\ncfg_dict is empty but ' +\
              '{0} exists.'.format(os.path.basename(cfg)))
        print(' This usually occurs when the eol is set incorrectly. '+\
              'Unix eol characters are known to work.\n')
        cfg_dict = None

    return cfg_dict


def extract_specials(cfg_dict,specials = [],overwrite=False):
    """Extracts special configuration keys from dictionary and returns them.

    Args:
        cfg_dict (:obj:`dict`): Configuration dictionary
        specials (:obj:`list`): list of special strings to extract if they are
            present in ``cfg_dict``. Default is ``default_special_str``. Any
            special strings given are appended to ``default_special_str`` rather
            than replacing it as long as ``overwrite`` is False.
        overwrite (:obj:`bool`): If False [default] then any strings given in
            ``specials`` are appended to ``default_special_str``. If True then
            only those strings included in ``specials`` are searched for.

    Returns:
        Tuple of two dictionaries. Dictionary of specials found in ``cfg_dict``
            with keys of the special strings. Dictionary of ``cfg_dict`` with
            special items removed. If no specials found then ``specials_dict``
            will be {}.
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