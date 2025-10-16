# -*- coding: utf-8 -*-

"""Module that exposes the routines and utilities making up SPYDCMTK
"""

import os
import sys
import base64
import argparse
import numpy as np
import shutil
import pydicom as dicom

# Local imports 
import spydcmtk.dcmTools as dcmTools
import spydcmtk.dcmTK as dcmTK
from spydcmtk.spydcm_config import SpydcmTK_config


class INTERACTIVE():
    def __init__(self, study, outputPath) -> None:
        self.study = study
        self.outputPath = outputPath
        #
        self.options = {
            '1': ("Data summary", self.dataSummary),
            '2': ("Build VTS", self.buildVTS),
            '3': ("Build FDQ", self.buildFDQ),
            '4': ("Build overview image", self.buildOverviewImage),
            'q': ("Quit", self.quit)
        }

    def displayMenu(self):
        print("\nSelect an option:")
        for key, (description, _) in self.options.items():
            print(f"{key}: {description}")

    def getUserInput(self, question="your choice"):
        return input(f"Enter {question}: ")

    def setOutputPath(self):
        if self.outputPath is None:
            self.outputPath = self.getUserInput("output path")
            self.outputPath = os.path.abspath(self.outputPath)
            if not os.path.isdir(self.outputPath):
                print(f"Output path {self.outputPath} does not exist. Please enter a valid path.")
                self.setOutputPath()

    def run(self):
        while True:
            self.displayMenu()
            choice = self.getUserInput()
            if choice in self.options:
                self.options[choice][1]()  # Execute the corresponding function
            else:
                print("Invalid option. Please try again.")

    def dataSummary(self):
        print(self.study.getStudySummary())

    def buildVTS(self):
        self.dataSummary()
        self.setOutputPath()
        seNum = self.getUserInput("series number")
        try: 
            seNum = int(seNum)
            dcmSeries = self.study.getSeriesByID(seNum)
            outputFilename = self.getUserInput(f"file name to save at {self.outputPath} (vts)")
            outputpath = os.path.join(self.outputPath, outputFilename)
            dcmSeries.writeToVTS(outputpath)
        except ValueError:
            print("Invalid option. Please try again")

    def buildFDQ(self):
        self.dataSummary()
        self.setOutputPath()
        if self.study[0].IS_PHILIPS():
            seNum_ = self.getUserInput("series numbers for FDQ as: PX PY PZ :")
        else:
            seNum_ = self.getUserInput("series numbers for FDQ as: MAG PX PY PZ :")
        try: 
            seNum_4 = seNum_.strip().split(' ')
            seNum_4 = [int(i) for i in seNum_4]
            if self.study[0].IS_PHILIPS():
                seNum_4 = [seNum_4[0]] + seNum_4 
            outputFilename = self.getUserInput(f"file name to save at {self.outputPath} (pvd)")
            outputpath = os.path.join(self.outputPath, outputFilename)
            self.study.writeFDQ(seNum_4, outputpath, 'Vel')
        except ValueError:
            print("Invalid option. Please try again")

    def buildOverviewImage(self):
        self.dataSummary()
        self.setOutputPath()
        seNum = self.getUserInput("series number")
        outputFilename = self.getUserInput(f"file name to save at {self.outputPath} (png) - leave blank to show")
        if outputFilename == '':
            outputpath = None
        else:
            outputpath = os.path.join(self.outputPath, outputFilename)
        self.study.getSeriesByID(seNum).buildOverviewImage(outputpath)

    def quit(self):
        print("Exiting the menu.")
        exit()  


def writeDirectoryToNII(dcmDir, outputPath, fileName):
    """ Write a directory of dicom files to a Nifti (`*.nii.gz`) file. 
        Uses dcm2nii so MUST have dcm2nii installed and within path.

    Args:
        dcmDir (str): Path to directory containing dicom files
        outputPath (str): Path to output directory where to save nifti
        fileName (str): Name of output nii.gz file (will rename nii.gz output from dcm2nii)
    """
    return dcmTools.writeDirectoryToNII(dcmDir, outputPath, fileName)


