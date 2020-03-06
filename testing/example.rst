
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
		-o PCASP_faam_20191107_v001_r000_cal.nc


Resultant `cal-nc`
~~~~~~~~~~~~~~~~~~

This results in the cal-nc file;

	`PCASP_faam_20191107_v001_r000_cal.nc <https://github.com/FAAM-146/cal-nc/blob/master/testing/PCASP_faam_20191107_v001_r000_cal.nc>`_

Reading this netCDF file with

.. code-block:: console

	ncdump PCASP_faam_20191107_v001_r000_cal.nc > PCASP_faam_20191107_v001_r000_cal.cdl

results in the `cdl` file;

	`PCASP_faam_20191107_v001_r000_cal.cdl <https://github.com/FAAM-146/cal-nc/blob/master/testing/PCASP_faam_20191107_v001_r000_cal.cdl>`_


.. literalinclude:: ../testing/PCASP_faam_20191107_v001_r000_cal.cdl
	:tab-width: 2


Appending to existing `cal-nc` file
-----------------------------------

Note that it is up to the user to ensure that data appended to an existing file
is sensible.

.. code-block:: console

    (cal-nc) user@pc:~/git/cal-nc$ python cal_ncgen.py '/smb/faam-two/data/Documents/Instruments/Cloud Physics/PCASPs/Calibrations/2019 calibrations/20191107_P2_postACSIS5/PCASP_faam_20191107_v001_r000_cal.nc'
        -u time 20200128
        -u applies_to C213
        --user="Graeme Nott <graeme.nott@faam.ac.uk>"
        --hist="<now> Cal for FAAM test flight"
        -u traceability "269nm (#166237). 303nm (#196947). 345nm (#199283). 401nm (#211099). 453nm (#166631). 510nm (#218477). 600nm (#213249). 702nm (#211842). 803nm (#209453). 903nm (#218704). 994nm (#200992). 1.101um (#212683). 1.361um (#199629). 1.592um (#204268). 1.745um (#205235). 2.020um (#181058). 2.10 um (#213339). 2.504um (#190272). 3.007um (#185943)."
        -u comment "Cal'd with PCASP-1"
        -u cal_flag 0
        -u parsefile '/smb/faam-two/data/Documents/Instruments/Cloud Physics/PCASPs/Calibrations/2020 calibrations/20200128_P1P2_calibration/P2_results/20200128_P2_cal_results_cs.csv'
        -o '/smb/faam-two/data/Documents/Instruments/Cloud Physics/PCASPs/Calibrations/2020 calibrations/20200128_P1P2_calibration/P2_results/PCASP-2_faam_20191107_v001_r001_cal.nc'



python cal_ncgen.py '/smb/faam-two/data/Documents/Instruments/Cloud Physics/PCASPs/Calibrations/2019 calibrations/20191107_P2_postACSIS5/PCASP_faam_20191107_v001_r000_cal.nc' -u time 20200128 -u applies_to C213 --user="Graeme Nott <graeme.nott@faam.ac.uk>" --hist="<now> Cal for FAAM test flight" -u traceability "269nm (#166237). 303nm (#196947). 345nm (#199283). 401nm (#211099). 453nm (#166631). 510nm (#218477). 600nm (#213249). 702nm (#211842). 803nm (#209453). 903nm (#218704). 994nm (#200992). 1.101um (#212683). 1.361um (#199629). 1.592um (#204268). 1.745um (#205235). 2.020um (#181058). 2.10 um (#213339). 2.504um (#190272). 3.007um (#185943)." -u comment "Cal'd with PCASP-1" -u cal_flag 0 -u parsefile '/smb/faam-two/data/Documents/Instruments/Cloud Physics/PCASPs/Calibrations/2020 calibrations/20200128_P1P2_calibration/P2_results/20200128_P2_cal_results_cs.csv' -o '/smb/faam-two/data/Documents/Instruments/Cloud Physics/PCASPs/Calibrations/2020 calibrations/20200128_P1P2_calibration/P2_results/PCASP-2_faam_20191107_v001_r001_cal.nc'

python cal_ncgen.py testing/PCASP1_cal_test-1.cdl -u parsefile testing/PCASP1_testcals.cfg --user="Fred <fred@fre.com>" --hist="<now> testing" -o testing/PCASP1_testcal20200306.nc
