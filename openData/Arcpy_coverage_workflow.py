# Romain MAZIERE (ARCEP) 2017-07-12
# Workflow to generate the shapefiles for the opendata
# Need Python 2.7 and ArcPy

import arcpy, logging
from os import path, sep, makedirs, removedirs
from datetime import date, datetime
from shutil import copy, rmtree

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

def nameModify(filePath, add):
  fileExtension = filePath.split(".")[-1]
  return path.dirname(filePath) + sep + path.basename(filePath).replace("." + fileExtension, "") + "_" + add + "." + fileExtension

def fileCopier(inputFilePath, outputPath):
  if(path.exists(outputPath)):
    copy(inputFilePath, outputPath)
    logger.info("Copy file " + inputFilePath + " into " + outputPath)
  else:
    logger.error("The directory " + outputPath + " doesn't exist !")
  
def shpCopy(inputFilePath, outputPath):
  logger.info("Copy shapefile")
  destination = outputPath + path.basename(inputFilePath)
  arcpy.CopyFeatures_management(inputFilePath, destination)
  logger.info("The copy is : " + destination)
  
def dirCreator(filePath):
  if not path.exists(path.dirname(filePath)):
    makedirs(path.dirname(filePath), True)
  
def dirDeletor(filePath):
  if path.exists(filePath):
    rmtree(filePath)
    
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
  outputFilename = nameModify(outputPath, "Single")
  arcpy.MultipartToSinglepart_management(inputPath, outputFilename)
  deleteField(outputFilename, "ORIG_FID")
  arcpyLogger(arcpyVerboseLevel)
  logger.info("The singlepart file, generated in " + str(duration(dateTime)) + " is : " + outputFilename)
  return outputFilename

def reprojector(inputPath, outputCS):
  dateTime = datetime.now()
  if(checkFileSRID(inputPath) == "RGF_1993_Lambert_93" or checkFileSRID(inputPath) == "RGF93_Lambert_93"):
    logger.info("The shapefile is already in Lambert 93.")
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

def split(inputPath, outputPath, choice):
  dateTime = datetime.now()
  logger.info("Split the shape")
  #Use GeoFla shapeFiles http://professionnels.ign.fr/geofla
  # To obtain country shapeFile, merge the departments shapefile
  '''country_shp = "{Your data path}\France_2016-06-00235.shp" # 0
  department_shp = "{Your data path}\Departement_2016-06-00235.shp" # 1
  city_shp = "{Your data path}\Commune_2016-06-00236.shp" # 2'''

  country_shp = "C:\\Travail\\Work\\France_2016-06-00235.shp" # 0
  department_shp = "C:\\Travail\\Work\\Departement_2016-06-00235.shp" # 1
  city_shp = "C:\\Travail\\Work\\Commune_2016-06-00236.shp" # 2
  
  
  
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
  requiredFields = ["ID_GEOFLA", "CODE_DEPT", "NOM_DEPT", "CODE_REG", "NOM_REG", "LEGENDE", "LEGEND"]
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
  
def LoDGenerator(inputPath, outputPath, simplificationValue):
  dateTime = datetime.now()
  logger.info("Generate the LoD " + str(simplificationValue))
  outputFilename = nameModify(inputPath, str(simplificationValue) + "m")
  arcpy.SimplifyPolygon_cartography(inputPath, outputFilename, "POINT_REMOVE", str(simplificationValue) + " Meters", str((simplificationValue*simplificationValue)/4) + " SquareMeters", "RESOLVE_ERRORS", "NO_KEEP", "")
  arcpyLogger(arcpyVerboseLevel)
  logger.info("The " + str(simplificationValue) + "m LoD file, generated in " + str(duration(dateTime)) + " is : " + outputFilename)
  return outputFilename