def buildTableOfDicomParamsForManuscript(topLevelDirectoryList, outputCSVPath, seriesDescriptionIdentifier=None, ONE_FILE_PER_DIR=True):
    """ Build a simple table of dicom parameters that would be suitable for input into a scientific manuscript.
        Output is comma delimited multiline string of Tr, Te (etc) stats. 

    Args:
        topLevelDirectoryList (list): list of str that are paths to directories containing dicom files
        outputCSVPath (str): path to outputCSV
        seriesDescriptionIdentifier (str, optional): A substring of SeriesDescription tag used to select certian series only. Defaults to None.
        ONE_FILE_PER_DIR (bool, optional): Set false to read all dicoms, can set True for faster reading if dicoms organised. Default: True
    """
    dfData = []
    for inspectDir in topLevelDirectoryList:
        try:
            ssL = dcmTK.ListOfDicomStudies.setFromDirectory(inspectDir, OVERVIEW=True, HIDE_PROGRESSBAR=True, ONE_FILE_PER_DIR=ONE_FILE_PER_DIR)
        except IndexError: # no dicoms found 
            continue
        for ss in ssL:
            if seriesDescriptionIdentifier is not None:
                matchingSeries = ss.getSeriesMatchingDescription([seriesDescriptionIdentifier], RETURN_SERIES_OBJ=True)
            else:
                matchingSeries = ss
            if matchingSeries is not None:
                for iSeries in matchingSeries:
                    resDict = iSeries.getSeriesInfoDict(extraTags=SpydcmTK_config.MANUSCRIPT_TABLE_EXTRA_TAG_LIST)
                    resDict["Identifier"] = dcmTools.getDicomFileIdentifierStr(iSeries[0])
                    dfData.append(resDict)
    stats = {}
    dfData = sorted(dfData, key=lambda i:i["Identifier"])
    tagList = sorted(dfData[0].keys())
    strOut = ','+','.join(tagList) + '\n'
    for row in dfData:
        strOut += ','
        for i in tagList:
            strOut += f'{row[i]},'
            stats.setdefault(i, []).append(row[i])
        strOut += '\n'
    strOut += '\n\nSTATS:\n'
    for label, myFunc in zip(['Mean', 'Standard Deviation', 'Median', 'Min', 'Max'], 
                             [np.mean, np.std, np.median, np.min, np.max]):
        for k1 in range(len(tagList)):
            if k1 == 0:
                strOut += f'{label},'
            try:
                strOut += f'{myFunc(stats[tagList[k1]])},'
            except:
                strOut += 'NAN,'
        strOut += '\n'
    with open(outputCSVPath, 'w') as fid:
        fid.write(strOut)
    return outputCSVPath


def getAllDirsUnderRootWithDicoms(rootDir, QUIET=True, FORCE_READ=False):
    fullDirsWithDicoms = []
    for root, _, files in os.walk(rootDir):
        for iFile in files:
            thisFile = os.path.join(root, iFile)
            try:
                dicom.dcmread(thisFile, stop_before_pixels=True, defer_size=16, force=FORCE_READ) # will error if not dicom
                if not QUIET:
                    print('OK: %s'%(thisFile))
                fullDirsWithDicoms.append(root)
                break
            except dicom.filereader.InvalidDicomError:
                if not QUIET:
                    print('FAIL: %s'%(thisFile))
                continue
    return fullDirsWithDicoms


def anonymiseInPlace(dicomDirectory, anonName=None, anonID="", QUIET=False):
    if anonName is None:
        ds = returnFirstDicomFound(dicomDirectory)
        if ds is None:
            return # Nothing to anonymise... 
        anonName = ""
    #
    tmpDir = dicomDirectory+".TEMP.WORKING"
    os.rename(dicomDirectory, tmpDir)
    dcmTools.streamDicoms(tmpDir, dicomDirectory, anonName=anonName, anonID=anonID, HIDE_PROGRESSBAR=QUIET)
    shutil.rmtree(tmpDir)


