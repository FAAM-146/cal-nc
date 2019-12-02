"""
Import all cal parser functions
"""

from . import generic
from . import temperature
from . import wcm2000
from . import pcasp


# Project information
__title__ = 'FAAM Calibration netCDF'
__description__ = 'Creation/updates of nc files for FAAM calibration data'
__institution__ = 'FAAM - Facility for Airborne Atmospheric Measurements'
__version__ = '0.3'
__author__ = 'Graeme Nott'
__author_email__ = 'graeme.nott@faam.ac.uk'
__copyright__ = '2019, FAAM'


# List of data reader modules in reader/
__all__ = ['generic',
           # Primary instruments
           'temperature', 'wcm2000',
           # Core cloud physics
           'pcasp']

# ----------------------------------------------------------------------
def proc_map(instr):
    """Maps raw instrument nickname string to the appropriate processing class.

    Function to map instrument nickname string to the appropriate
    instrument processing class. This string may be given as a global
    nc attribute or with the ``--instr=instr`` option of cal_ncgen.

    Args:
        instr (:obj:`str`): Unique instrument identification string,
            case-insensitive.

    Returns:
        Class object relating to instrument or None if no match.
    """

    # Map of instrument names to processing classes
    # Each list of strings can have many instr strings. However, each
    # of these strings must be unique within proc_map.
    proc_map = {}

    # Primary instruments
    proc_map[temperature.DIT] = ['DIT']       # Deiced temperature
    proc_map[temperature.NDIT] = ['NDIT']     # Non-deiced temperature
    proc_map[wcm2000.WCM2000] = ['WCM-2000','WCM2000','SEA']

    # Core cloud physics
    proc_map[pcasp.PCASP] = ['PCASP','PCASP-1','PCASP-2','PCASP-X',
                             'PCASP1','PCASP2','PCASPX']

    # Search proc_map dictionary for exact match to instr string.
    # Will only return the first instance.
    for k,v in proc_map.items():
        if instr.lower() in [v_.lower() for v_ in v]:
            return k

    return None
