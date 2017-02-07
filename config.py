# config file for MHHC algorithm
import os
# path to workspace of Python
workspace = r"c:\Users\jsilhavy\Documents\PhD\Thesis\Vyzkum" + os.path.sep
# workspace = r"c:\Users\jsilhavy\Documents\Prace\Projekty\Uni\Thesis\Git\Vyzkum" + os.path.sep
# path to worskpace of PCI (cloud be the same or different)
workspacePCI = "C:" + os.path.sep
# path to results dir
resultsDir = workspace + "Results" + os.path.sep

# switcher for computation in central.py
hasPCIdone = True
onlyHiearchy = False

# internal folder structure
hlWS = "HLs" + os.path.sep
combiWS = "process" + os.path.sep
runEAS = "runEAS" + os.path.sep
shpWS = "shp" + os.path.sep 
shpLinesWS = "shpLines" + os.path.sep
negativeWS = "negative" + os.path.sep
positiveWS = "positive" + os.path.sep
unsureWS = "unsure" + os.path.sep
temp = "temp" + os.path.sep
flowWS = "flow" + os.path.sep 
relevantWS = "relevant" + os.path.sep
outAllWS =  "outAll" + os.path.sep
mergeWS = "merge" + os.path.sep
easiWS = "easi" + os.path.sep
scriptWS = "EAS" + os.path.sep
bundleWS = "bundle" + os.path.sep
streamWS = "stream" + os.path.sep
shpRotateWS = "shpRotate" + os.path.sep
clearWS =  "clear" + os.path.sep
histWS = "hist" + os.path.sep
imageData = "ImageData" + os.path.sep


##############################
### STEP 01 - DEM creation ###
##############################
# list of names of source DEMs
DEMs = ["sd_sr_dem_30"]
# source dir of DEMs
sourceDir = workspace + "DEM" + os.path.sep
# in case of irregular shape of DEM set 1, otherwise set 0
isDEMNotRectangle = 1
# buffer size for clipping irregular area
clipDEMSize = 400 # shloud depend of cell size or area

########################################
### STEP 02 - Hillshades parameters ###
#######################################
# angle step for hillshade
azimuthStep = 15
# size of agnle range (180 could be applied for rotating only half of round)
azimuthMax = 360
# angle range for hillshade
azimuths = range(0,azimuthMax,azimuthStep)
# altitude of hilhade
altitude = 30

#################################
### STEP 03 Line extraction  ###
################################
# parameters of PCI Geomatica (LINE modul)
# http://www.pcigeomatics.com/geomatica-help/references/pcifunction_r/python/p_line.html
# TODO popsat vyznam parametru
athr = 0
dthr = 0
fthr = 1
radi = 10
gthr = 10
lthr = 10

#######################################
### STEP 04 - Noise removing        ###
#######################################
splitField = "split"
# name of dataset after noise removal
relevantMergedName = "relevantMerged.shp"
# name of dataset after mergeg lines without noise removal for MHHCA clustering algorithm
relevantMergedNameLite = "relevantMerged_lite.shp"

# thresholds to differentiate relevant and non relevant lines
# mean
parMeaNon = 2
parMeaRel = 4
# median
parMedNon = 2
parMedRel = 4

# count threshold for noise removing
relevantT = 3

#############################
### STEP 05 - Clusters    ###
#############################

# azimuth threshold
azimuthTreshold = 20
# count threshold
clusterT = 4

# count threshold for visualisation
filterCount = 4

# switcher to use memory saving (1 = true, 0 = false)
memorySaving = 1
# count threshold for memory saving
optimalStop = 2000

# method of computing the average line
averageMethod = "centroid" # "lw_average" # "aritmetic", "lw_average", "centers", "centroid"

## parameter for graph plots
yMax = 4
radMax = 5

# parameters for MHHCA method
# path to compiled MHHCA algorithm
gisExePath = r"ProgramKIV\GIS_linie_4\gis.exe"

# width and height of constructed buffer
xKIV = 150
yKIV = 200

# count threshold
clusterTKIV = 1
# count threshold for visualisation
filterCountKIV = 4

# name of internal dataset
bundleMergedName = "bundleMerged.shp"

###################################################
### STEP 06 - Classification of lineaments      ###
###################################################
# TODO popsat vyznam parametru
bufferSizeRidges = 30
parMeaRidge = 10
parMeaValley = 50
parMedRidge = 2
parMedValley = 15

#############################
### Artefact removal      ###
#############################
rotationStep = 9
rotationMax = 45
rotations = range(0, rotationMax, rotationStep)

#############################
### Utilities             ###
#############################

# find out the cell size from name of input DEM
def getCellSize(DEM):
  codeSApos = DEM.rfind("_")
  return int(DEM[codeSApos+1:])

# definition of study area abbreviations for naming convention
def getSA(DEM):
  codeSApos = DEM.find("_")
  codeSA =DEM[0:codeSApos]
  if codeSA == "sd":
    SA = "SumavaDMR"
  else:
    SA = codeSA
  return SA

# path of MXD document to create output
def getInputMXDPath(SA):
  return workspace + imageData + "%s.mxd" % SA

# definition of DEM type abbreviations for naming convention
def getSourceDEM(DEM):
  codeSApos = DEM.find("_")
  codeSourceDEMpos = DEM[codeSApos+1:].find("_") + codeSApos+1
  codeSourceDEM = DEM[codeSApos+1:codeSourceDEMpos] 
  if codeSourceDEM == "zm":
    sourceDEM = "ZM50"
  elif codeSourceDEM == "lls":
    sourceDEM = "LLS"
  elif codeSourceDEM == "d4":
    sourceDEM = "DMR4G"
  elif codeSourceDEM == "d5":
    sourceDEM = "DMR5G"
  elif codeSourceDEM == "d":
    sourceDEM = "DMU25"
  elif codeSourceDEM == "as":
    sourceDEM = "ASTER"
  elif codeSourceDEM == "sr":
    sourceDEM = "SRTM"
  else:
    sourceDEM = codeSourceDEM
  return sourceDEM

# definition of buffer size limits
def getBufferSizeCluster():
  bufferSizeClusterMin = 100
  bufferSizeClusterMax = 200
  return [bufferSizeClusterMin, bufferSizeClusterMax]

# find out the rotation from file name
def getRotationAngle(DEM):
  codeSApos = DEM.rfind("_")
  codeRotation = DEM.find("_r")
  return int(DEM[codeRotation+2:codeSApos])

# find out the azimuth of hillshade from file name
def getHSAzimuth(shpName):
  angleStart = shpName.find("_")+1
  angleEnd = shpName.find("_", angleStart)
  return shpName[angleStart:angleEnd]