def returnFirstDicomFound(rootDir, FILE_NAME_ONLY=False, MatchingTag_dict=None):
    """
    Search recursively for first dicom file under root and return.
    If have dicoms in nice folder structure then this can be a fast way to find, e.g. all series with protocol X

    :param rootDir: directory on filesystem
    :param FILE_NAME_ONLY: If true will return the file name [Default False]
    :param MatchingTag_dict: If given then will only consider dicoms where tag(key) matches value given [Default None]
    :return: pydicom dataset<without pixel data> or fileName<str>
    """
    for root, _, files in os.walk(rootDir):
        for iFile in files:
            if 'dicomdir' in iFile.lower():
                continue
            thisFile = os.path.join(root, iFile)
            try:
                dataset = dicom.dcmread(thisFile, stop_before_pixels=True)
                if MatchingTag_dict is not None:
                    tf = []
                    for iKey in MatchingTag_dict.keys():
                        tf.append(str(dataset[iKey].value) == str(MatchingTag_dict[iKey]))
                    if not all(tf):
                        continue
                if FILE_NAME_ONLY:
                    return thisFile
                else:
                    return dataset
            except dicom.filereader.InvalidDicomError:
                continue
    return None

def getTag(pathToDicoms, tagName):
    """Convienience function to find first dicom and then get tag value

    Args:
        pathToDicoms (str): path to dicoms
        tagName (str): dicom tag name
    """
    ds = returnFirstDicomFound(pathToDicoms)
    return ds[tagName].value, ds.filename

def directoryToVTI(dcmDirectory, outputFolder, 
                   outputNamingTags=SpydcmTK_config.VTI_NAMING_TAG_LIST, 
                   QUITE=True, FORCE=False, TRUE_ORIENTATION=False):
    """Convert directory of dicoms to VTI files (one vti per series)
        Naming built from dicom tags: 

    Args:
        dcmDirectory (str): Directory containing dicom files
        outputFolder (str): Directory where vti output files to be written
        outputNamingTags (tuple, optional): Dicom tags used to generate vti file name. 
                        Defaults to ('PatientName', 'SeriesNumber', 'SeriesDescription')
        QUITE (bool, optional): Suppress output information. Defaults to True.
        FORCE (bool, optional): Set True to overwrite already present files. Defaults to False.

    Returns:
        list: List of output file names written
    """
    ListDicomStudies = dcmTK.ListOfDicomStudies.setFromInput(dcmDirectory, HIDE_PROGRESSBAR=QUITE, FORCE_READ=FORCE, OVERVIEW=False) 
    return _listDicomStudiesToVTI(ListDicomStudies, outputFolder=outputFolder, outputNamingTags=outputNamingTags, TRUE_ORIENTATION=TRUE_ORIENTATION)


def directoryToVTS(dcmDirectory, outputFolder,
                   outputNamingTags=SpydcmTK_config.VTI_NAMING_TAG_LIST, 
                   QUITE=True, FORCE=False):
    """Convert directory of dicoms to VTS files (Good for cine etc)
        Naming built from dicom tags: 

    Args:
        dcmDirectory (str): Directory containing dicom files
        outputFolder (str): Directory where vti output files to be written
        outputNamingTags (tuple, optional): Dicom tags used to generate vti file name. 
                        Defaults to ('PatientName', 'SeriesNumber', 'SeriesDescription')
        QUITE (bool, optional): Suppress output information. Defaults to True.
        FORCE (bool, optional): Set True to overwrite already present files. Defaults to False.

    Returns:
        list: List of output file names written
    """
    ListDicomStudies = dcmTK.ListOfDicomStudies.setFromInput(dcmDirectory, HIDE_PROGRESSBAR=QUITE, FORCE_READ=FORCE, OVERVIEW=False) 
    return _listDicomStudiesToVTI(ListDicomStudies, outputFolder=outputFolder, outputNamingTags=outputNamingTags, VTS=True)


