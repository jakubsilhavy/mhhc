# -*- coding: UTF-8 -*-
# tool's library for AutoLin
# TODO: make autoLin as Object and set some properties - like demWS.. 
import shutil
import os
import time
import traceback

import config
import math
import arcpy
import line_stats
import tbe
# import pylab
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.font_manager import FontProperties
arcpy.env.overwriteOutput = True
# Check out the ArcGIS Spatial Analyst extension license
if arcpy.CheckExtension("Spatial") == "Available":
    slic = arcpy.CheckOutExtension("Spatial")
#     print(slic)
else:
  print "No Spatial licence availiable!"
# print ("time %s - arcpy imported" % (time.strftime("%m%d_%H%M%S"))

class Cluster:
  def __init__(self):
    self.myId = []
    self.IDs = []
    self.Ax = []
    self.Ay = []
    self.Bx = []
    self.By = []
    self.A = []
    self.length = []

# setting paths for workspace
workspace = config.workspace
resultsDir = config.resultsDir
sourceDir = config.sourceDir

# TODO zachovat
# delete directory with input path
def deletePath(path):
  if os.path.exists(path):
    if os.path.isdir(path):
      print ("time %s - deleting %s" % (time.strftime("%m%d_%H%M%S"), path))
      shutil.rmtree(path)

# TODO zachovat
# creates demDirs directories in demWS folder
def createDEMdirs(demWS, demDirs):
  for demDir in demDirs:
    if not os.path.exists(demWS+demDir):
      os.mkdir(demWS+demDir)

# TODO zachovat
# create all dirs in path
def makeDirs(path):
  if not os.path.exists(path):
    os.makedirs(path)

# TODO zachovat
# clips input DEM using boundary and fill sinks
def clipAndFill(inRaster, outRaster, boundary, cellSize):
  # clip DEM by boundary FIRST!
  clipDEM = "in_memory\\" + "clipDEM_%i" % cellSize
  print "time %s - cliping DEM" % (time.strftime("%m%d_%H%M%S"))
  arcpy.Clip_management(inRaster, "#", clipDEM, boundary, "-3,402823e+038", "ClippingGeometry")
  # fill DEM - save to folder
  print "time %s - filling DEM" % (time.strftime("%m%d_%H%M%S"))
  arcpy.gp.Fill_sa(clipDEM, outRaster, "#")
  arcpy.Delete_management(clipDEM)
  arcpy.Delete_management(inRaster)

# TODO zachovat
# step 1 DEMs Creation
def createDEM(sourceWorkspace, inputs, boundary, resolutions, outDEMmask):
  sourceDir = config.sourceDir
  SA = config.getSA(outDEMmask)
  sourceDEM = config.getSourceDEM(outDEMmask)
  outDEMpath = sourceDir + SA + "\\" + sourceDEM + "\\"
  makeDirs(getDir(outDEMpath))

  # copy boundary to outDEMDir
  outBoundary = outDEMpath + "boundary.shp"
  arcpy.CopyFeatures_management(boundary, outBoundary)

  # process inputs regarding input type
  # TODO LLS type
  if (inputs["type"] == "VECTOR"):
    topoInputs = ""
    # clip vector inputs using boundary
    for vector in inputs["data"].split(";"):
      topoInputsField = vector.strip().split(" ")
      fcName = topoInputsField[0]
      fcPath = sourceWorkspace + fcName
      vectorClip = "in_memory\\" + os.path.splitext(fcName)[0]
      topoInputs += vectorClip + " " + topoInputsField[1] + " " + topoInputsField[2] + ";"
      print "time %s - clipping %s" % (time.strftime("%m%d_%H%M%S"), fcName)
      arcpy.Clip_analysis(fcPath, boundary, vectorClip)

    for cellSize in resolutions:
      outDEM = outDEMpath + outDEMmask + "%i" % cellSize
      if not os.path.exists(outDEM):
        # create temp DEM
        tempDEM = "in_memory\\" + "tempDEM_%i" % cellSize
        print "time %s - creating DEM raster" % (time.strftime("%m%d_%H%M%S"))
        arcpy.gp.TopoToRaster_sa(topoInputs, tempDEM, cellSize)
        clipAndFill(tempDEM, outDEM, boundary, cellSize)

  elif (inputs["type"] == "RASTER"):
    inDEM = sourceWorkspace + inputs["data"]
    for cellSize in resolutions:
      outDEM = outDEMpath + outDEMmask + "%i" % cellSize
      if not os.path.exists(outDEM):
        resampleDEM = "in_memory\\" + "resDEM_%i" % cellSize
        print "time %s - resampling DEM" % (time.strftime("%m%d_%H%M%S"))
        arcpy.Resample_management(inDEM, resampleDEM, cellSize, "BILINEAR")
        clipAndFill(resampleDEM, outDEM, boundary, cellSize)

# TODO zachovat
def selectAndWrite(lineSHP, zonalP, gridCode, myField):
  # select by attributes: from zonalP using gridcode
  arcpy.MakeFeatureLayer_management (zonalP, "zonalP")
  zonalPFields = arcpy.ListFields("zonalP")
  gridFieldName = "GRIDCODE"
  for zonalField in zonalPFields:
    if "grid" in zonalField.name.lower():
      gridFieldName = zonalField.name
  myExpression = '"%s" = %d' % (gridFieldName, gridCode)
  arcpy.SelectLayerByAttribute_management ("zonalP", "NEW_SELECTION", myExpression)
  # select by location: from lineSHP which have centroid in selected zonalP
  arcpy.MakeFeatureLayer_management(lineSHP, "lineSHP")
  arcpy.SelectLayerByLocation_management("lineSHP", "have_their_center_in", "zonalP", "", "NEW_SELECTION")  
  # write to selected lineSHP attribude gridcode to field zonalP
  myValue = 1
  if gridCode == 1:
    myValue = -1
  if gridCode == 2:
    myValue = 0
  arcpy.CalculateField_management("lineSHP",myField,myValue,"PYTHON_9.3","#")
  arcpy.SelectLayerByAttribute_management ("zonalP", "CLEAR_SELECTION")
  arcpy.SelectLayerByAttribute_management ("lineSHP", "CLEAR_SELECTION")

# TODO zachovat
# input - shp as a single lines, raster with value, buffer size and parameters for selection
# output - directory with separated lines
def zonalLine(inSHP, inRaster, bufferSize, meaPars, medPars, outSHP, outSHPPositive, outSHPUnsure):
  print ("time %s - starting zonal for %s" % (time.strftime("%m%d_%H%M%S"), getName(inSHP)))
  tempWS = config.temp
  demDirs = [tempWS]
  inDir = getDir(inSHP)
  createDEMdirs(inDir, demDirs)
  
  # buffer inSHP
  lineSHPBuffName = getName(inSHP)[:-4]+"_buff%d.shp" % bufferSize
  lineSHPDir = inDir + tempWS + getName(inSHP)[:-4] + "bf\\"
  if not os.path.exists(lineSHPDir):
    os.mkdir(lineSHPDir)
  lineSHPBuff = lineSHPDir + lineSHPBuffName 
  if not os.path.exists(lineSHPBuff):
    arcpy.Buffer_analysis(inSHP,lineSHPBuff,"%d Meters" % bufferSize,"FULL","ROUND","NONE","#")
  
  # zonal stats - zones: bufferSHP, inRaster, stat - mean, median
  zonalRMed = lineSHPDir + "zonMed"
  zonalRMea = lineSHPDir + "zonMea"
  if not os.path.exists(zonalRMed):
#     print ("time %s - creating zonalR MEDIAN" % (time.strftime("%m%d_%H%M%S"))
    arcpy.gp.ZonalStatistics_sa(lineSHPBuff,"FID",inRaster,zonalRMed,"MEDIAN","DATA")
  if not os.path.exists(zonalRMea):
#     print ("time %s - creating zonalR MEAN" % (time.strftime("%m%d_%H%M%S"))
    arcpy.gp.ZonalStatistics_sa(lineSHPBuff,"FID",inRaster,zonalRMea,"MEAN","DATA")    
  
  # reclassify zone rasters using threshold for flowAcc field (3 classes - positive, unsure, negative)
  # reclassify MEDIAN and toPolygon
  parMedRidge = medPars[0]
  parMedValley = medPars[1]
  zonalRMedRec = lineSHPDir + "zMed%d_%d" % (parMedRidge, parMedValley)
  if not os.path.exists(zonalRMedRec):
    parMedRidge+=0.01
    parMedValley-=0.01
#     print ("time %s - reclassify zonalR MEDIAN" % (time.strftime("%m%d_%H%M%S"))
    arcpy.gp.Reclassify_sa(zonalRMed,"VALUE","0 %d 1;%d %d 2;%d 10000000 3" % (parMedRidge, parMedRidge, parMedValley, parMedValley),zonalRMedRec,"NODATA")
  # toPolygon
  zonalPMedRec = zonalRMedRec + ".shp"
  if not os.path.exists(zonalPMedRec):
#     print ("time %s - to polygon zonalR MEDIAN" % (time.strftime("%m%d_%H%M%S"))
    arcpy.RasterToPolygon_conversion(zonalRMedRec,zonalPMedRec,"SIMPLIFY","VALUE")

  # reclassify MEAN and toPolygon
  parMeaRidge = meaPars[0]
  parMeaValley = meaPars[1]
  zonalRMeaRec = lineSHPDir + "zMea%d_%d" % (parMeaRidge, parMeaValley)
  if not os.path.exists(zonalRMeaRec):
    parMeaRidge+=0.01
    parMeaValley-=0.01  
#     print ("time %s - reclassify zonalR MEAN" % (time.strftime("%m%d_%H%M%S"))
    arcpy.gp.Reclassify_sa(zonalRMea,"VALUE","0 %d 1;%d %d 2;%d 10000000 3" % (parMeaRidge, parMeaRidge, parMeaValley, parMeaValley),zonalRMeaRec,"NODATA")
  # toPolygon
  zonalPMeaRec = zonalRMeaRec + ".shp"
  if not os.path.exists(zonalPMeaRec):
#     print ("time %s - to polygon zonalR MEAN" % (time.strftime("%m%d_%H%M%S"))
    arcpy.RasterToPolygon_conversion(zonalRMeaRec,zonalPMeaRec,"SIMPLIFY","VALUE")  
    
  # select and write inSHP, zonalP, outWS
  # cteate 3 new fields flowAccMED, flowAccMEAN and flowAccTrue for lineSHP
  arcpy.AddField_management(inSHP, "fMED", "LONG", 9, "", "", "", "NULLABLE", "NON_REQUIRED")
  arcpy.AddField_management(inSHP, "fMEAN", "LONG", 9, "", "", "", "NULLABLE", "NON_REQUIRED")
  arcpy.AddField_management(inSHP, "fTrue", "LONG", 9, "", "", "", "NULLABLE", "NON_REQUIRED")
  # set null the fields (because 0 is not rewrited!)

  # select and write attributes
  for zonalP in [zonalPMedRec, zonalPMeaRec]:
    statField = "fMED"
    if zonalP.rfind("zMea")+1:
      statField = "fMEAN"  
    for gridCode in [1, 2, 3]:
      selectAndWrite(inSHP, zonalP, gridCode, statField)
  # combine Med and Mea to "fTrue"
  arcpy.CalculateField_management("lineSHP","fTrue","!fMED! + !fMEAN!","PYTHON_9.3","#")
  
  # Separating lines - positive and negative
  # A) negative lines > 0  
  outDir = getDir(outSHP) 
  if not os.path.exists(outDir):
    os.mkdir(outDir)
  # select by attributes: from "lineSHP" using "fTrue"
  myExpression = '"fTrue" > 0'
  arcpy.SelectLayerByAttribute_management ("lineSHP", "NEW_SELECTION", myExpression)
  arcpy.CopyFeatures_management("lineSHP", outSHP)
  
  # B) if positive lines parameter is set:
  if (len(outSHPPositive) > 0):
    outDir = getDir(outSHPPositive) 
    if not os.path.exists(outDir):
      os.mkdir(outDir)
    # select by attributes: from "lineSHP" using "fTrue"
    myExpression = '"fTrue" < 0'
    arcpy.SelectLayerByAttribute_management ("lineSHP", "NEW_SELECTION", myExpression)
    arcpy.CopyFeatures_management("lineSHP", outSHPPositive)
    
  # C) if unsure lines parameter is set:
  if (len(outSHPUnsure) > 0):
    outDir = getDir(outSHPUnsure) 
    if not os.path.exists(outDir):
      os.mkdir(outDir)
    # select by attributes: from "lineSHP" using "fTrue"
    myExpression = '"fTrue" = 0'
    arcpy.SelectLayerByAttribute_management ("lineSHP", "NEW_SELECTION", myExpression)
    arcpy.CopyFeatures_management("lineSHP", outSHPUnsure)

