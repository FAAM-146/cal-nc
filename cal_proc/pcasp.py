"""
File containing all PCASP instrument processor classes.
"""

from .generic import Generic
import os.path
import numpy as np
import pdb


# Map cal file variable names to nc variables
var_map = {'bin_cal/ADC_thres': lambda d: np.vstack((d['Lower Boundaries'].base,
                                                     d['Lower Boundaries'].base)),

           'bin_cal/x-section': lambda d: np.vstack((d['Lower Cross Section Boundaries'].base,
                                                     d['Upper Cross Section Boundaries'].base)),
           'bin_cal/bin_cal/x-section_err': lambda d: np.vstack((d['Lower Cross Section Boundary Errors'].base,
                                                                 d['Upper Cross Section Boundary Errors'].base)),
           'bin_cal/x-section_width': lambda d: d['Width of Cross Section Boundaries'],
           'bin_cal/x-section_width_err': lambda d: d['Width of Cross Section Boundary Errors'],
           'bin_cal/dia_centre': lambda d: d['Channel Centre'],
           'bin_cal/dia_centre_err': lambda d: d['Channel Centre Errors'],
           'bin_cal/dia_width': lambda d: d['Channel Widths'],
           'bin_cal/dia_width_err': lambda d: d['Channel Width Errors']}


