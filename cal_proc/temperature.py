"""
File containing all primary instrument temperature instrument processor
classes.

.. todo::
    
    This needs significant work

"""

from .generic import Generic

class NDIT(Generic):
    """Parses and processes calibration data files for instrument::

        NDIT: Non-deiced temperature probe
    """

    def __init__(self,ds):
        """
        
        Args:
            ds (:obj:`netCDF4.dataset`): Dataset from ingested netCDF file.
        """
        Generic.__init__(self,ds)


    def update(self,dvars):
        """Updates attributes and variables of ndit nc object.

        Args:
            dvars (:obj:`dict`): 
        """
        if dvars is None:
            return

        pass

class DIT(Generic):
    """Parses and processes calibration data files for instrument::

        DIT: Deiced temperature probe
    """

    def __init__(self,ds):
        """

        Args:
            ds (:obj:`netCDF4.dataset`): Dataset from ingested netCDF file.
        """
        Generic.__init__(self,ds)


    def update(self,dvars):
        """Updates attributes and variables of ndit nc object.

        Args:
            dvars (:obj:`dict`): 
        """
        if dvars is None:
            return

        pass