# TODO zachovat
# input - shp as a single lines, raster with value, buffer size and parameters for selection
# output - directory with separated lines
def zonalLineRelevant(inSHP, inRaster, bufferSize, countThreshold, outSHP, statistic):
  print ("time %s - starting zonal for %s" % (time.strftime("%m%d_%H%M%S"), getName(inSHP)))
  tempWS = config.temp
  demDirs = [tempWS]
  inDir = getDir(inSHP)
  createDEMdirs(inDir, demDirs)
  
  # buffer inSHP
  # lineSHPBuffName = getName(inSHP)[:-4]+"_buff%d.shp" % bufferSize
  lineSHPBuffName = getName(inSHP)[:-4]+"_buff%d" % bufferSize
  # TODO "in_memory"
  lineSHPDir2 = inDir + tempWS + getName(inSHP)[:-4] + "bf_"
  lineSHPDir = "in_memory\\" + getName(inSHP)[:-4] + "bf_"
  # TODO "in_memory"
  # if not os.path.exists(lineSHPDir):
  #   os.mkdir(lineSHPDir)
  lineSHPBuff = lineSHPDir + lineSHPBuffName
  if not os.path.exists(lineSHPBuff):
    arcpy.Buffer_analysis(inSHP,lineSHPBuff,"%d Meters" % bufferSize,"FULL","ROUND","NONE","#")
  
  # zonal stats - zones: bufferSHP, inRaster, stat - mean
  if statistic == "MEAN":
    zonalRName = "zMea"
    statField = "fMEAN"
  elif statistic == "MEDIAN":
    zonalRName = "zMed"
    statField = "fMED"
    
  zonalRMea = lineSHPDir + zonalRName
  if not os.path.exists(zonalRMea):
    arcpy.gp.ZonalStatistics_sa(lineSHPBuff,"FID",inRaster,zonalRMea,statistic,"DATA")    
    # TODO "in_memory"
    arcpy.Delete_management(lineSHPBuff)
  # reclassify zone rasters using threshold for flowAcc field (3 classes - positive, unsure, negative)
  # reclassify MEAN and toPolygon
  zonalRMeaRec = lineSHPDir + zonalRName+"%d" % (countThreshold)
  # recclasification condition
  countThreshold -= 0.01
  if not os.path.exists(zonalRMeaRec):
#     print ("time %s - reclassify zonalR MEAN" % (time.strftime("%m%d_%H%M%S"))
    arcpy.gp.Reclassify_sa(zonalRMea,"VALUE","0 %d 1;%d 10000000 3" % (countThreshold, countThreshold),zonalRMeaRec,"NODATA")
    # TODO "in_memory"
    arcpy.Delete_management(zonalRMea)
  # toPolygon
  # zonalPMeaRec = zonalRMeaRec + ".shp"
  zonalPMeaRec = zonalRMeaRec + "_P"
  # zonalPMeaRec = lineSHPDir2 + zonalRName+"%d" % (countThreshold) + ".shp"
  if not os.path.exists(zonalPMeaRec):
#     print ("time %s - to polygon zonalR MEAN" % (time.strftime("%m%d_%H%M%S"))
    arcpy.RasterToPolygon_conversion(zonalRMeaRec,zonalPMeaRec,"SIMPLIFY","VALUE")  
    # TODO "in_memory"
    arcpy.Delete_management(zonalRMeaRec)
  # select and write inSHP, zonalP, outWS
  # cteate new field flowAccMEAN for lineSHP
  if (arcpy.ListFields(inSHP, statField)== []):
    arcpy.AddField_management(inSHP, statField, "LONG", 9, "", "", "", "NULLABLE", "NON_REQUIRED")
  # set null the fields (because 0 is not rewrited!)

  # select and write attributes
  for gridCode in [1, 3]:
    selectAndWrite(inSHP, zonalPMeaRec, gridCode, statField)
  # TODO "in_memory"
  arcpy.Delete_management(zonalPMeaRec)
  # Separating lines - positive and negative
  # A) negative lines > 0  
  outDir = getDir(outSHP) 
  if not os.path.exists(outDir):
    os.mkdir(outDir)
  # select by attributes: from "lineSHP" using "fTrue"
  myExpression = '%s > 0' % statField
  arcpy.SelectLayerByAttribute_management ("lineSHP", "NEW_SELECTION", myExpression)
  arcpy.CopyFeatures_management("lineSHP", outSHP)
     
# TODO zachovat
def getName(inSHP):
   inSHP = inSHP[inSHP.rfind("\\")+1:]
   return inSHP

# TODO zachovat
def getDir(inSHP):
   inSHP = inSHP[0:inSHP.rfind("\\")+1]
   return inSHP

# TODO zachovat
# for each input row line returns list of points
def getPoints(feat):
  partnum = 0
  # Step through each part of the feature
  pnts = []
  for part in feat:
      # Step through each vertex in the feature
      for pnt in feat.getPart(partnum):
              pnts.append(pnt)
      partnum += 1 
  return pnts

# TODO zachovat
# calculates statistics length and azimuth (from north clockwise)
# write fields "azimuth" and "length" to attribute table of inSHP  
def calcStats(inSHP):
#   print ("time %s - calculating stats" % (time.strftime("%m%d_%H%M%S"))
  # add fields before creating cursors !! - otherwise Python crash !!
  if (arcpy.ListFields(inSHP, "azimuth")== []):
    arcpy.AddField_management(inSHP, "azimuth", "FLOAT", 9, 2, "", "", "NULLABLE", "NON_REQUIRED")
  if (arcpy.ListFields(inSHP, "length")== []):
    arcpy.AddField_management(inSHP, "length", "FLOAT", 9, 2, "", "", "NULLABLE", "NON_REQUIRED")

  rows = arcpy.UpdateCursor(inSHP)
  desc = arcpy.Describe(inSHP)
  shapefieldname = desc.ShapeFieldName 
  for row in rows:
    feat = row.getValue(shapefieldname)
    pnts = getPoints(feat)
    if (pnts != []):
      A = pnts[0]
      B = pnts[1]
      azimuth = line_stats.lineAzimuth(A,B)
      length = line_stats.lineLength(A,B)
      row.azimuth = azimuth
      row.length = length
      rows.updateRow(row)

# TODO zachovat
# input: raster DEM - output: flowAcc in flowWS directory
def getFlowAcc(demWS, inDEM):
  flowWS = config.flowWS
  flowAcc = demWS + flowWS + "flowAcc"
  if not os.path.exists(flowAcc):
    # create dirs in workspace
    tempWS = config.temp
    demDirs = [tempWS, flowWS]
    createDEMdirs(demWS, demDirs)
    # fiiling skipped - already filled by dataprep!
    outFill = inDEM
    # compute FlowAcc from DEM
    flowDir = demWS + flowWS + "flowDir"
    if not os.path.exists(flowDir):
      print ("time %s - createFlowDir" % (time.strftime("%m%d_%H%M%S")))
      arcpy.gp.FlowDirection_sa(outFill,flowDir,"NORMAL","#")  
    # output must be INTEGER due to zonalStats!
    print ("time %s - createFlowAcc" % (time.strftime("%m%d_%H%M%S")))
    arcpy.gp.FlowAccumulation_sa(flowDir,flowAcc,"#","INTEGER")
  return flowAcc

# TODO zachovat
# returns center of raster
def getRotationCenter(inRaster):
  X = getRasterInfo(inRaster, "LEFT", 1)
  Y = getRasterInfo(inRaster, "TOP", 1)
  return arcpy.Point(X, Y)

# TODO zachovat
#output is integer
def getRasterInfo(inRaster, rasterProperty, isRound):
  if os.path.exists(inRaster):
    rasterInfo = arcpy.GetRasterProperties_management(inRaster, rasterProperty)
    rasterProperty = rasterInfo.getOutput(0)
    rasterProperty = float (rasterProperty.replace(",", ".", 1))
    if (isRound):
      rasterProperty = round (rasterProperty)
    return rasterProperty

# TODO unused
# export calculated statistics with coordinates (length and azimuth (from north clockwise))
# read geometry and fields "azimuth" and "length" from attribute table of inSHP
def exportStats(inSHP, outTXT):
  print ("time %s - exporting stats to file %s" % (time.strftime("%m%d_%H%M%S"), outTXT))
  # add fields before creating cursors !! - otherwise Python crash !!
  azimuthField = "azimuth"
  lengthField = "length"

  rows = arcpy.SearchCursor(inSHP)
  desc = arcpy.Describe(inSHP)
  shapefieldname = desc.ShapeFieldName
  
  # open file to write
  outTXT = open(outTXT, "w")
  for row in rows:
    feat = row.getValue(shapefieldname)
    pnts = getPoints(feat)
    A = pnts[0]
    B = pnts[1]
    azimuth = row.azimuth
    length = row.length
    outTXT.write("%i; %i; %i; %i; %i; %0.2f; %0.2f\n" %(row.FID, A.X, A.Y, B.X, B.Y, azimuth, length))
  outTXT.close()

# TODO zachovat
# split all SHPs in input folder and copy to output folder
def splitLines(demWS, shpWS, outWS):
  shp_listDir = os.listdir(demWS+shpWS)
  for mySHP in shp_listDir:
    if mySHP[-4:] == ".shp":
      # split input lines to outWS
      inSHP = demWS + shpWS + mySHP
      splitLine(inSHP, demWS, outWS)

# TODO zachovat
# split input lines to line segments
def splitLine(inSHP, demWS, outWS):
  shpName = getName(inSHP)
  lineSHPName = shpName
  lineSHPDir = demWS + outWS 
  if not os.path.exists(lineSHPDir):
    os.mkdir(lineSHPDir)
  lineSHP = lineSHPDir + lineSHPName
  if not os.path.exists(lineSHP):
    arcpy.SplitLine_management(inSHP, lineSHP)

# TODO zachovat
# erase all lines from shpLinesWS which lie in boundary defined by inDEMBuffer
def eraseBoundarySHP(inDEMBuffer, demWS):  
  # raster is not rectangle
  # Improvement - if exists inDEMBuffer.shp <=> raster is not rectangle
  print ("time %s - DEM raster is irregular" % (time.strftime("%m%d_%H%M%S")))
  tempWS = config.temp
  demDirs = [tempWS]
  createDEMdirs(demWS, demDirs)
  shpLinesWS = config.shpLinesWS
  # clip all input SHPs according to buffer +/- clipDEMSize m
  clipDEMSize = config.clipDEMSize
  # inDEMBuffer must exist!
  if os.path.exists(inDEMBuffer):
    # create buffer + clipDEMSize m
    bufferPlus = demWS + tempWS + "bufferP.shp"
    if not os.path.exists(bufferPlus):
      arcpy.Buffer_analysis(inDEMBuffer,bufferPlus,"%d Meters" % clipDEMSize,"FULL","ROUND","NONE","#")
    # create buffer - clipDEMSize m
    bufferMinus = demWS + tempWS + "bufferM.shp"
    if not os.path.exists(bufferMinus):
      arcpy.Buffer_analysis(inDEMBuffer,bufferMinus,"%d Meters" % -clipDEMSize,"FULL","ROUND","NONE","#")
    # create round buffer (erase)
    bufferErase = demWS + tempWS + "bufferE.shp"
    if not os.path.exists(bufferErase):
      arcpy.Erase_analysis(bufferPlus, bufferMinus, bufferErase)
    arcpy.MakeFeatureLayer_management(bufferErase, "bufferErase")
    # selection and deleteFeatures is made below
    shp_listDir = os.listdir(demWS+shpLinesWS)
    for mySHP in shp_listDir:
      if mySHP[-4:] == ".shp":
        lineSHP = demWS + shpLinesWS + mySHP
        # deleting boundary lines for irregular raster
        print ("time %s - processing %s" % (time.strftime("%m%d_%H%M%S"), mySHP))
        arcpy.MakeFeatureLayer_management(lineSHP, "lineSHP")
        arcpy.SelectLayerByLocation_management("lineSHP","COMPLETELY_WITHIN","bufferErase","","NEW_SELECTION")
        arcpy.DeleteFeatures_management("lineSHP")
  else:
    print ("Raster buffer %s does not exist" %(inDEMBuffer))

