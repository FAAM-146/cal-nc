#! /usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
General utility functions. Primarily for file manipulation etc
"""


# import datetime, pytz
# import netCDF4
import os.path
# import shutil

import pdb

# import cal_proc
# from cal_proc import *
# from .nc_conf import *


__all__ = ['default_file_dir',
           'default_tmp_dir',
           'default_cdl_dir',
           'filepath']


# Default directories where files may be found
default_file_dir = ['.']

# Directory where temporary files are stored
default_tmp_dir = ['./tmp']

# Default directories where cdl file/s may be stored
# Searched in order
default_cdl_dir = ['.','cal_cdl']


def filepath(f,paths=default_file_dir):
    """
    Find path where file, f, exists. If does not exist then return f

    param f: String or filepath obj of file
    param paths: List of path strings to search. Default is default_file_dir

    returns: If valid file is found then this is returned. If no valid path
        is found then f is returned.
    """

    if isinstance(paths,(str)):
        paths = [paths]

    for p_ in paths:
        
        if os.path.isfile(os.path.abspath(os.path.join(p_,f))):
            return os.path.abspath(os.path.join(p_,f))
    
    return f



