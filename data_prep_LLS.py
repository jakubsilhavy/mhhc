# Data preparation for autoLin
# input: boundary of area - shp polygon; contour lines
# output: filled DEM
import time
import os
# import config
startTime = time.strftime("%m%d_%H%M%S")
print "time %s - started" % (startTime)
import arcpy
import autoLin
arcpy.CheckOutExtension("3D")
print "time %s - arcpy imported" % (time.strftime("%m%d_%H%M%S"))
# Set the geoprocessor object property to overwrite existing outputs
arcpy.gp.overwriteOutput = True

# setup paths
terrain = r"D:\Kuba\PhD_data\Thesis\AutoLin\Zdroje\Mentlik\Srni\DMR.gdb\Prasily\Prasily_Terrain"
resolutions = range(10,11,5)
outDEMmask = r"d:\Kuba\PhD_data\Thesis\AutoLin\DEM\Prasily\LLS\pr_lls_dem_"

#TODO: clip by boundary
for cellSize in resolutions:
    outDEM = outDEMmask + "%i" % cellSize
    if not os.path.exists(outDEM):
      # create temp DEM
      tempDEM = autoLin.getDir(outDEM) + "tempDEM"
      if not os.path.exists(tempDEM):
        arcpy.TerrainToRaster_3d(terrain,tempDEM,"FLOAT","LINEAR","CELLSIZE %i" %cellSize,"0")        
      # fill DEM - save to folder
      try:
        print "time %s - filling DEM %s" % (time.strftime("%m%d_%H%M%S"), outDEM)
        arcpy.gp.Fill_sa(tempDEM,outDEM,"#")
      except:
        print "DEM %s failed - continue with next one" % outDEM
        autoLin.deletePath(tempDEM)
        continue
      # delete tempDEM
      autoLin.deletePath(tempDEM)
    else:
      print "skip DEM %s" %outDEM