# TODO unused
# copy PRJ for files without PRJ file
def completePRJ(inPRJ, inDir):
  shp_listDir = os.listdir(inDir)
  for mySHP in shp_listDir:
    if mySHP[-4:] == ".shp":
      prjName = inDir + mySHP[:-4] + ".prj"
      print (prjName)
      print (os.path.exists(prjName))
      if not os.path.exists(prjName):
        shutil.copyfile(inPRJ, prjName)

# TODO zachovat
# computes raster of relevance
def getRelevantRaster(inDir, bufferSize, outAllR, DEM):
  print ("time %s - computing relevant raster" % (time.strftime("%m%d_%H%M%S")))
  sourceDir = config.sourceDir
  SA = config.getSA(DEM)
  sourceDEM = config.getSourceDEM(DEM)
  rasterDEM = sourceDir + SA + "\\" + sourceDEM + "\\" + DEM
  tempWS = config.temp
  demDirs = [tempWS]
  createDEMdirs(inDir, demDirs)
  cellSize = bufferSize
  # list of rasters to merge
  tiffNames = []
  # for each lineaments according to DEM
  shp_listDir = os.listdir(inDir)
  for shpName in shp_listDir:
    if shpName[-4:] == ".shp":
      inSHP = inDir + shpName
      angleStart = shpName.find("_")+1
      angleEnd = shpName.find("_", angleStart)
      rotateAngle = shpName[shpName.rfind("_")+1:-4]
      outLineName = shpName[0:angleEnd] + "_" +rotateAngle
      outLineR = "in_memory\\" + outLineName
      outLineB = "in_memory\\" + outLineName+"B"
      # buffer inSHP
      lineSHPBuffName = shpName[:-4]+"_buff%d" % bufferSize
      lineSHPBuff = "in_memory\\" + lineSHPBuffName
      if not os.path.exists(lineSHPBuff):
        arcpy.Buffer_analysis(inSHP,lineSHPBuff,"%d Meters" % bufferSize,"FULL","ROUND","NONE","#")
      if not os.path.exists(outLineB):
        # create filed, fill with 1 in order to convert vector to raster
        myField = "binary"
        myValue = 1
        # COMPUTING WITH BUFFER instead of line
        inSHP = lineSHPBuff
        arcpy.AddField_management(inSHP, myField, "SHORT", 2, "", "", "", "NULLABLE", "NON_REQUIRED")
        arcpy.CalculateField_management(inSHP,myField,myValue,"PYTHON_9.3","#")
        # polyline to raster, use this field
        if not os.path.exists(outLineR):
          desc = arcpy.Describe(rasterDEM)
          arcpy.env.extent = desc.extent
          arcpy.PolygonToRaster_conversion(inSHP,myField,outLineR,"CELL_CENTER","NONE",cellSize)
          arcpy.env.extent = "default"
        try:
          # reclassify NoData to 0 !
          arcpy.gp.Reclassify_sa(outLineR,"VALUE","1 1;NODATA 0",outLineB,"DATA")
          tiffNames.append(outLineB)
        except Exception as e:
          print (e)
      arcpy.Delete_management(outLineR)
      arcpy.Delete_management(lineSHPBuff)
  # raster calculator to sum up every raster
  myExpression = ""
  tif_listDir = tiffNames
  for inTIF in tif_listDir:
    myExpression += "\"" + inTIF + "\" + "
  myExpression = myExpression[0:len(myExpression)-2]
  arcpy.gp.RasterCalculator_sa(myExpression, outAllR)

  for inTIF in tif_listDir:
    arcpy.Delete_management(inTIF)

# TODO zachovat
# remove non relevant lines
def relevant(inDir, countThreshold, bufferSize, relevantMerged, DEM):
  tempWS = config.temp
  relevantWS = config.relevantWS
  demDirs = [tempWS, relevantWS]
  createDEMdirs(inDir, demDirs)
  splitField = config.splitField
  
  inRaster = inDir + tempWS + "outAllR"
  # create sum of rasters
  if not os.path.exists(inRaster):
    getRelevantRaster(inDir, bufferSize, inRaster, DEM)
  else:
    print ("Out all raster exist")
  
  # select only relevant lines according to raster approach (same as in Negatives)    
  shp_listDir = os.listdir(inDir)
  for mySHP in shp_listDir:
    if mySHP[-4:] == ".shp":
      inSHP = inDir + mySHP
      lineSHPRelevantsName = mySHP[:-4]+".shp"
      lineSHPRelevant = inDir + relevantWS + lineSHPRelevantsName
      if not os.path.exists(lineSHPRelevant):
        # zonal with one statistic
        zonalLineRelevant(inSHP, inRaster, bufferSize, countThreshold, lineSHPRelevant, "MEDIAN")

  #   # merge to oneSHP
  if not os.path.exists(relevantMerged):
    mergeLines(inDir+relevantWS, relevantMerged)
    # compute azimuths and lenghts
  try:
    calcStats(relevantMerged)
  except Exception as e:
    print (e)
  print ("time %s - deleting relevantWS" % (time.strftime("%m%d_%H%M%S")))
  deletePath(inDir + relevantWS)

# TODO zachovat
def mergeLines(inDir, outMerge):
  toMerge = ""
  splitField = config.splitField
  shp_listDir = os.listdir(inDir)
  for mySHP in shp_listDir:
    if mySHP[-4:] == ".shp":
      inSHP = inDir + mySHP
      if (arcpy.ListFields(inSHP, splitField) == []):
        arcpy.AddField_management(inSHP, splitField, "TEXT")
      splitName = mySHP[:-4]
      arcpy.CalculateField_management(inSHP, splitField, "'%s'" % splitName, "PYTHON_9.3", "#")
      toMerge += "%s;" % (inSHP)
  arcpy.Merge_management(toMerge, outMerge)

##########################################################################################################################
##################################### C L U S T E R   L I N E ############################################################
##########################################################################################################################
# TODO zachovat
# class for working with lines - id, length and azimuth
class line:
  def __init__(self, ID, azimuth, length):
    self.ID = ID
    self.azimuth = azimuth
    self.length = length

# TODO zachovat
# get statistic properties of input set
def getProperties(mySet):
  mySet.sort()
  n = len(mySet)
  myMin = mySet[0]
  myMax = mySet[n-1]
  mean = sum(mySet)/len(mySet)
  std = math.sqrt(sum((x-mean) ** 2 for x in mySet) / n)
  medianIndex = int(0.5*(n+1))
  if len(mySet) == 1:
    median = mySet[0]
  else:
    median = mySet[medianIndex]
#   print (" n: %i \n mean: %0.2f \n std: %0.2f \n median: %0.2f \n min: %0.2f \n max: %0.2f \n " % (n, mean, std, median, myMin, myMax)
  return [n, mean, std, median, myMin, myMax]

# TODO zachovat
# split merged lines using splitField
def splitMerged(relevantMerged, outDir):
  splitField = config.splitField
  # split relevantMerged
  cursor = arcpy.SearchCursor(relevantMerged, "","", splitField)
  splitNames = []
  for c in cursor:
    splitNames.append(c.getValue(splitField))
  # remove duplicates
  uniqueNames = {}.fromkeys(splitNames).keys()
  for splitName in uniqueNames:
    outSHP = outDir + splitName+".shp"
    if not os.path.exists(outSHP):
      arcpy.MakeFeatureLayer_management(relevantMerged,splitName, "%s = '%s'" % (splitField, splitName))
      arcpy.CopyFeatures_management(splitName, outSHP)

# TODO zachovat
# compute line clusters
def cluster(relevantMerged, countThreshold, stopInterval, relevantMergedB, bundleMerged, tb, DEM):
  # config:
  [bufferSizeMin, bufferSizeMax] = config.getBufferSizeCluster()
  azimuthTreshold = config.azimuthTreshold
  # load relevantMerged to in_memory
  relevantMergeLayer = "relevantMerged"
  myMemoryFeature = "in_memory" + "\\" + relevantMergeLayer
  arcpy.CopyFeatures_management(relevantMerged, myMemoryFeature)  
  arcpy.MakeFeatureLayer_management(myMemoryFeature, relevantMergeLayer)
  
  # calculates ID for deleting (FID is recalculated each time after deleting)
  print("calculates ID for deleting")
  if (arcpy.ListFields(relevantMergeLayer, "ShapeId_1")== []):
    arcpy.AddField_management(relevantMergeLayer, "ShapeId_1", "LONG", 8, 2, "", "", "NULLABLE", "NON_REQUIRED")
  arcpy.CalculateField_management(relevantMergeLayer,"ShapeId_1","!FID!","PYTHON_9.3","#")

  # for each row in relevantMerged
  # cursor for iterate rows in length descend order!
  clusterID = 0
  blueSet = []
  bundleSet = []
