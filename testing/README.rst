Testing Calibration netCDF
==========================

The ``/testing`` directory includes some files to test the code and any scripts that you write.

.. code-block:: console

    (cal-nc) user@pc:~\git\cal-nc$ python cal_ncgen.py fred.nc bob.cdl testing/PCASP1_cal_test-1.cdl testing/PCASP1_cal_test-2.cdl --update parsefile testing/PCASP1_testcals.cfg -u comment "testing stuff" -o testing/PCASP1_test.nc


This command does the following;

* Neither ``fred.nc`` nor ``bob.cdl`` exist so these files are ignored.
* The *master* input cdl file is ``PCASP1_cal_test-1.cdl``. A netCDF file shall be created from this and then subsequent calibration data shall be added/appended to it.
* The second input file, ``testing/PCASP1_cal_test-2.cdl`` contains additional data in existing variables and groups and this shall be appended to the *master* nc file. Groups and variables that do not already exist within the *master* shall be added to it.
* The ``--update`` argument ``parsefile`` indicates that the configuration file ``testing/PCASP1_testcals.cfg`` should be parsed using a PCASP1-specific  parser and the data added/appended to the *master* nc.
* An additional string in the root attribute ``comment`` shall be added to the *master* nc as long as it does not conflict with an existing attribute.
* With the ``-o`` argument, the output is saved to the netCDF file ``testing/PCASP1_test.nc``.


Have a go...


    .. todo::

        This should be in a sphinx-readable file and README.rst pointed to the resultant file.