def _listDicomStudiesToVTI(ListDicomStudies, outputFolder, outputNamingTags=SpydcmTK_config.VTI_NAMING_TAG_LIST, QUIET=True, TRUE_ORIENTATION=False, VTS=False):
    outputFiles = []
    for iDS in ListDicomStudies:
        for iSeries in iDS:
            if VTS:
                # print(f"DICOMS TO VTS IS NOT IMPLEMENTED YET")
                fOut = iSeries.writeToVTS(outputPath=outputFolder, outputNamingTags=outputNamingTags)
            else:
                fOut = iSeries.writeToVTI(outputPath=outputFolder, outputNamingTags=outputNamingTags, TRUE_ORIENTATION=TRUE_ORIENTATION)
            outputFiles.append(fOut)
            if not QUIET:
                print(f'Written {fOut}')
    return outputFiles

# =========================================================================
# =========================================================================
## DATA TO HTML
# =========================================================================
def convertInputsToHTML(listOfFilePaths, outputFile=None, glanceHtml=None, QUIET=False, DEBUG=False):
    """Convert inputs to HTML viewable via ParaViewGlance (3D volumes and/or surface polymeshes)
    
    Keyword arguments:
    listOfFilePaths             -- May be nii, vtk or dicoms
    outputFile (optional)       -- Full path to outputfile, if not given then use first input path. Defaults to None.
    glanceHtml (optional)       -- Full path to glanceHtml template file, if not given then use default. Defaults to None.
    QUIET (optional)            -- Set True to suppress output. Defaults to False.
    DEBUG (optional)            -- Set True to prevent cleanup of intermediary files. Defaults to False.
    Return: path to html file written
    """
    
    CLEAN_UP_LIST = []
    FILE_TO_VTK_LIST = []
    ## --- Check inputs ---
    # Glance html
    if glanceHtml is None:
        thisDir = os.path.split(os.path.realpath(__file__))[0]
        glanceHtml = os.path.join(thisDir, 'ParaViewGlance.html')
        if not QUIET:
            print('Using ParaView glance file: %s'%(glanceHtml))
    if not os.path.isfile(glanceHtml):
        raise ValueError('%s does not exist'%(glanceHtml))
    if type(listOfFilePaths) != list:
        listOfFilePaths = [listOfFilePaths]
    ## --- Output file ---
    if outputFile is None:
        outputDir, fName = os.path.split(listOfFilePaths[0])
        fNameOut = os.path.splitext(fName)[0]+'.html'
        outputFile = os.path.join(outputDir, fNameOut)
    elif os.path.isdir(outputFile):
        outputDir = outputFile
        _, fName = os.path.split(listOfFilePaths[0])
        fNameOut = os.path.splitext(fName)[0]+'.html'
        outputFile = os.path.join(outputDir, fNameOut)
    else:
        outputDir, fNameOut = os.path.split(outputFile)

    ## --- VTK Objs / file paths ---
    for iPath in listOfFilePaths:
        if os.path.isfile(iPath):
            if iPath.endswith('nii') or iPath.endswith('nii.gz') :
                iPath = dcmTK.dcmVTKTK.fIO.readNifti(iPath)
                CLEAN_UP_LIST.append(iPath)
            FILE_TO_VTK_LIST.append(iPath)
        else:
            if os.path.isdir(iPath): # If path to dicoms
                dcmToVTKPath = directoryToVTI(iPath, outputDir, TRUE_ORIENTATION=False)
                for ifile in dcmToVTKPath:
                    if ifile.endswith('.pvd'):
                        FILE_TO_VTK_LIST += list(dcmTK.dcmVTKTK.fIO.readPVDFileName(ifile).values())
                    else:
                        FILE_TO_VTK_LIST.append(ifile)
                CLEAN_UP_LIST += dcmToVTKPath
            else:
                raise ValueError('%s does not exist' % (iPath))

    ## --- Build HTML Recursivly ---
    if not QUIET:
        print('Writing %s from base html %s, using:'%(outputFile, glanceHtml))
        for iFile in listOfFilePaths:
            print('    %s'%(iFile))

    for k1, iFile in enumerate(FILE_TO_VTK_LIST):
        outputTemp = outputFile[:-5]+'_TEMP%d.html'%(k1)
        glanceHtml = vtkToHTML(iFile, glanceHtml, outputTemp)
        CLEAN_UP_LIST.append(outputTemp)
    os.rename(CLEAN_UP_LIST.pop(), outputFile)

    ## --- Clean up --- // Skipped if in DEBUG mode
    if not DEBUG:
        if not QUIET:
            print('Cleaning up:', str(CLEAN_UP_LIST))
        for ifile in CLEAN_UP_LIST:
            if iFile.endswith('.pvd'):
                dcmTK.dcmVTKTK.fIO.deleteFilesByPVD(iFile)
            else:
                os.unlink(ifile)

    return outputFile