#   tb.log("cluster ordering")
  # order cursor from the longest to the shortest line
  rows = arcpy.SearchCursor(relevantMergeLayer, "","","","length D")
  # fill the blueset with the rows
  for row in rows:
    blueLine = line(row.ShapeId_1, row.azimuth, row.length)
    blueSet.append(blueLine)
  del rows

  # cleaning
  relevantBackups = []
  # memory push intervals
  blueSetLength = len(blueSet)
  blueInterval =blueSetLength/4+4

  blueIterator = 0
  ######################################  
  # for each line in blueset           #
  ######################################
  for blueLine in blueSet[:stopInterval]:
    myExpression = '"ShapeId_1" =%i' % (blueLine.ID)
    arcpy.SelectLayerByAttribute_management(relevantMergeLayer,"NEW_SELECTION", myExpression)
    noSelected = int(arcpy.GetCount_management(relevantMergeLayer).getOutput(0))
    # if line with ID exists
    if (noSelected == 1):
      # make buffer around blueSHP (bigBuffer for completely within) 
      tempBuffer = "in_memory\\tempBuffer"
      # ? Question of buffer size! # dynamic buffer size according to blueLength - 1/10
      blueLength = blueLine.length
      bufferSize = int(blueLength/10)
      # supremum of buffersize (for extra long paralel lines near together)
      if (bufferSize > bufferSizeMax):
        bufferSize = bufferSizeMax
      # infimum of buffersize (for short lines - small buffer not sufficient)
      if (bufferSize < bufferSizeMin):
        bufferSize = bufferSizeMin
      arcpy.Buffer_analysis(relevantMergeLayer,tempBuffer,"%d Meters" % bufferSize,"FULL","ROUND","ALL","#")
      arcpy.MakeFeatureLayer_management(tempBuffer, "tempBuffer")
      # select all orange in buffer of blue 
      # intersect is better but slower - we will see
      arcpy.SelectLayerByLocation_management(relevantMergeLayer, "COMPLETELY_WITHIN", "tempBuffer", "", "NEW_SELECTION")
      noSelected = int(arcpy.GetCount_management(relevantMergeLayer).getOutput(0))
      isBundle = False
      
      if (noSelected >= countThreshold):  
        # create expression +/- azimuthTreshold from blueLine
        blueMin = blueLine.azimuth - azimuthTreshold
        if blueMin < 0:
          blueMin += 180
        blueMax = blueLine.azimuth + azimuthTreshold
        if blueMax > 180:
          blueMax -= 180
        # this condition is useless. Azimuth is always >=0 and <180, after this simplification the myExpression is the same for both cases. The only important thing is to convert extremes to interval <0,180)
        if (blueLine.azimuth < azimuthTreshold) or (blueLine.azimuth > 180 - azimuthTreshold):
          myExpression = '("azimuth" >= %i and "azimuth" < %i) or ("azimuth" > %i and "azimuth" < %i)' % (0, blueMax, blueMin, 180)
        else:  
          myExpression = '"azimuth" > %i and "azimuth" < %i ' % (blueMin, blueMax)
        ### SELECT THE CLUSTER LINES ###
        arcpy.SelectLayerByAttribute_management(relevantMergeLayer,"SUBSET_SELECTION", myExpression)
        # performance optimalization - go threw only bundle lines
       
        # get count - if < countThreshold do not save, only delete!
        noSelected = int(arcpy.GetCount_management(relevantMergeLayer).getOutput(0))
        if (noSelected >= countThreshold):
          isBundle = True
      
      if (isBundle):        
        clusterID =  blueLine.ID
        # im_memory bundle
        bundle = "in_memory\\line%i" % blueLine.ID
        try:
          arcpy.Buffer_analysis(relevantMergeLayer,bundle,"%d Meters" % 10,"FULL","ROUND","ALL","#")
          # make layer from in_memory bundle
          arcpy.MakeFeatureLayer_management(bundle, "bundle")
          bundleSet.append(bundle)
        except:
          try:
            arcpy.Buffer_analysis(relevantMergeLayer,bundle,"%d Meters" % 12,"FULL","ROUND","ALL","#")
            # make layer from in_memory bundle
            arcpy.MakeFeatureLayer_management(bundle, "bundle")
            bundleSet.append(bundle)
          except:
            continue
                    
        arcpy.AddField_management(bundle, "count", "LONG", 9, "", "", "", "NULLABLE", "NON_REQUIRED")
        arcpy.AddField_management(bundle, "azimuth", "LONG", 9, "", "", "", "NULLABLE", "NON_REQUIRED")
        arcpy.AddField_management(bundle, "length", "LONG", 9, "", "", "", "NULLABLE", "NON_REQUIRED")      

        arcpy.CalculateField_management(bundle,"count",noSelected,"PYTHON_9.3","#")
        
        lengthList = []
        azimuthList = []
        
        # compute stats on selection (cluster lines)
        clusterRows = arcpy.SearchCursor(relevantMergeLayer)
        for clusterRow in clusterRows:
          lengthList.append(clusterRow.getValue("length"))
          azimuthList.append(clusterRow.getValue("azimuth"))
        del clusterRows
        # length stats
        [n, mean, std, median, myMin, myMax] = getProperties(lengthList)
        arcpy.CalculateField_management(bundle, "length", "%i" % int(mean+std),"PYTHON_9.3","#")
        
        azimuthList.sort()
        azimuthMin = azimuthList[0]
        azimuthMax = azimuthList[n-1]
        
        # solve problem with angle numbers!
        # set is on border of azimuths (180-0)
        if ((azimuthMax-azimuthMin)>(2*azimuthTreshold)):
          # new set - recclassify
          azimuthListPlus = [] 
          for azimuth in azimuthList:
            if azimuth > (2*azimuthTreshold):
              azimuthListPlus.append(azimuth-180)  
            else:
              azimuthListPlus.append(azimuth)
          # replace azimuthList
          azimuthList = azimuthListPlus
          
        # compute azimuth statistics
        [n, mean, std, median, myMin, myMax] = getProperties(azimuthList)
        if mean<0:
          mean +=180
        arcpy.CalculateField_management(bundle, "azimuth", "%i" % int(mean),"PYTHON_9.3","#")
      # delete from merged
      arcpy.DeleteFeatures_management(relevantMergeLayer)

####################################  E N D   F O R  ###########################################

  print ("backup")
  # a) backup relevantMerged to disk
  arcpy.SelectLayerByAttribute_management(relevantMergeLayer, "CLEAR_SELECTION")
  arcpy.CopyFeatures_management(relevantMergeLayer, relevantMergedB)
  relevantBackups.append(relevantMergedB)
  # write memory bundles to disk
  # bundleMerged = demWS+bundleWS + "bundleMerged_%i.shp" % blueIterator
  toMerge = ""
  for bundle in bundleSet:
    toMerge+= "in_memory\\%s;" % bundle
#   print toMerge
  # TODO: don't merge if toMerge is empty !
  try:
    arcpy.Merge_management(toMerge,bundleMerged)
    relevantBackups.append(bundleMerged)
  except Exception as e:
    print (toMerge)
    print (e)
  # free memory
  del bundleSet
  
# TODO zachovat
def createBundleLines(demWS):
  mergeWS = config.mergeWS
  bundleWS = config.bundleWS
  tempWS = config.temp
  demDirs = [tempWS]
  createDEMdirs(demWS, demDirs)
  
  print("cluster line algorithm")
  # merge to oneSHP
  bundleMerged = demWS+mergeWS + config.bundleMergedName
  toMerge = ""
  shp_listDir = os.listdir(demWS+bundleWS)
  for mySHP in shp_listDir:
    if mySHP[-4:] == ".shp":
      toMerge+= "%s;" %(demWS+bundleWS+mySHP)  
  # print toMerge
  if len(toMerge) > 0:
    arcpy.Merge_management(toMerge,bundleMerged)
    # createCentroids
    centroidsPoints = demWS + mergeWS + "bundlePoints.shp"
    arcpy.FeatureToPoint_management(bundleMerged, centroidsPoints, "CENTROID")
    # compute average line points
    centroidsLines = demWS + tempWS + "bundleLines.shp"
    centroidsLinesJoin = demWS + mergeWS + "bundleLines.shp"
    newLineList =[]
    shapeName = arcpy.Describe(centroidsPoints).shapeFieldName
    rows = arcpy.SearchCursor(centroidsPoints)
    for row in rows:
      arrayLine = arcpy.Array()
      feat = row.getValue(shapeName)
      pnt = feat.firstPoint
      azimuth = row.getValue("azimuth")
      length = row.getValue("length")
      dX = math.sin(math.radians(azimuth))/2*length
      dY = math.cos(math.radians(azimuth))/2*length
      startPoint = arcpy.Point(pnt.X-dX, pnt.Y-dY)
      arrayLine.add(startPoint)
      endPoint = arcpy.Point(pnt.X+dX, pnt.Y+dY)    
      arrayLine.add(endPoint)
      plyLine = arcpy.Polyline(arrayLine)
      newLineList.append(plyLine)
    del rows
    arcpy.CopyFeatures_management(newLineList, centroidsLines)
    
    arcpy.env.qualifiedFieldNames = False
    arcpy.MakeFeatureLayer_management(centroidsLines, "centroidsLines")
    arcpy.MakeFeatureLayer_management(centroidsPoints, "centroidsPoints")
    arcpy.AddJoin_management("centroidsLines","FID","centroidsPoints","FID","KEEP_ALL")
    arcpy.CopyFeatures_management("centroidsLines",centroidsLinesJoin)
  else:
    print ("bundleWS is empty")

# TODO zachovat
# function to make EAS script for PCI Geomatica - commands for line extraction                         
def printEAS(demWS, scriptEAS, inHill):
  table = open(scriptEAS, 'a')
  dbvs = 3
  workspacePCI = config.workspacePCI
  hlWS = config.hlWS
  easiWS = config.easiWS
  shpWS = config.shpWS   
  demWS = demWS.replace(workspace, workspacePCI)

  table.write("! Setting parameters \n")
  table.write("athr= {0}\n".format(config.athr))
  table.write("dthr= {0}\n".format(config.dthr))
  table.write("fthr= {0}\n".format(config.fthr))
  table.write("radi= {0}\n".format(config.radi))
  table.write("gthr = {0}\n".format(config.gthr))
  table.write("lthr = {0}\n".format(config.lthr))
  table.write("fili = \""+demWS+hlWS+inHill+"\"\n")
  table.write("filo = \""+demWS+easiWS+inHill+".pix\"\n")
  table.write("run fimport\n")
  table.write("fili = filo\n")
  table.write("dboc = 1\n")
  table.write("dbic = 1\nDBVS=\nrun line\n")
  table.write("dbic = \n")
  table.write("DBVS = "+str(dbvs)+"\n")
  table.write("FTYPE = \"SHP\"\n")
  table.write("filo = \""+demWS+shpWS+inHill+".shp\"\n")
  table.write("run fexport\n\n")
  table.close()

# TODO zachovat
# Tool for prepare rasters for extraction
# Input - dem, azimuth range, rotation range
# Output - HLs in dem result directory for each rotation and one EAS script
def extractionRasters(DEM, azimuths, rotations):
  # directories for results
  runEAS = config.runEAS
  hlWS = config.hlWS
  easiWS = config.easiWS
  shpWS = config.shpWS 
  demDirs = [hlWS, easiWS, shpWS]

  # creates runEAS dir
  runEASDir = resultsDir + runEAS
  if not os.path.exists(runEASDir):
    os.mkdir(runEASDir)
  scriptEAS = runEASDir+"%s_%s.EAS" % (time.strftime("%m%d_%H%M%S"), DEM)
  
  SA = config.getSA(DEM)
  sourceDEM = config.getSourceDEM(DEM)
  # input DEM
  inRaster = sourceDir + "\\" + SA + "\\" + sourceDEM + "\\" + DEM
  centerPoint = getRotationCenter(inRaster)

  # parameters
  altitude = config.altitude

  # in case of NO rotation
  rotateDEM0 = DEM.replace("dem", "r%i" % 0)
  demWS0 = resultsDir + SA + "\\" + sourceDEM + "\\" + rotateDEM0 + "\\"
  
  # for each rotation in rotations
  for rotation in rotations:
    rotateDEM = DEM.replace("dem", "r%i" % rotation)
    demWS = resultsDir + SA + "\\" + sourceDEM + "\\" + rotateDEM + "\\"
    # creates directories for result
    if not os.path.exists(demWS):
      os.makedirs(demWS)
    createDEMdirs(demWS, demDirs)
    
    # compute rotated HLs
    for azimuth in azimuths:
      outHL = demWS + hlWS + "hs_%i_r%i" % (azimuth, rotation)
      # if HL exists - will not be calculated again
      if not os.path.exists(outHL):
        print ("time %s - creating HL with azimuth %s" % (time.strftime("%m%d_%H%M%S"), azimuth))
        if rotation == 0:
          arcpy.gp.HillShade_sa(inRaster,outHL,azimuth,altitude,"","")
        else:
          HL0 = demWS0 + hlWS + "hs_%i_r%i" % (azimuth, 0)
          centerInput = "%s %s" % (centerPoint.X, centerPoint.Y)
          arcpy.Rotate_management(HL0, outHL, rotation, centerInput ,"CUBIC")
        printEAS(demWS, scriptEAS, getName(outHL))

# TODO zachovat
# roate point using centre and angle
def rotatePoint(center, point, angle):
  angleRad = math.radians(angle)
  xB = center.X + (point.X - center.X)*math.cos(angleRad)-(point.Y - center.Y)*math.sin(angleRad)
  yB = center.Y + (point.X - center.X)*math.sin(angleRad)+(point.Y - center.Y)*math.cos(angleRad)
  pointB = arcpy.Point(xB, yB) 
  return pointB

# TODO zachovat
# rotate shapefile using centre and angle to output rotatedSHP file
def rotateSHP(inSHP,center, angle, rotatedSHP):
  newLineList =[]
  desc = arcpy.Describe(inSHP)
  shapeName = desc.shapeFieldName
  rows = arcpy.SearchCursor(inSHP)
  for row in rows:
    feat = row.getValue(shapeName)
    partnum = 0
    for part in feat:
      # a new pair of points 
      arrayLine = arcpy.Array()
      # Step through each vertex in the feature
      for pnt in feat.getPart(partnum):
          if pnt:
              pnt2 = rotatePoint(center, pnt, angle)
              arrayLine.add(pnt2)
          else:
              # If pnt is None, this represents an interior ring
              print ("Interior Ring:")
      plyLine = arcpy.Polyline(arrayLine)
      newLineList.append(plyLine)
      partnum += 1 
  arcpy.CopyFeatures_management(newLineList, rotatedSHP)

