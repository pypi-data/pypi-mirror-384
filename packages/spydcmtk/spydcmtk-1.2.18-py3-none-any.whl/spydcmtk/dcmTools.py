# -*- coding: utf-8 -*-

"""Basic helper tools here
"""

import os
import datetime
import glob
import numpy as np
import tarfile
import shutil
import zipfile
import pydicom as dicom
from tqdm import tqdm
from ngawari import fIO

from spydcmtk.spydcm_config import SpydcmTK_config

# =========================================================================
## CONSTANTS
# =========================================================================
mm_to_m = 0.001
cm_to_m = 0.01
ms_to_s = 0.001
m_to_mm = 1000.0


class DicomTags(object):
    # these are based on keyword value
    Modality = 0x0008, 0x0060
    Manufacturer = 0x0008, 0x0070
    ManufacturerModelName = 0x0008, 0x1090
    SoftwareVersions = 0x0018, 0x1020
    StudyDescription = 0x0008, 0x1030
    SeriesDescription = 0x0008, 0x103e
    BodyPartExamined = 0x0018, 0x0015
    SliceThickness = 0x0018, 0x0050
    RepetitionTime = 0x0018, 0x0080
    EchoTime = 0x0018, 0x0081
    InversionTime = 0x0018, 0x0082
    NumberOfAverages = 0x0018, 0x0083
    MagneticFieldStrength = 0x0018, 0x0087
    SpacingBetweenSlices = 0x0018, 0x0088
    TriggerTime = 0x0018, 0x1060
    NominalInterval = 0x0018, 0x1062
    HeartRate = 0x0018, 0x1088
    CardiacNumberOfImages = 0x0018, 0x1090
    TriggerWindow = 0x0018, 0x1094
    ReceiveCoilName = 0x0018, 0x1250
    AcquisitionMatrix = 0x0018, 0x1310
    FlipAngle = 0x0018, 0x1314
    PatientPosition = 0x0018, 0x5100
    PatientOrientation = 0x0020, 0x0020
    ImagePositionPatient = 0x0020, 0x0032
    ImageOrientationPatient = 0x0020, 0x0037
    StudyInstanceUID = 0x0020, 0x000d
    SeriesInstanceUID = 0x0020, 0x000e
    SeriesNumber = 0x0020, 0x0011
    PixelSpacing = 0x0028, 0x0030
    StudyDate = 0x0008, 0x0020
    PatientName = 0x0010, 0x0010
    PatientID = 0x0010, 0x0020
    PatientDateOfBirth = 0x0010, 0x0030
    PatientSex = 0x0010, 0x0040
    InstanceNumber = 0x0020, 0x0013
    StudyID = 0x0020, 0x0010
    AccessionNumber = 0x0008, 0x0050


def getTagCode(tagName):
    return eval("DicomTags.%s" % (tagName))


def getStdDicomTags():
    allVar = vars(DicomTags)
    res = []
    for iVar in allVar:
        val = getTagCode(iVar)
        if type(val) == tuple:
            if len(val) == 2:
                res.append(iVar)
    return res


def getDicomTagsDict():
    tt = getStdDicomTags()
    return dict(zip([i for i in tt], [eval("DicomTags.%s" % (i)) for i in tt]))


def countFilesInDir(dirName):
    N = 0
    if os.path.isdir(dirName):
        for _, _, filenames in os.walk(dirName):  # @UnusedVariable
            N += len(filenames)
    return N



def writeDictionaryToJSON(fileName, dictToWrite):
    return fIO.writeDictionaryToJSON(fileName, dictToWrite)


def parseJsonToDictionary(fileName):
    return fIO.parseJsonToDictionary(fileName)


def fixPath(p):
    return p.encode('utf8', 'ignore').strip().decode()

def cleanString(ss):
    if not type(ss) == str:
        return ss
    ss = ss.replace('^', '-')
    ss = ss.replace(' ', '_')
    ss = ss.replace('__', '_')
    keepcharacters = ('-', '.', '_', 'ö','ü','ä','é','è','à')
    ss = "".join([c for c in ss if (c.isalnum() or (c.lower() in keepcharacters))]).rstrip()
    while True:
        try:
            if ss[-1] == '.':
                ss = ss[:-1]
            else:
                break
        except IndexError:
            pass
            break
    while True:
        try:
            if ss[0] == '_':
                ss = ss[1:]
            else:
                break
        except IndexError:
            pass
            break
    return fixPath(ss)


