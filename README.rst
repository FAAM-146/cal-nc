Calibration netCDF
==================


Calibration Data Background:
----------------------------

Instrument calibration is an integral part of scientific operations at FAAM as part of the mission to provide the highest level of quality assurance with measurements. The calibration procedures, traceability, and data itself must be provided to the end user in a manner that is clear, robust, and linked with the measurement data to which it applies. Instrument calibration parameters to date have been dealt with in a somewhat piecemeal manner and as such clarity in particular has been reduced for the user.

Core primary instrument calibrations are generally held in a text file called the flight constants file. There is a unique file for each flight and the file contains all of the parameters that are applied to the raw data to convert them to physical units as contained within the FAAM core netCDF. Some instrument data, such as those contained within the core cloud physics netCDF, does not have calibrations applied. The relevant calibration data is supplied separately for the user to apply. These calibration text files are stored on the FAAM website and emailed out to users.


Introduction:
-------------
To present calibration data in a consistant manner, to facilitate archiving of the data, and include traceability information and references, data is stored in a netCDF file of a specified structure. netCDF has been chosen as, although it is perhaps unnecessarily complicated for this application, it is commonly used for instrument data and is self-describing. The structure is flexible enough to hold many different types of instrument calibration information. The quantity of calibration information stored within the files will almost certainly be quite small so size and read/write speed are not a priority. Additionally, it is possible to insert these files into a netCDF4 data file as a sub-group and thus keep data and calibration together.

The proposed structure has been set with several central tenets in mind;

#. There is a single calibration file for each instrument,

#. A single instrument may require several different calibrations in order to produce calibrated data. These different aspects of the calibration are contained within separate groups within the same netCDF file,

#. A single file holds a time series of comparable calibrations,

#. The calibration and measurement data files each are contain references to the other. The data file should contain a boolean variable indicating whether the calibration has already been applied,

#. Calibrations are traceable by the inclusion of calibration metadata,

#. Future expansion and instruments can be accommodated.


Calibration files
^^^^^^^^^^^^^^^^^
The idea is that each instrument has its own calibration file [#fnote-multi_instr_nc]_, the filename shall follow current FAAM conventions with a structure such as::

    instr_faam_YYYYDDMM_v001_r000_cal.nc

where ``instr`` is a unique string identifier for each instrument, ``v001`` refers to the version of the software that produced the netCDF, and ``r000`` gives the revision of the file.


Calibration groups
^^^^^^^^^^^^^^^^^^
Some instruments may require different calibrations that are then both applied to the raw data within the processing software. An example of this is the PCASP; currently a calibration is applied to the flow meters readings plus a calibration is applied to the particle size bin boundaries. These two calibrations may be done at different times and they may be applied to the data at different times. Different calibrations are given in different groups within the same file. 

Time series data
^^^^^^^^^^^^^^^^
Each file contains a time series of calibrations as long as these calibrations are comparable [#fnote-noncomparable_cals]_.  Calibrations are held in an array with an unlimited dimension that is time/date of calibration.

This way it is straight forward to detect changes in comparable calibrations over time and also not to compare calibrations that are not comparable. For example if the instrument undergoes a sensor upgrade, comparing calibrations from before and after this hardware change is not meaningful.

Data and calibration referencing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
It is important that calibration information is easily linked to those datasets to which it applies and that the end user of the dataset understands whether the calibrations have already been applied or not. These are possibly quite difficult to satisfy depending on the instrument.

In each calibration group there is a variable called ``APPLIES_TO`` which has an entry for each calibration time in the series that points to the applicable measurement data to which this calibration data has been or should be applied to. 

Traceability
^^^^^^^^^^^^
Traceability of calibrations, calibration materials, and procedures is vital for user confidence in the data that FAAM provides. The calibration netCDF has to hold this information within the file. This may include certificates provided by manufacturers or third party calibration facilities, descriptions of procedures or links to these that detail the methods used, and/or references to papers or textbooks that serve as the basis of the procedures.

The structure provides several layers of references. In the root of the calibration netCDF file are global attributes ``references`` and ``readme``, these apply to all calibration information within the entire file and so are necessarily general. Within the root of each calibration group there is a ``references`` attribute that provides direct textual information or a link to an external reference detailing the calibration procedure relevant to that calibration group.

Most specifically, there is a ``TRACEABILITY`` variable within each calibration group that provides, for each calibration time, any information specific to that individual calibration. These may include images of calibration certificates for materials or equipment used, links to parent calibration netCDF files, name of the person carrying out the calibration, etc.


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

This nc file is then read in with the netCDF4 module. The instrument nickname is extracted from the resulting datasets global ``instr`` attribute amd this is used to instantiate the appropriate class for that instrument. The simplest class is ``generic`` which has methods for appending history and username information and that is all. All other classes inherit from generic and may include other methods to parse from ancillary files and and write this data into the nc file. This parsing will be highly specific to an instrument, thus the individual classes.


.. [#fnote-multi_instr_nc] Having only a single instrument will mean a lot of almost empty files for many of the primary instruments. It may be possible to combine many such calibrations in a single calibration file through the use of links.
.. [#fnote-noncomparable_cals] An exception to this may be when instrument calibrations are never comparable.
.. [#fnote-direct_ncgen_call] This means that a user can completely by-pass the use of this script and call ncgen directly on a user-generated cdl file. This is by design as it allows greater flexibility.