# TODO zachovat
# for each shp in structure call rotateSHP
def rotateBack(DEM, rotations):
  shpWS = config.shpWS
  SA = config.getSA(DEM)
  sourceDEM = config.getSourceDEM(DEM)
  inRaster = sourceDir + "\\" + SA + "\\" + sourceDEM + "\\" + DEM
  ceterPoint = getRotationCenter(inRaster)
  
  shpRotateWS = config.shpRotateWS
  demDirs = [shpRotateWS]
  
  # for each rotation in rotations
  for rotation in rotations:
    rotateDEM = DEM.replace("dem", "r%i" % rotation)
    demWS = resultsDir + SA + "\\" + sourceDEM + "\\" + rotateDEM + "\\"
    # if extracted SHPs exist
#     print os.path.exists(demWS+shpWS)
    if os.path.exists(demWS+shpWS):
      shp_listDir = os.listdir(demWS+shpWS)
      if len(shp_listDir) != 0:
        createDEMdirs(demWS, demDirs)
        for mySHP in shp_listDir:
          if mySHP[-4:] == ".shp":
            inSHP = demWS+shpWS+mySHP 
            rotatedSHP = demWS + shpRotateWS + "\\" + mySHP
            if not os.path.exists(rotatedSHP):
              if rotation != 0:
                rotateSHP(inSHP, ceterPoint, rotation, rotatedSHP)
              else:
                arcpy.Copy_management(inSHP, rotatedSHP)

# TODO zachovat
# spatial line clustering
def optimizedClusterLine(DEM, rotations, tb, lock):
  lock.acquire()
  optimalStop = config.optimalStop

  clearWS = config.clearWS
  shpLinesWS = config.shpLinesWS
  bundleWS = config.bundleWS
  mergeWS = config.mergeWS
  demDirs = [bundleWS, clearWS, mergeWS]

  SA = config.getSA(DEM)
  sourceDEM = config.getSourceDEM(DEM)

  # for each rotation in rotations
  for rotation in rotations:
    rotateDEM = DEM.replace("dem", "r%i" % rotation)
    tb.log("optimizedClusterLine: %s" % rotateDEM)
    demWS = resultsDir + SA + "\\" + sourceDEM + "\\" + rotateDEM + "\\"
    if os.path.exists(demWS + shpLinesWS):
      createDEMdirs(demWS, demDirs)

      # first relevant
      inDir = demWS + shpLinesWS
      relevantMergedName = config.relevantMergedName
      bundleMergedName = config.bundleMergedName
      relevantT = config.relevantT
      clusterT = config.clusterT
      if (rotation == 99):
        relevantT -= 2
        clusterT -= 2
      bufferSize = config.getCellSize(DEM)
      relevantMerged = demWS + mergeWS + relevantMergedName
      bundleMerged = demWS + mergeWS + bundleMergedName
      if not os.path.exists(relevantMerged):
        tb.log("relevant")
        relevant(inDir, relevantT, bufferSize, relevantMerged, DEM)

      bundleLines = demWS + mergeWS + "bundleLines.shp"
      if not os.path.exists(bundleLines):
        result = arcpy.GetCount_management(relevantMerged)
        relevantCount = int(result.getOutput(0))
        relevantCountStart = relevantCount
        stopInterval = relevantCount / 8
        while (relevantCount > optimalStop):
          # cluster line
          relevantMergedB = demWS + clearWS + "RM_%i.shp" % (relevantCount-stopInterval)
          bundleMerged = demWS + bundleWS + "BM_%i.shp" % (relevantCount-stopInterval)
          makeDirs(getDir(relevantMergedB))
          tb.log("cluster")
          cluster(relevantMerged, clusterT, stopInterval, relevantMergedB, bundleMerged, tb, DEM)

          # split merged
          tb.log("splitMerged")
          relevantSplit = relevantMergedB
          relevantSplitName = getName(relevantSplit)
          splitDir = getDir(relevantSplit)+"split_%s\\" % relevantSplitName[:-4]
          makeDirs(splitDir)
          splitMerged(relevantSplit, splitDir)

          # relevant
          bufferSize = config.getCellSize(DEM)
          relevantCleared = relevantMergedB[:-4] + "_C.shp"
          tb.log("relevant")
          relevant(splitDir, relevantT, bufferSize, relevantCleared, DEM)

          # cycle
          relevantMerged = relevantCleared
          result = arcpy.GetCount_management(relevantMerged)
          relevantCount = int(result.getOutput(0))
          # more than 1/2 remains - 1/8 else 1/4
          if (relevantCountStart/2+2) <= relevantCount:
            stopInterval = relevantCount / 8
          else:
            stopInterval = relevantCount / 4
          print (relevantCount)

        # cluster line
        relevantMergedB = demWS + clearWS + "RM_%i.shp" % (relevantCount-stopInterval)
        bundleMerged = demWS + bundleWS + "BM_%i.shp" % (relevantCount-stopInterval)
        makeDirs(getDir(relevantMergedB))
        tb.log("cluster")
        cluster(relevantMerged, clusterT, optimalStop, relevantMergedB, bundleMerged, tb, DEM)

        # Create Average Lines of Bundles
        tb.log("createBundleLines")
        createBundleLines(demWS)
        # computeAndPlotHist(bundleLines)
  lock.release()

# TODO zachovat
# plot histograms using folder structure
def computeAndPlotHists(DEM, rotations, classType):
  mergeWS = config.mergeWS
  negativeWS = config.negativeWS
  SA = config.getSA(DEM)

  yMax = config.yMax
  radMax = config.radMax
  print ("compute and plot histogram")
  graphTitle = "Rotation"
  sourceDEM = config.getSourceDEM(DEM)
  filterCount = config.filterCount
  filterCountKIV = config.filterCountKIV
  histWS = config.histWS[:-1]+"_%s" %config.getCellSize(DEM)+"\\"
  demDirs = [histWS]
  createDEMdirs(resultsDir + SA + "\\" + sourceDEM + "\\", demDirs)

  # for each rotation in rotations
  for rotation in rotations:
    rotateDEM = DEM.replace("dem", "r%i" % rotation)
    demWS = resultsDir + SA + "\\" + sourceDEM + "\\" + rotateDEM + "\\"
    if classType == "all":
      bundleLines = demWS + mergeWS + "bundleLines.shp"
      bundleLinesKIV = demWS + mergeWS + "bundleLines_KIV.shp"
    elif classType == "negative":
      bundleLines = demWS + negativeWS + "bundleLines_NU.shp"
      bundleLinesKIV = demWS + negativeWS + "bundleLines_KIV_NU.shp"
    elif classType == "positive":
      bundleLines = demWS + negativeWS + "bundleLines_P.shp"
      bundleLinesKIV = demWS + negativeWS + "bundleLines_KIV_P.shp"
    outHist = bundleLinesKIV[:-4] + "_hist.csv"
    histDir = resultsDir + SA + "\\" + sourceDEM + "\\" + histWS

    if os.path.exists(bundleLinesKIV):
      if not os.path.exists(outHist):
        getHistogram(bundleLinesKIV, filterCountKIV)
      plotHist(outHist, histDir + getName(bundleLinesKIV)[:-4] + "_r%i_hist.png" %rotation, yMax, radMax, "", "%s %s dg" % (graphTitle, rotation), "C# KIV", "", 4,4, "png")

# TODO zachovat
def splitAndErase(DEM, rotations):
  shpRotateWS = config.shpRotateWS
  shpLinesWS = config.shpLinesWS
  demDirs = [shpLinesWS]

  SA = config.getSA(DEM)
  sourceDEM = config.getSourceDEM(DEM)
    
  # for each rotation in rotations
  for rotation in rotations:
    rotateDEM = DEM.replace("dem", "r%i" % rotation)
    demWS = resultsDir + SA + "\\" + sourceDEM + "\\" + rotateDEM + "\\"
    if os.path.exists(demWS + shpRotateWS):
      createDEMdirs(demWS, demDirs)
      # split lines
      splitLines(demWS, shpRotateWS, shpLinesWS)
      # raster is not rectangle
      inDEMBuffer = sourceDir + SA + "\\" + sourceDEM + "\\" + "boundary.shp"
      print ("eraseB")
      if os.path.exists(inDEMBuffer):
        eraseBoundarySHP(inDEMBuffer, demWS)
      else:
        print ("Do not clip - boundary does not exist!")

# get csv for length weigthted histogram
# Improvement remove filterCount param - is not general need
# Improvement make output histogram as input parameter, not output
# TODO zachovat
def getHistogram(inSHP, filterCount):
  # if count field exists
  if not (arcpy.ListFields(inSHP, "count")== []):
    # use only features with more than filterCount in count field
    arcpy.MakeFeatureLayer_management(inSHP, "inSHP", '"count" >= %i' % filterCount)
  else:
    # use all features
    arcpy.MakeFeatureLayer_management(inSHP, "inSHP")

  # if azimuth and lenght stats not exists
  if (arcpy.ListFields(inSHP, "azimuth")== [] or arcpy.ListFields(inSHP, "length")== []):
    # calculate azimuth and lenght
    calcStats(inSHP)
  # output histogram statistics
  if ((inSHP)[-4:] == ".shp"):
    histFileName = inSHP[:-4] + "_hist.csv"
  else:
    histFileName = getDir(getDir(inSHP)[:-1]) + getName(inSHP) + "_hist.csv"

  histFile = open(histFileName, 'w')

  # total length and total count
  rows = arcpy.SearchCursor("inSHP")
#   rows = arcpy.SearchCursor(inSHP)
  totalCount = int(arcpy.GetCount_management("inSHP").getOutput(0))
#   totalCount = 0
  totalLength = 0
  histM = []
#   cluster = []
  for row in rows:
    histM.append([row.azimuth, row.length])
    totalLength += row.getValue("length")
#     totalCount +=1
  print (totalLength)
  print (totalCount)

  # for each degree count number and total length
  for az in range(0,180,1):
    noSelected = 0
    intervalLength = 0
    for row in histM:
      A = row[0]
      if (az <= A < az+1):
        noSelected += 1
        intervalLength += row[1]
    if (noSelected != 0):
      histText = "%i; %i; %0.2f; %f; %f\n" % (az, noSelected, intervalLength, (float(noSelected)/totalCount*100), (100*float(intervalLength)/totalLength))
      histText = histText.replace(".", ",")
      histFile.write(histText)
    else:
      histText = "%i; 0; 0; 0; 0\n" % az
      histFile.write(histText)

  histFile.close()
  return histFileName

def copyAngles(DEM, rotations, azimuths):
  shpLinesWS = config.shpLinesWS
  mergeWS = config.mergeWS
  demDirs = [shpLinesWS]
  
  # copy and rename bundleLines.shp to new DEM based folder r9x
  SA = config.getSA(DEM)
  SA3 = SA+"_III"
  sourceDEM = config.getSourceDEM(DEM)
  outWS = resultsDir + SA3 + "\\" + sourceDEM + "\\"

  for azimuth in azimuths:
    outDEM = DEM.replace("dem", "r%i" % azimuth)
    makeDirs(outWS+outDEM)
    outDemWS = outWS + outDEM + "\\"
    createDEMdirs(outDemWS, demDirs)
    for rotation in rotations:
      rotateDEM = DEM.replace("dem", "r%i" % rotation)
      demWS = resultsDir + SA + "\\" + sourceDEM + "\\" + rotateDEM + "\\"
      inSHPName = "hs_%i_r%i.shp" %(azimuth, rotation)
      inSHP = demWS + shpLinesWS + inSHPName 
      
      if os.path.exists(inSHP):
        copySHP = outDemWS + shpLinesWS + inSHPName
        if not os.path.exists(copySHP):
          print ("copy %s" % copySHP)
          arcpy.Copy_management(inSHP, copySHP)