def vtkToHTML(vtkDataPath, glanceHtml, outputFile):
    # Extract data as base64
    with open(vtkDataPath, "rb") as data:
        dataContent = data.read()
        base64Content = base64.b64encode(dataContent)
        base64Content = base64Content.decode().replace("\n", "")
    # Create new output file
    with open(glanceHtml, mode="r", encoding="utf-8") as srcHtml:
        with open(outputFile, mode="w", encoding="utf-8") as dstHtml:
            for line in srcHtml:
                if "</body>" in line:
                    dstHtml.write("<script>\n")
                    dstHtml.write('var contentToLoad = "%s";\n\n' % base64Content)
                    dstHtml.write(
                        'Glance.importBase64Dataset("%s" , contentToLoad, glanceInstance.proxyManager);\n'
                        % os.path.basename(vtkDataPath)
                    )
                    dstHtml.write("glanceInstance.showApp();\n")
                    dstHtml.write("</script>\n")
                dstHtml.write(line)
    return outputFile


### ====================================================================================================================
##          RUN VIA MAIN
### ====================================================================================================================
# Override error to show help on argparse error (missing required argument etc)
class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)
##  ========= INSPECTION / VERIFICATION =========
def inspect(dStudies, FULL):
    frmtStr = dStudies.getSummaryString(FULL)
    print(frmtStr)

def checkArgs(args):
    allActionArgs = [args.nii, 
                args.inspect, 
                args.inspectFull, 
                args.inspectQuick,
                args.outputFolder is not None,
                args.vti,
                args.INTERACTIVE]
    return any(allActionArgs)