def dbDateToDateTime(dbDate):
    try:
        return datetime.datetime.strptime(dbDate, '%Y%m%d')
    except ValueError:
        return datetime.datetime.strptime(dbDate, '%Y%m%dT%H%M%S')


def dateTime_to_dbString(dateTime):
    return dateTime.strftime('%Y%m%d')


def distPts(pt1, pt2):
    try:
        dist = np.sqrt((pt1[0] - pt2[0]) ** 2 + (pt1[1] - pt2[1]) ** 2 + (pt1[2] - pt2[2]) ** 2)
    except IndexError:
        dist = np.sqrt((pt1[0] - pt2[0]) ** 2 + (pt1[1] - pt2[1]) ** 2)
    return dist


def _isCompressed(ds):
    """
    Check if dicom dataset is compressed or not
    """
    uncompressed_types = ["1.2.840.10008.1.2",
                            "1.2.840.10008.1.2.1",
                            "1.2.840.10008.1.2.1.99",
                            "1.2.840.10008.1.2.2"]

    if ('TransferSyntaxUID' in ds.file_meta) and (ds.file_meta.TransferSyntaxUID in uncompressed_types):
        return False
    elif 'TransferSyntaxUID' not in ds.file_meta:
        return False
    return True

def instanceNumberSortKey(val):
    try:
        return int(__getTags(val, ['InstanceNumber'])['InstanceNumber'])
    except (ValueError, IOError, AttributeError):
        return 99e99

def sliceLoc_InstanceNumberSortKey(val):
    """
    Sort by slice location 1st (group all slices together), then instance number
    """
    try:
        return (float(__getTags(val, ['SliceLocation'])['SliceLocation']), float(__getTags(val, ['InstanceNumber'])['InstanceNumber']))
    except (ValueError, IOError, AttributeError):
        return (99e9, 99e9)

def __getTags(dataset, tagsList):
    tagsDict = {}
    for iKey in tagsList:
        tagsDict[iKey] = dataset.get(iKey, 'Unknown')
    return tagsDict


def getRootDirWithSEdirs(startDir):
    """
    Search from startDir until find rootDir with format of subdirs:
        `SE123_` etc

    param1: start directory of search
    return: rootdirectory with subfolders of SE{int}_ format (startDir if not found)
    """

    def __isSEDirFormat(dd):
        if dd[:2] == "SE":
            try:
                int(dd.split("_")[0][2:])
            except ValueError:
                return False
            return True
        return False

    dicomRootDir = startDir
    for root, dirs, _ in os.walk(startDir):
        if any([__isSEDirFormat(dd) for dd in dirs]):
            dicomRootDir = root
            break
    return dicomRootDir


def seriesNumbersToDicomDirList(dicomRootDir, seriesNumbers):
    if not type(seriesNumbers) == list:
        seriesNumbers = [seriesNumbers]
    dicomRootDir = getRootDirWithSEdirs(dicomRootDir)
    SEList = os.listdir(dicomRootDir)
    dicomDirs = []
    for iSE in seriesNumbers:
        ii = [jj for jj in SEList if "SE%d" % (iSE) in jj.split('_')]
        dicomDirs.append(os.path.join(dicomRootDir, ii[0]))
    return dicomDirs


def walkdir(folder):
    """Walk through each files in a directory"""
    for dirpath, _, files in os.walk(folder):
        for filename in files:
            yield os.path.abspath(os.path.join(dirpath, filename))