# TODO zachovat
# prepare data for last step of hierachical clustering
def finalCluster(DEM, clusterName):
  azimuths = config.azimuths
  rotations = config.rotations
  shpLinesWS = config.shpLinesWS
  mergeWS = config.mergeWS
  demDirs = [shpLinesWS]

  # copy and rename bundleLines.shp to new DEM based folder r9x
  SA = config.getSA(DEM)
  sourceDEM = config.getSourceDEM(DEM)

  outWS = resultsDir + SA + "\\" + sourceDEM + "\\"
  outDEM = DEM.replace("dem", "r%i" % clusterName)

  for rotation in rotations:
    rotateDEM = DEM.replace("dem", "r%i" % rotation)
    demWS = resultsDir + SA + "\\" + sourceDEM + "\\" + rotateDEM + "\\"
    inSHP = demWS + mergeWS + "bundleLines.shp"
    
    if os.path.exists(inSHP):
      createDEMdirs(outWS, [outDEM]) 
      outDemWS = outWS + outDEM + "\\"
      createDEMdirs(outDemWS, demDirs)
      copySHP = outDemWS + shpLinesWS + "hs_%i_r%i.shp" %(rotation, clusterName)
      if not os.path.exists(copySHP):
        print ("copy %s" % copySHP)
        arcpy.Copy_management(inSHP, copySHP)

# computes lines statistics of length
def getLineLengthStats(inSHP, statFile):
  # compute stats to output temp table
  print "time %s - getting LENGTH stats" % (time.strftime("%m%d_%H%M%S"))
  mergedStats = inSHP[:-4] + "_stats.dbf"
  if (arcpy.ListFields(inSHP, "length") == []):
    calcStats(inSHP)
  arcpy.Statistics_analysis(inSHP, mergedStats, "length SUM; length MEAN; length MIN; length MAX", "#")

  curT = arcpy.SearchCursor(mergedStats)
  # one row supposed
  row = curT.next()
  desc = arcpy.Describe(mergedStats)
  for field in desc.fields[1:]:
    fieldName = field.Name
    print "%s = %s" % (fieldName, row.getValue(fieldName))
    value = "%0.2f" % row.getValue(fieldName)
    value = value.replace(".", ",")
    statFile.write("%s;" % value)
  statFile.write("\n")
  # delete temp stats table
  arcpy.Delete_management(mergedStats)

# TODO zachovat
# STEP 06 - Classification of lineaments
def classifyRidges(DEM, rotations):
  print ("time %s - running script for DEM %s" % (time.strftime("%m%d_%H%M%S"), DEM))
  # directories for results
  mergeWS = config.mergeWS
  negativeWS = config.negativeWS
  tempWS = config.temp
  flowWS = config.flowWS
  demDirs = [negativeWS, tempWS, flowWS]
  
  bufferSize = config.bufferSizeRidges
  meaPar = [config.parMeaRidge, config.parMeaValley]
  medPar = [config.parMedRidge, config.parMedValley]  

  # input DEM
  SA = config.getSA(DEM)
  sourceDEM = config.getSourceDEM(DEM)
  inDEM = sourceDir + SA + "\\" + sourceDEM + "\\" + DEM
  
  for rotation in rotations:
    rotateDEM = DEM.replace("dem", "r%i" % rotation)
    demWS = resultsDir + SA + "\\" + sourceDEM + "\\" + rotateDEM + "\\"
    lineSHP = demWS + mergeWS + "bundleLines.shp"
    print (lineSHP)
    if os.path.exists(lineSHP):
      createDEMdirs(demWS, demDirs)
      
      # compute FlowAcc for DEM
      flowAcc = getFlowAcc(demWS, inDEM)
      
      # call function to separate ridges and valleys lines
      mySHP = getName(lineSHP)
      lineSHPNegativesName = mySHP[:-4]+"_N.shp"
      lineSHPNegative = demWS + negativeWS + lineSHPNegativesName
      lineSHPPositivesName = mySHP[:-4]+"_P.shp"
      lineSHPPositive = demWS + negativeWS + lineSHPPositivesName
      lineSHPUnsuresName = mySHP[:-4]+"_U.shp"
      lineSHPUnsure = demWS + negativeWS + lineSHPUnsuresName      
      # classify lines using threshold for flowAcc field (3 classes - positive, unsure, negative)
      zonalLine(lineSHP, flowAcc, bufferSize, meaPar, medPar, lineSHPNegative, lineSHPPositive, lineSHPUnsure)
      
      # 7.11. merge non tested :-)
      lineSHPNUName = mySHP[:-4]+"_NU.shp"
      lineSHPNU = demWS + negativeWS + lineSHPNUName
      arcpy.Merge_management("%s;%s" % (lineSHPNegative,lineSHPUnsure),lineSHPNU)

# TODO zachovat
# function to compare two lines
def compareLines(blueSHP, orangeSHP, isClip, logFileName, azimuthTreshold, bufferSize):
  try:
    logFile = open(logFileName, 'a')
    # if statistics does not exist -> compute!
    if (arcpy.ListFields(blueSHP, "azimuth") == []) or (arcpy.ListFields(blueSHP, "length") == []):
      calcStats(blueSHP)
    if (arcpy.ListFields(orangeSHP, "azimuth") == []) or (arcpy.ListFields(orangeSHP, "length") == []):
      calcStats(orangeSHP)
    # parameters from config/input
    usedMethod = "Centroids"
    if isClip:
      usedMethod = "Clip"
    logFile.write("%s; %s; %s; %i; %i;" % (blueSHP, orangeSHP, usedMethod, azimuthTreshold, bufferSize))
    # correlation based on count
    noSimilar = 0
    # length weighted correlation index
    corrISum = 0
    lengthCorrSum = 0
    lengthA = 0

    rows = arcpy.SearchCursor(blueSHP)
    for row in rows:
      lengthA += row.getValue("length")

    ### IF USING CENTROID METHOD
    if not isClip:
      # from orange make centroids
      orangeSHPLyr = orangeSHP[:-4] + "_centroids.shp"
      if not os.path.exists(orangeSHPLyr):
        arcpy.FeatureToPoint_management(orangeSHP, orangeSHPLyr, "CENTROID")
      arcpy.MakeFeatureLayer_management(orangeSHPLyr, "orangeLyr")

    # count number of lines in blueSHP
    result = arcpy.GetCount_management(blueSHP)
    noFeatures = int(result.getOutput(0))
    noLines = noFeatures
    procento = 0
    # for each feature in blue
    for val in range(0, int(noFeatures), 1):
      orangeLength = 0
      # layer for blue
      arcpy.MakeFeatureLayer_management(blueSHP, "blueFeat", "FID = %i" % val)

      ### IF USING CLIP METHOD
      # TODO: test azimuth before cliping!
      if isClip:
        # make buffer around blueLine
        blueBuffer = blueSHP[:-4] + "_buffer.shp"
        arcpy.Buffer_analysis("blueFeat", blueBuffer, "%d Meters" % bufferSize, "FULL", "ROUND", "NONE", "#")
        # find intersection with orange
        orangeSHPLyr = orangeSHP[:-4] + "_clip.shp"
        arcpy.Clip_analysis(orangeSHP, blueBuffer, orangeSHPLyr, "#")
        arcpy.MakeFeatureLayer_management(orangeSHPLyr, "orangeLyr")
      else:
        # find intersection with orange
        arcpy.SelectLayerByLocation_management("orangeLyr", "WITHIN_A_DISTANCE", "blueFeat", "%d Meters" % bufferSize,
                                               "NEW_SELECTION")

      ### AT THIS POINT, orangeLyr EXISTS in every case

      # number of selected orange features
      result = arcpy.GetCount_management("orangeLyr")
      noFeatures = int(result.getOutput(0))
      #       print "Pocet pruseciku: %i" % noFeatures

      # if the intersect exists
      if (noFeatures != 0):
        # get sttributes for blueSHP
        rows = arcpy.SearchCursor("blueFeat")
        # blueFeat je jen jeden radek!
        for row in rows:
          azimuth = row.getValue("azimuth")
          blueLength = row.getValue("length")
          blueMin = azimuth - azimuthTreshold
          if blueMin < 0:
            blueMin = 180 + blueMin
          blueMax = azimuth + azimuthTreshold
          if blueMax > 180:
            blueMax = blueMax - 180
          if (azimuth < azimuthTreshold) or (azimuth > 180 - azimuthTreshold):
            myExpression = '("azimuth" >= %i and "azimuth" < %i) or ("azimuth" > %i and "azimuth" < %i)' % (
            0, blueMax, blueMin, 180)
          else:
            myExpression = '"azimuth" > %i and "azimuth" < %i ' % (blueMin, blueMax)
            ### SELECT THE SIMILAR LINES ###
            #         print myExpression
          ###
          # use SUBSET_SELECTION IF USING CENTROID METHOD
          selectionMethod = "SUBSET_SELECTION"
          if isClip:
            selectionMethod = "NEW_SELECTION"

          arcpy.SelectLayerByAttribute_management("orangeLyr", selectionMethod, myExpression)

          noSelected = int(arcpy.GetCount_management("orangeLyr").getOutput(0))
          #           print "Pocet podobnych linii: %i" % noSelected
          if (noSelected != 0):
            ### IF USING CLIP METHOD recalculate length stats
            if isClip:
              calcStats("orangeLyr")
            # count length of orange
            rows = arcpy.SearchCursor("orangeLyr")
            for row in rows:
              orangeLength += row.getValue("length")
            corrI = min(float(orangeLength) / blueLength, 1)
            #             print corrI
            # correlation improvement - if correlation is grater than 80 % it can be considered like 100 %
            # prof. Minar disagree -> 1.66 = switched off
            if (corrI > 1.66):
              lengthCorrSum += blueLength
            else:
              lengthCorrSum += min(orangeLength, blueLength)
            corrISum += corrI
            #           print "orangeLength sum = %0.2f, blueLength = %0.2f corrI = %0.2f" %(orangeLength, blueLength, corrI)
            noSimilar += 1
            aktualni = val * 100 / noLines
            if (procento - aktualni != 0):
              print "%s pct" % (val * 100 / noLines)
            procento = aktualni
            #   print noSimilar
    corrA = float(lengthCorrSum) / lengthA * 100  # length weigthed divided by length
    corrB = float(noSimilar) / noLines * 100  # based on correlated no. lines
    corrC = float(corrISum) / noLines * 100  # length weigthed divided by no. lines
    logFile.write("%0.2f; %i; %i; %0.2f; %i; %i; %0.2f; %0.2f;\n" % (
    corrA, lengthA, lengthCorrSum, corrB, noLines, noSimilar, corrC, corrISum))
    # nezamenovat DeleteFeatures s Delete

    arcpy.Delete_management(orangeSHPLyr)
    if isClip:
      arcpy.Delete_management(blueBuffer)
    print corrA
  # logFile.write("from %i lines, %s lines correlated with line B, thus correlation is %0.2f pct with tolerance of %i degrees in radius of %i\n" % (noLines, noSimilar, float(noSimilar)/noLines*100, azimuthTreshold, bufferSize))
  #   logFile.write("length weighted correlation index is %0.2f thus correlation is %0.2f pct\n" % (corrISum,float(corrISum)/noLines*100))
  #   logFile.write("Sum of correlation length is %0.2f thus correlation is %0.2f pct\n" % (lengthCorrSum,corrA)
  except Exception, e:
    print e
    #     logFile.write(e)
    traceback.print_exc(file=logFile)
  finally:
    logFile.close()


