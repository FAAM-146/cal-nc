"""
File containing all PCASP instrument processor classes.
"""

from .generic import Generic
import os.path
import numpy as np
import pdb


# Map cal file variable names to nc variables
var_map = {'bin_cal/ADC_thres':
                lambda d: np.ma.dstack((d['data']['Lower Thresholds'],
                                        d['data']['Upper Thresholds'])),
           'bin_cal/x-section':
                lambda d: np.ma.dstack((d['data']['Lower Cross Section Boundaries'],
                                        d['data']['Upper Cross Section Boundaries'])),
           'bin_cal/x-section_err':
                lambda d: np.ma.dstack((d['data']['Lower Cross Section Boundary Errors'].base,
                                        d['data']['Upper Cross Section Boundary Errors'].base)),
           'bin_cal/x-section_width':
                lambda d: d['data']['Width of Cross Section Boundaries'],
           'bin_cal/x-section_width_err':
                lambda d: d['data']['Width of Cross Section Boundary Errors'],
           'bin_cal/dia_centre':
                lambda d: d['data']['Channel Centre'],
           'bin_cal/dia_centre_err':
                lambda d: d['data']['Channel Centre Errors'],
           'bin_cal/dia_width':
                lambda d: d['data']['Channel Widths'],
           'bin_cal/dia_width_err':
                lambda d: d['data']['Channel Width Errors'],
           'bin_cal/calibration_file':
                lambda d: d['metadata']['cal file'],
           'bin_cal/source_file':
                lambda d: d['metadata']['input file']
           }


class PCASP(Generic):
    """Parses and processes calibration data files for instrument: PCASP.

        **PCASP:** Passive Cavity Aerosol Spectrometer Probe

    """


    def __init__(self,ds):
        """

        Args:
            ds (:obj:`netCDF4.dataset`): Dataset from ingested netCDF file.
        """

        Generic.__init__(self,ds)


    def update(self,largs):
        """Make any change to the pcasp object.

        Args:
            largs (:obj:`list`): List of lists of arbitrary arguments to apply
                to nc

        .. todo::

            This is actually not used and looks hella complicated. Change so
            is more useful?

        Examples:

            .. warning::

                These usage examples are now out of date.

            The ``largs`` list is from

            .. code-block:: console

                $ python cal_ncgen.py --update option

            and may be one of the following types;

            * A list [of lists] of cdl files of data to be written into the nc
              object. This option is chosen based on extension ``.cdl``. If more
              than one cdl file is offered then it must be given as a single
              entry. eg;

              .. code-block:: console

                $ python cal_ncgen.py -u PCASP_20170725.cdl PCASP_20171114.cdl

            * A list [of lists] of PCASP diameter calibration files output from
              ``cstodconverter``. This option is chosen based on filename ending
              with ``d.csv``. If more than one calibration file is offered then
              it must be given as a single entry. eg;

              .. code-block:: console

                $ python cal_ncgen.py -u 20170725_P1_cal_results_PSLd.csv 20171114_P1_cal_results_PSLd.csv

            * A list nc attribute/value or variable/value pairs. For attributes
              that are strings, the value is concatenated to the existing string
              with a delimiting comma (non-char attributes will probably throw
              an error). Variables will be appended to the end of the existing
              variable numpy array. Note that variable attributes cannot be
              appended to. The attribute/variable names must be given exactly as
              in the existing nc file. Any containing group/s is given with
              forward slashes, eg

              .. code-block:: console

                $ python cal_ncgen.py -u bin_cal/time 2769 2874 -u bin_cal/applies_to C027-C055 C057-C071 2818.5, 2864.5

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


    def update_bincal_from_file(self,cal_file,vars_d):
        """Appends bin calibration data in calibration file to that in nc file.

        Args:
            cal_file (:obj:`str` or :obj:`pathlib`): Filename of calibration
                PCASP calibration csv file to be read. Is recognised as
                ending in 'cs' or 'd' so user needs to provide some quality
                assurance on the input files.
            vars_d(:obj:`dict`): Dictionary of any additional variables
                associated with those contained within the datafile. At the very
                least this should contain any associated coordinate variables,
                eg `time`.
        """
        from . import reader

        if (cal_file == None) or (os.path.isfile(cal_file) == False):
            # Nothing to do
            return

        caldata = None
        if all((os.path.splitext(cal_file)[0].endswith('cs'),
               os.path.splitext(cal_file)[1].lower() == '.csv')):
            caldata = reader.opc_calfile(cal_file,f_type='pcasp_cs')
        elif all((os.path.splitext(cal_file)[0].endswith('d'),
                 os.path.splitext(cal_file)[1].lower() == '.csv')):
            caldata = reader.opc_calfile(cal_file,f_type='pcasp_d')

        if caldata == None:
            # Error in the cal_file
            return

        # Add var_map data to vars. However do not overwrite any items in var
        # That is, items explicitly given in config file have precedence over
        # items in var_map. This can be used to overwrite defaults in var_map
        # with an entry in the config file if required.
        #print('Variables passed to update_bincal_from_file() in vars_d:')
        #for k in vars_d.keys(): print(k)
        #print()
        for k,v in ((k_,v_) for k_,v_ in var_map.items() if k_ not in vars_d):
            try:
                vars_d[k] = v(caldata)
            except KeyError as err:
                # Variable in var_map does not exist in file therefore skip
                #pdb.set_trace()
        #        print('{} not found in {}'.format(k,os.path.basename(cal_file)))
                pass
            except Exception as err:
                print('  Failed. ',err)
                pdb.set_trace()
                pass
            else:
                pass
        #        print('Add {} to self.ds'.format(k))

        try:
            msg = self.append_dict(vars_d)
        except Exception as err:
            print('err: {}'.format(err))
            pdb.set_trace()

