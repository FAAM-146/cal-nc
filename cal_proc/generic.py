

import datetime, pytz


class Generic():
    """
    Minimal parent class for instrument-specific parsing and processing
    of calibration data suitable for writing to the calibration netCDF.
    """

    def __init__(self,ds):
        """

        :param ds: dataset from ingested cal_nc file
            Note that cal_nc file as been read using r+. Thus variables (?)
            and attributes cannot be appended to. Values must be read to
            a python variable, the nc key deleted, then rewritten with
            appropriate modfications.
        :type ds:  netCDF4.dataset
        :returns ds:
        """
        self.dataset = ds


    def __str__(self):
        """
        Help, specifically with regards to structure of update() method if
        it exists. If update() does not exist then use docstr of processor
        class __init__()
        """

        # To print name of instance use: type(self).__name__
        import pdb

        h1 = self.__doc__

        try:
            h2 = h1 + '\n' + self.update.__doc__
        except AttributeError:
            pdb.set_trace()
            h2 = h1

        try:
            h3 = h2  + '\n' + self._add__str__()
        except AttributeError:
            pdb.set_trace()
            h3 = h2

        return h3


    def update_hist(self,update=None):
        """
        Update the global history attribute with today's date string
        The history attribute is a single string of comma-delineated
        substrings.

        :param update: Update for history string. If None (default) then
            auto-generate string based on today's date. If 'NA' then do
            nothing. Else add update to history attribute.
        :type update: String
        """

        if update is None:
            # With datetime v3.6 can use timespec='seconds' to drop ms
            # Timezone aware timestamp is generated by default.
            t_ = \
            datetime.datetime.now(pytz.utc).replace(microsecond=0).isoformat()
            update = '{} Auto update'.format(t_)

        if update is 'NA':
            # This assumes that all updates have been handled in the cdl
            # file. So nothing needs to be done here.
            pass
        else:
            hist_ = self.dataset.history
            del(self.dataset.history)
            self.dataset.history = '{}, {}'.format(hist_,update)


    def update_user(self,update=None):
        """
        Update the global username attribute with current username string.
        The username attribute is a single string of comma-delineated
        substrings.

        :param update: Update for username string. If None (default) then
            ask user, usually given as 'username <user@email>'. If 'NA'
            then do nothing.
        :type update: String
        """

        if update is None:
            # May be able to automatically generate a username but
            # ask user to be sure.
            update = input('\nEnter username <email> [Enter for cdl]: ')
            if update == '':
                # Assume that user wants to use data already in cdl
                update = 'NA'

        if update is 'NA':
            # This assumes that all updates have been handed in the cdl
            # file. So nothing needs to be done here
            pass
        else:
            user_ = self.dataset.username
            del(self.dataset.username)
            self.dataset.username = '{}, {}'.format(user_,update)