def computeHist(inSHP, myDict, yMax, radMax, fileFormat):
  # output stats are placed in the same dir as input with the derived names
  # output statistic CSV - this file can be processed in Excell to plot graphs
  outStats = getHistogram(inSHP, 0)  # return name inSHP[:-4] + "_hist.csv"
  # output histogram PNG
  if ((inSHP)[-4:] == ".shp"):
    outFile = inSHP[:-4] + "_hist." + fileFormat
  else:
    outFile = getDir(getDir(inSHP)[:-1]) + getName(inSHP) + "_hist." + fileFormat

  print outFile
  try:
    name = myDict[getName(inSHP)[:-4]]
  except KeyError:
    print "no dict defined"
  finally:
    name = getName(inSHP)
  print name
  plotHist(outStats, outFile, yMax, radMax, "", u"Smerova statistika %s" % name, name, "B", 4, 4, fileFormat)

def compareTwoHists(inSHP, inSHP0, yMax, radMax, fileFormat):
  # output stats are placed in the same dir as input with the derived names
  # output statistic CSV - this file can be processed in Excell to plot graphs

  outStats = getHistogram(inSHP, 0)  # return name inSHP[:-4] + "_hist.csv"
  outStats0 = getHistogram(inSHP0, 0)  # return name inSHP[:-4] + "_hist.csv"

  # output histogram PNG
  outFile = inSHP[:-4] + "_compare_hist." + fileFormat
  name = getName(inSHP)[:-4]
  name0 = getName(inSHP0)[:-4]
  plotHist(outStats, outFile, yMax, radMax, outStats0, "Comparison %s with %s" % (name, name0), name, name0, 4,
                   4, fileFormat)

def plotHist(inHistPath, outPNG, yMax, radMax, inHist0Path, graphTitle, labelA, labelB, filterCountA, filterCountB, fileFormat):
  headerFont = FontProperties()
  headerFont.set_weight("bold")
  headerFont.set_size("xx-large")  
  captionFont = FontProperties()
#   captionFont.set_weight("bold")
  captionFont.set_size("x-large")
  axisFont = FontProperties()
  axisFont.set_size("large")
  axisFont.set_weight("bold")
  colorA = "blue"
  colorB = "red"
  t = range(0, 180, 1)
  count0 = 0
  if not inHist0Path == "":
    inHist0 = open(inHist0Path, "r")
    s0 = []
    
    for row in inHist0:
      rs = row.split(";")
      lw = rs[4].strip()
      count0 += int(rs[1].strip())
      s0.append(float(lw.replace(",", ".")))
  
    mA0 = []
    for i in t:
      if i < 3:
        subsetA = s0[i-3:]
        subsetB = s0[:i+4]
        subset = subsetA+subsetB
      elif i > 176:
        subsetA = s0[i-3:]
        subsetB = s0[:4-(len(s0)-i)]
        subset = subsetA+subsetB
      else:
        subset = s0[i-3:i+4]
      mA0value = mean = sum(subset)/len(subset)
      mA0.append(mA0value)

  count = 0
  inHist = open(inHistPath, "r")
  s = []
  
  for row in inHist:
    rs = row.split(";")
    lw = rs[4].strip()
    count += int(rs[1].strip())
    s.append(float(lw.replace(",", ".")))

  
  mA = []
  for i in t:
    if i < 3:
      subsetA = s[i-3:]
      subsetB = s[:i+4]
      subset = subsetA+subsetB
    elif i > 176:
      subsetA = s[i-3:]
      subsetB = s[:4-(len(s)-i)]
      subset = subsetA+subsetB
    else:
      subset = s[i-3:i+4]
    mAvalue = mean = sum(subset)/len(subset)
    mA.append(mAvalue)
  
  plt.clf()
  fig = plt.figure()
  if not inHist0Path == "":
    gs = gridspec.GridSpec(1, 3, width_ratios=[3, 1, 1])
  else:
   gs = gridspec.GridSpec(1, 2, width_ratios=[3, 1])
  ax1 = fig.add_subplot(gs[0])  
  
  plt.plot(t, mA, linewidth=3.0, color = colorA, label = labelA)
  if not inHist0Path == "":
    plt.plot(t, mA0, linewidth=3.0, color = colorB, label = labelB)
  
  plt.xlabel(u'uhel [dg]', fontproperties=axisFont)
  plt.ylabel(u'pomer delek [%]', fontproperties=axisFont)
  inHistName = getName(inHistPath)
  plt.title(graphTitle, fontproperties=headerFont)
  plt.legend()
  plt.grid(True)
  
  F = plt.gcf()
  if inHist0Path == "":
    ax1.bar(t, s, color="gray", edgecolor='none')
  
  F.set_size_inches(24,6)# resetthe size
  plt.xticks(range(0,len(t)+5,5), fontproperties=axisFont)
  if yMax > 0:
    plt.yticks(range(0,yMax,1), fontproperties=axisFont)
    plt.ylim(0,yMax)
  plt.xlim(0,180)
  plt.tight_layout()
  
  #### add polar plot ####
  ax = fig.add_subplot(gs[1], polar=True)
#   ax.set_title("c# KIV")
  step = 5
  t = range(0, 180, step)
  mP = []
  for i in t:
    mP.append(sum(s[i:i+step-1]))
  mP += mP
  theta = np.linspace(0.0, 2 * np.pi, 360/step, endpoint=False)
  radii = np.random.rand(len(theta))
  width = step*np.pi/180

  ax.set_theta_zero_location('N')
  ax.set_theta_direction(-1)
  ax.set_yticks(range(0,radMax,2))
  xLabels = ax.get_xticklabels()
  myKwargs = {"fontproperties": captionFont}

#   for xLabel in xLabels:
#     print xLabel
  dg = u'\xb0'
  ax.set_xticklabels((u'0%s' % dg, u'45%s' % dg, u'90%s' % dg, u'135%s' % dg, u'180%s' % dg, u'225%s' % dg, u'270%s' % dg, u'315%s' % dg), fontproperties=captionFont)
  yLabels = ax.get_yticklabels()
#   for yLabel in yLabels: 
#     print yLabel
  ax.set_ylim(0,radMax)
  bars = ax.bar(theta, mP, width=width, bottom=0.0)

  # Use custom colors and opacity
  for r, bar in zip(radii, bars):
      bar.set_facecolor(colorA)
      bar.set_alpha(0.5)
      bar.set_edgecolor(colorA)
#   for i in np.linspace(0.0, 2 * np.pi, 8, endpoint=False):
#     for j in range(0,15,3):
#       plt.text(i,j, "%i,%i" % (i*180/np.pi,j))
  plt.text(315.0/180*np.pi, 1.42*radMax, labelA, fontproperties=captionFont)
  plt.text(225.0/180*np.pi, 1.72*radMax, u"Pocet:%i" % (count), fontproperties=captionFont)

  if not inHist0Path == "":
    #### add polar plot ####
    ax2 = fig.add_subplot(gs[2], polar=True)
  #   ax2.set_title("Python")
    step = 5
    t = range(0, 180, step)
    mP0 = []
    for i in t:
      mP0.append(sum(s0[i:i+step-1]))
    mP0 += mP0  
    theta = np.linspace(0.0, 2 * np.pi, 360/step, endpoint=False)
    radii = np.random.rand(len(theta))
    width = step*np.pi/180
  
    ax2.set_theta_zero_location('N')
    ax2.set_theta_direction(-1)
    ax2.set_yticks(range(0,radMax,2))
    ax2.set_ylim(0,radMax)
    bars = ax2.bar(theta, mP0, width=width, bottom=0.0)
     
    # Use custom colors and opacity
    for r, bar in zip(radii, bars):
        bar.set_facecolor(colorB)
        bar.set_alpha(0.5)
        bar.set_edgecolor(colorB)
    plt.text(315.0/180*np.pi, 10, labelB, fontproperties=captionFont)
    plt.text(225.0/180*np.pi, 12, "Count:%i\ncT:%i" % (count0, filterCountB), fontproperties=captionFont)
  plt.subplots_adjust(wspace=0.1)
  F.savefig(outPNG, format=fileFormat)
#   plt.show()
  if not inHist0Path == "":
    inHist0.close()
  inHist.close()
  plt.close('all')

# MHHCA preparation
# export coordinates from input SHP to TXT
# polarize lines to directions 0-180 dg 
# polarizace nezafunguje na prechodu 179-0 a v jeho okoli - nevhodne treba pro KIV a! a pak nevhodne pro prumerovani
def polarize(inSHP, outTXTName):
#   outTXTName = inSHP[:-4]+"_XYA_P.txt"
  outTXT = open(outTXTName, "w")
  
  textLog = "ID; A.X; A.Y; B.X; B.Y; A; L\n"
  outTXT.write(textLog)
  
  rows = arcpy.SearchCursor(inSHP, "","","","length D")
#   rows = arcpy.SearchCursor(inSHP, "","","")
  desc = arcpy.Describe(inSHP)
  shapefieldname = desc.ShapeFieldName 
  for row in rows:
    feat = row.getValue(shapefieldname)
    pnts = getPoints(feat)
    A = pnts[0]
    B = pnts[1]

    dY = (A.Y - B.Y)
    dX = (A.X - B.X)
    atan2 = math.atan2(dY,dX)
    alpha = math.degrees(atan2)
#     print ("(%i,%i): %i dg, %f rad" % (B.X, B.Y, alpha, atan2)
    
    if 90 >= alpha > -90:
#       print ("switch"
      C = A
      A = B
      B = C
    textLog = "%i;%i;%i;%i;%i;%i;%i;\n" % (row.FID, A.X, A.Y, B.X, B.Y, row.azimuth, row.length)
    outTXT.write(textLog)
  
  outTXT.close()

# MHHCA preparation
def writeAverageSHP(clusterSet, resultSHP, clusterT, inSHP):
  averageMethod = config.averageMethod
#   tb.log("prepare SHP")
  azimuthTreshold = config.azimuthTreshold
  polylineList =[]
  attributeList = []
  countList = []
  for c in clusterSet:
    # filter clusters with insufficient number of lines      
    if len(c.IDs) >= clusterT:
      # if cluster is on the border 179-0-1 (suppose that azimuth threshold has been applied)
      if (max(c.A) - min(c.A)) > 2*azimuthTreshold:
        # for every lines with A < 0 - switch start to end
        for i in range(0,len(c.A),1):
          if c.A[i] > 2*azimuthTreshold:
            Cx = c.Ax[i]
            Cy = c.Ay[i]
            c.Ax[i] = c.Bx[i]
            c.Ay[i] = c.By[i]
            c.Bx[i] = Cx
            c.By[i] = Cy
            
#       print c.myId
      
      if (averageMethod == "aritmetic"):
        # aritmetic average of coordinates
        Ax = (sum(c.Ax)/len(c.Ax))
        Ay = (sum(c.Ay)/len(c.Ay))
        Bx = (sum(c.Bx)/len(c.Bx))
        By = (sum(c.By)/len(c.By))
      elif(averageMethod == "centers"):
        # preserve only centers as cluster's representants
        Ax = c.Ax[0]
        Ay = c.Ay[0]
        Bx = c.Bx[0]
        By = c.By[0]
      elif (averageMethod == "lw_average"):
        sumAx = 0
        sumAy = 0
        sumBx = 0
        sumBy = 0      
        for i in range (0, len(c.Ax), 1):
          length = c.length[i]
          sumAx += c.Ax[i]*length
          sumAy += c.Ay[i]*length
          sumBx += c.Bx[i]*length
          sumBy += c.By[i]*length
        sumLength = sum(c.length)
        Ax = sumAx/sumLength
        Ay = sumAy/sumLength
        Bx = sumBx/sumLength
        By = sumBy/sumLength
      elif (averageMethod == "centroid"):
        sumAx = 0
        sumAy = 0
        sumBx = 0
        sumBy = 0      
        for i in range (0, len(c.Ax), 1):
          length = c.length[i]
          sumAx += c.Ax[i]*length
          sumAy += c.Ay[i]*length
          sumBx += c.Bx[i]*length
          sumBy += c.By[i]*length
        sumLength = sum(c.length)
        Ax = sumAx/sumLength
        Ay = sumAy/sumLength
        Bx = sumBx/sumLength
        By = sumBy/sumLength
        cX = (Ax+Bx)/2
        cY = (Ay+By)/2
