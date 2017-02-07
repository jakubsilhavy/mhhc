# Data preparation for autoLin
# inputs:
# boundary of area - shp polygon
# vector inputs with description (contour lines,..)
# list of resotulions
# output: filled DEM
import time
import config
startTime = time.strftime("%m%d_%H%M%S")
print "time %s - started" % (startTime)
import arcpy
import autoLin
print "time %s - arcpy imported" % (time.strftime("%m%d_%H%M%S"))
# Set the geoprocessor object property to overwrite existing outputs
arcpy.gp.overwriteOutput = True

# setup inputs
boundary = r"d:\PhD\Thesis\Vyzkum\Zdroje_DEM\boundary.shp"

# sourceWorkspace = r"d:\PhD\Thesis\Vyzkum\Zdroje_DEM\ZM50" + "\\"
# inputs = {"type": "VECTOR", "data": "vrstevnice_arc.shp HEIGHT Contour"}
# resolutions = [30]
# outDEMmask = r"sd_zm_dem_"

# sourceWorkspace = r"d:\PhD\Thesis\Vyzkum\Zdroje_DEM\DMU25" + "\\"
# inputs = {"type": "VECTOR", "data": "vymezeni_vrst.shp HODNOTA Contour"}
# resolutions = [30]
# outDEMmask = r"sd_d_dem_"

# sourceWorkspace = r"d:\PhD\Thesis\Vyzkum\Zdroje_DEM\DMR4G" + "\\"
# inputs = {"type": "RASTER", "data": "dmr4g"}
# resolutions = [30]
# outDEMmask = r"sd_d4_dem_"

sourceWorkspace = r"d:\PhD\Thesis\Vyzkum\Zdroje_DEM\DMR5G" + "\\"
inputs = {"type": "RASTER", "data": "dmr5g"}
resolutions = [30]
outDEMmask = r"sh_d5_dem_"

# sourceWorkspace = r"d:\PhD\Thesis\Vyzkum\Zdroje_DEM\ASTER" + "\\"
# inputs = {"type": "RASTER", "data": "aster_utm"}
# resolutions = [30]
# outDEMmask = r"sd_as_dem_"

# sourceWorkspace = r"d:\PhD\Thesis\Vyzkum\Zdroje_DEM\SRTM" + "\\"
# inputs = {"type": "RASTER", "data": "srtm_utm"}
# resolutions = [30]
# outDEMmask = r"sd_sr_dem_"

autoLin.createDEM(sourceWorkspace, inputs, boundary, resolutions, outDEMmask)