def getDicomDictFromCompressed(compressedFile, QUIET=True, FORCE_READ=False, FIRST_ONLY=False, OVERVIEW_ONLY=False,
                        matchingTagValuePair=None):
    compressedFileL = compressedFile.lower()
    if compressedFileL.endswith('tar') or compressedFileL.endswith('tar.gz'):
        return getDicomDictFromTar(compressedFile, QUIET=QUIET, FORCE_READ=FORCE_READ, FIRST_ONLY=FIRST_ONLY,
                                   OVERVIEW_ONLY=OVERVIEW_ONLY, matchingTagValuePair=matchingTagValuePair)
    elif compressedFileL.endswith('zip'):
        return getDicomDictFromZip(compressedFile, QUIET=QUIET, FORCE_READ=FORCE_READ, FIRST_ONLY=FIRST_ONLY,
                                   OVERVIEW_ONLY=OVERVIEW_ONLY, matchingTagValuePair=matchingTagValuePair)
    return None


def getDicomDictFromTar(tarFileToRead, QUIET=True, FORCE_READ=False, FIRST_ONLY=False, OVERVIEW_ONLY=False,
                        matchingTagValuePair=None):
    # for sub dir in tar get first dicom - return list of ds
    dsDict = {}
    if tarFileToRead.endswith('gz'):
        tar = tarfile.open(tarFileToRead, "r:gz")
    else:
        tar = tarfile.open(tarFileToRead)
    successReadDirs = set()
    for member in tar:
        if member.isfile():
            root = os.path.split(member.name)[0]
            if FIRST_ONLY and (root in successReadDirs):
                continue
            thisFile=tar.extractfile(member)
            try:
                dataset = dicom.dcmread(thisFile, stop_before_pixels=OVERVIEW_ONLY, force=FORCE_READ)
                if matchingTagValuePair is not None:
                    if dataset.get(matchingTagValuePair[0], 'NIL') != matchingTagValuePair[1]:
                        continue
                studyUID = str(dataset.StudyInstanceUID)
                seriesUID = str(dataset.SeriesInstanceUID)
                if studyUID not in dsDict:
                    dsDict[studyUID] =  {}
                if seriesUID not in dsDict[studyUID]:
                    dsDict[studyUID][seriesUID] = []
                dsDict[studyUID][seriesUID].append(dataset)

                if FIRST_ONLY:
                    successReadDirs.add(root)
            except dicom.filereader.InvalidDicomError:
                if not QUIET:
                    print('FAIL: %s'%(thisFile))
    tar.close()
    return dsDict


def getDicomDictFromZip(zipFileToRead, QUIET=True, FORCE_READ=False, FIRST_ONLY=False, OVERVIEW_ONLY=False,
                        matchingTagValuePair=None):
    """Read a zip archive, extract dicoms to structures dictionary
    """
    dsDict = {}
    with zipfile.ZipFile(zipFileToRead) as zf:
        for file in zf.namelist():
            with zf.open(file) as thisFile:
                try:
                    dataset = dicom.dcmread(thisFile, stop_before_pixels=OVERVIEW_ONLY, force=FORCE_READ)
                    if matchingTagValuePair is not None:
                        if dataset.get(matchingTagValuePair[0], 'NIL') != matchingTagValuePair[1]:
                            continue
                    studyUID = str(dataset.StudyInstanceUID)
                    seriesUID = str(dataset.SeriesInstanceUID)
                    if studyUID not in dsDict:
                        dsDict[studyUID] =  {}
                    if seriesUID not in dsDict[studyUID]:
                        dsDict[studyUID][seriesUID] = []
                    dsDict[studyUID][seriesUID].append(dataset)

                    if FIRST_ONLY:
                        return dsDict
                except (dicom.filereader.InvalidDicomError, AttributeError):
                    if not QUIET:
                        print('FAIL reading: %s'%(thisFile))
    return dsDict

