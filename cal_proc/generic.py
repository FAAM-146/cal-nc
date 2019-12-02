#! /usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Generic instrument class.
"""


import datetime, pytz
import numpy as np
import os.path
import netCDF4

import pdb


def walk_dstree(ds):
    """Recursive Dataset group generator.

    from: http://unidata.github.io/netcdf4-python/netCDF4/index.html#section2

    Args:
        ds (:obj:`netCDF4.Dataset`): Dataset
    """
    values = ds.groups.values()
    yield values
    for value in ds.groups.values():
        for children in walk_dstree(value):
            yield children


def append_time(otime,ntime,concat_axis=0):
    """Appends time variable/s to existing time coordinate.

    Note that increasing the size of the ``time`` coordinate also increases the
    size of all of the dependent variables.

    Args:
        otime (:obj:`netCDF4.Variable`): Original Dataset time coordinate. As
            is coordinate dimensionality is 1d.
        ntime (:obj:`netCDF4.Variable` or `iterable`): New time variables to
            append to `otime`. May either be a netCDF4 variable or a simple
            iterable of values. These values may be datetime objects. If the
            values are strings some attempt to convert them will be done. If
            they are numbers then it is assumed that units and calendar are
            compatible with those in `otime`.

    Returns:
        A netCDF4 variable with the same units and calendar as `otime`.
    """

    import datetime

    time_fmts = ['%Y%m%dT%H:%M:%S.%f','%Y-%m-%dT%H:%M:%S.%f',
                 '%Y%m%dT%H:%M:%S',   '%Y-%m-%dT%H:%M:%S',
                 '%Y%m%dT%H:%M',      '%Y-%m-%dT%H:%M',
                 '%Y%m%dT%H',         '%Y-%m-%dT%H',
                 '%Y%m%d',            '%Y-%m-%d']

    # Convert original times into datetime objects
    try:
        ocalendar = otime.calendar
    except AttributeError:
        ocalendar = 'standard'

    try:
        odatetime = netCDF4.num2date(otime[:],otime.units,ocalendar)
    except IndexError:
        # num2date does not work on empty arrays
        odatetime = np.array([])

    if type(ntime) == netCDF4.Variable:
        # Convert new times into datetime objects
        try:
            ncalendar = ntime.calendar
        except AttributeError:
            ncalendar = 'standard'

        try:
            ndatetime = netCDF4.num2date(ntime[:],ntime.units,ncalendar)
        except IndexError:
            # num2date does not work on empty arrays
            ndatetime = np.array([])

    else:
        if isinstance(ntime,(int,float,str)):
            ntime = np.array([ntime])

        if (type(ntime[0]) == str) or (ntime.dtype.kind in ['U','S']):
            # Attempt to convert the times into a list of datetime object
            # Assume that all formats are the same!
            for t_fmt in time_fmts:
                try:
                    _ = datetime.datetime.strptime(ntime[0],t_fmt)
                except ValueError:
                    pass
                else:
                    break

                # Reverse date part of t_fmt
                try:
                    indx = t_fmt.index('T')
                except ValueError:
                    t_fmt = t_fmt[::-1]
                else:
                    t_fmt = t_fmt[:indx][::-1]+t_fmt[indx:]

                try:
                    _ = datetime.datetime.strptime(ntime[0],t_fmt)
                except ValueError:
                    continue
                else:
                    break

            print('t_fmt = ',t_fmt)
            ndatetime = [datetime.datetime.strptime(n_,t_fmt) for n_ in ntime]

        else:
            # Assume are numbers in same format as those in otime
            ndatetime = netCDF4.num2date(ntime,otime.units,ocalendar)


    adatetime = np.ma.concatenate((odatetime,ndatetime),axis=concat_axis)

    return netCDF4.date2num(adatetime,otime.units,ocalendar)


class Generic():
    """Parent class for general instrument parsing and processing.

    Generic forms the basis for all specific instrument processor classes.
    """

    def __init__(self,ds):
        """

        Args:
            ds (:obj:`netCDF4.Dataset`): Dataset from ingested cal_nc file

        .. note::

            I don't think that this is actually true anymore...

            Note that cal_nc file as been read using r+. Thus variables (?)
            and attributes cannot be appended to. Values must be read to
            a python variable, the nc key deleted, then rewritten with
            appropriate modfications.

        """
        self.ds = ds


    def __str__(self):
        """
        Help, specifically with regards to structure of update() method if
        it exists. If update() does not exist then use docstr of processor
        class __init__()

        .. todo::

            This needs to be updated

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


    def update_ver(self):
        """Includes program version information as root attribute.

        Version information is determined from ``cal_proc.__init__()``.
        Any existing version strings shall be overwritten.
        """

        from cal_proc import __version__

        self.ds.software_version = __version__


    def update_hist(self,update=None):
        """Updates the global history attribute.

        The history nc attribute is a single string of comma-delineated text.

        Args:
            update (:obj:`str` or :obj:`list`): Update for history string.
                If None (default) then auto-generate string based on today's
                datetime. If given then append update/s to history attribute
                string. Any ``<now>`` or ``<today>`` strings are changed to
                today's datetime.
        """

        # With datetime v3.6 can use timespec='seconds' to drop ms
        # Timezone aware timestamp is generated by default.
        t_ = datetime.datetime.now(pytz.utc).replace(microsecond=0).strftime('%Y%m%dT%H%M')

        if update is None:
           update = '{} Auto update'.format(t_)

        elif update is 'NA':
            # This assumes that all updates have been handled in the cdl
            # file. So nothing needs to be done here.
            update = ''

        elif hasattr(update,'__iter__') and type(update) not in [str]:
            # If is a list of strings then join
            update = ', '.join(update[:])

        # Change any shortcuts to today's date
        update = update.replace('<today>',t_).replace('<now>',t_)

        try:
            hist_ = self.ds.history
        except AttributeError as err:
            # username attribute does not exist so create it
            self.ds.history = update
        else:
            # username attribute already exists to append to end of string
            del(self.ds.history)
            if hist_ in ['',None]:
                self.ds.history = update
            else:
                self.ds.history = '{}, {}'.format(hist_,update)


    def update_user(self,update=None):
        """Updates the global username attribute.

        The username nc attribute is a single string of comma-delineated text.

        Args:
            update (:obj:`str` or :obj:`list`): Update for username string.
                If None (default) then auto-generate string based on previous
                entries in netCDF and ask user. String usually given as
                `username <user@email>`. Append username/s to existing attribute
                string.
        """

        # Extract existing username from ds
        try:
            user_ = self.ds.username
        except AttributeError as err:
            # username attribute does not exist so create it
            user_ = None
            last_user_ = None
        else:
            last_user_ = user_.split(',')[-1].strip()

        if update in ['',None]:
            # No username given so use last entry from nc if possible but
            # confirm with user
            if last_user_ in ['',None]:
                while update in ['',None]:
                    update = input("\nEnter 'username <email>': ").strip()
            else:
                update = input("\nEnter 'username <email>' [enter for {}]: ".format(last_user_)).strip()
                if update == '':
                    update = last_user_
        # elif update is 'NA':
        #     # This assumes that all updates have been handed in the cdl
        #     # file. So nothing needs to be done here
        #     update = ''

        elif hasattr(update,'__iter__') and type(update) not in [str]:
            # If is a list of strings then join
            update = ', '.join(update[:])

        if user_ in ['',None]:
            self.ds.username = update
        else:
            # username attribute already exists to append to end of string
            del(self.ds.username)
            self.ds.username = '{}, {}'.format(user_,update)


    def change_val(self,var,old_val,new_val):
        """Changes a single variable/attribute value.

        The variable or attribute name must be given along with the old
        value, ``old_val``, that is to be change to ``new_val``. If ``old_val``
        is not found then nothing is done.

        .. todo::

            Not implemented

        """

        pass


    def _add_coord(self,coord,vals):
        """Adds extra values to end of an unlimited coordinate.

        If a coordinate is increased in size then all of the variables that
        depend on that coordinate are increased to the same size along the
        unlimited dimension. This internal method should usually be followed by
        ``_add_var()``.

        Args:
            coord (:obj:`str`): string of path/name of coordinate variable. This
                can be found with
                ``os.path.join(self.ds[coord].group().path,self.ds[coord].name)``
            vals (`iterable`): Iterable of values to append to the end of
                ``self.ds[coord]``. Type must match the dtype of the coordinate
                variable.
        """

        # Ensure that is unlimited coordinate
        # Annoyingly have to split path and variable name
        cpath,cname = os.path.split(coord)

        if cpath in ['','/']:
            unlim = self.ds.dimensions[cname].isunlimited()
        else:
            unlim = self.ds[cpath].dimensions[cname].isunlimited()

        if (self.ds[coord].ndim != 1) or \
           (self.ds[coord].name != self.ds[coord].dimensions[0]) or \
           (unlim is False):
            # Either the variable name passed is not a coordinate (ie the
            # variable name and dimension are the same and 1d) or the
            # coordinate is not unlimited and thus cannot be extended.
            print('{} is not an unlimited coordinate'.format(coord))
            return -1

        # Ensure vals is an array and preserve any masking
        vals = np.ma.atleast_1d(vals)

        try:
            self.ds[coord][:] = append_time(self.ds[coord],vals,0)
        except Exception as err:
            print(err)
            pdb.set_trace()

        return 0


    def _add_var(self,var,vals):
        """Adds extra values to end of an already extended variable.

        If a coordinate is increased in size then all of the variables that
        depend on that coordinate are increased to the same size along the
        unlimited dimension. If the variable holds numbers then these extra
        values are masked. If the variable holds strings then they are just
        empty strings and there is no masking. This method writes the new
        values in vals into these new array positions of var. If the
        number of values is > number of new elements at the end of the
        array then it is assumed that there is an error and no action is taken.

        Args:
            var (:obj:`str`): string of path/name of variable. This
                can be found with
                ``os.path.join(self.ds[var].group().path,self.ds[var].name)``
            vals (`iterable`): Iterable of values to append to the end of
            ``self.ds[var]``. Type must match the dtype of the variable.
        """

        # Ensure vals is an array and preserve any masking
        vals = np.ma.atleast_1d(vals)

        if vals.ndim == self.ds[var].ndim - 1:
            # Assume that only a single element in the unlimited dimension
            # has been given in vals. Increase number of dimension to match var
            # This assures (?) that 0 axis is the unlimited one...
            vals = np.expand_dims(vals[::],axis=0)

        assert vals.ndim == self.ds[var].ndim, \
               'Mismatch in number of dimensions'

        # Annoyingly have to split path and variable name
        vpath,vname = os.path.split(var)

        # Find unlimited dimension for this var
        for i,d_ in enumerate(self.ds[var].dimensions):
            try:
                unlim_dim = self.ds[vpath].dimensions[d_].isunlimited()
            except IndexError as err:
                # Assume this is because you're in the root
                unlim_dim = self.ds.dimensions[d_].isunlimited()

            if unlim_dim:
                break

        try:
            _ = unlim_dim
        except NameError as err:
            print(err)
            print('Variable {} does not have unlimited dimension'.format(var))
            return

        # Create slice to write to the correct dimension
        # That is the last elements of the unlimited dimension

        # .. TODO::
        #   Need to check that this works for adding more than one new value
        if self.ds[var].ndim == 1:
            idx = slice(-1*len(vals),None)
        else:
            idx = [slice(None)] * self.ds[var].ndim

            # Don't use slice obj as I can't work out what is going on!
            idx[0] = -1#slice(-1,None)
            idx[1] = range(len(vals[0]))#slice(None,len(vals[0]))


        if (self.ds[var].dtype in [str]) and \
           ((self.ds[var][idx] == '').all()):
            # Strings are vlen arrays which have more limited access
            # Need to write each individual string seperately (?)
            for i,val in enumerate(vals[::-1]):
                self.ds[var][-1*(i+1)] = val

        elif any((self.ds[var][idx].mask.all(),
                  np.isfinite(self.ds[var][idx].base).all())):
            # Assume that all other types of variables are masked
            try:
                self.ds[var][idx] = vals[0]
            except Exception as err:
                print('Variable: {}'.format(var))
                print(err)
                pdb.set_trace()

        else:
            print('Insufficient empty space in {}!'.format(var))


    def append_var(self,var,coord_vals,var_vals):
        """
        Method to append to an existing netCDF4 variable and associated coord

        .. todo::

            Redundant/not currently used.

        The extra coordinate values are appended to the coordinate of vname
        in self. This automatically creates the same number of masked entries
        in all of the variables that depend on that coordinate.

        :param var: String of path/name of variable. This can be found with
            ``os.path.join(self.ds[var].group().path,self.ds[var].name)``
        :type var: String
        :param coord_vals: Iterable of values to append to the end of unlimited
            coordinate of variable var.
        :type coord_vals: List or array
        :param var_vals: Iterable of values to append to the end of var. Must
            be the same length as coord_vals in the unlimited dimension.
        :type var_vals: List or array

        .. note::

            This is a bit complicated/not sensible. It is possible/probable
            to add a variable (along with the coord) then append to a different
            variable that uses the same coordinate which then writes the same
            coordinate values into the coordinate again.
        """

        # # Find unlimited dimension of variable
        # for i,dim_ in enumerate(var.dimensions):
        #     if var.isunlimited():
        #         break

        # if type(nvar) == netCDF4.Variable:
        #     # Extract values out of variable
        #     nvars = nvar[:]
        # elif isinstance(nvar,(int,float,str)):
        #     # Ensure that new variables is a list if not a netCDF4 variable
        #     nvars = [nvar]

        # if ovar.dtype == str:
        #     avar = ovar.rstrip(',') + ','.join(nvars)
        # else:
        #     avar = np.ma.concatenate((ovar[:],nvars), axis=i)


    def append_dict(self,var_d):
        """Appends multiple variables with a single coordinate.

        Multiple variable values that use the same coordinate can be appended
        to existing dataset variables in one go. Variables that do not already
        exist in the dataset are ignored. Use add instead...

        Args
            var_d (:obj:`dict`): Dictionary of multiple variable values to be
                appended. Dictionary keys are the variable path+name strings
                and the dictionary values are either a netCDF variable or a
                sub-dictionary of values and attributes

        .. todo::

            Currently does not accept netCDF4 variable values.
            Currently only accepts iterable of data.

        .. code-block:: python

            var_d = {coord: netCDF4.Variable,
                     var1:  [1,2,3,4,5],
                     var2:  {'_data': [1,2,3,4,5],
                             'var2_attr1': 'var2 attribute 1',
                             'var2_attr1': 'var2 attribute 1', ...}
                     var3:  'Fred'}

        Note that all variables should be the same length if they are
        list-like. Any variables not the same length as the maximum length
        variable will be broadcast so that they are longer. This could well
        have unintended concequences however it does mean that variables that
        are the same thing repeated for all coordinate values (eg var3)
        will be replicated automatically.

        .. NOTE::

            This is not done yet!

        There is nothing special about the coordinate variable, the function
        identifies the coordinate as being the variable with the same name
        as its dimension.
        """

        # Find coordinate variable
        coord_d = {}
        var_keys = list(var_d.keys())
        for k_ in var_keys:
            try:
                if self.ds[k_].name == self.ds[k_].dimensions[0]:
                    coord_d[k_] = var_d.pop(k_)
            except IndexError as err:
                # Variable does not exist in dataset so remove from var_d
                _ = var_d.pop(k_)

        for k_,v_ in coord_d.items():
            err = self._add_coord(k_,v_)
            if err == -1:
                return -1

        for k_,v_ in var_d.items():
            try:
                self._add_var(k_,v_)
            except Exception as err:
                print('Variable: {}'.format(k_))
                print(err)
                pdb.set_trace()



    def append_dataset(self,ds,
                       force_append=['username','history'],
                       exclude=[]):
        """Adds groups, attributes, dimensions, and variables from ds.

        Attributes of ``self.ds`` shall take priority over those of the same
        name in `ds`, such attribute values of `ds` shall be ignored. The
        exception is if the attribute key is included in ``force_append``. In
        this case the resultant attribute shall be a comma-delineated
        combination string of the individual attributes with that from ``ds``
        being appended to that of ``self.ds``.

        Variables from ``ds`` are appended to the same variable in ``self``. The
        variables are sorted by the unlimited dimension. Variables only in
        ds shall be added to ``self``.

        Any groups, attributes, or variables in ``ds`` that are not to be
        added or appended can be specified as a list with `exclude`.

        Args:
            ds (:obj:`netCDF4.Dataset`) netCDF Dataset to add into ``self.ds``
            force_append (:obj:`list`): List of any root or group attribute
                strings that should always be appended to, even if they are
                identical. Default is ['username','history']. Group attribule
                strings must include full path.
            exclude (:obj:`list`): List of attribute or variable name strings
                (but not variable attributes) that are not to be added or
                appended to.

        """


        def append_group(mgrp,ngrp):
            """Updates master ds group with values from new ds group.

            Either input may be a dataset, in which case the root group is
            operated on, or a group/subgroup within the dataset. This function
            does not walk down through any subsequent groups.

            Args:
                mgrp (:obj:`netCDF4.Dataset`): Master dataset object which may
                    be root or a group.
                ngrp (:obj:`netCDF4.Dataset`): Dataset object the contents of
                    which shall be added or appended to those in the master
                    dataset object.
            """

            # Add any new attributes, ignore any conflicts, string append any others
            new_attrs = {k_:v_ for (k_,v_) in ngrp.__dict__.items() \
                         if k_ not in mgrp.ncattrs()}
            app_attrs = {k_:v_ for (k_,v_) in ngrp.__dict__.items() \
                         if (k_ in mgrp.ncattrs() and v_ != mgrp.getncattr(k_) and k_ in force_append)}

            mgrp.setncatts(new_attrs)

            for k_,v_ in app_attrs.items():
                if mgrp.getncattr(k_) == '':
                    app_attr = ngrp.getncattr(k_)
                else:
                    app_attr =  ', '.join([mgrp.getncattr(k_)[::],
                                           ngrp.getncattr(k_)])
                mgrp.setncattr_string(k_,app_attr)

            # Add any new dimensions
            new_dim = {d_:v_ for (d_,v_) in ngrp.dimensions.items() if d_ not in mgrp.dimensions}
            mgrp.dimensions.update(new_dim)

            # Add any new variables
            new_var = {n_:v_ for (n_,v_) in ngrp.variables.items() \
                       if n_ not in mgrp.variables}
            mgrp.variables.update(new_var)

            # Concatenate any variables along the unlimited dimension
            # that exist in master already. Do this in two steps as operating
            # directly on the dataset coordinate/s affects the dependent
            # variables immediately.
            # Note that new/changed variable attributes are not added.

            for n_ in ngrp.variables.keys():
                try:
                    fred = np.array_equal(ngrp.variables[n_][:],
                                      mgrp.variables[n_][:])
                except:
                    print('Error with array_equal')
                    pdb.set_trace()

            app_var = {n_:v_ for (n_,v_) in ngrp.variables.items() \
                       if all([n_ in mgrp.variables,
                               not np.array_equal(ngrp.variables[n_][:],
                                                  mgrp.variables[n_][:])])}

            mod_var = {}
            for n_,v_ in app_var.items():

                # Find unlimited dimension
                for i,d_ in enumerate(mgrp.variables[n_].dimensions):
                    if mgrp.dimensions[d_].isunlimited():
                        break

                # Convert datetime stamps to datetime then back again ensuring
                # units are those of the master group.
                # Determine if timestamp with variable name and units that
                # include 'since'. A bit flakey but hopefully ok.
                if all(['time' in n_.lower(),
                        'units' in mgrp.variables[n_].ncattrs()]) \
                   and 'since' in mgrp.variables[n_].units.lower():

                    mod_var[n_] = append_time(mgrp.variables[n_],
                                              ngrp.variables[n_])

                else:

    ### TODO: Use pint to make sure any units in variables are comparable
    ###       and convert new variables to those used in master

                    mod_var[n_] = np.ma.concatenate((mgrp.variables[n_][:],
                                                     ngrp.variables[n_][:]),
                                                    axis=i)

            # Write modified variables back into master
            for n_,v_ in mod_var.items():
                mgrp.variables[n_][:] = v_


        # Determine path strings to all (sub-)groups in both datasets
        mgrps = []
        for grps in walk_dstree(self.ds):
            mgrps.extend([g_.path for g_ in grps])

        ngrps = []
        for grps in walk_dstree(ds):
            ngrps.extend([g_.path for g_ in grps])

        # Determine groups that are in the new dataset that are not in the master
        # Create an equivalent empty group in the master, group will be filled
        # by calling append_dsgroup(). Sort list by length of string so
        # create upper level groups before any sub-groups.
        for grp in sorted(set(ngrps).difference(mgrps),key=len):
            self.ds.createGroup(grp)

        # Copy any new root attributes, dimensions, and/or variables to master
        append_group(self.ds,ds)

        # Do the same for all groups and sub-groups
        for grp in ngrps:
            append_group(self.ds[grp],ds[grp])



