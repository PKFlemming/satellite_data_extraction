# satellite_data_extraction
The two scripts here were used to  
1) extract Aerosol Optical Depth data from Nasa satellite data dumps  (modis_5_2.py)
2) collate that data by season (AODbySeason.py)
The data was then mapped in ArcGIS and Moving Window Regression (MWR) was used to analyse it, along with other candidate variables. MWR code can be found [here](https://github.com/PKFlemming/MovingWindowRegression), as can the dissertation that presents the findings. Please note that this dissertation was one sixth of an undergrad degree, and the AOD data comprised one of more than a dozen variables analysed, so this code values function far above form.

Data sourced from [LAADS DAAC](https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/61/MOD04_L2/). Instructions on wget commands to use for bulk access are also provided there.
