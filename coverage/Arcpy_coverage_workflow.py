#!python2
# Romain MAZIERE (ARCEP) 2017-08-17
# Workflow to clean, split and standardize coverage shapefiles
# Need Python 2.7 and ArcPy

import arcpy, logging, sys
from os import path, sep, makedirs, removedirs
from datetime import date, datetime
from shutil import copy, rmtree

arcpy.env.overwriteOutput = True #overwrite existing files

def duration(dateTime):
  deltaTime = (datetime.now() - dateTime)
  return "%s %.2d:%.2d:%.2d" %(deltaTime.days, deltaTime.seconds/3600, (deltaTime.seconds/60)%60, deltaTime.seconds%60)
  
def arcpyLogger(severity):# 0 : Process message, 1 : Warning, 2 : Error
  if(arcpy.GetMessages(severity) != ""):
    if(severity == 0):
      logger.info(arcpy.GetMessages(severity))
    elif(severity == 1):
      logger.warning(arcpy.GetMessages(severity))
    elif(severity == 2):
      logger.error(arcpy.GetMessages(severity))

def rename(inputFilename, outputPath, add):
  inputFileExtension = inputFilename.split(".")[-1]
  
  print(path.dirname(outputPath))
  print(path.basename(inputFilename).replace("." + inputFileExtension, ""))
  
  return path.dirname(outputPath) + sep + path.basename(inputFilename).replace("." + inputFileExtension, "") + "_" + add + "." + inputFileExtension

def nameModify(filePath, add):
  fileExtension = filePath.split(".")[-1]
  return path.dirname(filePath) + sep + path.basename(filePath).replace("." + fileExtension, "_" + add + "." + fileExtension)

def fileCopier(inputFilePath, outputFilePath):
  outputPath = path.dirname(outputFilePath)
  if(path.exists(outputPath)):
    copy(inputFilePath, outputFilePath)
    logger.info("Copy file " + inputFilePath + " into " + outputFilePath)
  else:
    logger.error("The directory " + outputPath + " doesn't exist !")
  
def shpCopy(inputFilePath, outputFilePath):
  logger.info("Copy shapefile")
  logger.info(outputFilePath)
  arcpy.CopyFeatures_management(inputFilePath, outputFilePath)
  logger.info("The copy is : " + outputFilePath)
  
def dirCreator(filePath):
  if not path.exists(path.dirname(filePath)):
    makedirs(path.dirname(filePath), True)
    logger.debug("Create directory : " + filePath)
  
def dirDeletor(filePath):
  if path.exists(filePath):
    rmtree(filePath)
    logger.debug("Delete directory : " + filePath)

def setSRID(inputPath, srid):
  sr = arcpy.SpatialReference(srid)
  arcpy.DefineProjection_management(infc, sr)
  arcpyLogger(arcpyVerboseLevel)

def checkFileSRID(inputPath):
  inputFileDsc = arcpy.Describe(inputPath)
  if(inputFileDsc.spatialReference.Name == "Unknown"):
    logger.error("Error ! The input file SRID is undefined !")
    exit()
  else:
    return inputFileDsc.spatialReference.Name
  
def multipart2singlepart(inputPath, outputPath):
  dateTime = datetime.now()
  logger.info("Multipart To Singlepart")
  outputFilename = outputPath + path.basename(nameModify(inputPath, "Single"))
  arcpy.MultipartToSinglepart_management(inputPath, outputFilename)
  deleteField(outputFilename, "ORIG_FID")
  arcpyLogger(arcpyVerboseLevel)
  logger.info("The singlepart file, generated in " + str(duration(dateTime)) + " is : " + outputFilename)
  return outputFilename

def reprojector(inputPath, outputCS):
  dateTime = datetime.now()
  if(checkFileSRID(inputPath) == "RGF_1993_Lambert_93" or checkFileSRID(inputPath) == "RGF93_Lambert_93"):
    logger.info("The shapefile is already in " + str(outputCS) + ".")
    return inputPath
  else:
    logger.info("Reproject to " + str(outputCS))
    outputFilename = nameModify(inputPath, str(outputCS))
    if checkFileSRID(inputPath):
      if(checkFileSRID(inputPath) == "NTF_Paris_Lambert_zone_II"):
        logger.info("Change the srid to NTF_Lambert_zone_II")
        arcpy.DefineProjection_management(inputPath, "PROJCS['NTF_Lambert_Zone_II',GEOGCS['GCS_NTF',DATUM['D_NTF',SPHEROID['Clarke_1880_IGN',6378249.2,293.4660212936265]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Lambert_Conformal_Conic'],PARAMETER['False_Easting',600000.0],PARAMETER['False_Northing',2200000.0],PARAMETER['Central_Meridian',2.337229166666667],PARAMETER['Standard_Parallel_1',46.8],PARAMETER['Scale_Factor',0.99987742],PARAMETER['Latitude_Of_Origin',46.8],UNIT['Meter',1.0]]")
      arcpy.Project_management(inputPath, outputFilename, outputCS, "RGF_1993_To_NTF_NTv2")
      arcpyLogger(arcpyVerboseLevel)
      logger.info("The reprojected file, generated in " + str(duration(dateTime)) + " is : " + outputFilename)
      return outputFilename