def globalWorkflow(inputFilename, outputCS=2154):
  logger.info("The temp dir is : " + tempDataPath)
  
  # Try to clean Fields before begin process
  deleteAllFields(inputFilename)
  
  # Simplify the Shape Multipart geometries to Singlepart geometries
  singlePartFile = multipart2singlepart(inputFilename, tempDataPath + outputFilenameBase)
  del inputFilename

  # Reproject the Shape
  reprojecedFile = reprojector(singlePartFile, outputCS)
  del singlePartFile
  
  # Cut the country
  cutedFile = split(reprojecedFile, tempDataPath, 0)
  del reprojecedFile
  # Clean the fields list by removing undesired fields
  deleteAllFields(cutedFile)
  shpCopy(cutedFile, outputHierarchy)

  # Split the Shape by departments or cities
  slitedFile = split(cutedFile, tempDataPath, splitChoice)
  del cutedFile
  # Clean the fields list by removing undesired fields
  deleteAllFields(slitedFile)
  shpCopy(slitedFile, outputHierarchy)

  for simplificationValue in simplificationValuesList :
    LoDFile = LoDGenerator(slitedFile, tempDataPath, simplificationValue)

    # Clean the fields list by removing undesired fields
    deleteAllFields(LoDFile)
    
    shpCopy(LoDFile, outputLoDHierarchy)
    
  return 1

print(" ------------------------------- ")
print("|             ARCEP             |")
print("| opendata shapefiles generator |")
print(" ------------------------------- \r\n")

beginDateTime = datetime.now()

# Logging config
logger = logging.getLogger('openDataGen')
stdoutLog = logging.StreamHandler()
fileLogPath = "c:\\Temp" + sep + "log_" + beginDateTime.strftime("%Y-%m-%d_%H-%M-%S") + ".log"
fileLog = logging.FileHandler(fileLogPath)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fileLog.setFormatter(formatter)
logger.addHandler(fileLog)
logger.setLevel(logging.INFO)

stdoutLog.setFormatter(formatter)
logger.addHandler(stdoutLog)

# Arcpy logging level
arcpyVerboseLevel = 1 # 0 : Process message, 1 : Warning, 2 : Error
logger.debug("arcpyVerboseLevel = " + str(arcpyVerboseLevel))

loopQuestion = ""
currentDate = str(date.today()) # For directory name
operatorsList = ["Bouygues_Telecom", "Free_Mobile", "Orange", "SFR"]
simplificationValuesList = [2500, 1000, 500, 250, 100, 50]