##  ========= RUN ACTIONS =========
def _runActions(args, ap):

    ####
    if args.dcmdump:
        ds = returnFirstDicomFound(args.inputPath, FILE_NAME_ONLY=False)
        print(ds)
    if args.tagValue is not None:
        val, fileName = getTag(args.inputPath, args.tagValue)
        print(f"{args.tagValue} = {val} (found at {fileName})")
    elif args.msTable:
        outputCSV = args.outputFolder if args.outputFolder.endswith('.csv') else os.path.join(args.outputFolder, 'ms.csv')
        fOut = buildTableOfDicomParamsForManuscript([args.inputPath], 
                                                    outputCSVPath= outputCSV,
                                                    seriesDescriptionIdentifier=None,
                                                    ONE_FILE_PER_DIR=False)
        print(f"Written Manuscript table like csv to {fOut}")
    else:
        # check arguments to avoid reading all dicoms and then doing nothing...
        if not checkArgs(args):
            ap.exit(0, f'No action given. Exiting SPYDCMTK without action\n')
        if args.STREAM:
            dcmTools.streamDicoms(args.inputPath, args.outputFolder, FORCE_READ=args.FORCE, HIDE_PROGRESSBAR=args.QUIET, SAFE_NAMING=args.SAFE)
            return 0
        ##
        ## NOW READING DICOMS
        try:
            onlyOverview = args.inspect or args.inspectFull or args.INTERACTIVE
            oneFilePerDir = args.inspectQuick or args.INTERACTIVE or args.seNumber or args.filter
            # If read one file per dir then will read all dicoms upon write out (or conversion). 
            # Only issue is if dicoms not well organised - TODO - NOTE this somewhere... Maybe bettter ad an option for force read all by user. 
            if not args.QUIET:
                print(f"READING...")
            ListDicomStudies = dcmTK.ListOfDicomStudies.setFromInput(args.inputPath, 
                                                                     ONE_FILE_PER_DIR=oneFilePerDir,
                                                                     HIDE_PROGRESSBAR=args.QUIET, 
                                                                     FORCE_READ=args.FORCE, 
                                                                     OVERVIEW=onlyOverview) 
            if args.SAFE:
                ListDicomStudies.setSafeNameMode()

            if args.seNumber is not None:
                if len(ListDicomStudies) > 1:
                    ListDicomStudies = ListDicomStudies.filterByTag('SeriesNumber', args.seNumber)
                else:
                    newListOfDicomStudies = []
                    for iStudy in ListDicomStudies: 
                        newListOfDicomStudies.append(iStudy.filterByTag('SeriesNumber', args.seNumber))
                    ListDicomStudies = dcmTK.ListOfDicomStudies(newListOfDicomStudies)

            if args.filter is not None:
                if len(ListDicomStudies) > 1:
                    ListDicomStudies = ListDicomStudies.filterByTag(args.filter[0], args.filter[1])
                else:
                    newListOfDicomStudies = []
                    for iStudy in ListDicomStudies: 
                        newListOfDicomStudies.append(iStudy.filterByTag(args.filter[0], args.filter[1]))
                    ListDicomStudies = dcmTK.ListOfDicomStudies(newListOfDicomStudies)

        except IOError as e:
            ap.exit(1, f'Error reading {args.inputPath}.\n    {e}')
            # Let IOERROR play out here is not correct input
        ##
        ## NOW ACTIONS
        if args.inspect or args.inspectFull or args.inspectQuick:
            for iStudy in ListDicomStudies:
                print(iStudy.getTopDir())
                print(iStudy.getStudySummary(args.inspectFull))
                print('\n')

        elif args.vti2dcm is not None:
            if not os.path.isfile(args.vti2dcm):
                ap.exit(1, f'ERROR: VTI file {args.vti2dcm} not found\n')
            try:
                vtiObj = dcmTK.dcmVTKTK.fIO.readVTKFile(args.vti2dcm)
            except OSError as e:
                ap.exit(1, f'ERROR reading VTI file: {e}\n')
            series = ListDicomStudies[0][0]
            series.sortBySlice_InstanceNumber()
            dcmDirOut = dcmTK.writeVTIToDicoms(vtiObj, series[0], outputDir=args.outputFolder)
            if not args.QUIET:
                print(f'Written {dcmDirOut}')
        # elif args.nii2dcm is not None:
        #     dcmTK.dcmVTKTK.fIO.readNifti(args.nii2dcm)
        elif args.INTERACTIVE:
            # TODO - check if multiple studies
            INTER = INTERACTIVE(ListDicomStudies[0], outputPath=args.outputFolder)
            INTER.run()

        else:
            if args.outputFolder is None:
                print(f'WARNING: outputFolder not given - setting to inputFolder')
                args.outputFolder = os.path.split(args.inputPath)[0]
            if args.nii:
                for iDS in ListDicomStudies:
                    for iSeries in iDS:
                        fOut = iSeries.writeToNII(outputPath=args.outputFolder)
                        if not args.QUIET:
                            print(f'Written {fOut}')
            elif args.vti:
                _listDicomStudiesToVTI(ListDicomStudies=ListDicomStudies, outputFolder=args.outputFolder, QUIET=args.QUIET, TRUE_ORIENTATION=args.TRUE_VTI_ORIENTATION)
            elif args.vts:
                _listDicomStudiesToVTI(ListDicomStudies=ListDicomStudies, outputFolder=args.outputFolder, QUIET=args.QUIET, VTS=True)
            elif args.html:
                for iDS in ListDicomStudies:
                    for iSeries in iDS:
                        fOut = convertInputsToHTML([iSeries.getRootDir()], args.outputFolder)
                        if not args.QUIET:
                            print(f'Written {fOut}')
            elif args.outputFolder is not None:
                if args.anonName is not None:
                    if not args.QUIET:
                        print(f"ANONYMISING...")
                    ListDicomStudies.anonymise(anonName=args.anonName, 
                                               anonPatientID=args.anonID, 
                                               removePrivateTags=args.REMOVE_PRIVATE_TAGS)
                    ListDicomStudies.resetUIDs()
                if not args.QUIET:
                    print(f"WRITTING...")
                outDirList = ListDicomStudies.writeToOrganisedFileStructure(args.outputFolder)
                if len(outDirList) > 0:
                    allDirsPresent = all([os.path.isdir(i) for i in outDirList])
                    res = 0 if allDirsPresent else 1
                    ap.exit(res, f'Transfer and sort from {args.inputPath} to {args.outputFolder} COMPLETE\n')
                else:
                    ap.exit(1, f'No dicoms written out for given conditions from {args.inputPath}\n')
        ##

