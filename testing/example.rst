
Example Creation of `cal-nc` File
=================================

The following command was used to create a `cal-nc` file for PCASP-2 using pre-ACRUISE and post-ARNA1 bin size calibrations and the sample flow calibrations from 8 May 2018.

.. code-block:: console

	(cal-nc) user@pc:~/git/cal-nc$ python cal_ncgen.py '/home/graeme/tmp/P2_cal/20191107_P2_cal.cdl'
		-u parsefile '/home/graeme/tmp/P2_cal/20191107_P2_cal.cfg'
		-u parsefile '/home/graeme/tmp/P2_cal/PCASP2_flowcal.cfg'
		--user="Graeme Nott <graeme.nott@faam.ac.uk>"
		--hist="20191129T0957 Initial creation"
		-o PCASP_faam_20191107_v001_r000_cal.nc


Resultant `cal-nc`
------------------

This results in the cal-nc file;

	`PCASP_faam_20191107_v001_r000_cal.nc <../testing/PCASP_faam_20191107_v001_r000_cal.nc>`_

Reading this netCDF file with

.. code-block:: console

	ncdump PCASP_faam_20191107_v001_r000_cal.nc > PCASP_faam_20191107_v001_r000_cal.cdl

results in the `cdl` file;

	`PCASP_faam_20191107_v001_r000_cal.cdl <../testing/PCASP_faam_20191107_v001_r000_cal.cdl>`_


.. literalinclude:: ../testing/PCASP_faam_20191107_v001_r000_cal.cdl
	:tab-width: 2
