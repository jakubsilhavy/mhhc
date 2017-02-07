# Data preparation for autoLin
# input: boundary of area - shp polygon; raster DMR
# output: filled DEM
import time
import os
# import config
startTime = time.strftime("%m%d_%H%M%S")
print "time %s - started" % (startTime)
import arcpy
import autoLin
print "time %s - arcpy imported" % (time.strftime("%m%d_%H%M%S"))
# Set the geoprocessor object property to overwrite existing outputs
arcpy.gp.overwriteOutput = True

# setup paths
inDEM = r"d:\Kuba\PhD_data\Thesis\AutoLin\Zdroje\Libor\dtm"
boundary = r"d:\Kuba\PhD_data\Thesis\AutoLin\Zdroje\Libor\boundary.shp"
resolutions = [30, 50, 75, 100]
outDEMmask = r"d:\Kuba\PhD_data\Thesis\AutoLin\DEM\Hronska\ZM50\hr_zm_dem_"

for cellSize in resolutions:
    outDEM = outDEMmask + "%i" % cellSize
    if not os.path.exists(outDEM):
      resampleDEM = autoLin.getDir(outDEM) + "resDEM_%i" % cellSize
      if not os.path.exists(resampleDEM):
        print "time %s - resampling DEM" % (time.strftime("%m%d_%H%M%S"))
        arcpy.Resample_management(inDEM, resampleDEM, cellSize, "BILINEAR")
        # clip DEM by boundary FIRST!
        clipDEM =  autoLin.getDir(outDEM) + "clipDEM_%i" % cellSize    
        if not os.path.exists(clipDEM):
          print "time %s - cliping DEM" % (time.strftime("%m%d_%H%M%S"))
          arcpy.Clip_management(resampleDEM,"#",clipDEM,boundary,"-3,402823e+038","ClippingGeometry")
        # fill DEM - save to folder
        print "time %s - filling DEM" % (time.strftime("%m%d_%H%M%S"))
        arcpy.gp.Fill_sa(clipDEM,outDEM,"#")
        # delete tempDEM
        autoLin.deletePath(clipDEM)
      autoLin.deletePath(resampleDEM)