# Import all cal parser functions

from .generic import *
from .temperature import *
from .PCASP import *

# List of data reader modules in reader/
__all__ = ['generic',
        # Primary instruments
           'NDIT', 'DIT',
        # Core cloud physics
           'PCASP']

# ----------------------------------------------------------------------
def proc_map(instr):
    """
    Map raw instrument nickname string to the appropriate processing class.

    Function to map instrument nickname string to the appropriate
    instrument processing class. This string may be given as a global
    nc attribute or with the --instr=instr option of cal_ncgen.__main__().

    :param instr: Unique instrument identifying string, case-sensitive
    :type instr: string
    :returns k: Class object relating to instrument or None if no match
    """

    # Map of instrument names to processing classes
    # Each list of strings can have many instr strings. However, each
    # of these strings must be unique within rmap.
    proc_map = {PCASP:      ['PCASP','PCASP-1','PCASP-2','PCASP-X',
                             'PCASP1','PCASP2','PCASPX'],
                NDIT:       ['NDIT'],
                DIT:        ['DIT']}

    # Search proc_map dictionary for exact match to instr string.
    # Will only return the first instance.
    for k,v in proc_map.items():
        if instr in v:
            return k

    return None