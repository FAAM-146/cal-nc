#! /usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
General utility functions. Primarily for file manipulation etc
"""

import os.path
import pdb


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
    """Finds path where file, f, exists from selection of paths.

    Single filename is given and the complete path for this file is found
    from a list of possible locations. If does not exist then return f.
    Note that if the file exists in two locations then the paths list carries
    with it the order of priority, only a single file is returned.

    Args:
        f (:obj:`str` or :obj:`pathlib`): Complete or part filename.
        paths (:obj:`list`): List of path strings to search. Default is
        ``default_file_dir``.

    Returns:
        If valid file is found the complete path/filename is returned. If no
        valid path is found then `f` is returned.
    """

    if isinstance(paths,(str)):
        paths = [paths]

    for p_ in paths:
        
        try:
            if os.path.isfile(os.path.abspath(os.path.join(p_,f))):
                return os.path.abspath(os.path.join(p_,f))
        except TypeError as err:
            print(err)
            return f

    return f