def merge(inputPath, outputPath):
  outputFilename = nameModify(outputPath, "Merge")
  arcpy.Dissolve_management(inputPath, outputPath, "", "", "SINGLE_PART", "DISSOLVE_LINES")
  arcpyLogger(arcpyVerboseLevel)
  logger.info("The merged geometry file, generated in " + str(duration(dateTime)) + " is : " + outputFilename)
  return outputFilename

def split(inputPath, outputPath, choice):
  dateTime = datetime.now()
  logger.info("Split the shape")
  country_shp = "" # 0
  department_shp = "C:\sig\\ressources\\ign\\2017\\admin_express\\ADE-COG_1-0_SHP_LAMB93_FR\\DEPARTEMENT.shp" # 1
  city_shp = "" # 2
  
  outputFilename = nameModify(inputPath, "splitByDept")
  split_shp = department_shp

  if (choice == 0):
    outputFilename = nameModify(inputPath, "cut")
    split_shp = country_shp
  elif (choice == 2):
    outputFilename = nameModify(inputPath, "splitByCity")
    split_shp = city_shp

  arcpy.Intersect_analysis([inputPath, split_shp], outputFilename)
  arcpyLogger(arcpyVerboseLevel)
  logger.info("The splited file, generated in " + str(duration(dateTime)) + " is : " + outputFilename)
  return outputFilename

def deleteField(inputFilename, dropFieldsList):
  dateTime = datetime.now()
  fields = arcpy.ListFields(inputFilename)
  nbrOfFields = len(fields)
  if (nbrOfFields > 3):
    arcpy.DeleteField_management(inputFilename, dropFieldsList)
    arcpyLogger(arcpyVerboseLevel)
    logger.debug("Fields deleted in " + str(duration(dateTime)))
  return inputFilename
  
def deleteAllFields(inputFilename):
  dateTime = datetime.now()
  fields = arcpy.ListFields(inputFilename)
  logger.debug("Nbr of Fields : " + str(len(fields)))
  requiredFields = ["operateur", "date", "techno", "usage", "niveau", "bande", "dept", "ID_GEOFLA", "CODE_DEPT", "NOM_DEPT", "CODE_REG", "NOM_REG", "LEGENDE", "LEGEND", "NOM_DEP", "INSEE_DEP", "INSEE_REG"]
  nbrOfFields = len(fields)
  if (nbrOfFields <= 3):
    return 0
  for field in fields:
    if((nbrOfFields > 3) and (field.type != "OID") and (field.type != "Geometry") and (field.name not in requiredFields)):
      logger.debug("Delete the field : " + field.name)
      arcpy.DeleteField_management(inputFilename, field.name)
      arcpyLogger(arcpyVerboseLevel)
      nbrOfFields = nbrOfFields - 1
  logger.debug("Fields deleted in " + str(duration(dateTime)))
  return 1
  
def getFieldsList(inputFilename):
  fields = arcpy.ListFields(inputFilename)
  for field in fields:
    logger.debug(field)
  arcpyLogger(arcpyVerboseLevel)
  
def geojsonConvert(inputFilename):
  dateTime = datetime.now()
  logger.info("GeoJSON Convertion")
  reprojecedFile = nameModify(inputFilename, "wgs84")
  
  outputFilename = path.dirname(inputFilename) + sep + path.basename(reprojecedFile).replace(reprojecedFile.split(".")[-1], "json")

  arcpy.Project_management(inputFilename, reprojecedFile, "GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]]", "", "PROJCS['RGF_1993_Lambert_93',GEOGCS['GCS_RGF_1993',DATUM['D_RGF_1993',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Lambert_Conformal_Conic'],PARAMETER['False_Easting',700000.0],PARAMETER['False_Northing',6600000.0],PARAMETER['Central_Meridian',3.0],PARAMETER['Standard_Parallel_1',44.0],PARAMETER['Standard_Parallel_2',49.0],PARAMETER['Latitude_Of_Origin',46.5],UNIT['Meter',1.0]]", "NO_PRESERVE_SHAPE", "", "NO_VERTICAL")
  arcpyLogger(arcpyVerboseLevel)
  logger.info("The wgs84 reprojected file, generated in " + str(duration(dateTime)) + " is : " + reprojecedFile)
  
  #shpCopy(reprojecedFile, outputPath + path.basename(inputDataPath).replace("." + inputFilename.split(".")[-1], "_clean_WGS84.shp"))
  
  arcpy.FeaturesToJSON_conversion(reprojecedFile, outputFilename, "NOT_FORMATTED", "NO_Z_VALUES", "NO_M_VALUES", "GEOJSON")

  arcpyLogger(arcpyVerboseLevel)
  logger.info("The GeoJSON file, generated in " + str(duration(dateTime)) + " is : " + outputFilename)
  
  fileCopier(outputFilename, outputPath + path.basename(inputDataPath).replace("." + inputFilename.split(".")[-1], "_clean_wgs84.geojson"))
  return outputFilename

