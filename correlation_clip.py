# compare two sets of lines
# import line_stats
import time
startTime = time.strftime("%m%d_%H%M%S")
import arcpy
import autoLin
import os
# import line_stats
arcpy.gp.overwriteOutput = True

print "time %s - arcpy imported" % (time.strftime("%m%d_%H%M%S"))


################## start ######################
# input:
# compareSHP = r"d:\PhD\Thesis\Papers\AutoLin\GISData\AutoLin_r5\Ziar50_30m\data_shp\auto_zm50_dem_40_r0.shp"
# bundleSHP = r"d:\PhD\Thesis\Papers\AutoLin\GISData\AutoLin_r5\Ziar50_30m\data_shp\auto_zm50_dem_40_r5.shp"

# bundleSHPDir = r"d:\PhD\Thesis\Papers\AutoLin\GISData\AutoLin"+"\\"
# bundleSHPs = ["auto_zm10_dem_30.shp", "expert_zm10.shp", "expert_zm10_gen.shp"]

# # log
# logFileName = autoLin.getDir(compareSHP) + "%s_log.csv" % time.strftime("%m%d_%H%M%S")
# logFile = open(logFileName, 'w')
# logFile.write("time %s - started\n" % startTime)
# #   # header 
# logFile.write("Tested; Reference; Method; Azimuth T; Buffer Size; Corr A; Total Length; Corr Length; Corr B; No. lines; No. correlated; Corr C;No. ratio\n")
# azimuthTreshold = 20
# bufferSize = 200
# logFile.close()

### Test of bundleLines count parameter ###
# minCount = 11
# maxCount = 24
# countRange = range(minCount, maxCount+1, 1)

# for c in countRange:
#   # make selection
#   arcpy.MakeFeatureLayer_management(bundleSHP, "bundleSHP", "count >= %i" % c)
#   bundleSHP_c = bundleSHP[:-4] + "_%i.shp" % c
#   if not os.path.exists(bundleSHP_c):
#     arcpy.CopyFeatures_management("bundleSHP", bundleSHP_c)
#   # compare two datasets
#   autoLin.compareLines(compareSHP, bundleSHP_c, 0)
#   autoLin.compareLines(bundleSHP_c, compareSHP, 0)

### Test of correlation parameters - azimut and buffer ###
# for az in range(10,31,5):  
#   azimuthTreshold = az
#   for size in range(50,301,50):
#     bufferSize = size
#     logFile.write("\nParameters - azimuthTreshold = %i, bufferSize = %i\n" %(azimuthTreshold, bufferSize))
#     # default comparison
#     autoLin.compareLines(compareSHP, bundleSHP, 0)
#     autoLin.compareLines(bundleSHP, compareSHP, 0)

### default comparison ###
# autoLin.compareLines(compareSHP, bundleSHP, 0)
# autoLin.compareLines(compareSHP, bundleSHP, 1)
# autoLin.compareLines(bundleSHP, compareSHP, 1)

### compare set of lines with compareSHP ###
# for bundleSHPName in bundleSHPs:
#   bundleSHP = bundleSHPDir + bundleSHPName
# #   print "%s: \n" %autoLin.getName(compareSHP) 
#   autoLin.compareLines(compareSHP, bundleSHP, 0)
# #   print "%s: \n" %bundleSHPName
#   autoLin.compareLines(bundleSHP, compareSHP, 0)

### folder TEST everyone with everyone ###
## TODO: corect compareList!!
# inDirs = [r"d:\PhD\Thesis\Papers\AutoLin\GISData\AutoLin_r5\Ziar10_30m\data_shp\compare" + "\\",r"d:\PhD\Thesis\Papers\AutoLin\GISData\AutoLin_r5\Ziar50_30m\data_shp\compare" + "\\",r"d:\PhD\Thesis\Papers\AutoLin\GISData\AutoLin_r5\SumavaPaper_30m\data_shp\compare" + "\\"]
inDirs = [r"d:\PhD\Thesis\Vyzkum\ZpracovaniVysledku\SumavaDMRcompare" + "\\"]
print inDirs

