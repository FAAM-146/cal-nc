"""
File containing all SEA WCM-2000 total water probe processor classes.
"""

from .generic import *


class WCM2000(Generic):
    """
    Class for parsing and processing of calibration data files for
    instrument::

        WCM2000: SEA WCM-2000 total water probe
    """

    def __init__(self,ds):
        """

        :param ds: dataset from ingested cal_nc file
        :type ds:  netCDF4.dataset
        """
        Generic.__init__(self,ds)


    def _add__str__(self):
        """
        Additional string describing this class and associated methods.

        This is used in addition to __str__ in the parent Generic() class
        when required. Generic.__str__ includes the docstr of this class
        plus that in self.update() if this method exists. If there are any
        other method docstrs or general text that may help with the usage of
        this class then they can be returned by this method.

        :returns: String
        """

        return ''


    def update(self,dvars,verbose=False):
        """
        Method to update attributes and variables of wcm2000 nc object

        :param dvars: Dictionary of attribute/variable key and value
            pairs. The dict keys are the attribute/variable name,
            including group paths relative to the root. Each dict either
            contains a scalar or iterable data value or, if applied to a
            variable (but not an attribute), a sub-dict that must
            include at least the key *'data'*. Other keys in the sub-dicts
            are attributes associated with that variable. The data value
            is a scalar or iterable to append to that attribute/variable.
            If a variable is given that does not already exist then it is
            ignored.
        :type dvars: dictionary
        :param verbose: If True then print info to stdout for each update.
            Default is False.
        :type verbose: boolean

        If the netCDF4 object ``self`` has only the following variables::

            float32 time(time)
                standard_name: time
                long_name: time of calibration

                time = 569., 669.;

            group /TWC:
                float32 r100(time)
                    long_name: TWC element resistance at 100deg C
                    units: milliohm

                float32 dtdr(time)
                    long_name: Change in TWC element resistance with temperature
                    units: deg C / milliohm

                r100 = 31.4473, 31.3362;
                dtdr = 33.9276, 33.8165;


        Then the following call,

        . .code-block:: python

            self.update({'time': 769,
                         'TWC/r100', {'data': 31.2251,
                                      'comment': 'Added comment'},
                         'TWC/dtdr', 33.7064})

        Shall result in the following nc structure::

            float32 time(time)
                standard_name: time
                long_name: time of calibration

                time = [569., 669. 769.];

            group /TWC:
                float32 r100(time)
                    long_name: 'TWC element resistance at 100deg C'
                    units: 'milliohm'
                    comment: 'Added comment'

                float32 dtdr(time)
                    long_name: 'Change in TWC element resistance with temperature'
                    units: 'deg C / milliohm'

                r100 = [31.4473, 31.3362, 31.2251];
                dtdr = [33.9276, 33.8165, 33.7064];

        Attribute and variables names may be given as strings, as in the example
        above or as the netCDF4 object variables. Efforts are made to coerse
        given variable data into the correct type, if this is impossible the
        update shall be ignored.
        """

        if dvars is None:
            return

        for var_name,var in dvars.items():

            if type(var) is dict:
                try:
                    var_data = var['data']
                except IndexError:
                    # Attribute/variable data does not exist
                    print("Must give 'data' key.")
                    pdb.set_trace()
            else:
                var_data = var

            # Determine current dimension length and expand variable along
            # that dimension by length of var being appended
            dim_name = self.ds[var_name].dims[0]
            dim_size = self.ds.dims[dim_name].size

            # Find dimension of variable data that corresponds to unlimited one
            dim_index = int(np.argwhere(np.atleast_1d(self.ds[var_name].shape) == dim_size))

            if verbose == True:
                curr_val = self.ds[var_name][:]
                print(var_name)
                print(curr_val)

            try:
                self.ds[var_name][dim_index+1::] = np.atleast_1d(np.asarray(var_data,
                                                             dtype=self.ds[var_name].dtype))
            except IndexError:
                # Attribute/variable does not exist
                continue
            except ValueError:
                # Cannot coerce the updated variables into the same type
                print('Update of {} cannot be coerced to type {}'.format(\
                         var_name, self.ds[var_name].dtype))
                continue

            if verbose == True:
                print(self.ds[var_name][:])
                print()
