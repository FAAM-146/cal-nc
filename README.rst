Calibration netCDF
==================

Introduction:
-------------
To present calibration data in a consistant manner, to facilitate archiving of the data, and include traceability information and references, data is stored in a netCDF file of a specified structure. netCDF has been chosen as, although it is perhaps unnecessarily complicated for this application, it is commonly used for instrument data and is self-describing. The structure is flexible enough to hold many different types of instrument calibration information. The quantity of calibration information stored within the files will almost certainly be quite small so size and read/write speed are not a priority. Additionally, it is possible to insert these files into a netCDF4 data file as a sub-group and thus keep data and calibration together.

A full specification can be found in FAAM technical document FAAM000003, "Calibration netCDF Structure".

The proposed structure has been set with several central tenets in mind;

#. There is a single calibration file for each instrument,

#. A single instrument may require several different calibrations in order to produce calibrated data. These different aspects of the calibration are contained within separate groups within the same netCDF file,

#. A single file holds a time series of comparable calibrations,

#. The calibration and measurement data files each are contain references to the other. The data file should contain a boolean variable indicating whether the calibration has already been applied,

#. Calibrations are traceable by the inclusion of calibration metadata,

#. Future expansion and instruments can be accommodated.


File Structure:
---------------
The file is divided into groups, the top level being the root and containing attributes that apply to contents of the entire file. This metadata contains information about the institution as well as the instrument covered by the file.

Global attributes
    Attributes that apply to the entire file contents, these are defined by the conventions. Contains information about where the data was produced, references, instrument information, dates of calibrations, and a history of file versions.

Calibration groups
    Separate calibration information are placed in different groups.

Array dimensions for calibration data are organised so that with each new calibration that is added to the file, the datetime dimension increases by one. Second and tertiary dimensions are set by the requirements of the instrument calibration parameters.

First dimension - time
    This is the unlimited dimension. This dimension is expanded each time a calibration is added to the file, which may be once a year or numerous times a flight.

Second dimension - cal
    This is a fixed dimension for the calibration information. For example, this may be a list of three parameters for a cubic fit or a list of thirty bin threshold values.

Further dimensions - vector
    These are fixed dimensions for any additional information. For example if the thirty bin thresholds have two parameters that describe a straight line fit.


netCDF Construction
===================

Templates for calibration netCDF files are done by hand in cdl. This is a text equivalent of the binary netCDF. For some instruments, the amount of calibration data may be so small that it can all be included in the cdl. For other instruments the data can be included in other files. These other files may be cdl with the correct variables as defined in the primary cdl or they may be any other file. These ancillary files are read in seperately and the data written into variables of the calibration netCDF that is created with the cdl template.

CDL templates:
--------------
There are at least two cdl files required. These and any others are combined to produce the final calibration netCDF.

Instrument cdl 1
    The top level instrument cdl has convention, institution, and instrument metadata that are written as netCDF global attributes. Convention and institution metadata are fixed. Instrument metadata applies to the entire file and includes instrument name/s, serial number, references, etc. Groups may be included in this file if there are multiple types of calibration for the same instrument. The primary coordinate is *time*, this may be a global attribute if it applies to all groups or may be a group coordinate if more appropriate.

Instrument cdl *n*
    Auxillary instrument cdl file/s can be written. These may be used if the quantity of data becomes unwieldy for a single file. These should not replicate attributes and dimensions of the primary cdl file but include data variables.

Ancillary files:
----------------
It may be that the quantity or dimensionality of calibration data makes it unwieldy to write into the cdl file by hand. In these situations it is easier to write the calibration data into another type of file and use a customized parser to ingest this data, massage it into the appropriate form, and write it into the netCDF. If this is the case the parser and processor of the ancillary data is included in the instrument processing class.

Script summary:
---------------

Mandatory script argument is either cdl or nc file.

* If cdl a new nc file will be created using the cdl as a template
* If nc then new data is appended into the file

If more than one cdl file is given then they shall be concatenated, there is little error checking besides removing the start and end braces. It is up to the user to ensure no conflicts etc.

If the input is cdl then ncgen is run to create an nc file [#fnote-direct_ncgen_call]_.

This nc file is then read in with the netCDF4 module. The instrument nickname is extracted from the resulting datasets global 'instr' attribute amd this is used to instantiate the appropriate class for that instrument. The simplest class is 'generic' which has methods for appending history and username information and that is all. All other classes inherit from generic and may include other methods to parse from ancillary files and and write this data into the nc file. This parsing will be highly specific to an instrument, thus the individual classes.

.. highlights::

    name:
        cal_ncgen.py

    description:
        Script to assist in the creation of calibration netCDF files.

    version:
        0.1

    python version:
        3.4

    author:
        Graeme Nott <graeme.nott@faam.ac.uk>

    created:
        Jan 2018

.. [#fnote-direct_ncgen_call] This means that a user can completely by-pass the use of this script and call ncgen directly on a user-generated cdl file. This is by design as it allows greater flexibility.