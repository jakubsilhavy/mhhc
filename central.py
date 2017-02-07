# central run file for autoLin methods - original file for whole MHHC algorithm
import autoLin
import config
import tbe
from multiprocessing import Lock

# setting paths for workspace
workspace = config.workspace
resultsDir = config.resultsDir
sourceDir = config.sourceDir
DEMs = config.DEMs

onlyHiearchy = config.onlyHiearchy

# for each DEM from config
for DEM in DEMs:
  # setting parameters form config
  hasPCIdone = config.hasPCIdone
  azimuths = config.azimuths
  rotations = config.rotations
  # setup paths for DEM
  SA = config.getSA(DEM)
  sourceDEM = config.getSourceDEM(DEM)
  # time log
  timeLogFileName = resultsDir + SA + "\\" + sourceDEM + "\\" + "%s_timeLog.txt" % DEM
  autoLin.makeDirs(resultsDir + SA + "\\" + sourceDEM)
  tb = tbe.timeStamp("", "", timeLogFileName)
  tb.log("start")
  
  if(not hasPCIdone):
    tb.log("extractionRasters")
    # prepare rasters for extraction
    autoLin.extractionRasters(DEM, azimuths, rotations)
    # extract rasters using PCI Geomatica outside this script!
  elif(not onlyHiearchy):
    tb.log("rotateBack")
    autoLin.rotateBack(DEM, rotations)
  
    # splitAtVertices and erase boundary
    tb.log("splitAndErase")
    autoLin.splitAndErase(DEM, rotations)

    # relevant and cluster  
    tb.log("optimizedClusterLine")
    lock = Lock()
    autoLin.optimizedClusterLine(DEM, rotations, tb, lock)
    tb.log("finish")
    tb.log("computeAndPlotHists")
    autoLin.computeAndPlotHists(DEM, rotations, "all")
    # TODO co s MXD?
    # tb.log("createMXD")
    # autoLin.createMXD(DEM, rotations)

if(hasPCIdone):
  # hiearchical clustering
  tb.log("hiearchicalClustering")
  for DEM in DEMs:
    # setup paths for DEM
    clusterName = 99
    tb.log("finalCluster")
    autoLin.finalCluster(DEM, clusterName)

    rotations = [clusterName]
    lock = Lock()
    autoLin.optimizedClusterLine(DEM, rotations, tb, lock)
    tb.log("classifyRidges")
    autoLin.classifyRidges(DEM, rotations)
    tb.log("computeAndPlotHists")
    autoLin.computeAndPlotHists(DEM, rotations, "all")
    autoLin.computeAndPlotHists(DEM, rotations, "negative")
    autoLin.computeAndPlotHists(DEM, rotations, "positive")
    # tb.log("createMXD")
    # autoLin.createMXD(DEM, config.rotations+[clusterName])

tb.log("finish")