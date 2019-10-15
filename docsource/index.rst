
FAAM Calibration netCDF documentation
=====================================

This document defines the netCDF file structure for storage of instrument calibration information as used by FAAM - the Facility for Airborne Atmospheric Measurements. These files provide traceability for all instrument calibrations, the linking of calibration information with applicable instrument data, and relevant calibration metadata all within a framework suitable for archival.

    .. tabularcolumns:: |r|l|

    .. list-table::
        :header-rows: 0
        :align: left
        :widths: auto

        * - Project
          - |ProjectTitle|
        * - Description
          - |ProjectDescription|
        * - Project version
          - |ProjectVersion|
        * - Python version
          - |PythonVersion|
        * - Author
          - |ProjectAuth| <|ProjectEmail|>
        * - Created
          - Jan 2018
        * - Modified
          - |todays_date|


Documentation
-------------

.. toctree::
    :maxdepth: 2
    :glob:

    readme


Functions and Modules
---------------------

.. toctree::
    :maxdepth: 2
    :glob:

    /_autosummary/cal_cdl
    /_autosummary/cal_ncgen
    /_autosummary/cal_proc*


.. |todays_date| date::