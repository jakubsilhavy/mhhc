__author__ = 'jsilhavy'
# compute directional statistics and visualization for single SHP
import autoLin
import os

# nameDict
bfDict = {"auto_dmu25_dem_30_r5":"BF Auto 30 m", "auto_dmu25_dem_60_r5": "BF Auto 60 m", "expert_dmu_25": "BF Expert", "geology_lines_zm50": "BF Fault Lines"}
cwcDict = {"auto_zm10_dem_30_r5": "CWC Auto 30 m", "expert_zm10": "CWC Expert", "expert_zm10_gen": "CWC Expert G", "geology_faults_zm10": "CWC Fault Lines"}
testDMRDict = {"sd_as_r0_30": "ASTER", "sd_sr_r0_30": "SRTM", "sd_d_r0_30": "DMU", "sd_d4_r0_30": "DMR 4G", "sd_d5_r0_30": "DMR 5G", "sd_zm_r0_30": "ZABAGED"}

myDir = {"r2p": "ArcGIS", "htp": "HTP", "pci": "PCI"}
myDir = {"lines_r0": "Bez rotace", "lines_r99": "MHHC", "pci": "PCI"}


inSHP = r"D:\PhD\Thesis\ImageData\Zdroje\Fig_mhhc_artefakt_qed\Fig_mhhc_artefakt_qed.gdb\lines_r99"
# inSHP2 = r"d:\PhD\Thesis\Vyzkum\ZpracovaniVysledku\SumavaDMRcompare\sd_d5_r0_30.shp"
autoLin.computeHist(inSHP, myDir, 2, 4, "svg")
# autoLin.computeHist(inSHP2, cwcDict, 3, 8, "png")
# autoLin.compareTwoHists(inSHP, inSHP2, 3, 8, "png")


### For all SHP in one Directory: ###
# inDir = r"d:\PhD\Thesis\Vyzkum\ZpracovaniVysledku\SumavaDMRcompare" + "\\"
# shp_listDir = os.listdir(inDir)
# for mySHP in shp_listDir:
#   if mySHP[-4:] == ".shp":
#     print mySHP
#     inSHP = inDir + mySHP
#     autoLin.computeHist(inSHP, testDMRDict, 3, 8, "png")