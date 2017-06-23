# mhhc
A new artefacts resistant method for automatic lineament extraction using Multi-Hillshade Hierarchic Clustering (MHHC)

Running sample

Sample DEM is already prepared from SRTM (c) xyz in the small area in Bohemia Forest Czech Republic.
Configure workspace and DEM to process
- open config.py in text editor
- set workspace to sample dir on computer where the ArcGIS Desktop is installed, e.g. r"c:\mhhc\sample"+os.path.sep
- set workspace to on computer where the PCI Geomatica is installed, e.g. r"c:\mhhc\sample"+os.path.sep
- set DEMs variable to ["sa_sr_dem_30"]
- set hasPCIdone variable to False
- let other parameters default
Run first part of computation - creating rasters for extraction:
- run central.py
Run second part using PCI Geomatica software
The line extraction is made using module LINE of PCI Geomatica software. The MHHC algorithm generates the EASI script files which can be run in EASI command line (part of PCI Geomatica software).
This manual suppose that the PCI Geomatica software is installed on the same machine. If not copy your workspace to different machine before computation a copy workspace back after computation.
- open EASI command line and execute this command with replacing lastFile with name of last file from runEAS directory:
  run "c:\mhhc\sample\Results\runEAS\lastFile.eas"
Run last part of algorithm
- open config.py in text editor
- set hasPCIdone variable to True
- run central.py

The results are placed in the folder: workspace + "Results\SampleArea\SRTM\sa_sr_r99_30\"
The computed lineaments are placed in subfolder: "merge\bundleLines.shp"
The classified lineaments are placed in subfolder "negative":
bundleLines_N.shp - negative lineaments
bundleLines_P.shp - positive lineaments
bundleLines_U.shp - lineaments with unsure classification
bundleLines_NU.shp - merged neative and unsure lineaments


Algorithm dependencies:
The algorithm is dependent on arcpy libraries, thus ArcGIS Desktop license is needed.
Part of algorithm is computed in software PCI Geomatica using generated EAS scripts. The PCI Geomatica 2013 and newer is required. 