def anonymiseDicomDS(dataset, UIDupdateDict={}, anon_birthdate=True, remove_private_tags=False, anonName=None, anonID=''):
    # Define call-back functions for the dataset.walk() function
    def PN_callback(ds, data_element):
        """Called from the dataset "walk" recursive function for all data elements."""
        if data_element.VR == "PN":
            data_element.value = 'anonymous'
        if "Institution" in data_element.name:
            data_element.value = 'anonymous'
        if (anonName is not None) & (data_element.name == "Patient's Name"):
            data_element.value = anonName
    # Remove patient name and any other person names
    try:
        dataset.walk(PN_callback)
    except TypeError: # TODO config setting to control level of warnings for this. 
        pass
    # Change ID
    dataset.PatientID = anonID
    # UIDs
    if 'SeriesInstanceUID' in UIDupdateDict.keys():
        dataset.SOPInstanceUID = dicom.uid.generate_uid()
        dataset.StudyInstanceUID = UIDupdateDict.get('StudyInstanceUID', dataset.StudyInstanceUID)
        dataset.SeriesInstanceUID = UIDupdateDict['SeriesInstanceUID']
    for name in ['OtherPatientIDs', 'OtherPatientIDsSequence', 'PatientAddress']:
        if name in dataset:
            delattr(dataset, name)
    if anon_birthdate:
        for name in ['PatientBirthDate']:
            if name in dataset:
                dataset.data_element(name).value = ''
    if remove_private_tags:
        try:
            dataset.remove_private_tags()
        except TypeError:
            pass
    return dataset

def getSaveFileNameFor_ds_UID(ds, outputRootDir):
    destFile = os.path.join(outputRootDir, ds.PatientID, ds.StudyInstanceUID, ds.SeriesInstanceUID, __getDSSaveFileName(ds, SAFE_NAMING=True))
    return destFile

def getSaveFileNameFor_ds(ds, outputRootDir, ANON=False):
    if ANON:
        destFile = os.path.join(outputRootDir, getStudyDirName(ds), getSeriesDirName(ds), __getDSSaveFileName(ds, SAFE_NAMING=False))
    else:
        destFile = os.path.join(outputRootDir, getPatientDirName(ds), getStudyDirName(ds), getSeriesDirName(ds), __getDSSaveFileName(ds, SAFE_NAMING=False))
    return destFile

def getPatientDirName(ds):
    try:
        return cleanString(f'{ds[DicomTags.PatientName].value}_{ds[DicomTags.PatientID].value}')
    except (TypeError, KeyError, AttributeError):
        try:
            return ds.PatientID
        except AttributeError:
            return ''
    
def getStudyDirName(ds):
    try:
        
        return cleanString(f'{ds[DicomTags.StudyDate].value}_{ds[DicomTags.StudyID].value}')
    except (TypeError, KeyError, AttributeError):
        return ds.StudyInstanceUID
    
def getSeriesDirName(ds):
    try:
        return cleanString(f'SE{ds[DicomTags.SeriesNumber].value}_{ds[DicomTags.SeriesDescription].value}')
    except (TypeError, KeyError, AttributeError):
        return ds.SeriesInstanceUID
    

def __getDSSaveFileName_Safe(ds):
    return 'IM-%s.dcm'%(ds.SOPInstanceUID)

def __getDSSaveFileName(ds, SAFE_NAMING):
    if SAFE_NAMING:
        return __getDSSaveFileName_Safe(ds)
    try:
        return 'IM-%05d-%05d.dcm'%(int(ds.SeriesNumber),
                                        int(ds.InstanceNumber))
    except (TypeError, KeyError, AttributeError):
        return __getDSSaveFileName_Safe(ds)

def getDicomFileIdentifierStr(ds):
    strOut = f'{ds[DicomTags.PatientName].value}_{ds[DicomTags.PatientID].value}_' +\
            f'{ds[DicomTags.StudyDate].value}_{ds[DicomTags.SeriesNumber].value}_{ds[DicomTags.InstanceNumber].value}'
    return cleanString(strOut)

def writeOut_ds(ds, outputRootDir, anonName=None, anonID='', UIDupdateDict={}, SAFE_NAMING=False, REMOVE_PRIVATE_TAGS=False):
    destFile = os.path.join(outputRootDir, __getDSSaveFileName(ds, SAFE_NAMING))
    os.makedirs(outputRootDir, exist_ok=True)
    if anonName is not None:
        ds = anonymiseDicomDS(ds, UIDupdateDict=UIDupdateDict, anonName=anonName, anonID=anonID, remove_private_tags=REMOVE_PRIVATE_TAGS)
    ds.save_as(destFile, enforce_file_format=True)
    return destFile

