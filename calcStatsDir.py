# calcStatsDir - spocte statistiky pro adresar
import arcpy
import autoLin
### For all SHP in one Directory: ###
inGdb = r"D:\PhD\Thesis\ImageData\Zdroje\Fig_mhhc_artefakt_influence\Fig_mhhc_artefakt_influence.gdb" + "\\"
arcpy.env.workspace = inGdb

datasets = arcpy.ListDatasets(feature_type='feature')

for fc in arcpy.ListFeatureClasses():
#   autoLin.calcStats(inGdb + fc)
  autoLin.computeHist(inGdb + fc, {}, 3, 8, "png")