while (loopQuestion.lower() != "n"):
  # Ask all paths
  inputDataPath = raw_input("Enter the filename's path : ")
  logger.debug("Shapefile : " + inputDataPath)
  logger.info("The shapefile is in " + checkFileSRID(inputDataPath))
  tempDataPath = raw_input("Enter the temp path on your local drive [C:\Temp\dataProcessing\](default) : ")
  outputDataPath = raw_input("Enter the OpenData path to create hierarchy : ")
  logger.debug("outputDataPath : " + outputDataPath)
  
  if(tempDataPath == ""):
    tempDataPath = "C:\\Temp\\dataProcessing\\"
    if(not path.exists(tempDataPath)):
      dirCreator(tempDataPath)
  elif(path.exists(tempDataPath)):
    print(tempDataPath + " allready exists.")
  else:
    print("Error ! The temp dir : " + tempDataPath + " is not valid !")
    exit()
  logger.debug("tempDataPath : " + tempDataPath)
  
  # Ask for the operator
  print("\r\nSelect the operator's data :")
  for index in range(len(operatorsList)):
    print(str(index) + " - " + operatorsList[index])
  
  operatorChoice = int(raw_input("Enter your choice : "))
  logger.debug("operatorChoice : " + operatorsList[operatorChoice])

  # Ask the technology
  print("\r\nWhich technology is it ?")
  print("2 - 2G")
  print("3 - 3G")
  print("4 - 4G")
  technologyChoice = int(raw_input("Enter your choice : "))
  if(technologyChoice < 2 or technologyChoice > 4):
    print("Error ! Your choice is invalid !")
    exit()
  logger.debug("technologyChoice : " + str(technologyChoice))
  
  # Ask for the data date
  dataDate = raw_input("\r\nEnter the date of the data (AAAAMM) : ")
  
  # Ask the output hierarchy
  print("\r\nThe output hierarchy :")
  print("1 - {CurrentDate}/{LoD}/{Operator} (default)")
  print("2 - {CurrentDate}/{Operator}/{LoD}")
  print("3 - {Operator}/{CurrentDate}/{LoD}")
  outputHierarchyChoice = raw_input("Enter your choice : ")
  if(outputHierarchyChoice != "" and outputHierarchyChoice.is_integer()):
    outputHierarchyChoice = int(outputHierarchyChoice)
  
  if outputHierarchyChoice == 2:
    outputLoDHierarchy = outputDataPath + currentDate + sep + operatorsList[operatorChoice] + sep + "LoD" + sep
    outputHierarchy = outputDataPath + currentDate + sep + operatorsList[operatorChoice] + sep
  elif outputHierarchyChoice == 3:
    outputLoDHierarchy = outputDataPath + operatorsList[operatorChoice] + sep + currentDate + sep + "LoD" + sep
    outputHierarchy = outputDataPath + operatorsList[operatorChoice] + sep + currentDate + sep
  else:
    outputLoDHierarchy = outputDataPath + currentDate + sep + "LoD" + sep + operatorsList[operatorChoice] + sep
    outputHierarchy = outputDataPath + currentDate + sep + operatorsList[operatorChoice] + sep
  
  logger.debug("outputHierarchy : " + outputHierarchy)
  
  # Ask the output files name
  print("\r\nThe output files name :")
  print("1 - {Operator}_Couv{Technology}_{DataDate} (default)")
  print("2 - {Operator}_{DataDate}_Couv{Technology}")
  outputfilenameTypeChoice = raw_input("Enter your choice : ")
  if(outputfilenameTypeChoice != ""):
    outputfilenameTypeChoice = int(outputfilenameTypeChoice)
  
  if outputfilenameTypeChoice == 2:
    outputFilenameBase = operatorsList[operatorChoice] + "_" + dataDate + "_Couv" + str(technologyChoice) + "G.shp"
  else:
    outputFilenameBase = operatorsList[operatorChoice] + "_Couv" + str(technologyChoice) + "G_" + dataDate + ".shp"
    
  logger.debug("outputFilenameBase : " + outputFilenameBase)
  
  # Ask the split shape
  print("\r\nSplit your file by :")
  print("1 - Departments (default)")
  print("2 - Cities")
  splitChoice = raw_input("Enter your choice : ")
  if(splitChoice != ""):
    splitChoice = int(splitChoice)
    
  logger.debug("splitChoice : " + str(splitChoice))

  # Ask to valid the LoD list
  print("\r\nThe default LoD list is : ")
  for simplificationValue in simplificationValuesList :
    print(simplificationValue)
  listValidation = raw_input("Are you okay about that ? Y/N (default=Y)")
  
  if(listValidation.lower() == "n"):
    #Ask about a new list
    value = 0
    simplificationValuesList = []
    while (value != "end"):
      value = raw_input("Enter a value ('end' to finish): ")
      if(value != "end" and value != 0):
        simplificationValuesList.append(int(value))
    
    print("\r\nYour LoD list is : ")
    for simplificationValue in simplificationValuesList :
      print(simplificationValue)
  
  logger.info("The LoD hierarchy will be : " + outputLoDHierarchy)
  logger.info("The output filename will be : " + outputFilenameBase)
  
  # Create directories
  dirCreator(tempDataPath)
  dirCreator(outputLoDHierarchy)
  dirCreator(outputHierarchy)
  
  if path.isfile(inputDataPath) and (inputDataPath.split(".")[-1] == "shp") :
    globalWorkflow(inputDataPath)
  else :
    print("Error ! Only process ShapeFile !")
    exit()
  
  fileCopier(fileLogPath, outputHierarchy)
  dirDeletor(tempDataPath)
  
  logging.info("The global process duration is : " + str(duration(beginDateTime)))
  print("The global process duration is : " + str(duration(beginDateTime)))
  loopQuestion = raw_input("Process another shapefile ? (Y/N)")
  
exit()