def streamDicoms(inputDir, outputDir, FORCE_READ=False, HIDE_PROGRESSBAR=False, SAFE_NAMING=False, anonName=None, anonID=""):
    nFiles = countFilesInDir(inputDir)
    outputDirTEMP = outputDir+".WORKING"
    try:
        os.rename(outputDir, outputDirTEMP)
    except FileNotFoundError:
        pass # OK - will make directory and rename at end
    for thisFile in tqdm(walkdir(inputDir), total=nFiles, leave=True, disable=HIDE_PROGRESSBAR):
        if 'dicomdir' in os.path.split(thisFile)[1].lower():
            continue
        if thisFile.endswith('json'):
            continue
        try:
            dataset = dicom.dcmread(thisFile, force=FORCE_READ, stop_before_pixels=False)
            if SAFE_NAMING: 
                fOut = getSaveFileNameFor_ds_UID(dataset, outputDirTEMP)
            else:
                fOut = getSaveFileNameFor_ds(dataset, outputDirTEMP, ANON=anonName is not None)
            os.makedirs(os.path.split(fOut)[0], exist_ok=True)
            if anonName is not None:
                dataset = anonymiseDicomDS(dataset, anonName=anonName, anonID=anonID, remove_private_tags=False)
            dataset.save_as(fOut, enforce_file_format=True)
        except dicom.filereader.InvalidDicomError:
            continue
    os.rename(outputDirTEMP, outputDir)

def readDicomFile_intoDict(dcmFile, dsDict, FORCE_READ=False, OVERVIEW=False):
    dsDict_temp = getDicomDictFromCompressed(dcmFile, OVERVIEW_ONLY=OVERVIEW, FORCE_READ=FORCE_READ)
    if dsDict_temp is not None: 
        for iStudyUID in dsDict_temp.keys():
            if iStudyUID in dsDict.keys():
                for iSeriesUID in dsDict_temp[iStudyUID].keys():
                    if iSeriesUID in dsDict[iStudyUID].keys():
                        dsDict[iStudyUID][iSeriesUID] += dsDict_temp[iStudyUID][iSeriesUID]
                    else:
                        dsDict[iStudyUID][iSeriesUID] = dsDict_temp[iStudyUID][iSeriesUID]
            else:
                dsDict[iStudyUID] = dsDict_temp[iStudyUID]
    else:
        dataset = dicom.dcmread(dcmFile, stop_before_pixels=OVERVIEW, force=FORCE_READ)
        studyUID = str(dataset.StudyInstanceUID)
        seriesUID = str(dataset.SeriesInstanceUID)
        if studyUID not in dsDict:
            dsDict[studyUID] =  {}
        if seriesUID not in dsDict[studyUID]:
            dsDict[studyUID][seriesUID] = []
        dsDict[studyUID][seriesUID].append(dataset)
    return dsDict


def organiseDicomHeirarchyByUIDs(rootDir, HIDE_PROGRESSBAR=False, FORCE_READ=False, ONE_FILE_PER_DIR=False, OVERVIEW=False, extn_filter=None, DEBUG=False):
    """Find all dicoms under "rootDir" and organise based upon UIDs

    Args:
        rootDir (str): Directory path under which to search
        HIDE_PROGRESSBAR (bool, optional): To hide tqdm progress bar. Defaults to False.
        FORCE_READ (bool, optional): Will tell pydicom to force read files that do not conform to dicom standard. Defaults to False.
        ONE_FILE_PER_DIR (bool, optional): For a fast summary, will read only first file found per subdirectory (if one knows that dicoms are already organised in such a format). Defaults to False.
        OVERVIEW (bool, optional): Will not read pixel data. Defaults to False.
        extn_filter (str, optional): For faster reading of large multi data directory trees pass an extension to filter upon (e.g. dcm) then will only read files ending in this extension. Defaults to None.
        DEBUG (bool, optional): Set true for debugging actions. Defaults to False.

    Returns:
        dict: A larger dictionary structure of {studyUID: {seriesUID: [list of pydicom datasets]}}
    """
    if os.path.isfile(rootDir):
        return readDicomFile_intoDict(rootDir, {}, FORCE_READ=FORCE_READ, OVERVIEW=OVERVIEW)
    dsDict = {}
    successReadDirs = set()
    nFiles = countFilesInDir(rootDir)
    for thisFile in tqdm(walkdir(rootDir), total=nFiles, leave=True, disable=HIDE_PROGRESSBAR):
        if extn_filter is not None:
            if not thisFile.endswith(extn_filter):
                continue
        if 'dicomdir' in os.path.split(thisFile)[1].lower():
            continue
        if thisFile.endswith('json'):
            continue
        if ONE_FILE_PER_DIR:
            thisDir, ff = os.path.split(thisFile)
            if thisDir in successReadDirs:
                continue
        try:
            readDicomFile_intoDict(thisFile, dsDict, FORCE_READ=FORCE_READ, OVERVIEW=OVERVIEW)
            if ONE_FILE_PER_DIR:
                successReadDirs.add(thisDir)
        except dicom.filereader.InvalidDicomError:
            if DEBUG:
                print(f"Error reading {thisFile}")
            continue
        except AttributeError:
            if DEBUG:
                print(f"Error reading {thisFile} - missing a needed dicom tag")
            continue
    return dsDict