# -----------------------------------------------------------------------------
def read_cal_file(cal_file,f_type='pcasp_d',reject_bins=None,invalid=-9999):
    """
    Function to read in csv files outputted from various calibration programs

    The output format is defined for different types of files.
    Data is returned in a dictionary.

    .. NOTE::
        This has been ripped straight from datafile_utils.py. Probably
        can do this better.

    :param cal_file: path and filename of calibration csv file to be read
    :type cal_file: string
    :param f_type: type of calibration file to read. One of;
                    'pcasp_d': output of CDtoDConverter.exe
                    'pcasp_cs': output of pcaspcal.exe
                    'cdp_d': output of CDtoDConverter.exe
                    'cdp_cs': output from ADs calibration program
    :type f_type: string
    :param reject_bins: List of bins that are not returned. Default is None
    :type reject_bins: list of integers
    :param invalid: Gives value of invalid values as used by input csv file.
                    Default is -9999
    :type invalid: string or number

    :return d: dictionary of metadata and data masked arrays
    """

    import csv, os.path
    import numpy



    # List of known types for help
    valid_types = {'pcasp_d':   'output of CDtoDConverter.exe [default]',
                   'pcasp_cs':  'output of pcaspcal.exe',
                   'cdp_d':     'output of CDtoDConverter.exe [default]',
                   'cdp_cs':    'output of CDP calibration program'}


    # Initialise dictionary
    d = {'metadata': {},
         'data'    : {}}


    def read_row_with_heading(line=''):
        '''
        Read comma-delineated row that starts with a heading and return the
        heading as a string and the row of data as an array
        '''

        # Strip off white space and extra commas
        # Split into heading and data
        row = line.strip().strip(',').split(',',1)

        if row[0].strip() is '':
            return None, None

        if len(row) == 1:
            return row[0], None

        try:
            # Try to create a list of numbers
            data = [float(v) for v in row[1].split(',') if v.strip() != '']
        except ValueError:
            # Create a list of strings
            data = [v.strip() for v in row[1].split(',') if v.strip() != '']
        else:
            # Mask invalid array entries but need to cope with float('NaN')
            data = numpy.ma.masked_invalid(data,invalid)
            data = numpy.ma.masked_values(data,invalid)

        return row[0], data


    if f_type.lower() in ['pcasp_d','cdp_d']:
        # The file formats for cdp and pcasp diameter files are identical
        # Input file is from CDtoDConverter.exe
        # Format is;
        # Line 1: Input filename
        # Line 2: Mie table filename
        # Line 4-13: Table of values, one row for each of the bins

        d['metadata']['cal file'] = os.path.abspath(cal_file)

        f = open(cal_file, 'r')

        # Read metadata at top of file
        line = f.readline()
        while line.strip() != '':
            # Read the metadata, is seperated from data table by blank line
            [k,v] = line.split(':',1)
            d['metadata'][k.strip()] = v.strip()
            line = f.readline()

        # Read the rest of the file
        line = f.readline()
        while line != '':
            # For some reason may get an extra ',' at the end thus double strip
            l = line.strip().strip(',').split(',')

            # Create masked array where masked values are invalid value
            for i in range(1,len(l)):
                # Loop through line and convert to numbers
                try:
                    l[i] = float(l[i])
                except ValueError:
                    if '-1.#IND' in l[i]:
                        # This is a C++ indeterminant. Convert to 'invalid' so
                        # is masked but print warning to user as this may
                        # signify problems with cal processing.
                        l[i] = invalid
                        print(
                    "\nWARNING: '-1.#IND' converted to {0}".format(invalid))
                        print(' File: {}\n'.format(os.path.basename(cal_file)))
                    else:
                        print('\nUnknown character encounted: {}'.format(l[i]))
                        print(' File: {}\n'.format(os.path.basename(cal_file)))
                        print(' Line: ',l)
                        print()
                        pdb.set_trace()
                except Exception as err:
                    print(err)
                    print(' File: {}\n'.format(os.path.basename(cal_file)))
                    pdb.set_trace()

            d['data'][l[0]] = numpy.ma.masked_equal(l[1:],invalid)

            line = f.readline()

        # Create array of bin numbers *** Starting at 1 ***
        d['data']['bin'] = numpy.arange(len(d['data']['Channel Centre'])) + 1

        # Close file
        f.close()


    elif f_type.lower() == 'pcasp_cs':
        # Input file is from pcaspcal.exe.

        d['metadata']['cal file'] = os.path.abspath(cal_file)
        d['data']['raw data'] = {}
        d['data']['Straight line fits'] = {}

        f = open(cal_file, 'r') # originally 'rb' for some reason

        # Read metadata at top of file
        # Read any empty/extra lines at top of file

        line = f.readline()
        while not line.strip().lower().startswith(\
                                      'data files used for calibration:'):
            #pdb.set_trace()
            line = f.readline()

        # Read through all data files used to create calibration
        d['metadata']['input files'] = []
        while line.strip() != '':
            # Read the metadata, is seperated from data table by blank line
            d['metadata']['input files'].append(line.strip())
            line = f.readline()

        # Find column headings for raw data table.
        # Problem is that currently (Sept2012) the first column heading is
        # misspelt Partricle Diameter (micron)'. So match characters 'P','D',
        # and '(' at beginning of line incase it is corrected in future.
        def find_headings(l):
            '''Put in func as need a try/except'''
            try:
                return l.split()[0].startswith('P') & \
                       l.split()[1].startswith('D') & \
                       l.split()[2].startswith('(')
            except:
                return False

        while find_headings(line) is False:
            line = f.readline()

        # Create list keys from headings. Ignore any extra ',' at end of line
        # Plus some headings seem to have an additional space at end
        headings = [h.strip() for h in line.strip().split(',') \
                    if h.strip() != '']

        for h in headings:
            d['data']['raw data'][h] = []

        # Read in the raw data table, is seperated from fits by blank line
        line = f.readline()
        while line.strip() != '':

            # 'Mode Channel (1-28)' data (row 10) may be non-integer which
            # generally means that histogram peak could not be found so was
            # not used in fitting procedure. Don't include this row in arrays
            try:
                tmp = int(line.split(',')[10])
            except:
                # Line has some non-int string so go onto next line
                pass
            else:
                for v,h in zip(line.strip().rstrip(',').split(','),headings):
                    # Columns of raw data have the following headings
                    # Partricle Diameter (micron),+/- (micron),
                    # Standard Deviation (micron),Particle Composition ,
                    # Refractive Index,
                    # Scattering Cross Section (micron squared),
                    # +/- (micron squared),Start Time (hh:mm:ss),
                    # End Time (hh:mm:ss),Date (yyyymmdd),Mode Channel (1-28),
                    # Mode Voltage (A-D counts),+/- (A-D counts)

                    d['data']['raw data'][h.strip()].append(v)
            finally:
                line = f.readline()

        # Sort out variable types in the raw data table and convert to arrays
        for h_i in [0,1,2,5,6,11,12]:
            # Convert folowing columns to arrays of floats;
            # 'Partricle Diameter (micron)', '+/- (micron)',
            # 'Standard Deviation (micron)',
            # 'Scattering Cross Section (micron squared)',
            # '+/- (micron squared)', 'Mode Voltage (A-D counts)',
            # '+/- (A-D counts)'
            d['data']['raw data'][headings[h_i]] = \
                numpy.array(d['data']['raw data'][headings[h_i]],dtype=float)

        for h_i in [4]:
            # Convert following columns to array of complex numbers
            # 'Refractive Index'

            # Create a 2d list of real and img parts of each number
            tmp = [c.rstrip('i').split('+') for \
                   c in d['data']['raw data'][headings[h_i]]]

            # Then convert tuples into complex numbers
            d['data']['raw data'][headings[h_i]] = \
                   numpy.array([complex(float(r),float(i)) for (r,i) in tmp])

        for h_i in [10]:
            # Convert the following columns to arrays of integers
            # 'Mode Channel (1-28)'
            try:
                d['data']['raw data'][headings[h_i]] = \
                numpy.array(d['data']['raw data'][headings[h_i]],dtype=int)
            except:
                pdb.set_trace()

        for h_i in [3,7,8,9]:
            # Convert the remaining columns to arrays of strings
            d['data']['raw data'][headings[h_i]] = \
                numpy.array(d['data']['raw data'][headings[h_i]],dtype=str)

        # Sort the raw data in terms of aerosol size
        sort_i = numpy.argsort(d['data']['raw data']\
                               ['Partricle Diameter (micron)'])

        for k in headings:
            d['data']['raw data'][k] = d['data']['raw data'][k].take(sort_i)

        # Skip any blank lines
        while line.strip() != 'Straight line fits':
            line = f.readline()

        # Read lines that contain raw input data
        # Read the straight line fit data
        line = f.readline()
        while not line.startswith('Lower Thresholds'):
            # Straight line fit data is separated from bin table by blank line
            [k,l] = read_row_with_heading(line)
            if k is not None:
                d['data']['Straight line fits'][k] = l

            line = f.readline()

        # Skip over empty lines
        while line.strip() == '': line = f.readline()

        # Read bin data and put into arrays
        while line.strip() != '':
            # Read through to the end of file
            [k,l] = read_row_with_heading(line)
            if k is not None:
                d['data'][k] = l

            line = f.readline()

        # Create array of bin numbers *** Starting at 1 ***
        d['data']['bin'] = numpy.arange(len(d['data']['Lower Thresholds'])) + 1

        # Close file
        f.close()

    elif f_type.lower() == 'cdp_cs':
        # Input file is from ADs CDP calibration program/s.

        d['metadata']['cal file'] = os.path.abspath(cal_file)