def globalWorkflow(inputFilename, outputCS=2154):
  logger.info("The temp dir is : " + tempDataPath)
  
  # Try to clean Fields before begin process
  deleteAllFields(inputFilename)
  
  # Simplify the Shape Multipart geometries to Singlepart geometries
  singlePartFile = multipart2singlepart(inputFilename, tempDataPath)
  del inputFilename

  # Reproject the Shape
  reprojecedFile = reprojector(singlePartFile, outputCS)
  del singlePartFile

  # Split the Shape by departments or cities
  slitedFile = split(reprojecedFile, tempDataPath, 1)
  del reprojecedFile
  
  # Clean the fields list by removing undesired fields
  deleteAllFields(slitedFile)
  shpCopy(slitedFile, outputPath + outputFilenameBase +  "_clean_L93.shp")
  
  #Convert into GeoJSON
  json = geojsonConvert(slitedFile)

  return 1

print(" ------------------------------- ")
print("|             ARCEP             |")
print("| coverage shapefiles workflow  |")
print(" ------------------------------- \r\n")

# Logging config
logger = logging.getLogger('coverage workflow')
stdoutLog = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger.setLevel(logging.INFO)
stdoutLog.setFormatter(formatter)
logger.addHandler(stdoutLog)

# Arcpy logging level
arcpyVerboseLevel = 1 # 0 : Process message, 1 : Warning, 2 : Error
logger.debug("arcpyVerboseLevel = " + str(arcpyVerboseLevel))

loopQuestion = ""

while (loopQuestion.lower() != "n"):
  beginDateTime = datetime.now()
  currentDate = str(date.today()) # For directory name
  fileLogPath = "c:\\Temp" + sep + "log_" + beginDateTime.strftime("%Y-%m-%d_%H-%M-%S") + ".log"
  fileLog = logging.FileHandler(fileLogPath)
  fileLog.setFormatter(formatter)
  logger.addHandler(fileLog)

  # input Data Path
  if(len(sys.argv) >= 2):
    inputDataPath = sys.argv[1]
  else:
    inputDataPath = raw_input("Enter the filename's path : ")
  logger.debug("Shapefile : " + inputDataPath)
  outputPath = path.dirname(inputDataPath) + sep
  outputFilenameBase = path.basename(inputDataPath).replace("." + inputDataPath.split(".")[-1], "")
  logger.info("The oututPath is : " + outputPath)
  logger.info("The output file name base is : " + outputFilenameBase)
  logger.info("The shapefile is in " + checkFileSRID(inputDataPath))
  
  # Temp dir
  if(len(sys.argv) < 3):
    tempDataPath = raw_input("Enter the temp path on your local drive [C:\Temp\dataProcessing\](default) : ")
  elif(len(sys.argv) >= 3):
    tempDataPath = sys.argv[2]
  if(tempDataPath == ''):
    tempDataPath = "C:\\Temp" + sep + "dataProcessing" + sep
  print("tempDataPath : " + tempDataPath)
  
  if(not path.exists(tempDataPath)):
    dirCreator(tempDataPath)
  elif(path.exists(tempDataPath)):
    print(tempDataPath + " already exists.")
  else:
    print("Error ! The temp dir : " + tempDataPath + " is not valid !")
    exit()
  logger.debug("tempDataPath : " + tempDataPath)
  
  # Create directories
  dirCreator(tempDataPath)
  
  if path.isfile(inputDataPath) and (inputDataPath.split(".")[-1] == "shp") :
    globalWorkflow(inputDataPath)
  else :
    print("Error ! Only process ShapeFile !")
    exit()
  
  dirDeletor(tempDataPath)
  
  logging.info("The global process duration is : " + str(duration(beginDateTime)))
  fileCopier(fileLogPath, outputPath)
  print("The global process duration is : " + str(duration(beginDateTime)))
  if(len(sys.argv) == 1):
    loopQuestion = raw_input("Process another shapefile ? (Y/N)")
  else:
    loopQuestion = 'n'
  
exit()
