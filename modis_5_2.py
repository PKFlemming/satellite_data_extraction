""""
First, the wget scripts scrape the MODIS files from the NASA server.
Then this code extracts the AODb data from the MODIS hdf4 files and writes the data to csv
main steps:
1) read hdf4 file
2) extract geolocation and AODb fields
3) loop thru swath: if AODb <> no data, get lat,lon
The data in csv is then processed with the separate script AODbySeason.py to gather together data for each season
"""""

import os
import csv
import rasterio as rio # this is the .hdf reader
import itertools

# function to get paths to all files in directory, including those in subfolders
def list_files(dir):
    r = []
    for root, dirs, files in os.walk(dir):
        for name in files:
            r.append(os.path.join(root, name))
    return r

# column headings. AOD_blue column is 470 nm aerosol optical depth (the variable of interest)
headers = ["lat", "lon", "AOD_blue", "year", "day", "time"]
fileStartMarker = ".A20" # to help slice into file names and extract time stamp
scaleFactorFloat = 0.001 # scaling factor from Modis metadata, accurate to 10dp
                        # see article at https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4554528/
scaleFactorInt = 1      # used if int. output preferred for ease of analysis (scaleFactor 0.001 applied post-analysis)

def extractData(dir):
    finalSlash = dir.rfind("\\")
    csvName = dir[finalSlash + 1:] + ".csv"  # name of output csv file, corresponding to input directory
    corruptFileLog = "corruptFileLog" + csvName # keep a record of no. of corrupt files
                                                # specific corrupt files were identified and redownloaded separately
    corruptFileCount = 0
    with open(csvName, 'a', newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(headers)

        dayOld = 0 # set day marker to 0
        for file in list_files(dir): # iterate over all files in directory. These are the hdf4 files with AODb data.
            if not file.endswith(".hdf"):
                continue # skip over any non-data files

            fileStart = file.find(fileStartMarker) + 2  # slice in and find timestamp
            fileRef = file[fileStart:].replace(".", "") # filenames have a fairly consistent encoding of timestamp data
                                                        # ... but not 100 %. This standardises it.
            year = int(fileRef[:4])                     # extract timestamp data
            day = int(fileRef[4:7])
            time = int(fileRef[7:11])

            # Check if we're at the start of a new day. If we are, we log info about any corrupt files from the day
            # we just finished scanning
            if day != dayOld:                                       # this tells us if we're at the start of a new day
                corruptFileRecord = [dayOld, corruptFileCount]      # prepare the record about corrupt files
                # log the corrupt file count to the corrupt file log
                with open(corruptFileLog, 'a', newline="") as log_file:
                    logWriter = csv.writer(log_file)
                    logWriter.writerow(corruptFileRecord)
                print(corruptFileRecord)        # show cumulative count of corrupt files
            dayOld = day

            try:
                dataset = rio.open(file, "r")   # get the whole dataset out of the hdf4 file
            except:
                corruptFileCount += 1           # if data can't be accessed, log that file as corrupted...
                continue                        # ...and skip to next file

            # The dataset contains all data logged by the satellite at that time and location, including lots that is
            # irrelevant to us. We slice in and access the specific subdatasets that are useful.
            sdsPaths = dataset.subdatasets      # get all subdatasets from within dataset
            lonsPath = sdsPaths[111]            # get paths to the desired subdatasets (Longitude, latitude, Aerosol
                                                # Optical Depth (all bands)). These indices were found by
                                                # inspecting the hdf4 files with a GUI hdf viewer
            latsPath = sdsPaths[112]
            AODpath = sdsPaths[51]

            lons = rio.open(lonsPath, "r")      # access longitudes
            lonsArray = lons.read(1)            # read the data into an array
            lats = rio.open(latsPath, "r")      # same for latitudes
            latsArray = lats.read(1)
            AOD = rio.open(AODpath, "r")        # access AOD data. This contains all bands; we only want the blue band
            AODbArray= AOD.read(1)              # read band1 (470 nm AOD = blue band, AODb) into array

            # get dimensions of arrays. "Along" and "across" are the terms used to refer to the dimensions of the swath
            # of readings that the satellite stores in one file- a 2d path segment.
            # the swath has slightly different dimensions in different files- i.e., datadumps made at different times/
            # places- but the same shape for all variables within a file, so we can get the shape of any variable and
            # use it for all of them. Choice of lons is arbitrary.
            nAlong = lonsArray.shape[0]
            nAcross = lonsArray.shape[1]
            alongList = list(range(nAlong))
            acrossList = list(range(nAcross))
            # make 2d array with dimensions of combined along,across arrays- i.e, dimensions of swath
            swath = itertools.product(alongList, acrossList)
            # note: each data point has coordinates that locate it within the swath (along, across) and *also* has
            # coords that locate it on the globe (lat, lon). These are not the same. We use the along, across coords
            # to go into the arrays and get the data. The first array we go into w the along, across coords is the AODb
            # array. Then we use the same along, across coords to go into the lat and lon arrays to get out the
            # corresponding lat and lon coords.

            for along, across in (swath):               # iterate over pairs of along, across coordinates in swath
                AODb_raw = AODbArray[along][across]     # for each pair, get the AODb value from the AODb array
                if AODb_raw == -9999:                   # if it == the NoData value, skip to next along,across pair
                    continue
                # If it's not NoData, extract the data
                AODb = AODb_raw * scaleFactorInt
                                # this isn't relevant now, but for dev purposes it was useful to scale the AODb values
                lon = lonsArray[along][across]          # get lat and lon coords
                lat = latsArray[along][across]
                # check whether point is within Karnataka/Andhra Pradesh (AP data was extracted too, from curiosity)
                if ((74 < lon < 85) and (11.5 < lat < 19.5) or          # bounding box of Karnataka + AP
                        (69 < lon < 78.5) and (22.5 < lat < 30.5)):     # bounding box of Rajasthan
                    # if the data is within one of these boxes, write it to csv
                    row = [lat, lon, AODb, year, day, time]     # prepare data
                    writer.writerow(row)                        # write data to csv for mapping

    # write out the log of corrupt files
    corruptFileRecord = [day, fileRef, corruptFileCount]
    with open(corruptFileLog, 'a', newline="") as log_file:
        logWriter = csv.writer(log_file)
        logWriter.writerow(corruptFileRecord)

    return (f"final corrupt file count for {csvName} at end of day {day} of year {year} = {corruptFileCount}")

# location of input data files
# each of these directories contains numbered subfolders
# each subfolder corresponds to one day, and contains ~100 hdf4 files
# each hdf4 file contains data for one set of observations
dir1 = r"first\dir\path\goes\here"
### other dirs go here ###
dir10 = r"last\dir\path\goes\here"

dirs = [] # dirs to extract from

for dir in dirs:
    try:
        extractData(dir)
    except:
        print(f"extraction failed at this point in {dir}; continuing with next dir")
        continue