def writeDirectoryToNII(dcmDir, outputPath, fileName):
    """Write directory of dicom files to nifti file.
        Requires dcm2nii which must be in path or provided via config. 
        Also writes json sidecar. s

    Args:
        dcmDir (str): Directory under which to find DICOMS
        outputPath (str): Directory where to save output
        fileName (str): Filename for output

    Raises:
        OSError: If dcm2nii path is not found

    Returns:
        str: full filename of new nifti file
    """
    if not os.path.isfile(SpydcmTK_config.dcm2nii_path):
        res = shutil.which(SpydcmTK_config.dcm2nii_path) # Maybe command name and in path
        if res is None:
            raise OSError(f"Program {SpydcmTK_config.dcm2nii_path} must exist and be set in config (or in path). ")
    dcm2niiCmd = f"{SpydcmTK_config.dcm2nii_path} {SpydcmTK_config.dcm2nii_options} -o '{outputPath}' '{dcmDir}'"
    print(f'RUNNING: {dcm2niiCmd}')
    os.system(dcm2niiCmd)
    extn = '.nii.gz' if '-z y' in SpydcmTK_config.dcm2nii_options else '.nii'
    list_of_files = glob.glob(os.path.join(outputPath, f'*{extn}')) 
    latest_file = max(list_of_files, key=os.path.getctime)
    newFileName = os.path.join(outputPath, fileName)
    os.rename(latest_file, newFileName)
    print(f"Renamed {latest_file} --> as {newFileName}")
    latest_json = latest_file.replace(extn, '.json')
    if os.path.isfile(latest_json):
        os.rename(latest_json, newFileName.replace(extn, '.json'))
    return newFileName


def buildFakeDS():
    meta = dicom.dataset.FileMetaDataset()
    meta.FileMetaInformationVersion = b"\x00\x01"
    meta.TransferSyntaxUID = ("1.2.840.10008.1.2.1")  # std transfer uid little endian, implicit vr
    meta.ImplementationVersionName = "spydcmtk"
    ds = dicom.dataset.FileDataset(f'/tmp/{dicom.uid.generate_uid()}.dcm', {}, file_meta=meta, preamble=b"\0" * 128)
    ds.add_new([0x0008,0x0005], 'CS', 'ISO_IR 100')
    ds.add_new([0x0008,0x0016], 'UI', '1.2.840.10008.5.1.4.1.1.7')
    ds.add_new([0x0008,0x0018], 'UI', dicom.uid.generate_uid())
    ds.add_new([0x0008,0x0020], 'DA', '20000101')
    ds.add_new([0x0008,0x0030], 'TM', '101010')
    ds.add_new([0x0008,0x0060], 'CS', 'MR')
    ds.add_new([0x0020,0x000d], 'UI', dicom.uid.generate_uid())
    ds.add_new([0x0020,0x000e], 'UI', dicom.uid.generate_uid())
    ds.add_new([0x0028,0x0002], 'US', 1)
    ds.add_new([0x0028,0x0004], 'CS', 'MONOCHROME2')
    ds.add_new([0x0028,0x0103], 'US', 0)
    ##
    ds.add_new([0x0010,0x0010], 'PN', "TEST^DATA")
    ds.add_new([0x0010,0x0020], 'LO', '12345')
    return ds

