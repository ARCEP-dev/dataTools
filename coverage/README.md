# Open Data python workflow Arcpy_coverage_workflow.py

This script uses the ArcGIS library : arcpy.

## Requirements
There are :
 - python 2.7
 - arcpy

 ## Summary

Developed using Arcgis 10.5 and the equivalent version of arcpy.

The script is interactive, asks you the input shapefile path, the output, some of configuration and personnalization.

You need to download French Geofla shapefiles, this is two shapefiles, one for the departments boundary, the other for cities boundary, which are avalabels on the [National Geographic Institute website](http://professionnels.ign.fr/geofla)

If you don't use Windows OS, you have to change some paths like the temporary path.

## How it works ?

1. Delete of the fields, because at this moment, this is not normalized, and useless.
2. Change from *multipolygon* to *polygon*, because the input shapefile contains **one unique** object, which is the global country coverage !
3. Change the projection and reproject to official SRID (Lambert 93).
4. Split the national coverage using the departments boundary or cities boundary.
5. Export it in the source directory.
6. Reproject it to WGS84.
7. Convert into GeoJSON and save it into the source directory.

Normally, if your computer doesn't died or crash, you can obtain :
- a shapefile in Lambert93,
- a GeoJSON in WGS84.

This is the first version of the script, there are no try/catch, no exeption managment, etc...
