
Example Creation of `cal-nc` File
=================================


Initial creation
----------------

The following command was used to create a `cal-nc` file for PCASP-2 using pre-ACRUISE and post-ARNA1 bin size calibrations and the sample flow calibrations from 8 May 2018.

.. code-block:: console

	(cal-nc) user@pc:~/git/cal-nc$ python cal_ncgen.py PCASP2_cal_template.cdl
		-u parsefile '/home/graeme/tmp/P2_cal/20191107_P2_cal.cfg'
		-u parsefile '/home/graeme/tmp/P2_cal/20180508PCASP2_flowcal.cfg'
		--user="Graeme Nott <graeme.nott@faam.ac.uk>"
		--hist="<now> Initial creation"
		-o PCASP-2_faam_20191107_v001_r000_cal.nc


Resultant `cal-nc`
~~~~~~~~~~~~~~~~~~

This results in the cal-nc file;

	`PCASP-2_faam_20191107_v001_r000_cal.nc <https://github.com/FAAM-146/cal-nc/blob/master/testing/PCASP-2_faam_20191107_v001_r000_cal.nc>`_

Reading this netCDF file with

.. code-block:: console

	ncdump PCASP-2_faam_20191107_v001_r000_cal.nc > PCASP-2_faam_20191107_v001_r000_cal.cdl

results in the `cdl` file;

	`PCASP_faam_20191107_v001_r000_cal.cdl <https://github.com/FAAM-146/cal-nc/blob/master/testing/PCASP_faam_20191107_v001_r000_cal.cdl>`_

the contents of which are;

.. literalinclude:: ../testing/PCASP-2_faam_20191107_v001_r000_cal.cdl
	:tab-width: 2


Appending to existing `cal-nc` file
-----------------------------------

Note that it is up to the user to ensure that data appended to an existing file
is sensible. This is especially true as it is possible for example to append diameter data for different particle refractive indices without any form of indication in the variable attributes.

.. code-block:: console

    (cal-nc) user@pc:~/git/cal-nc$ python cal_ncgen.py 'testing/PCASP-2_faam_20191107_v001_r000_cal.nc'
        -u bin_cal/time 20200128
        -u bin_cal/applies_to C213
        -u bin_cal/traceability "269nm (#166237). 303nm (#196947). 345nm (#199283). 401nm (#211099). 453nm (#166631). 510nm (#218477). 600nm (#213249). 702nm (#211842). 803nm (#209453). 903nm (#218704). 994nm (#200992). 1.101um (#212683). 1.361um (#199629). 1.592um (#204268). 1.745um (#205235). 2.020um (#181058). 2.10 um (#213339). 2.504um (#190272). 3.007um (#185943)."
        -u bin_cal/cal_flag 0
        -u bin_cal/cal_flag 1
        -u parsefile testing/20200128_P2_cal_results_PSLd.csv
        --user="Graeme Nott <graeme.nott@faam.ac.uk>"
        --hist="<now> Cal for FAAM test flight"
        -o 'testing/PCASP-2_faam_20191107_v001_r001_cal.nc'


This command will append the size calibration data from ``testing/20200128_P2_cal_results_PSLd.csv`` to that in ``testing/PCASP-2_faam_20191107_v001_r000_cal.nc`` and save the result as new revision of the same file ``testing/PCASP-2_faam_20191107_v001_r001_cal.nc``. Variables that are not included in the .csv file are included using the ``--update`` or ``-u`` option. Variable names given in this way must include the path to the variable in the netCDF, in this case the information in the calibration csv file should go in the ``bin_cal`` group. Note that multiple ``--update``'s of a single variable are acceptable as shown for the ``bin_cal/cal_flag`` variable. However as only as single calibration source csv has been given the second one is ignored.