#        d['data']['raw data'] = {}
        d['data']['Straight line fits'] = {}

        f = open(cal_file, 'rb')

        # Read any empty/extra lines at top of file
        line = f.readline()
        while line.strip() == '':
            line = f.readline()

        # Read through metadata
        while not line.title().startswith('Straight Line Fits'):
            # Discard empty lines
            [k,l] = read_row_with_heading(line)
            if k is not None:
                d['metadata'][k] = l

            line = f.readline()

        # Read the straight line fit data
        line = f.readline()
        while not line.title().startswith('Lower Thresholds'):
            # Straight line fit data is separated from bin table by blank line
            [k,l] = read_row_with_heading(line)
            if k is not None:
                d['data']['Straight line fits'][k] = l

            line = f.readline()

        # Read bin data and put into arrays
        while line.strip() != '':
            # Read through to the end of file
            [k,l] = read_row_with_heading(line)
            if k is not None:
                d['data'][k] = l

            line = f.readline()

        # Create array of bin numbers *** Starting at 1 ***
        d['data']['bin'] = numpy.arange(len(d['data']['Lower Thresholds']))+1

        # Close file
        f.close()


    else:
        print('\nUnknown calibration file type:')
        print('{0} Valid types are;'.format(os.path.basename(cal_file)))
        for k,v in valid_types.items():
            print(' {0}\t{1}'.format(k,v))

        print()
        d = None


    # Return arrays of only bins required
    if reject_bins is not None:

        try:
            del_bins = numpy.asarray(reject_bins,dtype=int)
        except:
            # Something happened
            pdb.set_trace()

        # Find bins to remove
        del_bins_i = numpy.where(numpy.in1d(d['data']['bin'],del_bins))[0]
        len_bins = d['data']['bin'].shape

        # Loop through all data arrays and delete offending elements
        # Note that metadata and raw data arrays are left unmodified

        for k,v in d['data'].items():
            try:
                v.shape == len_bins
            except:
                continue
            else:
                d['data'][k] = numpy.delete(v,del_bins_i)

    return d




