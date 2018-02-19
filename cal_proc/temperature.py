"""
File containing all primary instrument temperature instrument processor
classes.
"""

from .generic import generic

class NDIT(generic):
    """
    Class for parsing and processing of calibration data files for
    instruments;

    NDIT
    Non-deiced temperature probe
    """

    def __init__(self,ds):
        """

        :param ds: dataset from ingested cal_nc file
        :type ds:  netCDF4.dataset
        """
        generic.__init__(self,ds)


    def update_options(self,**kargs):
        """
        Method to determine any other additional changes to the nc obj

        :param kargs: dictionary of optional arguments
        :type kargs: dictionary
        """
        pass

class DIT(generic):
    """
    Class for parsing and processing of calibration data files for
    instruments;

    DIT
    Deiced temperature probe
    """

    def __init__(self,ds):
        """

        :param ds: dataset from ingested cal_nc file
        :type ds:  netCDF4.dataset
        """
        generic.__init__(self,ds)

    def update_options(self,**kargs):
        """
        Method to determine any other additional changes to the nc obj

        :param kargs: dictionary of optional arguments
        :type kargs: dictionary
        """
        pass