for inDir in inDirs:
  # log
  logFileName = inDir + "%s_log.csv" % time.strftime("%m%d_%H%M%S")
  logFile = open(logFileName, 'w')
  logFile.write("time %s - started\n" % startTime)
  # header
  logFile.write("Tested; Reference; Method; Azimuth T; Buffer Size; Corr A; Total Length; Corr Length; Corr B; No. lines; No. correlated; Corr C;No. ratio\n")
  logFile.close()

  azimuthTreshold = 20
  bufferSize = 200

  shpList = []
  shp_listDir = os.listdir(inDir)
  for mySHP in shp_listDir:
    if mySHP[-4:] == ".shp":
      shpList.append(inDir + mySHP)

#   compareList = ["auto_lls_dem30.shp"]

  i = 0
  for compareSHP in shpList[:-1]:
    i+=1
#   print compareSHP
    compareName = autoLin.getName(compareSHP)
    for bundleSHP in shpList[i:]:
      bundleName = autoLin.getName(bundleSHP)
      print compareName, bundleName
      autoLin.compareLines(compareSHP, bundleSHP, 1, logFileName, azimuthTreshold, bufferSize)
      autoLin.compareLines(bundleSHP, compareSHP, 1, logFileName, azimuthTreshold, bufferSize)
  logFile = open(logFileName, 'a')
  endTime = time.strftime("%m%d_%H%M%S")
  logFile.write("time %s - FINISH, start time was %s" % (endTime, startTime))
  logFile.close()

### structural comparison - every config result with expert list ###
# setting paths for workspace
# workspace = config.workspace
# vysledkyDir = config.vysledkyDir
# zdrojDir = config.zdrojDir
# mergeWS = config.mergeWS
# shpWS = config.shpWS
# negativeWS = config.negativeWS
#
# # DEMs = ["hr_zm_r0_100", "hr_zm_r0_75", "c_zm_r0_200", "c_zm_r0_150", "c_zm_r18_100", "sp_d_r99_50", "sp_d_r18_40", "c_zm_r9_50", "z5_zm_r99_40", "z5_zm_r0_40", "z5_zm_r99_30", "z_zm_r36_20", "c_zm_r0_25", "z_zm_r0_20"]
# # DEMs = ["z5_zm_r98_40"]
# DEMs = ["c_zm_r0_200", "c_zm_r0_150", "c_zm_r18_100", "sp_d_r99_50", "sp_d_r18_40", "c_zm_r9_50", "z5_zm_r99_40", "hr_zm_r0_100", "z5_zm_r99_30", "hr_zm_r0_75", "c_zm_r0_25"]
# logFileName = r"d:\PhD\Thesis\Vyzkum\ZpracovaniVysledku" + "\\" + "%s_log.csv" % time.strftime("%m%d_%H%M%S")
# logFile = open(logFileName, 'w')
# logFile.write("time %s - started\n" % startTime)
# # header
# logFile.write("Tested; Reference; Method; Azimuth T; Buffer Size; Corr A; Total Length; Corr Length; Corr B; No. lines; No. correlated; Corr C;No. ratio\n")
# logFile.close()
#
# for DEM in DEMs:
#   azimuthTreshold = 20
#   bufferSize = 200
#
#   SA = config.getSA(DEM)
#   sourceDEM = config.getSourceDEM(DEM)
#   demWS = vysledkyDir + SA + "\\" + sourceDEM + "\\" + DEM+ "\\"
#
#   bundleSHP = demWS + mergeWS + "bundleLines.shp"
#   compareSHP = demWS + mergeWS + "bundleLines_KIVb.shp"
#   print "%s - %s" % (compareSHP, bundleSHP)
# #   print DEM
#   autoLin.compareLines(compareSHP, bundleSHP, 1)
#   autoLin.compareLines(bundleSHP, compareSHP, 1)
#
# logFile = open(logFileName, 'a')
# endTime = time.strftime("%m%d_%H%M%S")
# logFile.write("time %s - FINISH, start time was %s" % (endTime, startTime))
# logFile.close()