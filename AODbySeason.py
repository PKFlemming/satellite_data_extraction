import os
import csv

""" 
modis_5_2.py extracts the AODb data (including lat, lon, date and time) from the hdf4 files and writes it to csv
This script takes those csvs as input and gathers data by season. This is necessary because dust levels in the monsoon
are irrelevant- any dust deposited will be washed off almost immediately. 
"""

dir = r"D:\UKuni\3rdYr\Project\GIS_data\DissPy\_outputCsvs\re_in\2013"  # location of input data
outdir = r"D:\UKuni\3rdYr\Project\GIS_data\DissPy\_outputCsvs\re_in\seasons_out_K"  # where to write out
winterCsv = os.path.join(outdir, "winter.csv")
preMonsoonCsv = os.path.join(outdir, "K_preMonsoon.csv") # K_ because currently working on Karnataka data
monsoonCsv = os.path.join(outdir, "K_monsoon.csv")
postMonsoonCsv = os.path.join(outdir, "K_postMonsoon.csv")
unassignedCsv = os.path.join(outdir, "K_unassigned.csv") # should come out empty

# open the output csvs (one for each season)
with open(winterCsv, 'a', newline="") as w,\
        open(preMonsoonCsv, 'a', newline="") as pre,\
        open(monsoonCsv, 'a', newline="") as m,\
        open(postMonsoonCsv, 'a', newline="") as post,\
        open(unassignedCsv, 'a', newline="") as u:
    # create the writer objects
    winterWriter = csv.writer(w)
    preMWriter = csv.writer(pre)
    monsoonWriter = csv.writer(m)
    postMonsoonWriter = csv.writer(post)
    unassignedWriter = csv.writer(u)
    for filename in os.listdir(dir): # iterate over AODb csvs
        fileIn = os.path.join(dir, filename)
        with open(fileIn) as csvfile:  # read in data
            data = list(csv.reader(csvfile))
            for row in data[1:]:
                print("scanning row") # just so we know when something's happening
                lat = float(row[0])
                day = float(row[4])
                AODb = row[2]
                if lat > 19: # < 19 for Rajasthan
                    continue # R is all above 19, K is all below
                # select data by day of year
                if day > 334.5 or day < 59.5:
                    winterWriter.writerow(row)
                    continue
                if 59.5 < day < 151.5:
                    preMWriter.writerow(row)
                    continue
                if 151.5 < day < 273.5:
                    monsoonWriter.writerow(row)
                    continue
                if 273.5 < day < 334.5:
                    postMonsoonWriter.writerow(row)
                    continue
                unassignedWriter.append(row) # this should- and does- come out empty