### ====================================================================================================================
### ====================================================================================================================
# S T A R T
#
def main():
    # --------------------------------------------------------------------------
    #  ARGUMENT PARSING
    # --------------------------------------------------------------------------
    ap = MyParser(description='Simple Python Dicom Toolkit - spydcmtk')

    ap.add_argument('-i', dest='inputPath', help='Path to find dicoms (file or directory or tar or tar.gz or zip)', type=str, default=None)
    ap.add_argument('-o', dest='outputFolder', help='Path for output - if set then will organise dicoms into this folder', type=str, default=None)

    ap.add_argument('-a', dest='anonName',
        help='anonymous name [optional - if not given, then not anoymised]', type=str, default=None)
    ap.add_argument('-aid', dest='anonID',
        help='anonymous ID [optional - only used if anonName is given, default=""]', type=str, default='')
    ap.add_argument('-RemovePrivateTags', dest='REMOVE_PRIVATE_TAGS',
        help='set to remove private tags during anonymisation [optional - only used if anonName is given, default="False"]', action='store_true')
    ap.add_argument('-filter', dest='filter',
        help='Will filter dicoms based on tag name and value. Tag name and value required. If input is multiple studies then act on each.', nargs=2, default=None)
    ap.add_argument('-seNumber', dest='seNumber',
        help='Will filter dicoms based on series number. Same as -filter SeriesNumber #', type=str, default=None)
    ap.add_argument('-inspect', dest='inspect',
        help='Will output a summary of dicoms to the terminal', action='store_true')
    ap.add_argument('-inspectFull', dest='inspectFull',
        help='Will output a full summary of dicoms to the terminal', action='store_true')
    ap.add_argument('-inspectQuick', dest='inspectQuick',
        help='Run inspection - expect organised file structure (read only one file per directory)', action='store_true')
    ap.add_argument('-msTable', dest='msTable',
        help='Will output a csv to outputFolder with tags info suitable for building manuscript style table', action='store_true')
    ap.add_argument('-dcmdump', dest='dcmdump',
        help='Will output a dump of all dicom tags to the terminal (from first found dicom)', action='store_true')
    ap.add_argument('-tag', dest='tagValue',
        help='Get tag value for first dicom found under input', type=str, default=None)
    ap.add_argument('-nii', dest='nii',
        help='Will convert each series to nii.gz. Naming: {PName}_{SE#}_{SEDesc}.nii.gz', action='store_true')
    ap.add_argument('-vti', dest='vti',
        help='Will convert each series to vti. Naming: {PName}_{SE#}_{SEDesc}.vti', action='store_true')
    ap.add_argument('-TRUE_VTI_ORIENTATION', dest='TRUE_VTI_ORIENTATION', help='Will resample vti data at true location (output different dimensiuons)', action='store_true')
    ap.add_argument('-vts', dest='vts',
        help='Will convert each series to vts. Naming: {PName}_{SE#}_{SEDesc}.vts', action='store_true')
    ap.add_argument('-html', dest='html',
        help='Will convert each series to html file for web viewing. Naming: outputfolder argument', action='store_true')
    #
    ap.add_argument('-vti2dcm', dest='vti2dcm',
        help='Will convert VTI to dicom series. Pass reference dicoms as input.', type=str, default=None)
    # ap.add_argument('-nii2dcm', dest='nii2dcm',
    #     help='Will convert NII to dicom series. Pass reference dicoms as input.', type=str, default=None)
    #
    ap.add_argument('-I', dest='INTERACTIVE', help='Will read input and launch interactive mode (provide options -i and optionally -o)', action='store_true')
    #
    ap.add_argument('-config', dest='configFile', help='Path to configuration file to use.', type=str, default=None)
    # -- program behaviour guidence -- #
    ap.add_argument('-SAFE', dest='SAFE', help='Safe naming - uses UIDs for naming to avoid potential conflicts.\n\t'+\
                        'Note, normal behaviour is to check for safe naming but certain conditions may require this.',
                            action='store_true')
    ap.add_argument('-FORCE', dest='FORCE', help='force reading even if not standard dicom (needed if dicom files missing header meta)',
                            action='store_true')
    ap.add_argument('-QUIET', dest='QUIET', help='Suppress progress bars and information output to terminal',
                            action='store_true')
    ap.add_argument('-INFO', dest='INFO', help='Provide setup (configuration) info and exit.',
                            action='store_true')
    ap.add_argument('-STREAM', dest='STREAM', help='To organise dicoms rapidly without any quality checking',
                            action='store_true')
    ##

    arguments = ap.parse_args()
    SpydcmTK_config.runconfigParser(arguments.configFile)
    if arguments.INFO:
        SpydcmTK_config.printInfo()
        sys.exit(1)

    if arguments.inputPath is not None:
        arguments.inputPath = os.path.abspath(arguments.inputPath)
        if not (os.path.isdir(arguments.inputPath) or os.path.isfile(arguments.inputPath)):
            print(f'## ERROR : Can not find input {arguments.inputPath}')
            print('EXITING')
            sys.exit(1)
        if not arguments.QUIET:
            print(f'Running SPYDCMTK with input {arguments.inputPath}')
    else:
        print(f'## ERROR : inputPath (-i option) must be provided. ')
        print('EXITING')
        sys.exit(1)

    ## -------------
    if arguments.outputFolder is not None:
        arguments.outputFolder = os.path.abspath(arguments.outputFolder)
        # Check if input is subdirectory of output
        if os.path.commonpath([arguments.inputPath]) == os.path.commonpath([arguments.inputPath, arguments.outputFolder]):
            print(f'## ERROR: Input directory ({arguments.inputPath}) cannot be a subdirectory of output directory ({arguments.outputFolder})')
            print('This would cause recursive copying and potential data corruption.')
            print('EXITING')
            sys.exit(1)

    _runActions(arguments, ap)


if __name__ == '__main__':

    main()