class PCASP(Generic):
    """
    Class for parsing and processing of calibration data files for
    instrument::

        PCASP: Passive Cavity Aerosol Spectrometer Probe
    """


    def __init__(self,ds):
        """

        :param ds: dataset from ingested cal_nc file
        :type ds:  netCDF4.dataset
        """
        Generic.__init__(self,ds)

        # datafiles is included in kargs and is not none and is relevant to
        # bin calibration


    def update(self,largs):
        """
        Method to make any change to the nc object

        :param largs: List of lists of arbitrary arguments to apply to nc

        The *largs* list is from

        :Example:

        >>> cal_ncgen.py --update *option*

        and may be one of the following types;

        * A list [of lists] of cdl files of data to be written into the nc
          object. This option is chosen based on extension ``.cdl``. If more than
          one cdl file is offered then it must be given as a single entry. eg;

          :Example:

          >>> cal_ncgen.py -u PCASP_20170725.cdl PCASP_20171114.cdl

        * A list [of lists] of PCASP diameter calibration files output from
          ``cstodconverter``. This option is chosen based on filename ending
          with ``d.csv``. If more than one calibration file is offered then it
          must be given as a single entry. eg;

          :Example:

          >>> cal_ncgen.py -u 20170725_P1_cal_results_PSLd.csv 20171114_P1_cal_results_PSLd.csv

        * A list nc attribute/value or variable/value pairs. For attributes
          that are strings, the value is concatenated to the existing string
          with a delimiting comma (non-char attributes will probably throw
          an error). Variables will be appended to the end of the existing
          variable numpy array. Note that variable attributes cannot be
          appended to. The attribute/variable names must be given exactly as
          in the existing nc file. Any containing group/s is given with
          forward slashes, eg

          :Example:

          >>> cal_ncgen.py -u bin_cal/time 2769 2874 -u bin_cal/applies_to C027-C055 C057-C071 2818.5, 2864.5

        Note that any spaces in filenames must be enclosed in quotes. All
        files are assumed to the same type as the first filename in the list.

        """

        if largs is None:
            return

        # Loop over outer list and determine action based on first element
        for larg in largs:

            if os.path.splitext(larg[0])[1] == 'cdl':
                # Auxillary cdl file/s
                #######
                # Do something with cdl files
                pass

            elif os.path.splitext(larg[0])[0].endswith('d') and \
                 os.path.splitext(larg[0])[1] == 'csv':
                # PCASP calibration file/s
                update_bincal(larg)

            elif larg[0] in self.ds:
                # Attribute/variable contained within nc object

                #####
                # Do something here to get attrib or var then append
                pass



    def update_bincal(self,datafiles):
        """
        Append bin calibration data in datafile/s to that already in nc

        :param datafiles: list of strings of path/filename
        """



        if datafiles == None:
            # Nothing to do
            return

        for dfile in datafiles:
            pdb.set_trace()
            if os.path.isfile(dfile):
                if os.path.splitext(datafiles[0])[0].endswith('cs'):
                    data = read_cal_file(dfile,f_type='pcasp_cs')
                elif os.path.splitext(datafiles[0])[0].endswith('d'):
                    data = read_cal_file(dfile,f_type='pcasp_d')
                else:
                    # Ignore unrelated file
                    pass

                # Append data to ds
                pdb.set_trace()
                #self.ds.

