"""
File containing all primary instrument temperature instrument processor
classes.
"""

from .generic import Generic

class NDIT(Generic):
    """
    Class for parsing and processing of calibration data files for
    instruments::

        NDIT: Non-deiced temperature probe
    """

    def __init__(self,ds):
        """

        :param ds: dataset from ingested cal_nc file
        :type ds:  netCDF4.dataset
        """
        Generic.__init__(self,ds)


    def update(self,largs):
        """
        Method to determine any other additional changes to the nc obj

        :param kargs: dictionary of optional arguments
        :type kargs: dictionary
        """
        if largs is None:
            return

        pass

class DIT(Generic):
    """
    Class for parsing and processing of calibration data files for
    instruments::

        DIT: Deiced temperature probe
    """

    def __init__(self,ds):
        """

        :param ds: dataset from ingested cal_nc file
        :type ds:  netCDF4.dataset
        """
        Generic.__init__(self,ds)

    def update(self,largs):
        """
        Method to determine any other additional changes to the nc obj

        :param kargs: dictionary of optional arguments
        :type kargs: dictionary
        """
        if largs is None:
            return

        pass