#         print cX, cY
#       print Ax, Ay
      arrayLine = arcpy.Array()
      if (averageMethod == "centroid"):
#         azimuth = c.A[0] # !! TEST !! -replace with average azimuth !!!
        # replica from cluster() ! 
        azimuthList = c.A
        azimuthList.sort()
        azimuthMin = azimuthList[0]
        azimuthMax = azimuthList[-1]
        # solve problem with angle numbers!
        # set is on border of azimuths (180-0)
        if ((azimuthMax-azimuthMin)>(2*azimuthTreshold)):
          # new set - recclassify
          azimuthListPlus = [] 
          for azimuth in azimuthList:
            if azimuth > (2*azimuthTreshold):
              azimuthListPlus.append(azimuth-180)  
            else:
              azimuthListPlus.append(azimuth)
          # replace azimuthList
          azimuthList = azimuthListPlus
          
        # compute azimuth statistics
        azimuthStats = getProperties(azimuthList)
        azimuth = azimuthStats[1]
        if azimuth<0:
          azimuth +=180
        lengthStats = getProperties(c.length)
        # upper quartile
        length = lengthStats[1] + lengthStats[2]
        # maximum
        # length = lengthStats[5]
        # TEST
#         length = lengthStats[5] + 2*config.xKIV
#         print ("mean: % i, std: %i, max: %i, max+2*bfsz: %i" % (lengthStats[1], lengthStats[2], lengthStats[5], lengthStats[5] + 2*config.xKIV)
        dX = math.sin(math.radians(azimuth))/2*length
        dY = math.cos(math.radians(azimuth))/2*length
        startPoint = arcpy.Point(cX-dX, cY-dY)
        arrayLine.add(startPoint)
        endPoint = arcpy.Point(cX+dX, cY+dY)
        arrayLine.add(endPoint)
#         print startPoint.X, startPoint.Y, endPoint.X, endPoint.Y
      else:
        startPoint = arcpy.Point(Ax, Ay)
        arrayLine.add(startPoint)
        endPoint = arcpy.Point(Bx, By)    
        arrayLine.add(endPoint)
      plyLine = arcpy.Polyline(arrayLine)
      polylineList.append(plyLine)
      attributeList.append(c.IDs[0])
      countList.append(len(c.IDs))
#   tb.log("write SHP")
  if not polylineList == []:
    arcpy.CopyFeatures_management(polylineList, resultSHP)
    countField = "count"
    if (arcpy.ListFields(resultSHP, countField)== []):
      arcpy.AddField_management(resultSHP, countField, "LONG", 8, 2, "", "", "NULLABLE", "NON_REQUIRED")
      
    # update cursor - fill attributes
    rows = arcpy.UpdateCursor(resultSHP)
    i = 0
    for row in rows:
      row.Id = attributeList[i]
      row.count = countList[i]
      rows.updateRow(row)
      i+=1
    del rows
  else:
    print ("No clusters created!")
  ### TEST ###
#   markClustersCursor(inSHP, clusterSet)

# MHHCA
# add attributes from row to cluster object 1 row = 1 line
def addLine(cluster, row):
  cluster.IDs.append(int(float(row[1])))
  cluster.Ax.append(float(row[2]))
  cluster.Ay.append(float(row[3]))
  cluster.Bx.append(float(row[4]))
  cluster.By.append(float(row[5]))
  cluster.A.append(float(row[6]))
  cluster.length.append(float(row[7]))

# MHHCA
# process result file and create list of clusters
def readClusters(resultTXT):
  results = open(resultTXT, "r")
  cluster = Cluster()
  clusterSet = []
  rows = []
  myId = 0
  
#   tb.log("read file")
  for result in results:
    rows.append(result)
  results.close()
  
#   tb.log("process clusters")
  addLine(cluster, rows[1].replace(",",".").split(";"))
  cluster.myId = myId
  myId +=1
  for row in rows[2:]:
    row = row.replace(",",".")
    row = row.split(";")
    if row[0] == "*":
      clusterSet.append(cluster)
      cluster = Cluster()
      cluster.myId = myId
      myId +=1
    addLine(cluster, row)
  clusterSet.append(cluster)
  return clusterSet    

# MHHCA
# inSHP - relevantMerged.shp - outSHP - bundleLines_KIV.shp
def clusterKIV(inSHP, resultSHP, tb):
  gisExePath = config.gisExePath
  # polarize SHP to TXT
  polarizedTXT = inSHP[:-4]+"_XYAL_P.txt"
  if not os.path.exists(polarizedTXT):
    tb.log("polarize")
    polarize(inSHP, polarizedTXT)
    tb.log("polarize - done")
  # compute KIV cluster algorithm
  resultTXT = inSHP[:-4]+"_result.txt"
  if not os.path.exists(resultTXT):
    X = config.xKIV
    Y = config.yKIV #config.bufferSizeKIV 
    A = config.azimuthTreshold
    # GIS.exe <input file path> <border X> <border Y> <border azimuth> <filter> <output file path>
    arguments = "%s %i %i %i %i %s" %(polarizedTXT, X, Y, A, 0, resultTXT)
    command = "%s %s" % (gisExePath, arguments)
    tb.log("cluster KIV command")
    os.system(command)
    tb.log("cluster KIV command done")
  
  tb.log("process results")
  myClusters = readClusters(resultTXT)
  clusterTKIV = config.clusterTKIV
  writeAverageSHP(myClusters, resultSHP, clusterTKIV, inSHP)
  tb.log("process results done")
  # delete temps
  os.remove(polarizedTXT)
  os.remove(resultTXT)

# MHHCA main method
def clusterLineKIV(DEM, rotations, tb):
  shpLinesWS = config.shpLinesWS
  mergeWS = config.mergeWS
  demDirs = [mergeWS]
  SA = config.getSA(DEM)
  sourceDEM = config.getSourceDEM(DEM)
  
  # for each rotation in rotations
  for rotation in rotations:
    rotateDEM = DEM.replace("dem", "r%i" %rotation)
    tb.log("ClusterLineKIV: %s" %(rotateDEM))
    demWS = resultsDir + SA + "\\" + sourceDEM + "\\" + rotateDEM + "\\"
    if os.path.exists(demWS + shpLinesWS):
      createDEMdirs(demWS, demDirs)
       
      # relevantLite - use own relevant - only merge shpLines!
      inDir = demWS + shpLinesWS
      relevantMergedNameLite = config.relevantMergedNameLite
      relevantMergedLite = demWS + mergeWS + relevantMergedNameLite
      
      if not os.path.exists(relevantMergedLite):
        tb.log("relevantLite")
        relevantLite(inDir, relevantMergedLite, tb)
        tb.log("relevantLite done")

      bundleLinesKIV = demWS + mergeWS + "bundleLines_KIV.shp"
      if not os.path.exists(bundleLinesKIV):
        tb.log("cluster KIV")
        clusterKIV(relevantMergedLite, bundleLinesKIV, tb)
        tb.log("cluster KIV done")

# MHHCA
# lite version of relevant - just merge all shpLines in inDir
def relevantLite(inDir, relevantMerged, tb):
  # merge to oneSHP
  if not os.path.exists(relevantMerged):
    toMerge = ""
    shp_listDir = os.listdir(inDir)
    for mySHP in shp_listDir:
      if mySHP[-4:] == ".shp":
        inSHP = inDir + mySHP
        toMerge+= "%s;" %(inSHP)
    # tb.log("merge")
    arcpy.Merge_management(toMerge,relevantMerged)
    # tb.log("calcStats")
    calcStats(relevantMerged)

def export(inSHPs, inLyrs, uzemi, outMxd):
  arcpy.gp.overwriteOutput = True
  # Layout preparation
  # path to mxd file
  mxd = arcpy.mapping.MapDocument(outMxd)
  print (mxd.filePath)
  print (inSHPs[0])
  sym_groupLayer = config.sym_groupLayer

  # dataframe
  df = arcpy.mapping.ListDataFrames(mxd)[0]
  # target dataFrame
  groupList = arcpy.mapping.ListLayers(mxd, uzemi, df)
  if len(groupList) == 0:
    groupLayer = arcpy.mapping.Layer(sym_groupLayer)
    arcpy.mapping.AddLayer(df, groupLayer)
    targetGroupLayer = arcpy.mapping.ListLayers(mxd, "jedna", df)[0]
    targetGroupLayer.name = uzemi
    groupList = arcpy.mapping.ListLayers(mxd, uzemi, df)
    print (len(groupList))
  targetGroupLayer = groupList[0]
  
  # for each shp display it in mxd
  for i in range(0,len(inSHPs),1):
    shp = inSHPs[i]
    # new layer from symbology
    sourceLayer = arcpy.mapping.Layer(inLyrs[i])
    # pridani vrstvy do mapy - bez symbologie
    shp_lyr = arcpy.mapping.Layer(shp)
#     print ("makeLyr " + shp_lyr
#     arcpy.mapping.AddLayer(df, shp_lyr)
    arcpy.mapping.AddLayerToGroup(df, targetGroupLayer, shp_lyr, "BOTTOM")
    updateLayer = arcpy.mapping.ListLayers(mxd, shp_lyr, df)[0]
    arcpy.mapping.UpdateLayer(df, updateLayer, sourceLayer, True)
    df.extent = updateLayer.getExtent()

  print ("ukladam")
  mxd.save()

def createMXD(DEM, rotations):
  # setting parameters form config
  azimuths = config.azimuths
  rotations = config.rotations
  methodKIV = config.methodKIV
  filterCount = config.filterCount
  filterCountKIV = config.filterCountKIV

  mergeWS = config.mergeWS
  histWS = config.histWS[:-1] + "_%s" % config.getCellSize(DEM) + "\\"

  # TODO symbology for input shp layers
  sym_bL = config.red_2pt_line
  sym_bL_KIV = config.blue_2pt_line
  sym_rM = config.gray_04pt_line

  # setup paths for DEM
  SA = config.getSA(DEM)
  inputMXDPath = config.getInputMXDPath(SA)
  print (inputMXDPath)
  inputMxd = arcpy.mapping.MapDocument(inputMXDPath)
  sourceDEM = config.getSourceDEM(DEM)
  outMxd = sourceDir + SA + "\\" + sourceDEM + "\\" + histWS + "compare_cT_%i_%i.mxd" % (filterCount, filterCountKIV)
  inputMxd.saveACopy(outMxd)
  print (outMxd)
  # for each rotation in rotations
  for rotation in rotations:
    rotateDEM = DEM.replace("dem", "r%i" % rotation)
    demWS = sourceDir + SA + "\\" + sourceDEM + "\\" + rotateDEM + "\\"

    bL = demWS + mergeWS + "bundleLines.shp"
    bL_KIV = demWS + mergeWS + "bundleLines_KIV%s.shp" % methodKIV
    rM_KIV = demWS + mergeWS + "relevantMerged_KIV.shp"
    #     rM =  demWS + mergeWS + "relevantMerged.shp"

    #     arcpy.MakeFeatureLayer_management(bL, "bL", '"count" >= %i' % filterCount)
    #     bL_lyr = bL[:-4]+".lyr"
    #     arcpy.SaveToLayerFile_management("bL",bL_lyr)

    arcpy.MakeFeatureLayer_management(bL_KIV, "bL_KIV", '"count" >= %i' % filterCountKIV)
    bL_KIV_lyr = bL_KIV[:-4] + ".lyr"
    arcpy.SaveToLayerFile_management("bL_KIV", bL_KIV_lyr)

    #     toExport = [bL_lyr, bL_KIV_lyr, rM, rM_KIV]
    #     symbology = [sym_bL, sym_bL_KIV, sym_rM, sym_rM]
    #     toExport = [bL_lyr, bL_KIV_lyr, rM_KIV]
    #     symbology = [sym_bL, sym_bL_KIV, sym_rM]
    toExport = [bL_KIV_lyr, rM_KIV]
    symbology = [sym_bL_KIV, sym_rM]
    export(toExport, symbology, "r%i" % rotation, outMxd)