'''
Created on Jan 6, 2016

@author: $Author: horen.tom@gmail.com$

This module is part of the ATE.org (meta) package.
--------------------------------------------------
This library implements the STDF standard to the full extend (meaning including optional field presence) to read/modify/write STDF files. 

Support:
    Endians: Little & Big 
    Versions & Extensions:
        V3 : standard, +
        V4 : standard, V4-2007, Memory:2010.1
    Modes: read & write
    compressions: gzip (read & write)
        
Disclaimer:
    Although all aspects of the library are tested extensively with unit tests, the library could only be tested in real life using standard STDF V4 files.
    It has not been used with STDF V4 extensions (lack of sample files) or STDF V3 (lack of sample files and specification)
        
License : GPL    
'''
import pprint
import sys
from numpy import record
if sys.version_info[0] < 3:
    raise Exception("The STDF library is made for Python 3") 

import os, time, struct, io, pickle, bz2
import gzip, hashlib, re, shutil
from tqdm import tqdm
from mimetypes import guess_type
from shutil import copyfileobj

from ATE.utils import DT, magicnumber

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

__version__ = '$Revision: 0.51 $'
__author__ = '$Author: tho $'

__latest_STDF_version__ = 'V4'

FileNameDefinitions = {
    'V3' : r'[a-zA-Z][a-zA-Z0-9_\$]{0,38}.[sS][tT][dD][a-zA-Z0-9_\.\$]{0,36}', # ?!?
    'V4' : r'[a-zA-Z][a-zA-Z0-9_]{0,38}\.[sS][tT][dD][a-zA-Z0-9_\.]{0,36}'
}

RecordDefinitions = {
    # Information about the STDF file
    (0,10)   : {'V3' : ['FAR', 'File Attributes Record', [('', False)]],                        'V4' : ['FAR', 'File Attributes Record', [('', True)]]                               },                                                    
    (0,20)   : {                                                                                'V4' : ['ATR', 'Audit Trail Record', [('', False)]]                                  },
    (0,30)   : {                                                                                'V4' : ['VUR', 'Version Update Record', [('V4-2007', True), ('Memory:2010.1', True)]]},
    # Data collected on a per lot basis
    (1,10)   : {'V3' : ['MIR', 'Master Information Record', [('', True)]],                      'V4' : ['MIR', 'Master Information Record', [('', True)]]                            },
    (1,20)   : {'V3' : ['MRR', 'Master Results Record', [('', True)]],                          'V4' : ['MRR', 'Master Results Record', [('', True)]]                                },
    (1,30)   : {                                                                                'V4' : ['PCR', 'Part Count Record', [('', True)]]                                    },
    (1,40)   : {'V3' : ['HBR', 'Hardware Bin Record', [('', False)]],                           'V4' : ['HBR', 'Hardware Bin Record', [('', False)]]                                 },
    (1,50)   : {'V3' : ['SBR', 'Software Bin Record', [('', False)]],                           'V4' : ['SBR', 'Software Bin Record', [('', False)]]                                 },
    (1,60)   : {'V3' : ['PMR', 'Pin Map Record', [('', False)]],                                'V4' : ['PMR', 'Pin Map Record', [('', False)]]                                      },
    (1,62)   : {                                                                                'V4' : ['PGR', 'Pin Group Record', [('', False)]]                                    },
    (1,63)   : {                                                                                'V4' : ['PLR', 'Pin List Record', [('', False)]]                                     },
    (1,70)   : {                                                                                'V4' : ['RDR', 'Re-test Data Record', [('', False)]]                                 },
    (1,80)   : {                                                                                'V4' : ['SDR', 'Site Description Record', [('', False)]]                             },
    (1,90)   : {                                                                                'V4' : ['PSR', 'Pattern Sequence Record', [('V4-2007', False)]]                      },
    (1,91)   : {                                                                                'V4' : ['NMR', 'Name Map Record', [('V4-2007', False)]]                              },
    (1,92)   : {                                                                                'V4' : ['CNR', 'Cell Name Record', [('V4-2007', False)]]                             },
    (1,93)   : {                                                                                'V4' : ['SSR', 'Scan Structure Record', [('V4-2007', False)]]                        },
    (1,94)   : {                                                                                'V4' : ['CDR', 'Chain Description Record', [('V4-2007', False)]]                     },
    (1,95)   : {                                                                                'V4' : ['ASR', 'Algorithm Specification Record', [('Memory:2010.1', False)]]         },
    (1,96)   : {                                                                                'V4' : ['FSR', 'Frame Specification Record', [('Memory:2010.1', False)]]             },
    (1,97)   : {                                                                                'V4' : ['BSR', 'Bit stream Specification Record', [('Memory:2010.1', False)]]        },
    (1,99)   : {                                                                                'V4' : ['MSR', 'Memory Structure Record', [('Memory:2010.1', False)]]                },
    (1,100)  : {                                                                                'V4' : ['MCR', 'Memory Controller Record', [('Memory:2010.1', False)]]               },
    (1,101)  : {                                                                                'V4' : ['IDR', 'Instance Description Record', [('Memory:2010.1', False)]]            },
    (1,102)  : {                                                                                'V4' : ['MMR', 'Memory Model Record', [('Memory:2010.1', False)]]                    },
    # Data collected per wafer
    (2,10)   : {'V3' : ['WIR', 'Wafer Information Record', [('', False)]],                      'V4' : ['WIR', 'Wafer Information Record', [('', False)]]                            },
    (2,20)   : {'V3' : ['WRR', 'Wafer Results Record', [('', False)]],                          'V4' : ['WRR', 'Wafer Results Record', [('', False)]]                                },
    (2,30)   : {'V3' : ['WCR', 'Wafer Configuration Record', [('', False)]],                    'V3' : ['WCR', 'Wafer Configuration Record', [('', False)]]                          },
    # Data collected on a per part basis
    (5,10)   : {'V3' : ['PIR', 'Part Information Record', [('', False)]],                       'V4' : ['PIR', 'Part Information Record', [('', False)]]                             },
    (5,20)   : {'V3' : ['PRR', 'Part Results Record', [('', False)]],                           'V4' : ['PRR', 'Part Results Record', [('', False)]]                                 },
    # Data collected per test in the test program
    (10,10)  : {'V3' : ['PDR', 'Parametric Test Description Record', [('', False)]]                                                                                                  },
    (10,20)  : {'V3' : ['FDR', 'Functional Test Description Record', [('', False)]]                                                                                                  }, 
    (10,30)  : {'V3' : ['TSR', 'Test Synopsis Record', [('', False)]],                          'V4' : ['TSR', 'Test Synopsis Record', [('', False)]]                                },
    # Data collected per test execution
    (15,10)  : {'V3' : ['PTR', 'Parametric Test Record', [('', False)]],                        'V4' : ['PTR', 'Parametric Test Record', [('', False)]]                              },
    (15,15)  : {                                                                                'V4' : ['MPR', 'Multiple-Result Parametric Record', [('', False)]]                   },
    (15,20)  : {'V3' : ['FTR', 'Functional Test Record', [('', False)]],                        'V4' : ['FTR', 'Functional Test Record', [('', False)]]                              },
    (15,30)  : {                                                                                'V4' : ['STR', 'Scan Test Record', [('V4-2007', False)]]                             },
    (15,40)  : {                                                                                'V4' : ['MTR', 'Memory Test Record', [('Memory:2010.1', False)]]                     },
    # Data collected per program segment
    (20,10)  : {'V3' : ['BPS', 'Begin Program Section Record', [('', False)]],                  'V4' : ['BPS', 'Begin Program Section Record', [('', False)]]                        },
    (20,20)  : {'V3' : ['EPS', 'End Program Section Record', [('', False)]],                    'V4' : ['EPS', 'End Program Section Record', [('', False)]]                          },
    # Data collected per test site
    (25,10)  : {'V3' : ['SHB', 'Site specific Hardware Bin record', [('+', False)]]                                                                                                  },
    (25,20)  : {'V3' : ['SSB', 'Site specific Software Bin record', [('+', False)]]                                                                                                  },
    (25,30)  : {'V3' : ['STS', 'Site specific Test Synopsis record', [('+', False)]]                                                                                                 },
    (25,40)  : {'V3' : ['SCR', 'Site specific part Count Record', [('+', False)]]                                                                                                    },
    # Generic Data
    (50,10)  : {'V3' : ['GDR', 'Generic Data Record', [('', False)]],                           'V4' : ['GDR', 'Generic Data Record', [('', False)]]                                 },
    (50,30)  : {'V3' : ['DTR', 'Datalog Text Record', [('', False)]],                           'V4' : ['DTR', 'Datalog Text Record', [('', False)]]                                 },
    # Teradyne extensions
    (180,-1) : {                                                                                'V4' : ['RR1', 'Records Reserved for use by Image software', [('', False)]]          },
    (181,-1) : {                                                                                'V4' : ['RR2', 'Records Reserved for use by IG900 software', [('', False)]]          },
    (220,201): {'V3' : ['BRR', '?!?', [('+', False)]]                                                                                                                                },
    (220,202): {'V3' : ['WTR', '?!?', [('+', False)]]                                                                                                                                },
    (220,203): {'V3' : ['ETSR', 'Extended Test Synopsis Record', [('+', False)]],                                                                                                    },
    (220,204): {'V3' : ['GTR', '?!?', [('+', False)]]                                                                                                                                },
    (220,205): {'V3' : ['ADR', '?!?', [('+', False)]]                                                                                                                                },
    (220,206): {'V3' : ['EPDR', 'Extended Parametric Test Description Record', [('+', False)]]                                                                                       }
}

class STDFError(Exception):
    pass

def ts_to_id(Version=__latest_STDF_version__, Extensions=None):
    '''
    This function returns a dictionary of TS -> ID for the given STDF version and Extension(s)
    If Extensions==None, then all available extensions are used
    '''
    retval = {}
    if Version in supported().versions():
        if Extensions==None:
            Extensions = supported().extensions_for_version(Version) + ['']
        else:
            exts = ['']
            for Extension in Extensions:
                if Extension in supported().extensions(Version):
                    if Extension not in exts:
                        exts.append(Extension)
            Extensions = exts
        for (REC_TYP, REC_SUB) in RecordDefinitions:
            if Version in RecordDefinitions[(REC_TYP, REC_SUB)]:
                for ext, _obligatory_flag in RecordDefinitions[(REC_TYP, REC_SUB)][Version][2]:
                    if ext in Extensions:
                        retval[(REC_TYP, REC_SUB)] = RecordDefinitions[(REC_TYP, REC_SUB)][Version][0]
    return retval

def id_to_ts(Version=__latest_STDF_version__, Extensions=None):
    '''
    This function returns a dictionary ID -> TS for the given STDF version and Extension(s)
    If Extensions==None, then all available extensions are used
    '''
    retval = {}
    temp = ts_to_id(Version, Extensions)
    for item in temp:
        retval[temp[item]]= item
    return retval


class supported(object):
    
    def __init__(self):
        pass
    
    def versions(self):
        '''
        This method will return a list of all versions that are supported.
        '''
        retval = []
        for (REC_TYP, REC_SUB) in RecordDefinitions:
            for Version in RecordDefinitions[(REC_TYP, REC_SUB)]:
                if Version not in retval:
                    retval.append(Version)
        return retval

    def extensions_for_version(self, Version=__latest_STDF_version__):
        '''
        This function will return a list of *ALL* Extensions that are supported for the given STDF Version.
        '''
        retval = []
        if Version in self.versions():
            for (Type, Sub) in RecordDefinitions:
                if Version in RecordDefinitions[(Type, Sub)]:
                    exts = RecordDefinitions[(Type, Sub)][Version][2]
                    for ext in exts:
                        if ext[0]!='' and ext[0] not in retval:
                            retval.append(ext[0])
        return retval
    
    def versions_and_extensions(self):
        '''
        This method returns a dictionary of all versions and the supported extensions for them
        '''
        retval = {}
        for version in self.supported_versions():
            retval[version] = self.extensions_for_version(version) 

class File(object):
    
    def __init__(self, FileName):
        self.__call__(FileName)
        
    def __call__(self, FileName): 
        # name & path
        self.file_name = os.path.abspath(FileName)
        self.path, self.name = os.path.split(self.file_name)
        self.base_name = self.name.split('.')[0]
        # File Exists
        if not os.path.isfile(self.file_name):
            raise IOError("File '%s' Not Found" % self.file_name)
        # compression support
        if re.search(r'stdf?\.gz$', self.name, re.I) and magicnumber.extension_from_magic_number_in_file(self.file_name)==['.gzip']: # gzip 
            self.is_compressed = True
            self.compression = 'gz'
        elif False: # zip
            pass
        elif False: # 7z
            pass
        else:
            self.is_compressed = False
        # Endian & Version
        if self.is_compressed:
            with gzip.open(self.file_name, 'rb') as fd:
                buff = fd.read(6)
            CPU_TYPE, STDF_VER = struct.unpack('BB', buff)
        else:
            CPU_TYPE, STDF_VER = struct.unpack('BB', self._get_bytes_from_file(4, 2))
        self.version = 'V%s' % STDF_VER
        if CPU_TYPE == 1: # sun 1,2,3,4
            self.endian = '>'
        elif CPU_TYPE == 2: # PC
            self.endian = '<'
        else:
            self.endian = '?'
        self.RHF = '%sHBB' % self.endian
        # verify if version supported
        if self.version not in supported().versions():
            name_valid_for_versions=self.is_valid_name_for_versions()
            if len(name_valid_for_versions)==0:
                raise STDFError("'%s' is not an STDF file" % self.file_name)
            else:
                raise STDFError("'%s' pretends to be an STDF file, but it is not" % self.file_name)
        if self.endian =='?':
            raise STDFError("Unsupported endian in '%s'" % self.file_name)
        # Save File Creation
        self.modification_time = os.path.getmtime(self.file_name)
        # record identification
        self.TS2ID = ts_to_id(self.version)
        self.ID2TS = id_to_ts(self.version)
        # file pointer
        if self.is_compressed:
            self.fd = gzip.open(self.file_name, 'rb')
        else:
            self.fd = open(self.file_name, 'rb')
        # indexes
        self.records_are_indexed = False
        self.record_index = {}
        self.tests_are_indexed = False
        self.test_index = {}
        
    def objects_from_indexed_file(self, index, records_of_interest=None):
        '''
         This is a Generator of records (not in order!) 
        '''
        if records_of_interest==None:
            roi = list(self.ID2TS.keys())
        elif isinstance(records_of_interest, list):
            roi = []
            for item in records_of_interest:
                if isinstance(item, str):
                    if (item in list(self.ID2TS.keys())) and (item not in roi):
                        roi.append(item)
        else:
            raise STDFError("STDF.objects_from_indexed_file(index, records_of_interest) : Unsupported records_of_interest" % records_of_interest)
        for REC_ID in roi:
            if REC_ID in index:
                for fp in index[REC_ID]:
                    OBJ = create_record_object(self.version, self.endian, REC_ID, get_record_from_file_at_position(self.fd, fp, self.RHF))
                    yield OBJ
        
        
    def build_record_index(self):
        '''
        This method will build an index of where which record starts in self.file_name
        '''
        def get_record_header(offset):
            fd.seek(offset)
            header = fd.read(4)
            REC_LEN, REC_TYP, REC_SUB = struct.unpack(FMT, header)
            return REC_LEN, REC_TYP, REC_SUB
        
        if not self.records_are_indexed:
            TS2ID = ts_to_id(self.version) 
            FMT = "%sHBB" % self.endian
            fp = 0 
            size = os.stat(self.file_name).st_size
            fd = open(self.file_name, 'rb')
            while True:
                REC_LEN, REC_TYP, REC_SUB = get_record_header(fp)
                ID = TS2ID[REC_TYP, REC_SUB]
                if ID in self.record_index:
                    self.record_index[ID].append(fp)
                else:
                    self.record_index[ID] = [fp]
                fp += (REC_LEN+4)
                if fp == size: break
            self.records_are_indexed = True
            
    def build_test_index(self):
        '''
        This method will build an index for each test
        '''
        # make sure the records are indexed
        if not self.records_are_indexed:
            self.build_record_index()
        # build the test index    
        if not self.tests_are_indexed:
            for OBJ in objects_from_indexed_file(self.fd, self.record_index, ['TSR']):
                print(OBJ)
#                 HEAD_NUM = OBJ.get_value('HEAD_NUM') 
#                 SITE_NUM = OBJ.get_value('SITE_NUM')
#                 TEST_TYP = OBJ.get_value('TEST_TYP')
#                 TEST_NUM = OBJ.get_value('TEST_NUM')
#                 EXEC_CNT = OBJ.get_value('EXEC_CNT')
#                 FAIL_CNT = OBJ.get_value('FAIL_CNT')
#                 TEST_NAM = OBJ.get_value('TEST_NAM')
#                 
#                 if TEST_NUM not in self.test_index:
#                     self.test_index[TEST_NUM] = {}
#                 if HEAD_NUM not in self.test_index[(TEST_NAM, TEST_NUM, TEST_TYP)]:
#                     self.test_index[(TEST_NAM, TEST_NUM, TEST_TYP)][HEAD_NUM] = {}
#                 if SITE_NUM not in self.test_index[(TEST_NAM, TEST_NUM, TEST_TYP)][HEAD_NUM]:
#                     self.test_index[(TEST_NAM, TEST_NUM, TEST_TYP)][HEAD_NUM][SITE_NUM] = {'CNT' : (EXEC_CNT, FAIL_CNT), 'REF' : []}
#                 
#                                                  
#             
#             
#         self.tests_are_indexed = True
                    
    def check_obligatory_records(self, rebuild_index=False):
        '''
        This method will check if the obligatory records are present in self.file_name
        '''
        # make sure the file is indexed
        if not self.is_indexed:
            self.build_index(rebuild_index)
        # compile a list of all possible records for self.version
        
        
        
        # Check if the obligatory records are found, 
        if 'PCR' not in self.index: print("WARNING : No PCR records found")
        #TODO: add other obligatory records here (make it dynamic from 'RecordDefinitions' 
        
    def _print_record_index(self, rebuild=False):
        if rebuild or not self.records_are_indexed:
            self.build_record_index(rebuild)
        for REC_ID in self.record_index:
            print("%s : %s" % (REC_ID, len(self.record_index[REC_ID])))    
        
    def _get_bytes_from_file(self, offset, number):
        '''
        This method will read 'number' bytes from file starting from 'offset' and return the buffer.
        '''
        fd = self.open()
        fd.seek(offset)
        buff = fd.read(number)
        fd.close()
        return buff
        
    def size(self):
        '''
        This method will return a tupple that denotes the size in bytes of self.file_name.
        (decompessed_size, compressed_size)
        If a file is not compressed, the 2 values in the tuple will be equal.
        '''
        decompressed_size = 0
        compressed_size = 0
        if self.is_compressed:
            compressed_size = os.stat(self.file_name).st_size
            with open(self.file_name, 'rb') as fd:
                fd.seek(-4, 2) # last 4 bytes give the unpacked size of the file
                decompressed_size = struct.unpack('<I', fd.read(4))[0]
        else:
            decompressed_size = os.stat(self.file_name).st_size
            compressed_size = decompressed_size
        return (decompressed_size, compressed_size)

    def open(self, mode='rb'):
        '''
        This method will return a transparent file handle to self.file_name
        '''
        if self.is_compressed:
            return gzip.open(self.file_name, mode)
        else:
            return open(self.file_name, mode)

    def md5(self):
        '''
        This method will calculate the md5 digest of self.file_name
        If self.file_name is compressed, it will calculate the md5 of the *UNCOMPRESSED* version.
        '''
        if self.is_compressed:
            return hashlib.md5(gzip.open(self.file_name, 'rb').read()).hexdigest().upper()
        else:
            return hashlib.md5(open(self.file_name, 'rb').read()).hexdigest().upper()

    def is_md5_file_name(self):
        '''
        This method will return True if the self.name is an MD5 file name.
        '''
        base_name = self.name.split('.')[0]
        if len(base_name)==36 and base_name.startswith('MD5_'):
            return True
        return False
    
    def check_md5(self):
        '''
        This method will return True if the file-name's md5 equals the actual digest of the (uncompressed) self.file_name.
        If self.file_name is not an md5 file name, the result is also False.
        '''
        if self.is_md5_file_name():
            if self.name.split('.')[0].replace('MD5_', '') == self.md5():
                return True
        return False
    
    def get_part_data(self, PIR_pointer):
        '''
        This method will seek self.fd to fp, and expect a PIR record (if not nothing will be returned)
        From the PIR it determines HEAD_NUM and SITE_NUM.
        The it continues to read records until it encounters either a PIR for the same HEAD_NUM/SITE_NUM or 
        a PRR With the same HEAD_NUM/SITE_NUM (in which case it also has a SOFT/HARD bin data for the part.
        The whole data-structure for the part is returned.
        '''
        def records_from_part(HEAD_NUM, SITE_NUM):
            while True:
                header = self.fd.read(4)
                REC_LEN, REC_TYP, REC_SUB = struct.unpack(self.RHF, header)
                footer = self.fd.read(REC_LEN)
                OBJ = create_record_object(self.version, self.endian, self.TS2ID[REC_TYP, REC_SUB], header+footer)
                REC_ID = self.TS2ID[REC_TYP, REC_SUB]
                if REC_ID in ['PRR', 'PTR', 'MPR', 'FTR']:
                    if OBJ.get_value('HEAD_NUM')==HEAD_NUM and OBJ.get_value('SITE_NUM'):
                        yield OBJ
                elif REC_ID == 'PIR':
                    if OBJ.get_value('HEAD_NUM')==HEAD_NUM and OBJ.get_value('SITE_NUM'):
                        break                
        
        retval = {'INF' : {'HEAD_NUM' : -1, 
                           'SITE_NUM' : -1, 
                           'PF' : '', 
                           'NUM_TEST' : 0,
                           'HARD_BIN' : -1,
                           'SOFT_BIN' : -1,
                           'X_COORD' : -32768,
                           'Y_COORD' : -32768,
                           'TEST_T' : 0,
                           'PART_ID' : '',
                           'PART_TXT' : '',
                           'PART_FIX' : ''},
                  'PTR' : {},
                  'MPR' : {},
                  'FTR' : {}}

        self.fd.seek(PIR_pointer)
        _, REC_TYP, REC_SUB, REC = read_record(self.fd, self.RHF)
        if self.TS2ID[(REC_TYP, REC_SUB)] != 'PIR': raise STDFError("Didn't get a file pointer set to a PIR")
        PIR = create_record_object(self.version, self.endian, 'PIR', REC)
        HEAD_NUM = PIR.get_value('HEAD_NUM')
        SITE_NUM = PIR.get_value('SITE_NUM')
        retval['INF']['HEAD_NUM'] = PIR.get_value('HEAD_NUM')
        retval['INF']['SITE_NUM'] = PIR.get_value('SITE_NUM')
        
        for OBJ in records_from_part(HEAD_NUM, SITE_NUM):
            if OBJ.id == 'PTR':
                HiSpecLim = OBJ.get_value('HI_SPEC')*pow(10, OBJ.get_value('HLM_SCAL'))
                LoSpecLim = OBJ.get_value('LO_SPEC')*pow(10, OBJ.get_value('LLM_SCAL'))
                HiTestLim = OBJ.get_value('HI_LIMIT')*pow(10, OBJ.get_value('HLM_SCAL'))
                LoTestLim = OBJ.get_value('LO_LIMIT')*pow(10, OBJ.get_value('LLM_SCAL'))
                Result = OBJ.get_value('RESULT')*pow(10, OBJ.get_value('RES_SCAL'))
                Unit = OBJ.get_value('UNITS')
                TEST_NUM = OBJ.get_value('TEST_NUM')
                TEST_FLG = OBJ.get_value('TEST_FLG')
                #PARM_FLG = OBJ.get_value('PARM_FLG')
                if TEST_FLG[6:] == ['0', '0']:
                    PF = 'P'
                elif TEST_FLG[6:] == ['0', '1']:
                    PF = 'F'
                else:
                    PF = '?'
                retval['PTR'][TEST_NUM] = (HiSpecLim, HiTestLim, Result, LoTestLim, LoSpecLim, Unit, PF)
            elif OBJ.id == 'MPR':
                pass
            elif OBJ.id == 'FTR':
                pass
            elif OBJ.id == 'PRR':
                retval['INF']['NUM_TEST'] = OBJ.get_value('NUM_TEST')
                retval['INF']['HARD_BIN'] = OBJ.get_value('HARD_BIN')
                retval['INF']['SOFT_BIN'] = OBJ.get_value('SOFT_BIN')
                retval['INF']['X_COORD'] = OBJ.get_value('X_COORD')
                retval['INF']['Y_COORD'] = OBJ.get_value('Y_COORD')
                retval['INF']['TEST_T'] = OBJ.get_value('TEST_T')
                retval['INF']['PART_ID'] = OBJ.get_value('PART_ID')
                retval['INF']['PART_TXT'] = OBJ.get_value('PART_TXT')
                retval['INF']['PART_FIX'] = OBJ.get_value('PART_FIX')
                if OBJ.get_value('PART_FLG')[3:5] == ['0', '0']:
                    retval['INF']['PF'] = 'P'
                elif OBJ.get_value('PART_FLG')[3:5] == ['1', '0']:
                    retval['INF']['PF'] = 'F'
                else:
                    retval['INF']['PF'] = '?'
                break
            else:
                raise "records from part should only return PTR/FTR/MPTR or PRR records"
        return retval
    
    def to_df(self, test_of_interest, with_progress=False):
        '''
        This method will create and return a pandas dataframe for test_of_interest
        '''
        pass

    def to_xlsx(self, tests_of_interest=None, also_clean_tests=True, with_progress=False):
        '''
        This method will save the data from the STDF file self.file_name to an .xslx file in the same
        directory as self.file_name. If the target file already exists, it will be overwritten. 
        '''
        if not self.is_snarfed:
            if with_progress:
                print("Collecting data ...")
            self.snarf(with_progress=with_progress)
            
#         if with_progress:
#            print "Writing data ..."
#             pbar = pb.ProgressBar(maxval=8, widgets=[pb.SimpleProgress() , ' =', pb.Percentage(), ' ', pb.Bar(), ' ', pb.Timer(), ' ',pb.ETA()]).start()

        
    # Create workbook
        xlsx_file_name = os.path.join(self.path, '%s.xlsx' % self.base_name )
        if os.path.exists(xlsx_file_name):
            os.unlink(xlsx_file_name)
        workbook = xlsxwriter.Workbook(xlsx_file_name)

        bold_right = workbook.add_format({'bold': True, 'align' : 'right'})

        bold = workbook.add_format({'bold': True})
        left = workbook.add_format({'align' : 'left'})
        right = workbook.add_format({'align' : 'right'})
        left_percent = workbook.add_format({'align' : 'left', 'num_format' : '0.00%'})

        failed = workbook.add_format({'pattern' : 1, 'bg_color' : 'red', 'bold' : True})
        
        
        
    # Information Sheet
        info_sheet = workbook.add_worksheet('Info')
        info_sheet.write( 0, 0, 'Date and time of job setup :');             info_sheet.write( 0, 1, self.data['INFO']['SETUP_T']);  info_sheet.write( 0, 2, str(DT(self.data['INFO']['SETUP_T'])))  
        info_sheet.write( 1, 0, 'Date and time first part tested :');        info_sheet.write( 1, 1, self.data['INFO']['START_T']);  info_sheet.write( 1, 2, str(DT(self.data['INFO']['START_T'])))
        info_sheet.write( 2, 0, 'Date and time last part tested :');         info_sheet.write( 2, 1, self.data['INFO']['FINISH_T']); info_sheet.write( 2, 2, str(DT(self.data['INFO']['FINISH_T']))) 
        info_sheet.write( 3, 0, 'Tester station number :');                  info_sheet.write( 3, 1, self.data['INFO']['STAT_NUM'])
        info_sheet.write( 4, 0, 'Test mode code [A/M/P/E/M/P/Q/space] :');   info_sheet.write( 4, 1, self.data['INFO']['MODE_COD'])
        info_sheet.write( 5, 0, 'Lot retest code [Y/N/0..9/space] :');       info_sheet.write( 5, 1, self.data['INFO']['RTST_COD'])
        info_sheet.write( 6, 0, 'Lot disposition code :');                   info_sheet.write( 6, 1, self.data['INFO']['DISP_COD'])
        info_sheet.write( 7, 0, 'Data protection code [0..9/A..Z/space] :'); info_sheet.write( 7, 1, self.data['INFO']['PROT_COD'])
        info_sheet.write( 8, 0, 'Burn-in time (in minutes) :');              info_sheet.write( 8, 1, self.data['INFO']['BURN_TIM'])
        info_sheet.write( 9, 0, 'Command mode code :');                      info_sheet.write( 9, 1, self.data['INFO']['CMOD_COD'])
        info_sheet.write(10, 0, 'Lot ID (customer specified) :');            info_sheet.write(10, 1, self.data['INFO']['LOT_ID'])
        info_sheet.write(11, 0, 'Part Type (or product ID) :');              info_sheet.write(11, 1, self.data['INFO']['PART_TYP'])
        info_sheet.write(12, 0, 'Name of node that generated data :');       info_sheet.write(12, 1, self.data['INFO']['NODE_NAM'])
        info_sheet.write(13, 0, 'Tester type :');                            info_sheet.write(13, 1, self.data['INFO']['TSTR_TYP'])
        info_sheet.write(14, 0, 'Job name (test program name) :');           info_sheet.write(14, 1, self.data['INFO']['JOB_NAM'])
        info_sheet.write(15, 0, 'Job (test program) revision number :');     info_sheet.write(15, 1, self.data['INFO']['JOB_REV'])
        info_sheet.write(16, 0, 'Sublot ID :');                              info_sheet.write(16, 1, self.data['INFO']['SBLOT_ID'])
        info_sheet.write(17, 0, 'Operator name or ID (at setup time) :');    info_sheet.write(17, 1, self.data['INFO']['OPER_NAM'])
        info_sheet.write(18, 0, 'Tester executive software type :');         info_sheet.write(18, 1, self.data['INFO']['EXEC_TYP'])
        info_sheet.write(19, 0, 'Tester exec software version number :');    info_sheet.write(19, 1, self.data['INFO']['EXEC_VER'])
        info_sheet.write(20, 0, 'Test phase or step code :');                info_sheet.write(20, 1, self.data['INFO']['TEST_COD'])
        info_sheet.write(21, 0, 'Test temperature :');                       info_sheet.write(21, 1, self.data['INFO']['TST_TEMP'])
        info_sheet.write(22, 0, 'Generic user text :');                      info_sheet.write(22, 1, self.data['INFO']['USER_TXT'])
        info_sheet.write(23, 0, 'Name of auxiliary data file :');            info_sheet.write(23, 1, self.data['INFO']['AUX_FILE'])
        info_sheet.write(24, 0, 'Package type :');                           info_sheet.write(24, 1, self.data['INFO']['PKG_TYP'])
        info_sheet.write(25, 0, 'Product family ID :');                      info_sheet.write(25, 1, self.data['INFO']['FAMLY_ID'])
        info_sheet.write(26, 0, 'Date code :');                              info_sheet.write(26, 1, self.data['INFO']['DATE_COD'])
        info_sheet.write(27, 0, 'Test facility ID :');                       info_sheet.write(27, 1, self.data['INFO']['FACIL_ID'])
        info_sheet.write(28, 0, 'Test floor ID :');                          info_sheet.write(28, 1, self.data['INFO']['FLOOR_ID'])
        info_sheet.write(29, 0, 'Fabrication process ID :');                 info_sheet.write(29, 1, self.data['INFO']['PROC_ID'])
        info_sheet.write(30, 0, 'Operation frequency or step :');            info_sheet.write(30, 1, self.data['INFO']['OPER_FRQ'])
        info_sheet.write(31, 0, 'Test specification name :');                info_sheet.write(31, 1, self.data['INFO']['SPEC_NAM'])
        info_sheet.write(32, 0, 'Test specification version number :');      info_sheet.write(32, 1, self.data['INFO']['SPEC_VER'])
        info_sheet.write(33, 0, 'Test flow ID :');                           info_sheet.write(33, 1, self.data['INFO']['FLOW_ID'])
        info_sheet.write(34, 0, 'Test setup ID :');                          info_sheet.write(34, 1, self.data['INFO']['SETUP_ID'])
        info_sheet.write(35, 0, 'Device design revision :');                 info_sheet.write(35, 1, self.data['INFO']['DSGN_REV'])
        info_sheet.write(36, 0, 'Engineering lot ID :');                     info_sheet.write(36, 1, self.data['INFO']['ENG_ID'])
        info_sheet.write(37, 0, 'ROM code ID :');                            info_sheet.write(37, 1, self.data['INFO']['ROM_COD'])
        info_sheet.write(38, 0, 'Tester serial number :');                   info_sheet.write(38, 1, self.data['INFO']['SERL_NUM'])
        info_sheet.write(39, 0, 'Supervisor name or ID :');                  info_sheet.write(39, 1, self.data['INFO']['SUPR_NAM'])
        info_sheet.write(40, 0, 'Handler ID :');                             info_sheet.write(40, 1, self.data['INFO']['HAND_ID'])
        info_sheet.write(41, 0, 'Probe Card / DIB ID :');                    info_sheet.write(41, 1, self.data['INFO']['PRB_CARD'])
        info_sheet.write(42, 0, 'Description from Tester exec :');           info_sheet.write(42, 1, self.data['INFO']['EXC_DESC'])
        info_sheet.write(43, 0, 'Description from user :');                  info_sheet.write(43, 1, self.data['INFO']['USR_DESC'])
        info_sheet.write(44, 0, 'Number of Test Heads :');                   info_sheet.write(44, 1, len(self.data['HEADS']));         info_sheet.write(44, 2, str(self.data['HEADS']))
        info_sheet.write(45, 0, 'Number of Test Sites :');                   info_sheet.write(45, 1, len(self.data['SITES']));         info_sheet.write(45, 2, str(self.data['SITES']))
        info_sheet.write(46, 0, 'Number of parts :');                        info_sheet.write(46, 1, self.data['INFO']['PART_CNT']);   info_sheet.write(46, 2, self.data['PARTS']);     info_sheet.write(46, 3, self.data['PASSES']+self.data['FAILS'])
        info_sheet.write(47, 0, 'Number of good parts :');                   info_sheet.write(47, 1, self.data['INFO']['GOOD_CNT']);                                                    info_sheet.write(47, 3, self.data['PASSES'])
        info_sheet.write(48, 0, 'Number of failed parts');                                                                                                                              info_sheet.write(48, 3, self.data['FAILS'])
        info_sheet.write(49, 0, 'Yield :')
        if self.data['PASSES']+self.data['FAILS']==0:
            info_sheet.write(49, 1, 0.0, left_percent)
        else:
            info_sheet.write(49, 1, float(self.data['PASSES'])/(self.data['PASSES']+self.data['FAILS']), left_percent)
        info_sheet.write(50, 0, 'Number of functional parts :');             info_sheet.write(50, 1, self.data['INFO']['FUNC_CNT'])
        info_sheet.write(51, 0, 'Number of re-tested parts :');              info_sheet.write(51, 1, self.data['INFO']['RTST_CNT'])
        info_sheet.write(52, 0, 'Number of aborted parts :');                info_sheet.write(52, 1, self.data['INFO']['ABRT_CNT'])
        if self.is_from_probing():
            info_sheet.write(53, 0, 'Probing :')
            info_sheet.write(53, 1, self.count_wafers())
            info_sheet.write(53, 2, str(self.enumerate_wafers()))
        else:
            info_sheet.write(53, 0, 'Final Test :')
            info_sheet.write(53, 1, 'yes')
        info_sheet.write(54, 0, 'Average cycle time :')
        info_sheet.write_formula('B55', '{=(B3-B2)/(D47)}')
        info_sheet.write(54, 2, 's/part')
        info_sheet.write(55, 0, 'Average indexing time :')
        info_sheet.write_formula('B56', '{=(B3-B2)/(D47/(B45*B46))}')
        info_sheet.write(55, 2, 's/group')

        info_sheet.set_column(0, 0, 34, bold_right) # Column A:A bold and aligned to the right
        info_sheet.set_column(1, 1, 20, left) # Column B:B normal and aligned tot he left
        info_sheet.set_column(2, 2, 50, left) # Column C:C normal and aligned to the left 
        info_sheet.set_column(3, 3, 50, left) # Column C:C normal and aligned to the left 
        
    # TEST descriptions
        test_sheet = workbook.add_worksheet('TESTS')
        test_sheet.write( 0,  0, 'TEST_NUM', bold)
        test_sheet.write( 0,  1, 'TEST_NAM', bold)
        test_sheet.write( 0,  2, 'TEST_TYP', bold)
        test_sheet.write( 0,  3, 'SEQ_NAM', bold)
        test_sheet.write( 0,  4, 'LTL', bold)
        test_sheet.write( 0,  5, 'UTL', bold)
        test_sheet.write( 0,  6, 'LSL', bold)
        test_sheet.write( 0,  7, 'USL', bold)
        test_sheet.write( 0,  8, 'UNITS', bold) 
        test_sheet.write( 0,  9, 'C_HLMFMT', bold) 
        test_sheet.write( 0, 10, 'C_LLMFMT', bold) 
        test_sheet.write( 0, 11, 'C_RESFMT', bold) 
        test_sheet.write( 0, 12, 'LLM_SCAL', bold)
        test_sheet.write( 0, 13, 'RES_SCAL', bold)
        test_sheet.write( 0, 14, 'HLM_SCAL', bold)
        row = 1
        for TEST_NUM in self.data['TEST']:
            test_sheet.write(row,  0, TEST_NUM)
            test_sheet.write(row,  1, self.data['TEST'][TEST_NUM]['TEST_NAM'])
            test_sheet.write(row,  2, self.data['TEST'][TEST_NUM]['TEST_TYP'])
            test_sheet.write(row,  3, self.data['TEST'][TEST_NUM]['SEQ_NAM'])
            test_sheet.write(row,  4, self.data['TEST'][TEST_NUM]['LTL'])
            test_sheet.write(row,  5, self.data['TEST'][TEST_NUM]['UTL'])
            test_sheet.write(row,  6, self.data['TEST'][TEST_NUM]['LSL'])
            test_sheet.write(row,  7, self.data['TEST'][TEST_NUM]['USL'])
            test_sheet.write(row,  8, self.data['TEST'][TEST_NUM]['UNITS']) 
            test_sheet.write(row,  9, self.data['TEST'][TEST_NUM]['C_HLMFMT']) 
            test_sheet.write(row, 10, self.data['TEST'][TEST_NUM]['C_LLMFMT']) 
            test_sheet.write(row, 11, self.data['TEST'][TEST_NUM]['C_RESFMT']) 
            test_sheet.write(row, 12, self.data['TEST'][TEST_NUM]['LLM_SCAL'])
            test_sheet.write(row, 13, self.data['TEST'][TEST_NUM]['RES_SCAL'])
            test_sheet.write(row, 14, self.data['TEST'][TEST_NUM]['HLM_SCAL'])
            row+=1
            
    # SBIN sheet
        sbin_sheet = workbook.add_worksheet('SOFT Bin')
        sbin_sheet.write(0, 0, 'SBIN_NUM', bold)
        sbin_sheet.write(0, 1, 'SBIN_NAM', bold)
        sbin_sheet.write(0, 2, 'P/F', bold)
        row = 1
        for SBIN_NUM in self.data['BIN']['SOFT']:
            sbin_sheet.write(row, 0, SBIN_NUM)
            sbin_sheet.write(row, 1, self.data['BIN']['SOFT'][SBIN_NUM][0])
            sbin_sheet.write(row, 2, self.data['BIN']['SOFT'][SBIN_NUM][1])
            row+=1
    
    # HBIN sheet
        hbin_sheet = workbook.add_worksheet('HARD Bin')
        hbin_sheet.write(0, 0, 'HBIN_NUM', bold)
        hbin_sheet.write(0, 1, 'HBIN_NAM', bold)
        hbin_sheet.write(0, 2, 'P/F', bold)
        row = 1
        for HBIN_NUM in self.data['BIN']['HARD']:
            hbin_sheet.write(row, 0, HBIN_NUM)
            hbin_sheet.write(row, 1, self.data['BIN']['HARD'][HBIN_NUM][0])
            hbin_sheet.write(row, 2, self.data['BIN']['HARD'][HBIN_NUM][1])
            row+=1
        
    # RESULT sheet
        result_sheet = workbook.add_worksheet('RESULT')
        result_sheet.write(0, 0, 'LOT', bold)
        result_sheet.write(0, 1, 'WAF', bold)
        result_sheet.write(0, 2, 'X', bold)
        result_sheet.write(0, 3, 'Y', bold)
        result_sheet.write(0, 4, 'HEAD', bold)
        result_sheet.write(0, 5, 'SITE', bold)
        result_sheet.write(0, 6, 'HBIN', bold)
        result_sheet.write(0, 7, 'SBIN', bold)
        result_sheet.write(0, 8, 'PART', bold)
        result_sheet.write(0, 9, 'PF', bold)
        for entry in self.data['META']:
            (LOT, WAFER, X_COORD, Y_COORD, HEAD, SITE, HBIN, SBIN, PART, PF) = self.data['META'][entry]
            result_sheet.write(entry+1, 0, LOT)
            result_sheet.write(entry+1, 1, WAFER)
            result_sheet.write(entry+1, 2, X_COORD)
            result_sheet.write(entry+1, 3, Y_COORD)
            result_sheet.write(entry+1, 4, HEAD)
            result_sheet.write(entry+1, 5, SITE)
            result_sheet.write(entry+1, 6, HBIN)
            result_sheet.write(entry+1, 7, SBIN)
            result_sheet.write(entry+1, 8, PART)
            if PF == 'P':
                result_sheet.write(entry+1, 9, 'P')
            else:
                result_sheet.write(entry+1, 9, 'F', failed)
        column = 10
        for TEST_NUM in list(self.data['PF'].keys()):
            if TEST_NUM in self.data['RESULT']: # Parametric test result
                crange = '%s1:%s1'%(xlsxwriter.utility.xl_col_to_name(column), xlsxwriter.utility.xl_col_to_name(column+1))
                result_sheet.set_column(column, column, 8, right)
                result_sheet.set_column(column+1, column+1, 2, left)
                result_sheet.merge_range(crange, self.data['TEST'][TEST_NUM]['TEST_NAM'], bold)
                for entry in range(len(self.data['PF'][TEST_NUM])):
                    if entry in self.data['RESULT'][TEST_NUM]:
                        if np.isfinite(self.data['RESULT'][TEST_NUM][entry]):
                            result_sheet.write(entry+1, column, self.data['RESULT'][TEST_NUM][entry])
                    if self.data['PF'][TEST_NUM][entry]:
                        result_sheet.write(entry+1, column+1, 'P')
                    else:
                        result_sheet.write(entry+1, column+1, 'F')
                column+=2 
            else: # functional test result
                result_sheet.write(0, column, self.data['TEST'][TEST_NUM]['TEST_NAM'], bold)
                for entry in range(len(self.data['PF'][TEST_NUM])):
                    if self.data['PF'][TEST_NUM][entry]:
                        result_sheet.write(entry+1, column, 'P')
                    else:
                        result_sheet.write(entry+1, column, 'F')
                column+=1

        result_sheet.freeze_panes(1, 10)
        
        
    # Test-Fail-Pareto sheet
        pareto_sheet = workbook.add_worksheet('Test Pareto')
        
    # Data sheet
    
    # PF sheet
    
    # Min sheet
    
    # Max sheet
    
    
    # ATR's
        ATR_sheet = workbook.add_worksheet("ATR's")
        ATR_sheet.write(0, 0, 'MOD_TIM', bold)
        ATR_sheet.write(0, 1, 'CMD_LINE', bold)
        row = 1
        for MOD_TIM in self.data['ATRs']:
            ATR_sheet.write(row, 0, MOD_TIM)
            ATR_sheet.write(row, 1, self.data['ATRs'][MOD_TIM])
            row+=1 
    
    # DTR's
        DTR_sheet = workbook.add_worksheet("DTR's")
        DTR_sheet.write(0, 0, 'PART', bold)
        DTR_sheet.write(0, 1, 'RECORD', bold)
        DTR_sheet.write(0, 2, 'TEXT_DAT', bold)
        row = 1
        for PART, RECORD in self.data['DTRs']:
            DTR_sheet.write(row, 0, PART)
            DTR_sheet.write(row, 1, RECORD)
            DTR_sheet.write(row, 3, self.data['DTRs'][(PART, RECORD)])
            row+=1
        
        workbook.close()

        #pbar.finish()

    def to_pdf(self):
        pass
        
    def to_pptx(self):
        pass
    
    def to_deav(self, DEAV_repository):
        pass

    def rename(self, NewFileName=None, preserve=False, overwrite='auto'):
        '''
        This method will rename self.file_name to NewName.
        If NewName is None, the name will be that of the MD5 hash of the file propper (it needs to fit in 39 characters!!!)
        If NewName contains a path, that will be used (=move & rename) and the object will be re-initialized, 
        if not, self.path will be pre-pended (=rename) and the re-initialization of the object will depend on 'preserve'
        If the extension(s) of NewFileName are not the same as self.file_name, nothing will be done (return value is False)
        If preserve is False a rename will be performed and the object will be re-initialized
        If preserve is True, the original file will be preserved (= copy action) and the object will *NOT* be re-initialized
        If overwrite is True, a pre-existing NewFileName will be overwritten.
        If overwrite is True, and a pre-existing NewFileName will not be overwritten(return value is False)
        If overwrite is 'auto', over writing will be done only if a pre-existing NewFileName is OLDER than self.file_name.
        The original modification time will always be preserved!
        On success, True will be returned, False otherwhise
        '''
        if NewFileName==None:
            NewFileName = os.path.join(self.path, "MD5_%s.%s" % (self.md5(), '.'.join(self.name.split('.')[1:])))
        NewFileName = os.path.abspath(NewFileName)
        if NewFileName == self.file_name:
            return False
        if os.path.exists(NewFileName):
            if not isinstance(overwrite, bool):
                if os.path.getmtime(NewFileName) >= self.modification_time:
                    overwrite = False
                else:
                    overwrite = True
            if overwrite == True:
                os.unlink(NewFileName)
        _, NewName = os.path.split(NewFileName)
        NewExts = '.%s' % '.'.join(NewName.split('.')[1:])
        OriginalExts = '.%s' % '.'.join(self.name.split('.')[1:])
        if NewExts == OriginalExts:
            shutil.copy2(self.file_name, NewFileName)
            os.utime(NewFileName, (time.time(), self.modification_time)) # just to be sure 
            if not preserve:
                os.unlink(self.file_name)
                self.__call__(NewFileName)
            retval = True
        else:
            retval = False
            #TODO: Implement implicit compression/decompression    
        return retval

    def compress(self, preserve=False, overwrite='auto'):
        '''
        This method will compress self.file_name if it is not already compressed, in which case nothing is done.
        If preserve is False (default), the original file will be removed and the object will be re-initialized with the compressed file.
        If preserve is True, the original file *NOT* be removed and the object will *NOT* be re-initialized.
        If overwrite is True (default) if the target file already exists, it is overwritten.
        If overwrite is False, nothing will be done if the target file already exists.
        If overwrite is 'auto', over writing will be done only if a pre-existing NewFileName is OLDER than self.file_name.
        The original modification time will always be preserved!
        On success, True will be returned, False otherwhise
        '''
        if not self.is_compressed:
            NewName = self.name+'.gz'
            NewFileName = os.path.join(self.path, NewName)
            if os.path.exists(NewFileName):
                if not isinstance(overwrite, bool):
                    if os.path.getmtime(NewFileName) >= self.modification_time:
                        overwrite = False
                    else:
                        overwrite = True
                if overwrite == True:
                    os.unlink(NewFileName)
            with open(self.file_name, 'rb') as f_in, gzip.open(NewFileName, 'wb') as f_out:
                copyfileobj(f_in, f_out)
            os.utime(NewFileName, (time.time(), self.modification_time)) # preserver original modification time!
            if not preserve:
                os.unlink(os.path.join(self.path, self.name))
                self.__call__(os.path.join(self.path, NewName))
            return True
        return False
        
    def decompress(self, preserve=False, overwrite='auto'):
        '''
        This method will de-compress self.file_name if it is compressed. If self.file_name is not compressed, nothing is done.
        If preserve is False, the original file will be removed and the object will be re-initialized with the de-compressed file.
        If preserve is True, the original file will *NOT* be removed and the object will *NOT* be re-initialized.
        If overwrite is True (default) if the target file already exists, it is overwritten.
        If overwrite is False, nothing will be done if the target file already exists.
        If overwrite is 'auto', over writing will be done only if a pre-existing NewFileName is OLDER than self.file_name.
        The original modification time will always be preserved!
        On success, True will be returned, False otherwhise
        '''
        if self.is_compressed:
            NewName = self.name[:-3]
            NewFileName = os.path.join(self.path, NewName)
            if os.path.exists(NewFileName):
                if not isinstance(overwrite, bool):
                    if os.path.getmtime(NewFileName) >= self.modification_time:
                        overwrite = False
                    else:
                        overwrite = True
                if overwrite == True:
                    os.unlink(NewFileName)
            with open(NewFileName, 'wb') as f_out, gzip.open(self.file_name, 'rb') as f_in:
                copyfileobj(f_in, f_out)
            os.utime(NewFileName, (time.time(), self.modification_time)) # preserve original modification time!
            if not preserve:
                os.unlink(os.path.join(self.path, self.name))
                self.__call__(os.path.join(self.path, NewName))
            return True
        return False

#    def _version_and_endian(self):
#        return _ver, _end
        
    def ends_on_record_boundary(self):
        '''
        This function will return True if FileName ends on a record boundary, False if it doesn't.
        
        This function will not use the 'records_from_file' iterator as that one just ignores the last 
        record if it is a corrupt one!
        
        It presumes that FileName exists, because if it doesn't exist the return value is also False!
        '''
        if guess_type(self.file_name)[1]=='gzip':
            with open(self.file_name, 'rb') as fd:
                fd.seek(-4, 2) # last 4 bytes give the unpacked size of the file
                fe = struct.unpack('I', fd.read(4))[0]
            with gzip.open(self.file_name, 'rb') as fd:
                while fd.tell() != fe:
                    header = fd.read(4)
                    if len(header)!=4:
                        return False # Header too short
                    else:
                        REC_LEN, _REC_TYP, _REC_SUB = struct.unpack('HBB', header)
                        _footer = fd.read(REC_LEN)
                        if len(_footer)!=REC_LEN:
                            return False # Footer too short
        else:
            with open(self.file_name, 'rb') as fd:
                fe = os.fstat(fd.fileno()).st_size 
                while fd.tell() != fe:
                    header = fd.read(4)
                    if len(header)!=4:
                        return False # Header too short
                    else:
                        REC_LEN, _REC_TYP, _REC_SUB = struct.unpack('HBB', header)
                        _footer = fd.read(REC_LEN)
                        if len(_footer)!=REC_LEN:
                            return False # Footer too short
        return True # End on record boundary

    def extensions(self):
        '''
        This method returns a list of the used extensions to the STDF version
        '''
        #TODO: Implement
        pass
    
    def count_records(self, records_of_interest=None):
        '''
        This method will return the number of records found in the STDF file.
        If of_interest==None, all records are considered, if not, only the 
        records in of_interest are considered.
        '''
        # set the records_of_interest right
        all_records = list(id_to_ts(self.version).keys())
        if records_of_interest==None:
            roi = all_records
        elif isinstance(records_of_interest, list):
            roi = []
            for item in records_of_interest:
                if item in all_records:
                    roi.append(item)
        else:
            raise STDFError("count_records(records_of_interest=%s) : Unsupported 'records_of_interest' type" % records_of_interest)
        # make sure the records in the file are indexed
        if not self.records_are_indexed:
            self.build_record_index()
        # count the records of interest
        retval = 0
        for REC_ID in self.record_index:
            if REC_ID in roi:
                retval+=len(self.record_index[REC_ID])
        return retval

    def count_tests(self):
        '''
        This method will find the number of unique tests in self.file_name
        '''
        TestCount = 0
        MaxTestCount = 0
        for _REC_LEN, REC_TYP, REC_SUB, _REC in records_from_file(self.file_name):
            if REC_TYP==5:
                if REC_SUB==10: # PIR = start
                    TestCount = 0    
                elif REC_SUB==20: # PRR = stop
                    if TestCount > MaxTestCount:
                        MaxTestCount = TestCount
            if REC_TYP==15: # PTR, FTR, MPR, STR or MTR
                TestCount+=1
        return MaxTestCount        

    def count_parts(self):
        '''
        This method will return the number of parts in self.file_name
        '''
        if self.data['PARTS']==None:
            self.data['PARTS'] = self.count_records(['PRR']) # PRR marks a tested part
        return self.data['PARTS']
    
    def count_wafers(self, recount=False):
        '''
        This function will determine how many wafers are located in self.file_name.
        '''
        if not self.is_snarfed or recount:
            self.data['WAFERS'] = {}
            for _, _, _, OBJ in records_from_file(self.file_name, unpack=True, of_interest=['WIR', 'WRR']):
                if OBJ.id == 'WIR':
                    HW = (OBJ.get_value('HEAD_NUM'), OBJ.get_value('WAFER_ID'))
                    if HW not in self.data['WAFERS']:
                        self.data['WAFERS'][HW] = {}
                        self.data['WAFERS'][HW]['START_T'] = [OBJ.get_value('START_T')]
                        if self.version=='V4': self.data['WAFERS'][HW]['SITE_GRP'] = [OBJ.get_value('SITE_GRP')]
                        else: self.data['WAFERS'][HW]['SITE_GRP'] = [255]
                    else:
                        self.data['WAFERS'][HW]['START_T'].append(OBJ.get_value('START_T'))
                        if self.version=='V4': self.data['WAFERS'][HW]['SITE_GRP'].append(OBJ.get_value('SITE_GRP'))
                        else: self.data['WAFERS'][HW]['SITE_GRP'].append(255)
                elif OBJ.id == 'WRR': # Wafer Result Record
                    HW = (OBJ.get_value('HEAD_NUM'), OBJ.get_value('WAFER_ID'))
                    if HW not in self.data['WAFERS']: # Re-create the corresponding WIR
                        self.data['WAFERS'][HW] = {}
                        self.data['WAFERS'][HW]['START_T'] = [OBJ.get_value('FINISH_T')]
                        if self.version=='V4': self.data['WAFERS'][HW]['SITE_GRP'] = [OBJ.get_value('SITE_GRP')]
                        else: self.data['WAFERS'][HW]['SITE_GRP'] = [255]
                    else:
                        self.data['WAFERS'][HW]['FINISH_T'] = OBJ.get_value('FINISH_T') 
                        self.data['WAFERS'][HW]['USR_DESC'] = OBJ.get_value('USR_DESC')
                        self.data['WAFERS'][HW]['EXC_DESC'] = OBJ.get_value('EXC_DESC')
                        if self.version=='V4': self.data['WAFERS'][HW]['FABWF_ID'] = OBJ.get_value('FABWF_ID')
                        else: self.data['WAFERS'][HW]['FABWF_ID'] = ''
                        if self.version=='V4': self.data['WAFERS'][HW]['FRAME_ID'] = OBJ.get_value('FRAME_ID')
                        else: self.data['WAFERS'][HW]['FRAME_ID'] = ''
                        if self.version=='V4': self.data['WAFERS'][HW]['FABWF_ID'] = OBJ.get_value('FABWF_ID')
                        else: self.data['WAFERS'][HW]['FABWF_ID'] = ''
                        if self.version=='V4': self.data['WAFERS'][HW]['MASK_ID'] = OBJ.get_value('MASK_ID')
                        else: self.data['WAFERS'][HW]['MASK_ID'] = ''
                        if self.version=='V4': self.data['WAFERS'][HW]['HAND_ID'] = ''
                        else: self.data['WAFERS'][HW]['FABWF_ID'] = OBJ.get_value('HAND_ID')
                        if self.version=='V4': self.data['WAFERS'][HW]['PRB_CARD'] = ''
                        else: self.data['WAFERS'][HW]['PRB_CARD'] = OBJ.get_value('PRB_CARD') 
        return len(self.data['WAFERS'])
    
    def count_test_heads(self, hold_on=-1, renew=False):
        '''
        '''
        return self.count_test_heads_and_sites(hold_on, renew)[0]
    
    def count_test_sites(self, hold_on=-1, renew=False):
        '''
        '''
        return self.count_test_heads_and_sites(hold_on, renew)[1]
    
    def count_test_heads_and_sites(self, hold_on=-1, renew=False):
        '''
        
        '''
        _hold_on = hold_on
        if (len(self.data['HEADS'])==0 or len(self.data['SITES'])==0) or renew:
            if renew:
                self.data['HEADS'] = []
                self.data['SITES'] = []
            if self.version=='V4':
                for _, _, _, REC in records_from_file(self.file_name, unpack=True, of_interest=['SDR', 'PMR', 'PTR', 'FTR']):
                    if REC.id in ['SDR', 'PMR']:
                        if REC.get_value('HEAD_NUM') not in self.data['HEADS']: 
                            self.data['HEADS'].append(REC.get_value('HEAD_NUM'))
                        if REC.get_value('SITE_NUM') not in self.data['SITES']: 
                            self.data['SITES'].append(REC.get_value('SITE_NUM'))
                    elif REC.id == 'PTR':
                        if REC.get_value('HEAD_NUM') not in self.data['HEADS']:
                            self.data['HEADS'].append(REC.get_value('HEAD_NUM'))
                            _hold_on = hold_on
                        if REC.get_value('SITE_NUM') not in self.data['SITES']:
                            self.data['SITES'].append(REC.get_value('SITE_NUM'))
                            _hold_on = hold_on
                        _hold_on-=1
                        if _hold_on==0: break
                    elif REC.id == 'FTR':
                        if REC.get_value('HEAD_NUM') not in self.data['HEADS']:
                            self.data['HEADS'].append(REC.get_value('HEAD_NUM'))
                            _hold_on = hold_on
                        if REC.get_value('SITE_NUM') not in self.data['SITES']:
                            self.data['SITES'].append(REC.get_value('SITE_NUM'))
                            _hold_on = hold_on
                        _hold_on-=1
                        if _hold_on==0: break
            else:
                # I know that STDF V3 knows PMR's, but I don't know the fields in V3 PMR's ...
                if self.look_for_records(of_interest=['PTR']): # use PTR's
                    for _, _, _, OBJ in records_from_file(self.file_name, unpack=True, of_interest=['PTR']):
                        if OBJ.get_value('HEAD_NUM') not in self.data['HEADS']:
                            self.data['HEADS'].append(OBJ.get_value('HEAD_NUM'))
                            _hold_on = hold_on
                        if OBJ.get_value('SITE_NUM') not in self.data['SITES']:
                            self.data['SITES'].append(OBJ.get_value('SITE_NUM'))
                            _hold_on = hold_on
                        _hold_on-=1
                        if _hold_on==0: break
                elif self.look_for_records(of_interest=['FTR']): # use FTR's
                    for _, _, _, OBJ in records_from_file(self.file_name, unpack=True, of_interest=['FTR']):
                        if OBJ.get_value('HEAD_NUM') not in self.data['HEADS']:
                            self.data['HEADS'].append(OBJ.get_value('HEAD_NUM'))
                            _hold_on = hold_on
                        if OBJ.get_value('SITE_NUM') not in self.data['SITES']:
                            self.data['SITES'].append(OBJ.get_value('SITE_NUM'))
                            _hold_on = hold_on
                        _hold_on-=1
                        if _hold_on==0: break
        return (len(self.data['HEADS']), len(self.data['SITES']))
    
    def enumerate(self):
        '''
        This method will build a map of the self.file_name so that many other methods 
        can work much faster.
        '''
        pass
    
    
    def enumerate_records(self, records_of_interest=None):
        '''
        This method will return a dictionary ID -> #, wher ID is the record
        ID of the found records, and # is the count of that record in the file.
        If of_interest is None, all records of the version are considered.
        If of_interest is a list, only the elements in the list are considered.
        '''
        retval = {}
#         ALL 
        
        
        valid_STDF_records = ts_to_id(self.version)
        if records_of_interest==None:
            of_interest = valid_STDF_records
        elif isinstance(of_interest, list):
            ID2TS = id_to_ts(self.version)
            tmp_list = []
            for item in of_interest:
                if isinstance(item, str):
                    if item in ID2TS:
                        if ID2TS[item] not in tmp_list:
                            tmp_list.append(ID2TS[item])
                elif isinstance(item, tuple) and len(item)==2:
                    if item in valid_STDF_records:
                        if item not in tmp_list:
                            tmp_list.append(item)
            of_interest = tmp_list
        else:
            raise STDFError("enumerate_records(of_interest=%s) : Unsupported 'of_interest'" % of_interest)
        
        for _REC_LEN, REC_TYP, REC_SUB, _REC in records_from_file(self.file_name):
            if (REC_TYP, REC_SUB) in of_interest:
                if valid_STDF_records[(REC_TYP, REC_SUB)] not in retval:
                    retval[valid_STDF_records[(REC_TYP, REC_SUB)]] = 1
                else:
                    retval[valid_STDF_records[(REC_TYP, REC_SUB)]] +=1
        return retval
    
    def enumerate_used_soft_bins(self):
        '''
        This method will return a dictionary with the soft bin categories used, and the count for each. (PRR based)
        '''
        retval = {}
        for _, _, _, OBJ in records_from_file(self.file_name, unpack=True, of_interest=['PRR']):
            SOFT_BIN = OBJ.get_value('SOFT_BIN')
            if SOFT_BIN in retval:
                retval[SOFT_BIN] += 1
            else:
                retval[SOFT_BIN] = 1
        return retval
    
    def enumerate_soft_bins(self):
        '''
        This method will return a dictionary of possible soft bin categories, their summary count and their name (SBR based)
        '''
        retval = {}
        for _, _, _, OBJ in records_from_file(self.file_name, unpack=True, of_interest=['SBR']):
            if OBJ.get_value('SBIN_NUM') not in retval:
                if self.version=='V4':
                    retval[OBJ.get_value('SBIN_NUM')] = (OBJ.get_value('SBIN_NAM'), OBJ.get_value('SBIN_CNT'), OBJ.get_value('SBIN_PF'))
                else:
                    retval[OBJ.get_value('SBIN_NUM')] = (OBJ.get_value('SBIN_NAM'), OBJ.get_value('SBIN_CNT'), ' ')
            else:
                (NAM, CNT, PF) = retval[OBJ.get_value('SBIN_NUM')]
                CNT+=OBJ.get_value('SBIN_CNT')
                retval[OBJ.get_value('SBIN_NUM')] = (NAM, CNT, PF)
        return retval        
    
    def enumerate_used_hard_bins(self):
        '''
        This method will return a dictionary with the hard bin categories used, and the count for each. (PRR based)
        '''
        retval = {}
        for _, _, _, OBJ in records_from_file(self.file_name, unpack=True, of_interest=['PRR']):
            HARD_BIN = OBJ.get_value('HARD_BIN')
            if HARD_BIN in retval:
                retval[HARD_BIN] += 1
            else:
                retval[HARD_BIN] = 1
        return retval
    
    def enumerate_hard_bins(self):
        '''
        This method will return a dictionary of possible soft bin categories, their summary count and their name (HBR based)
        '''
        retval = {}
        for _, _, _, OBJ in records_from_file(self.file_name, True, ['HBR']):
            if OBJ.get_value('HBIN_NUM') not in retval:
                if self.version=='V4':
                    retval[OBJ.get_value('HBIN_NUM')] = (OBJ.get_value('HBIN_NAM'), OBJ.get_value('HBIN_CNT'), OBJ.get_value('HBIN_PF'))
                else:
                    retval[OBJ.get_value('HBIN_NUM')] = (OBJ.get_value('HBIN_NAM'), OBJ.get_value('HBIN_CNT'), ' ')
            else:
                (NAM, CNT, PF) = retval[OBJ.get_value('HBIN_NUM')]
                CNT+=OBJ.get_value('HBIN_CNT')
                retval[OBJ.get_value('HBIN_NUM')] = (NAM, CNT, PF)
        return retval        
    
    def enumerate_used_tests(self, with_progress=False):
        '''
        This method will return a list of all test names used in self.file_name (PTR, FTR, MPR, STR & MTR based) 
        '''
        retval = []
        if with_progress:
            number_of_parts = self.count_parts()
            number_of_tests = self.count_tests()
            current_item = 0
            pbar = pb.ProgressBar(maxval=number_of_parts * number_of_tests, widgets=[pb.SimpleProgress() , ' =', pb.Percentage(), ' ', pb.Bar(), ' ',pb.Timer(), ' ', pb.ETA()]).start()
        for _, _, _, OBJ in records_from_file(self.file_name, unpack=True, of_interest=['PTR', 'FTR', 'MPR', 'STR', 'MTR']):
            if self.version=='V4':
                if OBJ.get_value('TEST_TXT')!='': TEST_NAM = OBJ.get_value('TEST_TXT')
                else: TEST_NAM = "%d" % OBJ.get_value('TEST_NUM')
            elif self.version=='V3':
                if OBJ.get_value('TEST_NAM')!='': TEST_NAM = OBJ.get_value('TEST_NAM')
                elif OBJ.get_value('TEXT_TXT')!='': TEST_NAM = OBJ.get_value('TEST_TXT')
                else: TEST_NAM = "%d" % OBJ.get_value('TEST_NUM')
            else:
                STDFError("test_names : Unsupported version %s" % self.version)    
            if TEST_NAM not in retval:
                retval.append(TEST_NAM)
            if with_progress:
                current_item += 1
                pbar.update(current_item)
        if with_progress:
            pbar.finish()
        return retval
    
    def enumerate_tests(self):
        pass # TSR based
    
    
    def enumerate_test_counts(self, with_progress=False):
        '''
        This method will return a dictionary with the test names (and numbers), and the count for each.
        '''
        retval = {'PTR' : {}, 'FTR' : {}, 'MTR' : {}, 'STR' : {}, 'MPR' : {}}
        if with_progress:
            number_of_parts = self.count_parts()
            number_of_tests = self.count_tests()
            current_item = 0
            pbar = pb.ProgressBar(maxval=number_of_parts * number_of_tests, widgets=[pb.SimpleProgress() , ' =', pb.Percentage(), ' ', pb.Bar(), ' ',pb.Timer(), ' ', pb.ETA()]).start()
        for _, _, _, OBJ in records_from_file(self.file_name, unpack=True, of_interest=list(retval.keys())):
            if self.version=='V4':
                if OBJ.get_value('TEST_TXT')!='': TEST_NAM = OBJ.get_value('TEST_TXT')
                else: TEST_NAM = "%d" % OBJ.get_value('TEST_NUM')
            elif self.version=='V3':
                if OBJ.get_value('TEST_NAM')!='': TEST_NAM = OBJ.get_value('TEST_NAM')
                elif OBJ.get_value('TEXT_TXT')!='': TEST_NAM = OBJ.get_value('TEST_TXT')
                else: TEST_NAM = "%d" % OBJ.get_value('TEST_NUM')
            else:
                STDFError("test_names : Unsupported version %s" % self.version)    
            if TEST_NAM in retval[OBJ.id]:
                retval[OBJ.id][TEST_NAM] += 1
            else:
                retval[OBJ.id][TEST_NAM] = 1
            if with_progress:
                current_item += 1
                pbar.update(current_item)
        if with_progress:
            pbar.finish()
        return retval
    
    def enumerate_test_fails(self, with_progress=False):
        '''
        This method will return a fail count per test (as opposed to soft/hard bin categories)
        '''
        #TODO: split up in test types
        retval = {}
        if with_progress:
            number_of_parts = self.count_parts()
            number_of_tests = self.count_tests()
            current_item = 0
            pbar = pb.ProgressBar(maxval=number_of_parts * number_of_tests, widgets=[pb.SimpleProgress() , ' =', pb.Percentage(), ' ', pb.Bar(), ' ', pb.Timer(), ' ', pb.ETA()]).start()

        for _, _, _, OBJ in records_from_file(self.file_name, unpack=True, of_interest=['PTR', 'FTR', 'MTR', 'STR']):
            if self.version=='V4':
                if OBJ.get_value('TEST_TXT')!='': TEST_NAM = OBJ.get_value('TEST_TXT')
                else: TEST_NAM = "%d" % OBJ.get_value('TEST_NUM')
            elif self.version=='V3':
                if OBJ.get_value('TEST_NAM')!='': TEST_NAM = OBJ.get_value('TEST_NAM')
                elif OBJ.get_value('TEXT_TXT')!='': TEST_NAM = OBJ.get_value('TEST_TXT')
                else: TEST_NAM = "%d" % OBJ.get_value('TEST_NUM')
            else:
                STDFError("test_names : Unsupported version %s" % self.version)    
            TEST_FLG = OBJ.get_value('TEST_FLG')
            if (TEST_FLG[6]=='1') or (TEST_FLG[6]=='0' and TEST_FLG[7]=='1'): # fail or no result
                if TEST_NAM in retval:
                    retval[TEST_NAM] += 1
                else:
                    retval[TEST_NAM] = 1
            if with_progress:
                current_item += 1
                pbar.update(current_item)
        if with_progress:
            pbar.finish()
        return retval
        
    def enumerate_wafers(self, recount=False):
        '''
        This method will return a list of wafer numbers in this STDF file.
        '''
        if not self.is_snarfed or recount:
            self.data['WAFERS'] = {}
            for _, _, _, OBJ in records_from_file(self.file_name, unpack=True, of_interest=['WIR', 'WRR']):
                if OBJ.id == 'WIR':
                    HW = (OBJ.get_value('HEAD_NUM'), OBJ.get_value('WAFER_ID'))
                    if HW not in self.data['WAFERS']:
                        self.data['WAFERS'][HW] = {}
                        self.data['WAFERS'][HW]['START_T'] = [OBJ.get_value('START_T')]
                        if self.version=='V4': self.data['WAFERS'][HW]['SITE_GRP'] = [OBJ.get_value('SITE_GRP')]
                        else: self.data['WAFERS'][HW]['SITE_GRP'] = [255]
                    else:
                        self.data['WAFERS'][HW]['START_T'].append(OBJ.get_value('START_T'))
                        if self.version=='V4': self.data['WAFERS'][HW]['SITE_GRP'].append(OBJ.get_value('SITE_GRP'))
                        else: self.data['WAFERS'][HW]['SITE_GRP'].append(255)
                elif OBJ.id == 'WRR': # Wafer Result Record
                    HW = (OBJ.get_value('HEAD_NUM'), OBJ.get_value('WAFER_ID'))
                    if HW not in self.data['WAFERS']: # Re-create the corresponding WIR
                        self.data['WAFERS'][HW] = {}
                        self.data['WAFERS'][HW]['START_T'] = [OBJ.get_value('FINISH_T')]
                        if self.version=='V4': self.data['WAFERS'][HW]['SITE_GRP'] = [OBJ.get_value('SITE_GRP')]
                        else: self.data['WAFERS'][HW]['SITE_GRP'] = [255]
                    else:
                        self.data['WAFERS'][HW]['FINISH_T'] = OBJ.get_value('FINISH_T') 
                        self.data['WAFERS'][HW]['USR_DESC'] = OBJ.get_value('USR_DESC')
                        self.data['WAFERS'][HW]['EXC_DESC'] = OBJ.get_value('EXC_DESC')
                        if self.version=='V4': self.data['WAFERS'][HW]['FABWF_ID'] = OBJ.get_value('FABWF_ID')
                        else: self.data['WAFERS'][HW]['FABWF_ID'] = ''
                        if self.version=='V4': self.data['WAFERS'][HW]['FRAME_ID'] = OBJ.get_value('FRAME_ID')
                        else: self.data['WAFERS'][HW]['FRAME_ID'] = ''
                        if self.version=='V4': self.data['WAFERS'][HW]['FABWF_ID'] = OBJ.get_value('FABWF_ID')
                        else: self.data['WAFERS'][HW]['FABWF_ID'] = ''
                        if self.version=='V4': self.data['WAFERS'][HW]['MASK_ID'] = OBJ.get_value('MASK_ID')
                        else: self.data['WAFERS'][HW]['MASK_ID'] = ''
                        if self.version=='V4': self.data['WAFERS'][HW]['HAND_ID'] = ''
                        else: self.data['WAFERS'][HW]['FABWF_ID'] = OBJ.get_value('HAND_ID')
                        if self.version=='V4': self.data['WAFERS'][HW]['PRB_CARD'] = ''
                        else: self.data['WAFERS'][HW]['PRB_CARD'] = OBJ.get_value('PRB_CARD') 
        retval = []
        for HEAD_NUM, WAFER_ID in self.data['WAFERS']:
            retval.append(WAFER_ID)
        return retval   
        
    def is_from_probing(self):
        '''
        This method will determine if the FileName holds probing info or not
        based on the presence of the WCR/WIR/WRR record(s).
        '''
        if not self.is_indexed:
            self.build_index()
        records_found = list(self.index.keys())
        if 'WIR' in records_found or 'WCR' in records_found or 'WRR' in records_found:
            return True
        return False
    
    def is_from_finaltest(self):
        '''
        This method will determine if the FileName is from final test or not
        '''
        return not self.is_from_probing()
        
    def is_conform_the_standard(self):
        '''
        This function will determine if a given FileName is valid according to the standard.
            - file name convention with respect to the version
            - obligatory records 
            - record order
            
        It presumes the FileName exists.
        
        if the file is a compressed one, it is decompressed, there should be only ONE file inside, and it should be an STDF file according to the above rules.
        '''
        pass #TODO: Implement
    
    def used_extenstions(self):
        '''
        This method will return a list of used extensions in the STDF file.
        '''
        pass #TODO: Implement
    
    def obligatory_records(self):
        '''
        This method will return a list of obligatory records (according to the spec) for the given version (and extensions)
        '''
#         retval = {}
#         if self.version in supported.versions():
#             exts = ['']
#             if type(Extensions) == list:
#                 for item in Extensions:
#                     if item in supported.extensions(Version):
#                         if item not in exts:
#                             exts.append(item)
#             elif Extensions != None:
#                 raise STDFError("'Extensions' error")
#     
#             for (REC_TYP, REC_SUB) in RecordDefinitions:
#                 if Version in RecordDefinitions[(REC_TYP, REC_SUB)]:
#                     for ext, obligatory_flag in RecordDefinitions[(REC_TYP, REC_SUB)][Version][2]:
#                         if ext in exts and obligatory_flag==True:
#                             retval[(REC_TYP, REC_SUB)] = RecordDefinitions[(REC_TYP, REC_SUB)][Version][0]
#         return retval
        pass #TODO: Implement
    
    def holds_obligatory_records(self):
        pass #TODO: Implement

    def is_valid_name_for_versions(self):
        '''
        This method will return a list of STDF versions that self.name is valid for.
        '''
        retval = []
        for Version in supported().versions():
            RE = re.compile(FileNameDefinitions[Version])
            if RE.match(self.name)!=None:
                retval.append(Version)
        return retval
    
    def get_part_pass_count(self, recount=False):
        '''
        This method will report the number of passed parts in self.file_name
        (based on PRR:PART_FLG:bits 3&4)
        '''
        return self.get_part_pass_and_fail_counts(recount=recount)[0]
    
    def get_part_fail_count(self, recount=False):
        '''
        This method will report the number of failed parts in self.file_name
        (based on PRR:PART_FLG:bits 3&4)
        '''
        return self.get_part_pass_and_fail_counts(recount=recount)[1]
    
    def get_part_pass_and_fail_counts(self, recount=False):
        '''
        This method will report the number of passes and fails in self.file_name
        (based on PRR:PART_FLG:bits 3&4)
        '''
        if recount or (self.data['PASSES']+self.data['FAILS']==0):
            self.data['PASSES'] = 0
            self.data['FAILS'] = 0
            for _, _, _, OBJ in records_from_file(self.file_name, unpack=True, of_interest=['PRR']):
                if OBJ.get_value('PART_FLG')[4] == '0': self.data['PASSES']+=1
                else: self.data['FAILS']+=1
        return self.data['PASSES'], self.data['FAILS']
    
    def get_yield(self):
        '''
        This method will return the yield for self.file_name [0.0..1.0]
        '''
        passes, fails = self.get_part_pass_and_fail_counts()
        total = passes + fails
        if total==0:
            return 0.0
        else:
            return float(passes)/total

    def get_info(self):
        '''
        This method will return a dictionary with the information from the MIR
        '''
        def decode_if_needed(buff):
            if isinstance(buff, str):
                return buff
            else:
                return "%s" % buff
            
        retval = {
            'Customer'    : '', # FAMLY_ID
            'Product'     : '', # PART_TYP
            'Lot'         : '', # LOT_ID
            'DateCode'    : '', # derived from START_T (or SETUP_T if START_T not available) in format YYWWD
            'Tester'      : '', # NODE_NAM:STAT_NUM
            'TestProgram' : '', # JOB_NAM:JOB_REV
            'TestSpec'    : ''  # SPEC_NAM:SPEC_VER        
        }
        
        for _REC_LEN, REC_TYP, REC_SUB, REC in records_from_file(self.file_name):
            if (REC_TYP == 1) and (REC_SUB == 10):
                if self.version == 'V4':
                    obj = create_record_object('V4', self.endian, 'MIR', REC)
                    # Customer
                    retval['Customer'] = decode_if_needed(obj.get_value('FAMLY_ID'))
                    # Product
                    retval['Product'] = decode_if_needed(obj.get_value('PART_TYP'))
                    # Lot (Do *NOT add Sublot !!!)
                    retval['Lot'] = decode_if_needed(obj.get_value('LOT_ID'))
                    # DateCode                    
                    _setup_time = decode_if_needed(obj.get_value('SETUP_T'))
                    _start_time = decode_if_needed(obj.get_value('START_T'))
                    if _setup_time != 0:
                        retval['DateCode'] = DT(_setup_time).datecode
                    elif _start_time != 0:
                        retval['DateCode'] = DT(_start_time).datecode
                    else:
                        retval['DateCode'] = decode_if_needed(obj.get_value('DATE_COD'))
                    # Tester
                    _node_name = decode_if_needed(obj.get_value('NODE_NAM'))
                    _stat_num = decode_if_needed(obj.get_value('STAT_NUM'))
                    if _node_name in _stat_num:
                        _stat_num = _stat_num.replace(_node_name, '')
                    retval['Tester'] = "%s:%s" % (_node_name, _stat_num)
                    # TestProgram
                    _job_name = decode_if_needed(obj.get_value('JOB_NAM'))
                    _job_ver = decode_if_needed(obj.get_value('JOB_REV'))
                    if _job_name in _job_ver:
                        _job_ver = _job_ver.replace(_job_name, '')
                    retval['TestProgram'] = "%s:%s" % (_job_name, _job_ver)
                    # TestSpec
                    _spec_name = decode_if_needed(obj.get_value('SPEC_NAM'))
                    _spec_ver = decode_if_needed(obj.get_value('SPEC_VER'))
                    if _spec_name in _spec_ver:
                        _spec_ver = _spec_ver.replace(_spec_name, '')
                    retval['TestSpec'] = "%s:%s" % (_spec_name, _spec_ver)
                elif self.version == 'V3':
                    obj = create_record_object('V3', self.endian, 'MIR', REC)
                    # Customer
                    retval['Customer'] = '?'
                    # Product
                    retval['Product'] = decode_if_needed(obj.get_value('PART_TYP'))
                    # Lot
                    _lot = decode_if_needed(obj.get_value('LOT_ID'))
                    _sub_lot = decode_if_needed(obj.get_value('SBLOT_ID'))
                    if _lot in _sub_lot:
                        _sub_lot = _sub_lot.replace(_lot, '')
                    retval['Lot'] = "%s:%s" % (_lot, _sub_lot)
                    # DateCode                    
                    _setup_time = decode_if_needed(obj.get_value('SETUP_T'))
                    _start_time = decode_if_needed(obj.get_value('START_T'))
                    if _setup_time != 0:
                        retval['DateCode'] = DT(_setup_time).datecode
                    elif _start_time != 0:
                        retval['DateCode'] = DT(_start_time).datecode
                    else:
                        retval['DateCode'] = ''
                    # Tester
                    _node_name = decode_if_needed(obj.get_value('NODE_NAM'))
                    _stat_num = decode_if_needed(obj.get_value('STAT_NUM'))
                    if _node_name in _stat_num:
                        _stat_num = _stat_num.replace(_node_name, '')
                    retval['Tester'] = "%s:%s" % (_node_name, _stat_num)
                    # TestProgram
                    _job_name = decode_if_needed(obj.get_value('JOB_NAM'))
                    _job_ver = decode_if_needed(obj.get_value('JOB_REV'))
                    if _job_name in _job_ver:
                        _job_ver = _job_ver.replace(_job_name, '')
                    retval['TestProgram'] = "%s:%s" % (_job_name, _job_ver)
                    # TestSpec
                    retval['TestSpec'] = '?'
                break
        return retval
    
    def dump_records(self, unpack=True, surpress_unknown=True, of_interest=None):
        stdf_valid_records = ts_to_id(self.version)
        if of_interest==None:
            of_interest = list(stdf_valid_records.keys()) 
        elif isinstance(of_interest, list):
            ID2TS = id_to_ts(self.version)
            tmp_list = []
            for item in of_interest:
                if isinstance(item, str):
                    if item in ID2TS:
                        if ID2TS[item] not in tmp_list:
                            tmp_list.append(ID2TS[item])
                elif isinstance(item, tuple) and len(item)==2:
                    if item in stdf_valid_records:
                        if item not in tmp_list:
                            tmp_list.append(item)
                else:
                    STDFError("dump_records(unpack=%s, surpress_unknown=%s, records_of_interest=%s) : Can not understand the types in 'records_of_interest'." % (unpack, surpress_unknown, of_interest))
            of_interest = tmp_list
        else:
            STDFError("dump_records(unpack=%s, surpress_unknown=%s, records_of_interst=%s) : Can not understand the 'records_of_interest' parameter." % (unpack, surpress_unknown, of_interest))

        if unpack:
            for REC_LEN, REC_TYP, REC_SUB, REC in records_from_file(self.file_name, True):
                if (REC_TYP, REC_SUB) in of_interest:
                    print(REC)
                elif not surpress_unknown:
                    print(REC)
        else:
            TS2ID = ts_to_id(self.version, self.extensions())
            for REC_LEN, REC_TYP, REC_SUB, REC in records_from_file(self.file_name, False):
                if (REC_TYP, REC_SUB) in of_interest:
                        print("   %s" % TS2ID[REC_TYP, REC_SUB])
                        print("      REC_LEN = '%d' [U*2] (Bytes of data following header)" % REC_LEN)
                        print("      REC_TYP = '%d' [U*1] (Record type)" % REC_TYP)
                        print("      REC_SUB = '%d' [U*1] (Record sub-type)" % REC_SUB)
                        print("      REC = '%s'" % hexify(REC))
                elif not surpress_unknown:
                        print("   ???")
                        print("      REC_LEN = '%d' [U*2] (Bytes of data following header)" % REC_LEN)
                        print("      REC_TYP = '%d' [U*1] (Record type)" % REC_TYP)
                        print("      REC_SUB = '%d' [U*1] (Record sub-type)" % REC_SUB)
                        print("      REC = '%s'" % hexify(REC))

    def trend_plot(self, parameter, df=None, with_progress=False):
        '''
        This method will plot the trend curve for parameter
        If no pandas data frame (df) is provided, one will be build.
        '''
        pass
    
class Parameter(object):
    
    def __init__(self, TEST_NUM, DATA):
        self.__call__(TEST_NUM, DATA)
    
    def __call__(self, TEST_NUM, DATA):
        
        
        
        pass
    
    def plot_trend(self, X_SIZE, Y_SIZE):
        fig = plt.figure()
        fig.add_plot(1,1,1)
        

class STDR(object):
    '''
    This is the Base Class Record for all STDF records
    '''
    buffer = b''
    
    def __init__(self, endian=None, record=None):
        self.id = 'STDR'
        self.missing_fields = 0
        self.local_debug = False
        self.buffer = ''
        self.fields = {
            'REC_LEN'  : {'#' :  0, 'Type' :  'U*2', 'Ref' : None, 'Value' :      0, 'Text' : 'Bytes of data following header        ', 'Missing' : None},
            'REC_TYP'  : {'#' :  1, 'Type' :  'U*1', 'Ref' : None, 'Value' :      0, 'Text' : 'Record type                           ', 'Missing' : None},
            'REC_SUB'  : {'#' :  2, 'Type' :  'U*1', 'Ref' : None, 'Value' :      0, 'Text' : 'Record sub-type                       ', 'Missing' : None},
            # Types for testing
            'K1'       : {'#' :  3, 'Type' :  'U*1', 'Ref' : None, 'Value' :   None, 'Text' : 'One byte unsigned integer reference   ', 'Missing' : 0},
            'K2'       : {'#' :  4, 'Type' :  'U*2', 'Ref' : None, 'Value' :   None, 'Text' : 'One byte unsigned integer reference   ', 'Missing' : 0},
            'U*1'      : {'#' :  5, 'Type' :  'U*1', 'Ref' : None, 'Value' :   None, 'Text' : 'One byte unsigned integer             ', 'Missing' : 0},
            'U*2'      : {'#' :  6, 'Type' :  'U*2', 'Ref' : None, 'Value' :   None, 'Text' : 'Two byte unsigned integer             ', 'Missing' : 0},
            'U*4'      : {'#' :  7, 'Type' :  'U*4', 'Ref' : None, 'Value' :   None, 'Text' : 'Four byte unsigned integer            ', 'Missing' : 0},
            'U*8'      : {'#' :  8, 'Type' :  'U*8', 'Ref' : None, 'Value' :   None, 'Text' : 'Eight byte unsigned integer           ', 'Missing' : 0},
            'U*?'      : {'#' :  9, 'Type' :  'U*1', 'Ref' : None, 'Value' :   None, 'Text' : 'Eight byte unsigned integer           ', 'Missing' : 0},
            'xU*1'     : {'#' :  9, 'Type' :  'U*1', 'Ref' : 'K1', 'Value' :   None, 'Text' : 'Eight byte unsigned integer           ', 'Missing' : 0},
            'xU*2'     : {'#' :  9, 'Type' :  'U*1', 'Ref' : 'K1', 'Value' :   None, 'Text' : 'Eight byte unsigned integer           ', 'Missing' : 0},
            'xU*4'     : {'#' :  9, 'Type' :  'U*1', 'Ref' : 'K1', 'Value' :   None, 'Text' : 'Eight byte unsigned integer           ', 'Missing' : 0},
            'xU*?'     : {'#' :  9, 'Type' :  'U*1', 'Ref' : 'K1', 'Value' :   None, 'Text' : 'Eight byte unsigned integer           ', 'Missing' : 0},
            'I*1'      : {'#' : 10, 'Type' :  'I*1', 'Ref' : None, 'Value' :   None, 'Text' : 'One byte signed integer               ', 'Missing' : 0},
            'I*2'      : {'#' : 11, 'Type' :  'I*2', 'Ref' : None, 'Value' :   None, 'Text' : 'Two byte signed integer               ', 'Missing' : 0},
            'I*4'      : {'#' : 12, 'Type' :  'I*4', 'Ref' : None, 'Value' :   None, 'Text' : 'Four byte signed integer              ', 'Missing' : 0},
            'I*8'      : {'#' : 13, 'Type' :  'I*8', 'Ref' : None, 'Value' :   None, 'Text' : 'Eight byte signed integer             ', 'Missing' : 0},
            'R*4'      : {'#' : 14, 'Type' :  'R*4', 'Ref' : None, 'Value' :   None, 'Text' : 'Four byte floating point number       ', 'Missing' : 0.0},
            'R*8'      : {'#' : 15, 'Type' :  'R*8', 'Ref' : None, 'Value' :   None, 'Text' : 'Eight byte floating point number      ', 'Missing' : 0.0},
            'C*1'      : {'#' : 16, 'Type' :  'R*8', 'Ref' : None, 'Value' :   None, 'Text' : 'One byte fixed length string          ', 'Missing' : '1'},
            'C*2'      : {'#' : 17, 'Type' :  'R*8', 'Ref' : None, 'Value' :   None, 'Text' : 'Two byte fixed length string          ', 'Missing' : '12'},
            'C*3'      : {'#' : 18, 'Type' :  'R*8', 'Ref' : None, 'Value' :   None, 'Text' : 'Three byte fixed length string        ', 'Missing' : '123'},
            'R*9'      : {'#' : 19, 'Type' :  'R*8', 'Ref' : None, 'Value' :   None, 'Text' : 'Nine byte fixed length string         ', 'Missing' : '123456789'},
            'C*10'     : {'#' : 20, 'Type' :  'R*8', 'Ref' : None, 'Value' :   None, 'Text' : 'Ten byte (2-digit) fixed length string', 'Missing' : '1234567890'}
            
# C*12 Fixed length character string:
# C*n Variable length character string
# C*f Variable length character string

# B*6 Fixed length bit-encoded data
# V*n Variable data type field:
# B*n Variable length bit-encoded field.
# D*n Variable length bit-encoded field.
# N*1 Unsigned integer data stored in a nibble.
# kxTYPE Array of data of the type specified.

        }
        # Endian
        if endian == None:
            endian = sys_endian()
        elif ((endian == '<') or (endian == '>')):
            self.endian = endian
        else:
            raise STDFError("%s object creation error: unsupported endian '%s'" % (self.id, endian))
        # Record 
        if record != None:
            if self.local_debug: print("len(%s) = %s" % (self.id, len(record)))
            self._unpack(record)
    
    def _default_init(self, endian=None, record=None):
        # missing fields
        self.missing_fields = 0
        # Buffer
        self.buffer = ''
        # Endian
        if endian == None:
            self.endian = sys_endian()
        elif ((endian == '<') or (endian == '>')):
            self.endian = endian
        else:
            raise STDFError("%s object creation error : unsupported endian '%s'" % (self.id, endian))
        # Record
        if record != None:
            if self.local_debug: print("len(%s) = %s" % (self.id, len(record)))
            self._unpack(record)
    
    def __call__(self, endian = None, record = None):
        '''
        Method to change contents of an already created object. (eg : Change endian)
        '''
        if endian != None:
            if ((endian == '<') or (endian == '>')):
                self.endian = endian
            else:
                raise STDFError("%s object creation error : unsupported endian '%s'" % (self.id, endian))
        if record != None:
            self._unpack(record)
    
    def get_fields(self, FieldID = None):
        '''
        Getter, returns a 7 element tuple (#, Type, Ref, Value, Text, Missing, Note)
        if FieldID is provided either in a string or numerical way.
        If it is not provided, it returns a (IN ORDER) list of (string) keys. 
        '''
        if FieldID == None:
            retval = [None] * len(self.fields)
            for field in self.fields:
                retval[self.fields[field]['#']] = field
            return retval
        else:
            if isinstance(FieldID, str):
                if FieldID in self.fields:
                    return(self.fields[FieldID]['#'],
                           self.fields[FieldID]['Type'], 
                           self.fields[FieldID]['Ref'],
                           self.fields[FieldID]['Value'],
                           self.fields[FieldID]['Text'],
                           self.fields[FieldID]['Missing'])
                else:
                    return (None, None, None, None, None)
            elif isinstance(FieldID, int):
                if FieldID in range(len(self.fields)):
                    for field in self.fields:
                        if self.fields[field]['#'] == FieldID:
                            return(self.fields[field]['#'],
                                   self.fields[field]['Type'], 
                                   self.fields[field]['Ref'],
                                   self.fields[field]['Value'],
                                   self.fields[field]['Text'],
                                   self.fields[field]['Missing'])
                else:
                    return (None, None, None, None, None)
            else:
                raise STDFError("%s.get_value(%s) Error : '%s' is not a string or integer" % (self.id, FieldID, FieldID))

    def get_value(self, FieldID):
        return self.fields[FieldID]['Value']

    def set_value(self, FieldID, Value):
        '''
        Setter, sets the Value of the FieldID
        '''
        FieldKey = ''
        if isinstance(FieldID, int):
            for field in self.fields:
                if self.fields[field]['#'] == FieldID:
                    FieldKey = field
            if FieldKey == '':
                raise STDFError("%s.set_value(%s, %s) Error : '%s' is not a valid key" % (self.id, FieldID, Value, FieldID))
        elif isinstance(FieldID, str):
            if FieldID not in self.fields:
                raise STDFError("%s.set_value(%s, %s) Error : '%s' is not a valid key" % (self.id, FieldID, Value, FieldID))
            else:
                FieldKey = FieldID
        else:
            raise STDFError("%s.set_value(%s, %s) : Error : '%s' is not a string or integer." % (self.id, FieldID, Value, FieldID))
        
        Type, Ref = self.get_fields(FieldKey)[1:3]
        K = None
        if Ref != '':
            K = self.get_fields(Ref)[3]
        Type, Bytes = Type.split("*")
        
        if Type.startswith('x'):
            if not isinstance(Value, list):
                raise STDFError("%s.set_value(%s, %s) Error : '%s' does not references a list." % (self.id, FieldKey, Value, "*".join((str(K), Type, Bytes))))
            length_type = self.fields[Ref]['Type']  
            if not length_type.startswith('U*'):
                raise STDFError("%s.set_value(%s, %s) Error : '%s' references a non unsigned integer." % (self.id, FieldKey, Value, "*".join((str(K), Type, Bytes))))
            if not length_type in ['U*1', 'U*2', 'U*4', 'U*8']:
                raise STDFError("%s.set_value(%s, %s) Error : '%s' references an unsupported unsigned integer." % (self.id, FieldKey, Value, "*".join((str(K), Type, Bytes))))

            if Type == 'xU': # list of unsigned integers
                temp = [0] * len(Value)                   
                if Bytes == '1':
                    for index in range(len(Value)):
                        if isinstance(Value[index], int):
                            if ((Value[index]>=0) and (Value[index]<=255)): temp[index]=Value[index]
                            else: raise STDFError("%s.set_value(%s, %s) Error : 'index[%s]=%s' can not be casted into U*1." % (self.id, FieldKey, Value, index, Value[index]))
                        else:
                            raise STDFError("%s.set_value(%s, %s) Error : 'index[%s]' is not an integer." % (self.id, FieldKey, Value, index))
                elif Bytes == '2':
                    for index in range(len(Value)):
                        if isinstance(Value[index], int):
                            if ((Value[index]>=0) and (Value[index]<=65535)): temp[index]=Value[index]
                            else: raise STDFError("%s.set_value(%s, %s) Error : 'index[%s]=%s' can not be casted into U*2" % (self.id, FieldKey, Value, index, Value[index]))
                        else:
                            raise STDFError("%s.set_value(%s, %s) Error : 'index[%s]' is not an integer." % (self.id, FieldKey, Value, index))
                elif Bytes == '4':
                    for index in range(len(Value)):
                        if isinstance(Value[index], int):
                            if ((Value[index]>=0) and (Value[index]<=4294967295)): temp[index]=Value[index]
                            else: raise STDFError("%s.set_value(%s, %s) Error : 'index[%s]=%s' can not be casted into U*4" % (self.id, FieldKey, Value, index, Value[index]))
                        else:
                            raise STDFError("%s.set_value(%s, %s) Error : 'index[%s]' is not an integer." % (self.id, FieldKey, Value, index))
                elif Bytes == '8':
                    for index in range(len(Value)):
                        if isinstance(Value[index], int):
                            if ((Value[index]>=0) and (Value[index]<=18446744073709551615)): temp[index]=Value[index]
                            else: raise STDFError("%s.set_value(%s, %s) Error : 'index[%s]=%s' can not be casted into U*8" % (self.id, FieldKey, Value, index, Value[index]))
                        else:
                            raise STDFError("%s.set_value(%s, %s) Error : 'index[%s]' is not an integer." % (self.id, FieldKey, Value, index))
                else:
                    raise STDFError("%s.set_value(%s, %s) Error : '%s' is an unsupported Type" % (self.id, FieldKey, Value, '*'.join((Type, Bytes))))
                self.fields[FieldKey]['Value'] = temp
                self.fields[Ref]['Value'] = len(temp)
                if self.local_debug: print("%s._set_value(%s, %s) -> Value = %s, Reference '%s' = %s" % (self.id, FieldKey, Value, temp, Ref, len(temp)))
                
            elif Type == 'xI': # list of signed integers
                temp = [0] * len(Value)                   
                if Bytes == '1':
                    for index in range(len(Value)):
                        if isinstance(Value[index], int):
                            if ((Value[index]>=-128) and (Value[index]<=128)): temp[index]=Value[index]
                            else: raise STDFError("%s.set_value(%s, %s) Error : 'index[%s]=%s' can not be casted into I*1" % (self.id, FieldKey, Value, index, Value[index]))
                        else:
                            raise STDFError("%s.set_value(%s, %s) Error : 'index[%s]' is not an integer." % (self.id, FieldKey, Value, index))
                elif Bytes == '2':
                    for index in range(len(Value)):
                        if isinstance(Value[index], int):
                            if ((Value[index]>=-32768) and (Value[index]<=32767)): temp[index]=Value[index]
                            else: raise STDFError("%s.set_value(%s, %s) Error : 'index[%s]=%s' can not be casted into I*2" % (self.id, FieldKey, Value, index, Value[index]))
                        else:
                            raise STDFError("%s.set_value(%s, %s) Error : 'index[%s]' is not an integer." % (self.id, FieldKey, Value, index))
                elif Bytes == '4':
                    for index in range(len(Value)):
                        if isinstance(Value[index], int):
                            if ((Value[index]>=-2147483648) and (Value[index]<=2147483647)): temp[index]=Value[index]
                            else: raise STDFError("%s.set_value(%s, %s) Error : 'index[%s]=%s' can not be casted into I*4" % (self.id, FieldKey, Value, index, Value[index]))
                        else:
                            raise STDFError("%s.set_value(%s, %s) Error : 'index[%s]' is not an integer." % (self.id, FieldKey, Value, index))
                elif Bytes == '8':
                    for index in range(len(Value)):
                        if isinstance(Value[index], int):
                            if ((Value[index]>=-36028797018963968) and (Value[index]<=36028797018963967)): temp[index]=Value[index]
                            else: raise STDFError("%s.set_value(%s, %s) Error : 'index[%s]=%s' can not be casted into I*8" % (self.id, FieldKey, Value, index, Value[index]))
                        else:
                            raise STDFError("%s.set_value(%s, %s) Error : 'index[%s]' is not an integer." % (self.id, FieldKey, Value, index))
                else:
                    raise STDFError("%s.set_value(%s, %s) Error : '%s' is an unsupported Type" % (self.id, FieldKey, Value, '*'.join((Type, Bytes))))
                self.fields[FieldKey]['Value'] = temp
                self.fields[Ref]['Value'] = len(temp)
                if self.local_debug: print("%s._set_value(%s, %s) -> Value = %s, Reference '%s' = %s" % (self.id, FieldKey, Value, temp, Ref, len(temp)))
            
            elif Type == 'xR': # list of floats
                temp = [0.0] * len(Value)                   
                if ((Bytes == '4') or (Bytes == '8')):
                    for index in len(Value):
                        temp[index] = float(Value[index]) # no checking for float & double, pack will cast with appropriate precision, cast integers.
                else:
                    raise STDFError("%s.set_value(%s, %s) Error : '%s' is an unsupported Type" % (self.id, FieldKey, Value, '*'.join((Type, Bytes))))
                self.fields[FieldKey]['Value'] = temp
                self.fields[Ref]['Value'] = len(temp)
                if self.local_debug: print("%s._set_value(%s, %s) -> Value = %s, Reference '%s' = %s" % (self.id, FieldKey, Value, temp, Ref, len(temp)))
            
            elif Type == 'xC': # list of strings
                temp = [''] * len(Value)                   
                if Bytes.isdigit():
                    raise STDFError("%s.set_value(%s, %s) : Unimplemented type '%s'" % (self.id, FieldKey, Value, str(K) + '*'.join((Type, Bytes))))
                elif Bytes == 'n':
                    raise STDFError("%s.set_value(%s, %s) : Unimplemented type '%s'" % (self.id, FieldKey, Value, str(K) + '*'.join((Type, Bytes))))
                elif Bytes == 'f':
                    raise STDFError("%s.set_value(%s, %s) : Unimplemented type '%s'" % (self.id, FieldKey, Value, str(K) + '*'.join((Type, Bytes))))
                else:
                    raise STDFError("%s.set_value(%s, %s) : Unsupported type '%s'" % (self.id, FieldKey, Value, str(K) + '*'.join((Type, Bytes))))
                self.fields[FieldKey]['Value'] = temp
                self.fields[Ref]['Value'] = len(temp)
                if self.local_debug: print("%s._set_value(%s, %s) -> Value = %s, Reference '%s' = %s" % (self.id, FieldKey, Value, temp, Ref, len(temp)))
            
            elif Type == 'xB': # list of list of single character strings being '0' or '1' (max length = 255*8 = 2040 bits)
                if Bytes.isdigit():
                    temp = [['0'] * (int(Bytes) * 8)] * len(Value)
                    raise STDFError("%s.set_value(%s, %s) : Unimplemented type '%s'" % (self.id, FieldKey, Value, str(K) + '*'.join((Type, Bytes))))
                elif Bytes == 'n':
                    temp = [['0'] * (int() * 8)] * len(Value) #TODO: Fill in the int() statement
                    raise STDFError("%s.set_value(%s, %s) : Unimplemented type '%s'" % (self.id, FieldKey, Value, str(K) + '*'.join((Type, Bytes))))
                elif Bytes == 'f':
                    temp = [['0'] * (int() * 8)] * len(Value) #TODO: Fill in the int() statement
                    raise STDFError("%s.set_value(%s, %s) : Unimplemented type '%s'" % (self.id, FieldKey, Value, str(K) + '*'.join((Type, Bytes))))
                else:
                    raise STDFError("%s.set_value(%s, %s) : Unsupported type '%s'" % (self.id, FieldKey, Value, str(K) + '*'.join((Type, Bytes))))
                self.fields[FieldKey]['Value'] = temp
                self.fields[Ref]['Value'] = len(temp)
                if self.local_debug: print("%s._set_value(%s, %s) -> Value = %s, Reference '%s' = %s" % (self.id, FieldKey, Value, temp, Ref, len(temp)))
                
            elif Type == 'xD': # list of list of single character strings being '0' and '1'(max length = 65535 bits)
                if Bytes.isdigit():
                    raise STDFError("%s.set_value(%s, %s) : Unimplemented type '%s'" % (self.id, FieldKey, Value, str(K) + '*'.join((Type, Bytes))))
                elif Bytes == 'n':
                    raise STDFError("%s.set_value(%s, %s) : Unimplemented type '%s'" % (self.id, FieldKey, Value, str(K) + '*'.join((Type, Bytes))))
                elif Bytes == 'f':
                    raise STDFError("%s.set_value(%s, %s) : Unimplemented type '%s'" % (self.id, FieldKey, Value, str(K) + '*'.join((Type, Bytes))))
                else:
                    raise STDFError("%s.set_value(%s, %s) : Unsupported type '%s'" % (self.id, FieldKey, Value, str(K) + '*'.join((Type, Bytes))))
                # assign from temp to field
                if self.local_debug: print("%s._set_value(%s, %s) -> Value = %s, Reference '%s' = %s" % (self.id, FieldKey, Value, temp, Ref, len(temp)))
                
            elif Type == 'xN': # list of list of nibble integers
                if not isinstance(Value, list):
                    raise STDFError("%s.set_value(%s, %s) : %s should be a list" % (self.id, FieldKey, Value, str(K) + '*'.join((Type, Bytes))))
                for nibble_list in Value:
                    if not isinstance(nibble_list, list):
                        raise STDFError("%s.set_value(%s, %s) Error : %s should be a list of list(s) of nibble(s)" % (self.id, FieldKey, Value, '*'.join((Type, Bytes))))
                if Bytes.isdigit():
                    for nibble_list in Value:
                        if len(nibble_list) != int(Bytes):
                            raise STDFError("%s.set_value(%s, %s) Error : %s should contain all lists of %s elements, %s found." % (self.id, FieldKey, Value, '*'.join((Type, Bytes)), Bytes, len(nibble_list)))
                    temp = Value
                elif Bytes == 'n':
                    raise STDFError("%s.set_value(%s, %s) : Unimplemented type '%s'" % (self.id, FieldKey, Value, str(K) + '*'.join((Type, Bytes))))
                elif Bytes == 'f':
                    raise STDFError("%s.set_value(%s, %s) : Unimplemented type '%s'" % (self.id, FieldKey, Value, str(K) + '*'.join((Type, Bytes))))
                else:
                    raise STDFError("%s.set_value(%s, %s) : Unsupported type '%s'" % (self.id, FieldKey, Value, str(K) + '*'.join((Type, Bytes))))
                self.fields[FieldKey]['Value'] = temp
                self.fields[Ref]['Value'] = len(temp)
                if self.local_debug: print("%s._set_value(%s, %s) -> Value = %s, Reference '%s' = %s" % (self.id, FieldKey, Value, temp, Ref, len(temp)))
                                   
            elif Type == 'xV': # list of tuple (type, value) where type is defined in spec page 62tuples
                '''
                 0 = B*0 Special pad field
                 1 = U*1 One byte unsigned integer 
                 2 = U*2 Two byte unsigned integer 
                 3 = U*4 Four byte unsigned integer 
                 4 = I*1 One byte signed integer 
                 5 = I*2 Two byte signed integer 
                 6 = I*4 Four byte signed integer 
                 7 = R*4 Four byte floating point number 
                 8 = R*8 Eight byte floating point number 
                10 = C*n Variable length ASCII character string (first byte is string length in bytes) 
                11 = B*n Variable length binary data string (first byte is string length in bytes)
                12 = D*n Bit encoded data (first two bytes of string are length in bits) 
                13 = N*1 Unsigned nibble
                '''
                if Bytes.isdigit():
                    raise STDFError("%s.set_value(%s, %s) : Unimplemented type '%s'" % (self.id, FieldKey, Value, str(K) + '*'.join((Type, Bytes))))
                elif Bytes == 'n':
                    raise STDFError("%s.set_value(%s, %s) : Unimplemented type '%s'" % (self.id, FieldKey, Value, str(K) + '*'.join((Type, Bytes))))
                elif Bytes == 'f':
                    raise STDFError("%s.set_value(%s, %s) : Unimplemented type '%s'" % (self.id, FieldKey, Value, str(K) + '*'.join((Type, Bytes))))
                else:
                    raise STDFError("%s.set_value(%s, %s) : Unsupported type '%s'" % (self.id, FieldKey, Value, str(K) + '*'.join((Type, Bytes))))
                # assign from temp to field
                if self.local_debug: print("%s._set_value(%s, %s) -> Value = %s, Reference '%s' = %s" % (self.id, FieldKey, Value, temp, Ref, len(temp)))
                
            else:
                raise STDFError("%s.set_value(%s, %s) Error : '%s' is an unsupported Type" % (self.id, FieldKey, Value, '*'.join((Type, Bytes))))
        else:
            temp = ''
            if Type == 'U': # unsigned integer
                if type(Value) not in [int, int]:
                    raise STDFError("%s.set_value(%s, %s) Error : '%s' is not a an integer" % (self.id, FieldKey, Value, Value))
                if Bytes == '1':
                    if ((Value>=0) and (Value<=255)): temp = Value
                    else: raise STDFError("%s.set_value(%s, %s) Error : '%s' can not be casted into U*1" % (self.id, FieldKey, Value, Value))
                elif Bytes == '2':
                    if ((Value>=0) and (Value<=65535)): temp = Value
                    else: raise STDFError("%s.set_value(%s, %s) Error : '%s' can not be casted into U*2" % (self.id, FieldKey, Value, Value))
                elif Bytes == '4':
                    if ((Value>=0) and (Value<=4294967295)): temp = Value
                    else: raise STDFError("%s.set_value(%s, %s) Error : '%s' can not be casted into U*4" % (self.id, FieldKey, Value, Value))
                elif Bytes == '8':
                    if ((Value>=0) and (Value<=18446744073709551615)): temp = Value
                    else: raise STDFError("%s.set_value(%s, %s) Error : '%s' can not be casted into U*8" % (self.id, FieldKey, Value, Value))
                else:
                    raise STDFError("%s.set_value(%s, %s) Error : '%s' is an unsupported Type" % (self.id, FieldKey, Value, '*'.join((Type, Bytes))))
                self.fields[FieldKey]['Value'] = temp
                if self.local_debug: print("%s._set_value(%s, %s) -> Value = %s" % (self.id, FieldKey, Value, temp))

            elif Type == 'I': # signed integer
                if type(Value) not in [int, int]:
                    raise STDFError("%s.set_value(%s, %s) : '%s' is not an integer" % (self.id, FieldKey, Value, Value))
                if Bytes == '1':
                    if ((Value>=-128) and (Value<=127)): temp = Value
                    else: raise STDFError("%s.set_value(%s, %s) : '%s' can not be casted into I*1" % (self.id, FieldKey, Value, Value))
                elif Bytes == '2':
                    if ((Value>=-32768) and (Value<=32767)): temp = Value
                    else: raise STDFError("%s.set_value(%s, %s) : '%s' can not be casted into I*2" % (self.id, FieldKey, Value, Value))
                elif Bytes == '4':
                    if ((Value>=-2147483648) and (Value<=2147483647)): temp = Value
                    else: raise STDFError("%s.set_value(%s, %s) : '%s' can not be casted into I*4" % (self.id, FieldKey, Value, Value))
                elif Bytes == '8':
                    if ((Value>=-36028797018963968) and (Value<=36028797018963967)): temp = Value
                    else: raise STDFError("%s.set_value(%s, %s) : '%s' can not be casted into I*8" % (self.id, FieldKey, Value, Value))
                else:
                    raise STDFError("%s.set_value(%s, %s) : Unsupported type '%s'" % (self.id, FieldKey, Value, '*'.join((Type, Bytes))))
                self.fields[FieldKey]['Value'] = temp
                if self.local_debug: print("%s._set_value(%s, %s) -> Value = %s" % (self.id, FieldKey, Value, temp))

            elif Type == 'R': # float
                if type(Value) not in [float, int, int]:
                    raise STDFError("%s.set_value(%s, %s) : '%s' is not a float" % (self.id, FieldKey, Value, Value))
                if ((Bytes == '4') or (Bytes == '8')): temp = float(Value) # no checking for float & double, pack will cast with appropriate precision
                else: raise STDFError("%s.set_value(%s, %s) : Unsupported type '%s'" % (self.id, FieldKey, Value, '*'.join((Type, Bytes))))
                self.fields[FieldKey]['Value'] = temp
                if self.local_debug: print("%s._set_value(%s, %s) -> Value = %s" % (self.id, FieldKey, Value, temp))
                
            elif Type == 'C': # string
                if not isinstance(Value, str):
                    raise STDFError("%s.set_value(%s, %s) Error : '%s' is not a python-string" % (self.id, FieldKey, Value, Value))
                if Bytes.isdigit():
                    temp = Value.strip()[:int(Bytes)]
                    #TODO: pad with spaces if the length doesn't match !!!
                elif Bytes == 'n':
                    temp = Value.strip()[:255]
                elif Bytes == 'f':
                    raise STDFError("%s.set_value(%s, %s) : Unimplemented type '%s'" % (self.id, FieldKey, Value, '*'.join((Type, Bytes))))
                else:
                    raise STDFError("%s.set_value(%s, %s) : Unsupported type '%s'" % (self.id, FieldKey, Value, '*'.join((Type, Bytes))))
                self.fields[FieldKey]['Value'] = temp
                if self.local_debug: print("%s._set_value(%s, %s) -> Value = %s" % (self.id, FieldKey, Value, temp))

            elif Type == 'B': # list of single character strings being '0' or '1' (max length = 255*8 = 2040 bits)
                if Bytes.isdigit(): 
                    if Bytes == '1': # can be a list of '1' and '0' or can be an unsigned 1 character byte
                        temp = ['0'] * 8
                        if isinstance(Value, int):
                            if (Value < 0) or (Value > 255):
                                raise STDFError("%s.set_value(%s, %s) : '%s' does contain an non-8-bit integer." % (self.id, FieldKey, Value, '*'.join((Type, Bytes))))
                            for Bit in range(8):
                                mask = pow(2, 7-Bit)
                                if (Value & mask) == mask:
                                    temp[Bit] = '1'
                        elif isinstance(Value, list):
                            if len(Value) != 8:
                                raise STDFError("%s.set_value(%s, %s) : '%s' does contain a list of 8 elements." % (self.id, FieldKey, Value, '*'.join((Type, Bytes))))
                            for Bit in range(8):
                                if not isinstance(Value[Bit], str):
                                    raise STDFError("%s.set_value(%s, %s) : '%s' does contain a list of 8 elements but there are non-string elements inside." % (self.id, FieldKey, Value, '*'.join((Type, Bytes))))
                                if Value[Bit] not in ['0', '1']:
                                    raise STDFError("%s.set_value(%s, %s) : '%s' does contain a list of 8 elements, all string, but none '0' or '1'." % (self.id, FieldKey, Value, '*'.join((Type, Bytes))))
                            temp = Value
                        else:
                            raise STDFError("%s.set_value(%s, %s) : assignment to 'B*1' is not an integer or list" % (self.id, FieldKey, Value))
                    else:
                        raise STDFError("%s.set_value(%s, %s) : Unimplemented type '%s'" % (self.id, FieldKey, Value, '*'.join((Type, Bytes))))
                elif Bytes == 'n':
                    if not isinstance(Value, list):
                        raise STDFError("%s.set_value(%s, %s) : assignment to '%s' is not a list" % (self.id, FieldKey, Value, '*'.join((Type, Bytes))))
                    # Determine how long the end result will be
                    result_length = 0
                    for index in Value:
                        if isinstance(Value[index], str):
                            if Value[index] in ['0', '1']:
                                result_length += 1
                            else:
                                raise STDFError("%s.set_value(%s, %s) : '%s' list does contain a string element that is not '1' or '0'." % (self.id, FieldKey, Value, '*'.join((Type, Bytes))))
                        elif isinstance(Value[index], int):
                            if (Value[index] >= 0) and (Value[index] <= 255):
                                result_length += 8
                            else:
                                raise STDFError("%s.set_value(%s, %s) : '%s' list does contain an non-8-bit integer." % (self.id, FieldKey, Value, '*'.join((Type, Bytes))))
                        else:
                            raise STDFError("%s.set_value(%s, %s) : '%s' list does contain an element that is not of type int or string." % (self.id, FieldKey, Value, '*'.join((Type, Bytes)))) 
                    if result_length / 8 != 0:
                        raise STDFError("%s.set_value(%s, %s) : '%s' list does not constitute a multiple of 8 bits." % (self.id, FieldKey, Value, '*'.join((Type, Bytes))))
                    temp = ['0'] * result_length
                    temp_index = 0
                    for value_index in range(len(Value)):
                        if isinstance(Value[value_index], str):
                            temp[temp_index] = Value[index]
                            temp_index += 1
                        elif isinstance(Value[value_index], int):
                            for Bit in range(8):
                                mask = pow(2, 7-Bit)
                                if (Value[value_index] & mask) == mask:
                                    temp[temp_index] = '1'
                                temp_index += 1
                        else:
                            raise STDFError("%s.set_value(%s, %s) : '%s' list does contain an element that is not of type int or string." % (self.id, FieldKey, Value, '*'.join((Type, Bytes))))
                elif Bytes == 'f':
                    raise STDFError("%s.set_value(%s, %s) : Unimplemented type '%s'" % (self.id, FieldKey, Value, '*'.join((Type, Bytes))))
                else:
                    raise STDFError("%s.set_value(%s, %s) : Unsupported type '%s'" % (self.id, FieldKey, Value, '*'.join((Type, Bytes))))
                self.fields[FieldKey]['Value'] = temp
                if self.local_debug: print("%s._set_value(%s, %s) -> Value = %s" % (self.id, FieldKey, Value, temp))
                
            elif Type == 'D': # list of single character strings being '0' and '1'(max length = 65535 bits)
                if not isinstance(Value, list):
                    raise STDFError("%s.set_value(%s, %s) Error : '%s' is not a list" % (self.id, FieldKey, Value, Value))
                if Bytes.isdigit():
                    if int(Bytes) > 65535:
                        raise STDFError("%s.set_value(%s, %s) Error : type '%s' can't be bigger than 65535 bits" % (self.id, FieldKey, Value, '*'.join((Type, Bytes))))
                    temp = ['0'] * int(Bytes) # set all bits to '0'
                    if len(Value) > len(temp):
                        raise STDFError("%s.set_value(%s, %s) Error : too many elements in Value" % (self.id, FieldKey, Value))
                    for i in range(len(Value)):
                        temp[i] = Value[i]
                elif Bytes == 'n':
                    temp = Value
                elif Bytes == 'f':
                    raise STDFError("%s.set_value(%s, %s) : Unimplemented type '%s'" % (self.id, FieldKey, Value, '*'.join((Type, Bytes))))
                else:
                    raise STDFError("%s.set_value(%s, %s) : Unsupported type '%s'" % (self.id, FieldKey, Value, '*'.join((Type, Bytes))))
                self.fields[FieldKey]['Value'] = temp
                if self.local_debug: print("%s._set_value(%s, %s) -> Value = %s" % (self.id, FieldKey, Value, temp))
                
            elif Type == 'N': # list of integers
                if not isinstance(Value, list):
                    raise STDFError("%s.set_value(%s, %s) Error : '%s' is not a list" % (self.id, FieldKey, Value, Value))
                for nibble in Value:
                    if ((nibble<0) or (nibble>15)):
                        raise STDFError("%s.set_value(%s, %s) Error : a non-nibble value is present in the list." % (self.id, FieldKey, Value))
                if Bytes.isdigit():
                    if int(Bytes) > 510:
                        raise STDFError("%s.set_value(%s, %s) Error : type '%s' can't be bigger than 510 nibbles" % (self.id, FieldKey, Value, '*'.join((Type, Bytes))))
                    temp = [0] * int(Bytes)
                    if len(Value) > len(temp):
                        raise STDFError("%s.set_value(%s, %s) Error : too many elements in Value" % (self.id, FieldKey, Value))
                    for i in range(len(Value)):
                        temp[i] = Value[i]
                elif Bytes == 'n':
                    raise STDFError("%s.set_value(%s, %s) : Unimplemented type '%s'" % (self.id, FieldKey, Value, '*'.join((Type, Bytes))))
                elif Bytes == 'f':
                    raise STDFError("%s.set_value(%s, %s) : Unimplemented type '%s'" % (self.id, FieldKey, Value, '*'.join((Type, Bytes))))
                else:
                    raise STDFError("%s.set_value(%s, %s) : Unsupported type '%s'" % (self.id, FieldKey, Value, '*'.join((Type, Bytes))))
                self.fields[FieldKey]['Value'] = temp
                if self.local_debug: print("%s._set_value(%s, %s) -> Value = %s" % (self.id, FieldKey, Value, temp))

            elif Type == 'V': # tuple (type, value) where type is defined in spec page 62
                '''
                 0 = B*0 Special pad field
                 1 = U*1 One byte unsigned integer 
                 2 = U*2 Two byte unsigned integer 
                 3 = U*4 Four byte unsigned integer 
                 4 = I*1 One byte signed integer 
                 5 = I*2 Two byte signed integer 
                 6 = I*4 Four byte signed integer 
                 7 = R*4 Four byte floating point number 
                 8 = R*8 Eight byte floating point number 
                10 = C*n Variable length ASCII character string (first byte is string length in bytes) 
                11 = B*n Variable length binary data string (first byte is string length in bytes)
                12 = D*n Bit encoded data (first two bytes of string are length in bits) 
                13 = N*1 Unsigned nibble
                '''
                if not isinstance(Value, tuple):
                    raise STDFError("%s.set_value(%s, %s) : '%s' is not a tuple", (self.id, FieldKey, Value, '*'.join((Type, Bytes))))
                if len(Value) != 2:
                    raise STDFError("%s.set_value(%s, %s) : '%s' is not a 2-element tuple", (self.id, FieldKey, Value, '*'.join((Type, Bytes))))
                if Value[0] not in [0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 'B*0', 'U*1', 'U*2', 'U*4', 'I*1', 'I*2', 'I*4', 'R*4', 'R*8', 'C*n', 'B*n', 'D*n', 'N*1']:
                    raise STDFError("%s.set_value(%s, %s) : '%s' first element of the tuple is not a recognized", (self.id, FieldKey, Value, '*'.join((Type, Bytes))))    
                if Bytes.isdigit():
                    raise STDFError("%s.set_value(%s, %s) : Unimplemented type '%s'" % (self.id, FieldKey, Value, '*'.join((Type, Bytes))))
                elif Bytes == 'n':
                    raise STDFError("%s.set_value(%s, %s) : Unimplemented type '%s'" % (self.id, FieldKey, Value, '*'.join((Type, Bytes))))
                elif Bytes == 'f':
                    raise STDFError("%s.set_value(%s, %s) : Unimplemented type '%s'" % (self.id, FieldKey, Value, '*'.join((Type, Bytes))))
                else:
                    raise STDFError("%s.set_value(%s, %s) : Unsupported type '%s'" % (self.id, FieldKey, Value, '*'.join((Type, Bytes))))
                self.fields[FieldKey]['Value'] = temp
                if self.local_debug: print("%s._set_value(%s, %s) -> Value = %s" % (self.id, FieldKey, Value, temp))

            else:
                raise STDFError("%s.set_value(%s, %s) Error : '%s' is an unsupported Type" % (self.id, FieldKey, Value, '*'.join((Type, Bytes))))
                   
    def _type_size(self, FieldID):
        '''
        support function to determine the type size
        '''
        FieldKey = ''
        if isinstance(FieldID, int):
            for field in self.fields:
                if self.fields[field]['#'] == FieldID:
                    FieldKey = field
            if FieldKey == '':
                raise STDFError("%s._type_size(%s) : '%s' is not a valid key" % (self.id, FieldID, FieldID))
        elif isinstance(FieldID, str):
            if FieldID not in self.fields:
                raise STDFError("%s._type_size(%s) : '%s' is not a valid key" % (self.id, FieldID, FieldID))
            else:
                FieldKey = FieldID
        else:
            raise STDFError("%s._type_size(%s) : '%s' is not a string or integer." % (self.id, FieldID,FieldID))
        
        Type, Ref, Value = self.get_fields(FieldKey)[1:4]
        K = None
        if Ref != '':
            K = self.get_fields(Ref)[3]
        Type, Bytes = Type.split("*")
        
        if Type.startswith('x'):
            if ((Type == 'xU') or (Type == 'xI')):
                if Bytes in ['1', '2', '4', '8']:
                    retval = int(Bytes) * K
                    if self.local_debug: print("%s._type_size(%s) = %s [%s]" % (self.id, FieldKey, retval, str(K) + '*'.join((Type, Bytes)))) 
                    return retval
                else:
                    raise STDFError("%s_type_size(%s) : Unsupported type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
            elif Type == 'xR':
                if Bytes in ['4', '8']:
                    retval = int(Bytes) * K
                    if self.local_debug: print("%s._type_size(%s) = %s [%s]" % (self.id, FieldKey, retval, str(K) + '*'.join((Type, Bytes)))) 
                    return retval
                else:
                    raise STDFError("%s_type_size(%s) : Unsupported type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
            elif Type == 'xC':
                if Bytes.isdigit():
                    retval = int(Bytes) * K
                    if self.local_debug: print("%s._type_size(%s) = %s [%s]" % (self.id, FieldKey, retval, str(K) + '*'.join((Type, Bytes)))) 
                    return retval
                elif Bytes == 'n':
                    raise STDFError("%s._type_size(%s) : Unimplemented type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                elif Bytes == 'f':
                    raise STDFError("%s._type_size(%s) : Unimplemented type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                else:
                    raise STDFError("%s_type_size(%s) : Unsupported type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
            elif Type == 'xB':
                if Bytes.isdigit():
                    raise STDFError("%s._type_size(%s) : Unimplemented type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                elif Bytes == 'n':
                    raise STDFError("%s._type_size(%s) : Unimplemented type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                elif Bytes == 'f':
                    raise STDFError("%s._type_size(%s) : Unimplemented type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                else:
                    raise STDFError("%s_type_size(%s) : Unsupported type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
            elif Type == 'xD':
                if Bytes.isdigit():
                    raise STDFError("%s._type_size(%s) : Unimplemented type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                elif Bytes == 'n':
                    raise STDFError("%s._type_size(%s) : Unimplemented type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                elif Bytes == 'f':
                    raise STDFError("%s._type_size(%s) : Unimplemented type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                else:
                    raise STDFError("%s_type_size(%s) : Unsupported type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
            elif Type == 'xN':
                if Bytes.isdigit():
                    bytes_to_pack = int(Bytes) / 2
                    if (int(Bytes) % 2) != 0:
                        bytes_to_pack += 1
                    retval = bytes_to_pack * K
                    if self.local_debug: print("%s._type_size(%s) = %s [%s]" % (self.id, FieldKey, retval, str(K) + '*'.join((Type, Bytes)))) 
                    return retval    
                elif Bytes == 'n':
                    raise STDFError("%s._type_size(%s) : Unimplemented type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                elif Bytes == 'f':
                    raise STDFError("%s._type_size(%s) : Unimplemented type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                else:
                    raise STDFError("%s_type_size(%s) : Unsupported type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
            elif type == 'xV':
                if Bytes.isdigit():
                    raise STDFError("%s._type_size(%s) : Unimplemented type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                elif Bytes == 'n':
                    raise STDFError("%s._type_size(%s) : Unimplemented type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                elif Bytes == 'f':
                    raise STDFError("%s._type_size(%s) : Unimplemented type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                else:
                    raise STDFError("%s_type_size(%s) : Unsupported type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
            else:
                raise STDFError("%s_type_size(%s) : Unsupported type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
        else:
            if ((Type == 'U') or (Type == 'I')):
                if Bytes in ['1', '2', '4', '8']:
                    retval = int(Bytes)
                    if self.local_debug: print("%s._type_size(%s) = %s [%s]" % (self.id, FieldKey, retval, '*'.join((Type, Bytes)))) 
                    return retval
                else:
                    raise STDFError("%s_type_size(%s) : Unsupported type '%s'" % (self.id, FieldKey, '*'.join((Type, Bytes))))
            elif Type == 'R':
                if Bytes in ['4', '8']:
                    retval = int(Bytes)
                    if self.local_debug: print("%s._type_size(%s) = %s [%s]" % (self.id, FieldKey, retval, '*'.join((Type, Bytes)))) 
                    return retval
                else:
                    raise STDFError("%s_type_size(%s) : Unsupported type '%s'" % (self.id, FieldKey, '*'.join((Type, Bytes))))
            elif Type == 'C':
                if Bytes.isdigit():
                    retval = int(Bytes)
                    if self.local_debug: print("%s._type_size(%s) = %s [%s]" % (self.id, FieldKey, retval, '*'.join((Type, Bytes)))) 
                    return retval
                elif Bytes == 'n':
                    retval = len(Value) + 1
                    if self.local_debug: print("%s._type_size(%s) = %s [%s]" % (self.id, FieldKey, retval, '*'.join((Type, Bytes))))
                    return retval
                elif Bytes == 'f':
                    retval = len(Value)
                    if self.local_debug: print("%s._type_size(%s) = %s [%s]" % (self.id, FieldKey, retval, '*'.join((Type, Bytes))))
                    return retval
                else:
                    raise STDFError("%s_type_size(%s) : Unsupported type '%s'" % (self.id, FieldKey, '*'.join((Type, Bytes))))
            elif Type == 'B':
                if Bytes.isdigit():
                    retval = int(Bytes)
                    if self.local_debug: print("%s._type_size(%s) = %s [%s]" % (self.id, FieldKey, retval, '*'.join((Type, Bytes)))) 
                    return retval
                elif Bytes == 'n':
                    bits_to_pack = len(Value)
                    bytes_to_pack = bits_to_pack / 8
                    if (bits_to_pack % 8) != 0:
                        bytes_to_pack += 1
                    if bytes_to_pack <= 255:
                        retval = bytes_to_pack + 1
                        if self.local_debug: print("%s._type_size(%s) = %s [%s]" % (self.id, FieldKey, retval, '*'.join((Type, Bytes)))) 
                        return retval
                    else:
                        raise STDFError("%s._type_size(%s) : '%s' can not hold more than 255 bytes" % (self.id, FieldKey, '*'.join((Type, Bytes))))
                elif Bytes == 'f':
                    raise STDFError("%s._type_size(%s) : Unimplemented type '%s'" % (self.id, FieldKey, '*'.join((Type, Bytes))))
                else:
                    raise STDFError("%s_type_size(%s) : Unsupported type '%s'" % (self.id, FieldKey, '*'.join((Type, Bytes))))
            elif Type == 'D':
                if Bytes.isdigit():
                    bytes_to_pack = int(Bytes) / 8
                    if (int(Bytes) % 8) != 0:
                        bytes_to_pack += 1
                    retval = bytes_to_pack
                    if self.local_debug: print("%s._type_size(%s) = %s [%s]" % (self.id, FieldKey, retval, '*'.join((Type, Bytes)))) 
                    return retval
                elif Bytes == 'n':
                    bits_to_pack = len(Value)
                    bytes_to_pack = bits_to_pack / 8
                    if (bits_to_pack % 8) != 0:
                        bytes_to_pack += 1
                    if bytes_to_pack <= 8192:
                        retval = bytes_to_pack + 2
                        if self.local_debug: print("%s._type_size(%s) = %s [%s]" % (self.id, FieldKey, retval, '*'.join((Type, Bytes))))
                        return retval
                    else:
                        raise STDFError("%s._type_size(%s) : '%s' can not hold more than 8192 bytes (=65535 bits)" % (self.id, FieldKey, '*'.join((Type, Bytes))))
                elif Bytes == 'f':
                    raise STDFError("%s._type_size(%s) : Unimplemented type '%s'" % (self.id, FieldKey, '*'.join((Type, Bytes))))
                else:
                    raise STDFError("%s_type_size(%s) : Unsupported type '%s'" % (self.id, FieldKey, '*'.join((Type, Bytes))))
            elif Type == 'N':
                if Bytes.isdigit():
                    bytes_to_pack = int(Bytes) / 2
                    if (int(Bytes) % 2) != 0:
                        bytes_to_pack += 1
                    retval = bytes_to_pack
                    if self.local_debug: print("%s._type_size(%s) = %s [%s]" % (self.id, FieldKey, retval, '*'.join((Type, Bytes))))
                    return retval  
                elif Bytes == 'n':
                    nibbles_to_pack = len(Value)
                    bytes_to_pack = nibbles_to_pack / 2
                    if (nibbles_to_pack % 2) != 0:
                        bytes_to_pack += 1
                    retval = bytes_to_pack + 1
                    if self.local_debug: print("%s._type_size(%s) = %s [%s]" % (self.id, FieldKey, retval, '*'.join((Type, Bytes))))
                    return retval
                elif Bytes == 'f':
                    raise STDFError("%s._type_size(%s) : Unimplemented type '%s'" % (self.id, FieldKey, '*'.join((Type, Bytes))))
                else:
                    raise STDFError("%s_type_size(%s) : Unsupported type '%s'" % (self.id, FieldKey, '*'.join((Type, Bytes))))
            elif Type == 'V':
                if Bytes.isdigit():
                    raise STDFError("%s._type_size(%s) : Unimplemented type '%s'" % (self.id, FieldKey, '*'.join((Type, Bytes))))
                elif Bytes == 'n':
                    raise STDFError("%s._type_size(%s) : Unimplemented type '%s'" % (self.id, FieldKey, '*'.join((Type, Bytes))))
                elif Bytes == 'f':
                    raise STDFError("%s._type_size(%s) : Unimplemented type '%s'" % (self.id, FieldKey, '*'.join((Type, Bytes))))
                else:
                    raise STDFError("%s_type_size(%s) : Unsupported type '%s'" % (self.id, FieldKey, '*'.join((Type, Bytes))))
            else:
                raise STDFError("%s_type_size(%s) : Unsupported type '%s'" % (self.id, FieldKey, '*'.join((Type, Bytes))))

    def _update_rec_len(self):
        '''
        Private method that updates the "bytes following the header" in the 'REC_LEN' field
        '''
        reclen = 0
        for field in self.fields:
            if field == 'REC_LEN' : continue
            if field == 'REC_TYP' : continue
            if field == 'REC_SUB' : continue
            reclen += self._type_size(field)
        if self.local_debug: print("%s._update_rec_len() = %s" % (self.id, reclen))
        self.fields['REC_LEN']['Value'] = reclen    
                
    def _pack_item(self, FieldID):
        '''
        Private method that packs a field from the record and returns the packed version.
        
        
            'KxT*S' 
                K = reference in other field
                T = Type (U, I, R, C, B, D, N, V)
                    U = Unsigned integer
                    I = Signed integer
                    R = Floating point
                    C = String
                    S = Long string
                    B = list of bytes
                    D = list of bits
                    N = list of nibbles
                    V = variable type
                S = Size (#, n, f)
                    # = size is given by the number
                    n = size is in the first byte (255=max)
                    f = size is in another field.
        '''
        FieldKey = ''
        if isinstance(FieldID, int):
            for field in self.fields:
                if self.fields[field]['#'] == FieldID:
                    FieldKey = field
            if FieldKey == '':
                raise STDFError("%s._pack_item(%s) Error : not a valid integer key" % (self.id, FieldID))
        elif isinstance(FieldID, str):
            if FieldID not in self.fields:
                raise STDFError("%s._pack_item(%s) Error : not a valid string key" % (self.id, FieldID))
            else:
                FieldKey = FieldID
        else:
            raise STDFError("%s._pack_item(%s) Error : not a string or integer key." % (self.id, FieldID))
        
        TypeFormat, Ref, Value = self.get_fields(FieldKey)[1:4] # get Type, Reference and Value
        if Value==None: Value=self.get_fields(FieldKey)[5] # get the 'missing' default
        Type, Size = TypeFormat.split("*")
        if Type.startswith('x'): 
            Type = Type[1:]
            TypeMultiplier = True
        else:
            TypeMultiplier = False
        if Ref!=None:
            if isinstance(Ref, str) and not TypeMultiplier:
                K = self.get_fields(Ref)[3]
            elif isinstance(Ref, tuple):
                if (len(Ref)==1 and not TypeMultiplier) or (len(Ref)==2 and TypeMultiplier):
                    K = self.get_fields(Ref[0])[3]
                else:
                    raise STDFError("%s._pack_item(%s) : Unsupported Reference '%s' vs '%s'" % (self.id, FieldKey, Ref, TypeFormat))
            else:
                raise STDFError("%s._pack_item(%s) : Unsupported Reference '%s' vs '%s'" % (self.id, FieldKey, Ref, TypeFormat))
        else:
            K = 1
        fmt = ''
        pkg = ''

        if Type == 'U': # (list of) Unsigned integer(s)
            if TypeMultiplier: ValueMask = Value
            else: ValueMask = [Value]
            if Size.isdigit():
                if Size == '1': fmt = '%sB' % self.endian   # 1 byte unsigned integer(s) 0 .. 255
                elif Size == '2': fmt = '%sH' % self.endian # 2 byte unsigned integer(s) 0 .. 65.535
                elif Size == '4': fmt = '%sI' % self.endian # 4 byte unsigned integer(s) 0 .. 4.294.967.295
                elif Size == '8': fmt = '%sQ' % self.endian # 8 byte unsigned integer(s) 0 .. 18446744073709551615
                else:
                    if TypeMultiplier: raise STDFError("%s._pack_item(%s) : Unsupported type-format '%s'" % (self.id, FieldKey, str(K) + TypeFormat))
                    else: raise STDFError("%s._pack_item(%s) : Unsupported type-format '%s'" % (self.id, FieldKey, TypeFormat))
            else:
                if TypeMultiplier: raise STDFError("%s._pack_item(%s) : Unsupported type-format '%s'" % (self.id, FieldKey, str(K) + TypeFormat))
                else: raise STDFError("%s._pack_item(%s) : Unsupported type-format '%s'" % (self.id, FieldKey, TypeFormat))
            for i in range(K):
                pkg+=struct.pack(fmt, ValueMask[i])
            if self.local_debug:
                if TypeMultiplier: print("%s._pack_item(%s)\n   '%s' [%s]\n   %s bytes" % (self.id, FieldKey, hexify(pkg), str(K) + TypeFormat, len(pkg))) 
                else: print("%s._pack_item(%s)\n   '%s' [%s]\n   %s bytes" % (self.id, FieldKey, hexify(pkg), TypeFormat, len(pkg)))
        elif Type == 'I': # (list of) Signed integer(s)
            if TypeMultiplier: ValueMask = Value
            else: ValueMask = [Value]
            if Size.isdigit():
                if Size == '1': fmt = '%sb' % self.endian   # 1 byte signed integer(s) -128 .. +127
                elif Size == '2': fmt = '%sh' % self.endian # 2 byte signed integer(s) -32.768 .. +32.767
                elif Size == '4': fmt = '%si' % self.endian # 4 byte signed integer(s) -2.147.483.648 .. +2.147.483.647
                elif Size == '8': fmt = '%sq' % self.endian # 8 byte signed integer(s) -9.223.372.036.854.775.808 .. +9.223.372.036.854.775.807
                else:
                    if TypeMultiplier: raise STDFError("%s._pack_item(%s) : Unsupported type-format '%s'" % (self.id, FieldKey, str(K) + TypeFormat))
                    else: raise STDFError("%s._pack_item(%s) : Unsupported type-format '%s'" % (self.id, FieldKey, TypeFormat))
            else:
                if TypeMultiplier: raise STDFError("%s._pack_item(%s) : Unsupported type-format '%s'" % (self.id, FieldKey, str(K) + TypeFormat))
                else: raise STDFError("%s._pack_item(%s) : Unsupported type-format '%s'" % (self.id, FieldKey, TypeFormat))
            for i in range(K):
                pkg+=struct.pack(fmt, ValueMask[i])
            if self.local_debug:
                if TypeMultiplier: print("%s._pack_item(%s)\n   '%s' [%s]\n   %s bytes" % (self.id, FieldKey, hexify(pkg), str(K) + TypeFormat, len(pkg))) 
                else: print("%s._pack_item(%s)\n   '%s' [%s]\n   %s bytes" % (self.id, FieldKey, hexify(pkg), TypeFormat, len(pkg)))
        elif Type == 'R': # (list of) floating point number(s)
            if TypeMultiplier: ValueMask = Value
            else: ValueMask = [Value]
            if Size.isdigit():
                if Size == '4': fmt = '%sf' % self.endian # (list of) 4 byte floating point number(s) [float] 
                elif Size == '8': fmt = '%sd' % self.endian # (list of) 8 byte floating point number(s) [double] 
                else:
                    if TypeMultiplier: raise STDFError("%s._pack_item(%s) : Unsupported type-format '%s'" % (self.id, FieldKey, str(K) + TypeFormat))
                    else: raise STDFError("%s._pack_item(%s) : Unsupported type-format '%s'" % (self.id, FieldKey, TypeFormat))
            else:
                if TypeMultiplier: raise STDFError("%s._pack_item(%s) : Unsupported type-format '%s'" % (self.id, FieldKey, str(K) + TypeFormat))
                else: raise STDFError("%s._pack_item(%s) : Unsupported type-format '%s'" % (self.id, FieldKey, TypeFormat))
            for i in range(K):
                pkg+=struct.pack(fmt, ValueMask[i])
            if self.local_debug:
                if TypeMultiplier: print("%s._pack_item(%s)\n   '%s' [%s]\n   %s bytes" % (self.id, FieldKey, hexify(pkg), str(K) + TypeFormat, len(pkg))) 
                else: print("%s._pack_item(%s)\n   '%s' [%s]\n   %s bytes" % (self.id, FieldKey, hexify(pkg), TypeFormat, len(pkg)))
        elif Type == 'C': # (list of) string(s)
            if TypeMultiplier: ValueMask = Value
            else: ValueMask = [Value]
            if Size.isdigit() or Size=='f' or Size == 'n':
                for i in range(K):
                    if Size == 'n':
                        pkg += struct.pack('B', len(ValueMask[i]))
                    pkg += ValueMask[i]
            else:
                if TypeMultiplier: raise STDFError("%s._pack_item(%s) : Unsupported type-format '%s'" % (self.id, FieldKey, str(K) + TypeFormat))
                else: raise STDFError("%s._pack_item(%s) : Unsupported type-format '%s'" % (self.id, FieldKey, TypeFormat))
            if self.local_debug:
                if TypeMultiplier: print("%s._pack_item(%s)\n   '%s' [%s]\n   %s bytes" % (self.id, FieldKey, hexify(pkg), str(K) + TypeFormat, len(pkg))) 
                else: print("%s._pack_item(%s)\n   '%s' [%s]\n   %s bytes" % (self.id, FieldKey, hexify(pkg), TypeFormat, len(pkg)))
        elif Type == 'S': # (list of) long string(s)
            if TypeMultiplier: ValueMask = Value
            else: ValueMask = [Value]
            if Size=='f' or Size == 'n':
                for i in range(K):
                    if Size == 'n':
                        pkg += struct.pack('%sH' % self.endian, len(ValueMask[i]))
                    pkg += ValueMask[i]
            else:
                if TypeMultiplier: raise STDFError("%s._pack_item(%s) : Unsupported type-format '%s'" % (self.id, FieldKey, str(K) + TypeFormat))
                else: raise STDFError("%s._pack_item(%s) : Unsupported type-format '%s'" % (self.id, FieldKey, TypeFormat))
            if self.local_debug:
                if TypeMultiplier: print("%s._pack_item(%s)\n   '%s' [%s]\n   %s bytes" % (self.id, FieldKey, hexify(pkg), str(K) + TypeFormat, len(pkg))) 
                else: print("%s._pack_item(%s)\n   '%s' [%s]\n   %s bytes" % (self.id, FieldKey, hexify(pkg), TypeFormat, len(pkg)))
        elif Type == 'B': # (list of) list of n*8 times '0' or '1'
            if TypeMultiplier: ValueMask = Value
            else: ValueMask = [Value]
            if Size.isdigit() or Size=='f' or Size == 'n': 
                for i in range(K):
                    bits_to_pack = len(ValueMask[i])
                    bytes_to_pack = bits_to_pack / 8 # Bits to pack should always be a multiple of 8, guaranteed by set_value
                    if Size == 'n':
                        pkg += struct.pack('B', bytes_to_pack)
                    for Byte in range(bytes_to_pack):
                        byte = 0
                        for Bit in range(8):
                            if ValueMask[i][(Byte * 8) + Bit] == '1':
                                byte+= pow(2, 7-Bit)
                        pkg += struct.pack('B', byte)
            else:
                if TypeMultiplier: raise STDFError("%s._pack_item(%s) : Unsupported type-format '%s'" % (self.id, FieldKey, str(K) + TypeFormat))
                else: raise STDFError("%s._pack_item(%s) : Unsupported type-format '%s'" % (self.id, FieldKey, TypeFormat))
            if self.local_debug:
                if TypeMultiplier: print("%s._pack_item(%s)\n   '%s' [%s]\n   %s bytes" % (self.id, FieldKey, hexify(pkg), str(K) + TypeFormat, len(pkg))) 
                else: print("%s._pack_item(%s)\n   '%s' [%s]\n   %s bytes" % (self.id, FieldKey, hexify(pkg), TypeFormat, len(pkg)))
        elif Type == 'D': # (list of) list of bits being '0' or '1'
            if TypeMultiplier: ValueMask = Value
            else: ValueMask = [Value]
            if Size.isdigit() or Size == 'f' or Size == 'n':
                for i in range(K):
                    temp_value = ValueMask[i]
                    bits_to_pack = len(temp_value)
                    bytes_to_pack = int(bits_to_pack) / 8
                    if Size == 'n':
                        pkg += struct.pack('%sH' % self.endian, bits_to_pack)
                    if (bits_to_pack % 8) != 0:
                        bytes_to_pack += 1
                        temp_value += ['0'] * (8-(bits_to_pack % 8)) # padd with '0' bits as specified in spec
                    for Byte in range(bytes_to_pack):
                        byte = 0
                        for Bit in range(8):
                            if temp_value[(Byte * 8) + Bit] == '1':
                                byte += pow(2, Bit)
                        pkg += struct.pack('B', byte)
            else:
                if TypeMultiplier: raise STDFError("%s._pack_item(%s) : Unsupported type-format '%s'" % (self.id, FieldKey, str(K) + TypeFormat))
                else: raise STDFError("%s._pack_item(%s) : Unsupported type-format '%s'" % (self.id, FieldKey, TypeFormat))
            if self.local_debug:
                if TypeMultiplier: print("%s._pack_item(%s)\n   '%s' [%s]\n   %s bytes" % (self.id, FieldKey, hexify(pkg), str(K) + TypeFormat, len(pkg))) 
                else: print("%s._pack_item(%s)\n   '%s' [%s]\n   %s bytes" % (self.id, FieldKey, hexify(pkg), TypeFormat, len(pkg)))
        elif Type == 'N': # (list of) a list of nibbles
            if TypeMultiplier: ValueMask = Value
            else: ValueMask = [Value]
            if Size.isdigit() or Size == 'f' or Size == 'n':
                for i in range(K): # number of nibble-lists
                    temp_value = ValueMask[i]
                    if Size == 'n':
                        pkg += struct.pack('B', len(temp_value)) # maximum 255 nibbles!
                    if is_odd(len(temp_value)):
                        temp_value.append(0)
                    for j in range(0, len(temp_value), 2):
                        N_odd = ValueMask[i][j] & 0x0F
                        N_even = (ValueMask[i][j+1] & 0xF0) << 4
                        byte = N_even | N_odd
                        pkg += struct.pack('B', byte)
            else:
                if TypeMultiplier: raise STDFError("%s._pack_item(%s) : Unsupported type-format '%s'" % (self.id, FieldKey, str(K) + TypeFormat))
                else: raise STDFError("%s._pack_item(%s) : Unsupported type-format '%s'" % (self.id, FieldKey, TypeFormat))
            if self.local_debug:
                if TypeMultiplier: print("%s._pack_item(%s)\n   '%s' [%s]\n   %s bytes" % (self.id, FieldKey, hexify(pkg), str(K) + TypeFormat, len(pkg))) 
                else: print("%s._pack_item(%s)\n   '%s' [%s]\n   %s bytes" % (self.id, FieldKey, hexify(pkg), TypeFormat, len(pkg)))
        elif Type == 'V': # (list of) variable types
            if TypeMultiplier: ValueMask = Value
            else: ValueMask = [Value]
            if Size == 'n':
                pass #TODO: Implement
            else:
                if TypeMultiplier: raise STDFError("%s._pack_item(%s) : Unsupported type-format '%s'" % (self.id, FieldKey, str(K) + TypeFormat))
                else: raise STDFError("%s._pack_item(%s) : Unsupported type-format '%s'" % (self.id, FieldKey, TypeFormat))
            if self.local_debug:
                if TypeMultiplier: print("%s._pack_item(%s)\n   '%s' [%s]\n   %s bytes" % (self.id, FieldKey, hexify(pkg), str(K) + TypeFormat, len(pkg))) 
                else: print("%s._pack_item(%s)\n   '%s' [%s]\n   %s bytes" % (self.id, FieldKey, hexify(pkg), TypeFormat, len(pkg)))
        else:
            if TypeMultiplier: raise STDFError("%s._pack_item(%s) : Unsupported type-format '%s'" % (self.id, FieldKey, str(K) + TypeFormat))
            else: raise STDFError("%s._pack_item(%s) : Unsupported type-format '%s'" % (self.id, FieldKey, TypeFormat))
        return pkg

    def _unpack_item(self, FieldID):
        if len(self.buffer) == 0:
            self.set_value(FieldID, self.fields[FieldID]['Missing'])
            self.missing_fields += 1
        else:
            FieldKey = ''
            if isinstance(FieldID, int):
                for field in self.fields:
                    if self.fields[field]['#'] == FieldID:
                        FieldKey = field
                if FieldKey == '':
                    raise STDFError("%s._unpack_item(%s) : not a valid integer key" % (self.id, FieldID))
            elif isinstance(FieldID, str):
                if FieldID not in self.fields:
                    raise STDFError("%s._unpack_item(%s) : not a valid string key" % (self.id, FieldID))
                else:
                    FieldKey = FieldID
            else:
                raise STDFError("%s._unpack_item(%s) : not a string or integer key." % (self.id, FieldID))
            
            Type, Ref, Value = self.get_fields(FieldKey)[1:4]
            K = self.get_fields(Ref)[3]
            Type, Bytes = Type.split("*")
            fmt = ''
            pkg = self.buffer
            
            if Type.startswith('x'):
                result = []
    
                if Type == 'xU': # list of unsigned integers
                    if Bytes.isdigit():
                        if Bytes == '1': fmt = self.endian + 'B'   # list of one byte unsigned integers 0..255
                        elif Bytes == '2': fmt = self.endian + 'H' # list of 2 byte unsigned integers 0..65535
                        elif Bytes == '4': fmt = self.endian + 'I' # list of 4 byte unsigned integers 0..4294967295
                        elif Bytes == '8': fmt = self.endian + 'Q' # list of 8 byte unsigned integers 0..18446744073709551615
                        else:
                            raise STDFError("%s._unpack_item(%s) : Unsupported type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                    else:
                        raise STDFError("%s._unpack_item(%s) : Unsupported type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                    for _ in range(K):
                        working_buffer = self.buffer[0:int(Bytes)]
                        self.buffer = self.buffer[int(Bytes):]
                        result.append(struct.unpack(fmt, working_buffer)[0])
                    if self.local_debug: print("%s._unpack_item(%s)\n   '%s' [%s] -> %s" % (self.id, FieldKey, hexify(pkg), str(K) + '*'.join((Type, Bytes)), result))    
                    self.set_value(FieldKey, result)     
                    
                elif Type == 'xI': # list of signed integers
                    if Bytes.isdigit():
                        if Bytes == '1': fmt = self.endian + 'b'   # list of one byte signed integers -127..127
                        elif Bytes == '2': fmt = self.endian + 'h' # list of 2 byte signed integers 
                        elif Bytes == '4': fmt = self.endian + 'i' # list of 4 byte signed integers 
                        elif Bytes == '8': fmt = self.endian + 'q' # list of 8 byte signed integers 
                        else:
                            raise STDFError("%s._unpack_item(%s) : Unsupported type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                    else:
                        raise STDFError("%s._unpack_item(%s) : Unsupported type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                    for _ in range(K):
                        working_buffer = self.buffer[0:int(Bytes)]
                        self.buffer = self.buffer[int(Bytes):]
                        result.append(struct.unpack(fmt, working_buffer)[0])
                    if self.local_debug: print("%s._unpack_item(%s)\n   '%s' [%s] -> %s" % (self.id, FieldKey, hexify(pkg), str(K) + '*'.join((Type, Bytes)), result))
                    self.set_value(FieldKey, result)     
                
                elif Type == 'xR': # list of floating point numbers
                    if Bytes.isdigit():
                        if Bytes == '4': fmt = self.endian + 'f'   # list of 4 byte floating point numbers (float) 
                        elif Bytes == '8': fmt = self.endian + 'd' # list of 8 byte floating point numbers (double) 
                        else:
                            raise STDFError("%s._unpack_item(%s) : Unsupported type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                    else:
                        raise STDFError("%s._unpack_item(%s) : Unsupported type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                    for _ in range(K):
                        working_buffer = self.buffer[0:int(Bytes)]
                        self.buffer = self.buffer[int(Bytes):]
                        result.append(struct.unpack(fmt, working_buffer)[0])
                    if self.local_debug: print("%s._unpack_item(%s)\n   '%s' [%s] -> %s" % (self.id, FieldKey, hexify(pkg), str(K) + '*'.join((Type, Bytes)), result))
                    self.set_value(FieldKey, result)     
                
                elif Type == 'xC': # list of strings
                    if Bytes.isdigit():
                        if int(Bytes) <= 255:
                            raise STDFError("%s._unpack_item(%s) : Unimplemented type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                        else:
                            raise STDFError("%s._unpack_item(%s) : Unsupported type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                    elif Bytes == 'n':
                        raise STDFError("%s._unpack_item(%s) : Unimplemented type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                    elif Bytes == 'f':
                        raise STDFError("%s._unpack_item(%s) : Unimplemented type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                    else:
                        raise STDFError("%s._unpack_item(%s) : Unsupported type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                    for _ in range(K):
                        working_buffer = self.buffer[0:int(Bytes)]
                        self.buffer = self.buffer[int(Bytes):]
                        result.append(struct.unpack(fmt, working_buffer)[0])
                    if self.local_debug: print("%s._unpack_item(%s)\n   '%s' [%s] -> %s" % (self.id, FieldKey, hexify(pkg), str(K) + '*'.join((Type, Bytes)), result))
                    self.set_value(FieldKey, result)     
                
                elif Type == 'xB': # list of list of '0' or '1'
                    if Bytes.isdigit():
                        raise STDFError("%s._unpack_item(%s) : Unimplemented type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                    elif Bytes == 'n':
                        raise STDFError("%s._unpack_item(%s) : Unimplemented type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                    elif Bytes == 'f':
                        raise STDFError("%s._unpack_item(%s) : Unimplemented type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                    else:
                        raise STDFError("%s._unpack_item(%s) : Unsupported type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                    if self.local_debug: print("%s._unpack_item(%s)\n   '%s' [%s] -> %s" % (self.id, FieldKey, hexify(pkg), str(K) + '*'.join((Type, Bytes)), result))
                    self.set_value(FieldKey, result)     
                
                elif Type == 'xD': # list of list of '0' or '1'
                    if Bytes.isdigit():
                        raise STDFError("%s._unpack_item(%s) : Unimplemented type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                    elif Bytes == 'n':
                        raise STDFError("%s._unpack_item(%s) : Unimplemented type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                    elif Bytes == 'f':
                        raise STDFError("%s._unpack_item(%s) : Unimplemented type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                    else:
                        raise STDFError("%s._unpack_item(%s) : Unsupported type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                    if self.local_debug: print("%s._unpack_item(%s)\n   '%s' [%s] -> %s" % (self.id, FieldKey, hexify(pkg), str(K) + '*'.join((Type, Bytes)), result))
                    self.set_value(FieldKey, result)     
                
                elif Type == 'xN': # list of a list of nibbles
                    if Bytes.isdigit():
                        result = []
                        if int(Bytes) <= 510:
                            if int(Bytes) == 1:
                                byteS = 1
                            else:
                                byteS = int(Bytes)/2
                                if is_odd(byteS): 
                                    byteS+=1
                            for _i in range(K):
                                tmp = []
                                for _j in range(byteS):
                                    working_buffer = self.buffer[0:1]
                                    self.buffer = self.buffer[1:]
                                    B = struct.unpack('B', working_buffer)[0]
                                    N1 = B & 0x0F
                                    N2 = (B & 0xF0) >> 4
                                    tmp.append(N1)
                                    tmp.append(N2)
                                if is_odd(byteS):
                                    tmp = tmp[0:-1] # remove the last element (which will be 0) from the list
                                result.append(tmp)
                        else:
                            raise STDFError("%s._unpack_item(%s) : Unsupported type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                    elif Bytes == 'n':
                        raise STDFError("%s._unpack_item(%s) : Unimplemented type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                    elif Bytes == 'f':
                        raise STDFError("%s._unpack_item(%s) : Unimplemented type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                    else:
                        raise STDFError("%s._unpack_item(%s) : Unsupported type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                    if self.local_debug: print("%s._unpack_item(%s)\n   '%s' [%s] -> %s" % (self.id, FieldKey, hexify(pkg), '*'.join((Type, Bytes)), result))
                    self.set_value(FieldKey, result)
                    
                elif Type == 'xV': # list of 2-element tuples
                    if Bytes.isdigit():
                        raise STDFError("%s._unpack_item(%s) : Unimplemented type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                    elif Bytes == 'n':
                        raise STDFError("%s._unpack_item(%s) : Unimplemented type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                    elif Bytes == 'f':
                        raise STDFError("%s._unpack_item(%s) : Unimplemented type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                    else:
                        raise STDFError("%s._unpack_item(%s) : Unsupported type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
                    if self.local_debug: print("%s._unpack_item(%s)\n   '%s' [%s] -> %s" % (self.id, FieldKey, hexify(pkg), str(K) + '*'.join((Type, Bytes)), result))
                    self.set_value(FieldKey, result)     
                else:
                    raise STDFError("%s._pack_item(%s) : Unsupported type '%s'" % (self.id, FieldKey, str(K) + '*'.join((Type, Bytes))))
            else:
                if Type == 'U': # unsigned integer
                    if Bytes.isdigit():
                        if Bytes == '1': fmt = "%sB" % self.endian   # unsigned char
                        elif Bytes == '2': fmt = "%sH" % self.endian # unsigned short
                        elif Bytes == '4': fmt = "%sL" % self.endian # unsigned long
                        elif Bytes == '8': fmt = "%sQ" % self.endian # unsigned long long
                        else:
                            raise STDFError("%s._unpack_item(%s) : Unsupported type '%s'" % (self.id, FieldKey, '*'.join((Type, Bytes))))
                        if len(self.buffer) < int(Bytes):
                            raise STDFError("%s._unpack_item(%s) : Not enough bytes in buffer (need %s while %s available)." % (self.id, FieldKey, Bytes, len(self.buffer)))
                        working_buffer = self.buffer[0:int(Bytes)]
                        self.buffer = self.buffer[int(Bytes):]
                        result = struct.unpack(fmt, working_buffer)[0]
                    else:
                        raise STDFError("%s._unpack_item(%s) : Unsupported type '%s'." % (self.id, FieldKey, '*'.join((Type, Bytes))))
                    if self.local_debug: print("%s._unpack_item(%s)\n   '%s' [%s] -> %s" % (self.id, FieldKey, hexify(pkg), '*'.join((Type, Bytes)), result))
                    self.set_value(FieldID, result)
                    
                elif Type == 'I': # signed integer
                    if Bytes.isdigit():
                        if Bytes == '1': fmt = "%sb" % self.endian   # signed char
                        elif Bytes == '2': fmt = "%sh" % self.endian # signed short
                        elif Bytes == '4': fmt = "%sl" % self.endian # signed long
                        elif Bytes == '8': fmt = "%sq" % self.endian # signed long long
                        else:
                            raise STDFError("%s._unpack_item(%s) : Unsupported type '%s'" % (self.id, FieldKey, '*'.join((Type, Bytes))))
                        if len(self.buffer) < int(Bytes):
                            raise STDFError("%s._unpack_item(%s) : Not enough bytes in buffer (need %s while %s available)." % (self.id, FieldKey, Bytes, len(self.buffer)))
                        working_buffer = self.buffer[0:int(Bytes)]
                        self.buffer = self.buffer[int(Bytes):]
                        result = struct.unpack(fmt, working_buffer)[0]
                    else:
                        raise STDFError("%s._unpack_item(%s) : Unsupported type '%s'." % (self.id, FieldKey, '*'.join((Type, Bytes))))    
                    if self.local_debug: print("%s._unpack_item(%s)\n   '%s' [%s] -> %s" % (self.id, FieldKey, hexify(pkg), '*'.join((Type, Bytes)), result))
                    self.set_value(FieldID, result)
                
                elif Type == 'R': # float
                    if Bytes.isdigit():
                        if Bytes == '4': fmt = "%sf" % self.endian # float
                        elif Bytes == '8': fmt = "%sd" % self.endian # double
                        else:
                            raise STDFError("%s._unpack_item(%s) : Unsupported type '%s'" % (self.id, FieldKey, '*'.join((Type, Bytes))))
                        if len(self.buffer) < int(Bytes):
                            raise STDFError("%s._unpack_item(%s) : Not enough bytes in buffer (need %s while %s available)." % (self.id, FieldKey, Bytes, len(self.buffer)))
                        working_buffer = self.buffer[0:int(Bytes)]
                        self.buffer = self.buffer[int(Bytes):]
                        result = struct.unpack(fmt, working_buffer)[0]
                    else:
                        raise STDFError("%s._unpack_item(%s) : Unsupported type '%s'." % (self.id, FieldKey, '*'.join((Type, Bytes))))    
                    if self.local_debug: print("%s._unpack_item(%s)\n   '%s' [%s] -> %s" % (self.id, FieldKey, hexify(pkg), '*'.join((Type, Bytes)), result))
                    self.set_value(FieldID, result)
                
                elif Type == 'C': # string
                    if Bytes.isdigit(): # C*1 C*2 ...
                        if len(self.buffer) < int(Bytes):
                            raise STDFError("%s._unpack_item(%s) : Not enough bytes in buffer (need %s while %s available)." % (self.id, FieldKey, Bytes, len(self.buffer)))
                        working_buffer = self.buffer[0:int(Bytes)]
                        self.buffer = self.buffer[int(Bytes):]
                        result = working_buffer.decode()
                    elif Bytes == 'n': # C*n
                        working_buffer = self.buffer[0:1]
                        self.buffer = self.buffer[1:]
                        n_bytes = struct.unpack('B', working_buffer)[0]
                        if len(self.buffer) < n_bytes:
                            raise STDFError("%s._unpack_item(%s) : Not enough bytes in buffer (need %s while %s available)." % (self.id, FieldKey, n_bytes, len(self.buffer)))
                        working_buffer = self.buffer[0:n_bytes]
                        self.buffer = self.buffer[n_bytes:]
                        result = working_buffer.decode()
                    elif Bytes == 'f': # C*f
                        n_bytes = self.get_fields(Ref)[3]
                        if len(self.buffer) < n_bytes:
                            raise STDFError("%s._unpack_item(%s) : Not enough bytes in buffer (need %s while %s available)." % (self.id, FieldKey, n_bytes, len(self.buffer)))
                        working_buffer = self.buffer[0:n_bytes]
                        self.buffer = self.buffer[n_bytes:]
                        result = working_buffer.decode()
                    else:
                        raise STDFError("%s._unpack_item(%s) : Unsupported type '%s'." % (self.id, FieldKey, '*'.join((Type, Bytes))))    
                    if self.local_debug: print("%s._unpack_item(%s)\n   '%s' [%s] -> %s" % (self.id, FieldKey, hexify(pkg), '*'.join((Type, Bytes)), result))
                    self.set_value(FieldID, result)
                
                elif Type == 'B': # list of single character strings being '0' or '1' (max length = 255*8 = 2040 bits)
                    if Bytes.isdigit(): # B*1 B*2 ...
                        if len(self.buffer) < int(Bytes):
                            raise STDFError("%s._unpack_item(%s) : Not enough bytes in buffer (need %s while %s available)." % (self.id, FieldKey, Bytes, len(self.buffer)))
                        working_buffer = self.buffer[0:int(Bytes)]
                        self.buffer = self.buffer[int(Bytes):]
                        temp = struct.unpack('B' * int(Bytes), working_buffer) # temp is a list (tuple) of 'Bytes' unsigned 1 byte bytes
                        result = ['0'] * (int(Bytes) * 8)
                        for Byte in range(len(temp)):
                            for Bit in range(8):
                                mask = pow(2, 7 - Bit)
                                if (temp[Byte] & mask) == mask : 
                                    result[(Byte * 8) + Bit] = '1'
                    elif Bytes == 'n': # B*n
                        working_buffer = self.buffer[0:1]
                        self.buffer = self.buffer[1:]
                        n_bytes = struct.unpack('B', working_buffer)[0]
                        if len(self.buffer) < n_bytes:
                            raise STDFError("%s._unpack_item(%s) : Not enough bytes in buffer (need %s while %s available)." % (self.id, FieldKey, n_bytes, len(self.buffer)))
                        working_buffer = self.buffer[0:n_bytes]
                        self.buffer = self.buffer[n_bytes:]
                        temp = struct.unpack('B' * n_bytes, working_buffer)
                        result = ['0'] * (n_bytes * 8)
                        for Byte in range(len(temp)):
                            for Bit in range(8):
                                mask = pow(2, 7 - Bit)
                                if (temp[Byte] & mask) == mask : 
                                    result[(Byte * 8) + Bit] = '1'
                    elif Bytes == 'f': # B*f
                        raise STDFError("%s._pack_item(%s) : Unimplemented type '%s'" % (self.id, FieldKey, '*'.join((Type, Bytes))))
                    else:
                        raise STDFError("%s._unpack_item(%s) : Unsupported type '%s'." % (self.id, FieldKey, '*'.join((Type, Bytes))))
                    if self.local_debug: print("%s._unpack_item(%s)\n   '%s' [%s] -> %s" % (self.id, FieldKey, hexify(pkg), '*'.join((Type, Bytes)), result))
                    self.set_value(FieldID, result)
                                    
                elif Type == 'D': # list of single character strings being '0' and '1'(max length = 65535 bits)
                    if Bytes.isdigit():
                        raise STDFError("%s._pack_item(%s) : Unimplemented type '%s'" % (self.id, FieldKey, '*'.join((Type, Bytes))))
                    elif Bytes == 'n':
                        working_buffer = self.buffer[0:2]
                        self.buffer = self.buffer[2:]
                        n_bits = struct.unpack('%sH' % self.endian, working_buffer)[0]
                        n_bytes = int(n_bits/8)
                        if n_bits % 8 != 0:
                            n_bytes += 1
                        result = ['0'] * (n_bytes * 8)
                        if len(self.buffer) < n_bytes:
                            raise STDFError("%s._unpack_item(%s) : Not enough bytes in buffer (need %s while %s available)." % (self.id, FieldKey, n_bytes, len(self.buffer)))
                        working_buffer = self.buffer[0:n_bytes]
                        self.buffer = self.buffer[n_bytes:]
                        result = ['0'] * n_bytes
                        for Byte in range(n_bytes):
                            B = struct.unpack('B', working_buffer[Byte])[0]
                            for Bit in range(8):
                                if B & pow(2, Bit) == 1:
                                    result[(Byte * 8) + Bit] = '1'
                        result = result[:n_bits] # strip off the paddings
                    elif Bytes == 'f':
                        raise STDFError("%s._pack_item(%s) : Unimplemented type '%s'" % (self.id, FieldKey, '*'.join((Type, Bytes))))
                    else:
                        raise STDFError("%s._unpack_item(%s) : Unsupported type '%s'." % (self.id, FieldKey, '*'.join((Type, Bytes))))
                    if self.local_debug: print("%s._unpack_item(%s)\n   '%s' [%s] -> %s" % (self.id, FieldKey, hexify(pkg), '*'.join((Type, Bytes)), result))
                    self.set_value(FieldID, result)
                
                elif Type == 'N': # list of integers
                    if Bytes.isdigit():
                        if len(self.buffer) < int(Bytes):
                            raise STDFError("%s._unpack_item(%s) : Not enough bytes in buffer (need %s while %s available)." % (self.id, FieldKey, Bytes, len(self.buffer)))
                        working_buffer = self.buffer[0:int(Bytes)]
                        self.buffer = self.buffer[int(Bytes):]
                        brol = []
                        for index in range(len(working_buffer)):
                            B = struct.unpack("%sB" % self.endian, working_buffer[index])[0]
                            N1 = B & 0x0F
                            N2 = (B & 0xF0) >> 4
                            brol.append(N1)
                            brol.append(N2)
                        brol = brol[:int(Bytes)]
                        self.set_value(FieldID, brol)
                    elif Bytes == 'n':
                        raise STDFError("%s._pack_item(%s) : Unimplemented type '%s'" % (self.id, FieldKey, '*'.join((Type, Bytes))))
                    elif Bytes == 'f':
                        raise STDFError("%s._pack_item(%s) : Unimplemented type '%s'" % (self.id, FieldKey, '*'.join((Type, Bytes))))
                    else:
                        raise STDFError("%s._unpack_item(%s) : Unsupported type '%s'." % (self.id, FieldKey, '*'.join((Type, Bytes))))
                    if self.local_debug: print("%s._unpack_item(%s)\n   '%s' [%s] -> %s" % (self.id, FieldKey, hexify(pkg), '*'.join((Type, Bytes)), result))
                    self.set_value(FieldID, result)
                
                elif Type == 'V': # tuple (type, value) where type is defined in spec page 62
                    '''
                     0 = B*0 Special pad field
                     1 = U*1 One byte unsigned integer 
                     2 = U*2 Two byte unsigned integer 
                     3 = U*4 Four byte unsigned integer 
                     4 = I*1 One byte signed integer 
                     5 = I*2 Two byte signed integer 
                     6 = I*4 Four byte signed integer 
                     7 = R*4 Four byte floating point number 
                     8 = R*8 Eight byte floating point number 
                    10 = C*n Variable length ASCII character string (first byte is string length in bytes) 
                    11 = B*n Variable length binary data string (first byte is string length in bytes)
                    12 = D*n Bit encoded data (first two bytes of string are length in bits) 
                    13 = N*1 Unsigned nibble
                    '''
                    if Bytes.isdigit():
                        raise STDFError("%s._pack_item(%s) : Unimplemented type '%s'" % (self.id, FieldKey, '*'.join((Type, Bytes))))
                    elif Bytes == 'n':
                        raise STDFError("%s._pack_item(%s) : Unimplemented type '%s'" % (self.id, FieldKey, '*'.join((Type, Bytes))))
                    elif Bytes == 'f':
                        raise STDFError("%s._pack_item(%s) : Unimplemented type '%s'" % (self.id, FieldKey, '*'.join((Type, Bytes))))
                    else:
                        raise STDFError("%s._pack_item(%s) : Unsupported type '%s'" % (self.id, FieldKey, '*'.join((Type, Bytes))))
                    if self.local_debug: print("%s._unpack_item(%s)\n   '%s' [%s] -> %s" % (self.id, FieldKey, hexify(pkg), '*'.join((Type, Bytes)), result))
                    self.set_value(FieldID, result)
                        
                else:
                    raise STDFError("%s.set_value(%s, %s) : Unsupported type '%s'" % (self.id, FieldKey, Value, '*'.join((Type, Bytes))))
                
    def _unpack(self, record):
        '''
        Private method to unpack a record (including header -to-check-record-type-) and set the appropriate values in fields.
        '''
        self.buffer = record
        
        if self.local_debug: print("%s._unpack(%s) with buffer length = %s" % (self.id, hexify(record), len(record))) 

        if record[2] != self.fields['REC_TYP']['Value']:
            raise STDFError("%s_unpack(%s) : REC_TYP doesn't match record" % hexify(record))
        
        if record[3] != self.fields['REC_SUB']['Value']:
            raise STDFError("%s_unpack(%s) : REC_SUB doesn't match record" % (self.id, hexify(record)))

        items = {}
        for index in self.fields:
            items[self.fields[index]['#']]=index
        for index in range(len(items)):
            self._unpack_item(items[index])
        
    def Vn_decode(self, BUFF, endian):
        '''
        This method unpacks a V*n field
        '''
        buffer_remainer = BUFF
        buffer_endian = endian
        retval = {}
        index = 1
    
        if buffer_endian not in ['<', '>']:
            raise STDFError("Vn_decode() : unsupported endian '%s'" % buffer_endian)
    
        return buffer_remainer #TODO: implement the tests for decoding of the V*n type and remove this bypass return statement
    
        while len(buffer_remainer) != 0:
            working_buffer = buffer_remainer[0:1]
            buffer_remainer = buffer_remainer[1:]
            local_type, = struct.unpack('b', working_buffer) # type identifier
            if local_type == 0: # B*0 Special pad field, of length 0 
                pass
            elif local_type == 1: # U*1 One byte unsigned integer
                working_buffer = buffer_remainer[0:1]
                buffer_remainer = buffer_remainer[1:]
                retval[index]['Type'] = 'U*1'
                retval[index]['Value'], = struct.unpack("%sB" % buffer_endian, working_buffer)
                index += 1
            elif local_type == 2: # U*2 Two byte unsigned integer
                working_buffer = buffer_remainer[0:2]
                buffer_remainer = buffer_remainer[2:]
                retval[index]['Type'] = 'U*2'
                retval[index]['Value'], = struct.unpack("%sH" % buffer_endian, working_buffer)
                index += 1
            elif local_type == 3: # U*4 Four byte unsigned integer
                working_buffer = buffer_remainer[0:4]
                buffer_remainer = buffer_remainer[4:]
                retval[index]['Type'] = 'U*4'
                retval[index]['Value'], = struct.unpack("%sI" % buffer_endian, working_buffer)
                index += 1
            elif local_type == 4: # I*1 One byte signed integer
                working_buffer = buffer_remainer[0:1]
                buffer_remainer = buffer_remainer[1:]
                retval[index]['Type'] = 'I*1'
                retval[index]['Value'], = struct.unpack("%sb" % buffer_endian, working_buffer)
                index += 1
            elif local_type == 5: # I*2 Two byte signed integer
                working_buffer = buffer_remainer[0:2]
                buffer_remainer = buffer_remainer[2:]
                retval[index]['Type'] = 'I*2'
                retval[index]['Value'], = struct.unpack("%sh" % buffer_endian, working_buffer)
                index += 1
            elif local_type == 6: # I*4 Four byte signed integer
                working_buffer = buffer_remainer[0:4]
                buffer_remainer = buffer_remainer[4:]
                retval[index]['Type'] = 'I*4'
                retval[index]['Value'], = struct.unpack("%si" % buffer_endian, working_buffer)
                index += 1
            elif local_type == 7: # R*4 Four byte floating point number
                working_buffer = buffer_remainer[0:4]
                buffer_remainer = buffer_remainer[4:]
                retval[index]['Type'] = 'R*4'
                retval[index]['Value'], = struct.unpack("%sf" % buffer_endian, working_buffer)
                index += 1
            elif local_type == 8: # R*8 Eight byte floating point number
                working_buffer = buffer_remainer[0:8]
                buffer_remainer = buffer_remainer[8:]
                retval[index]['Type'] = 'R*8'
                retval[index]['Value'], = struct.unpack("%sd" % buffer_endian, working_buffer)
                index += 1
            elif local_type == 10: # C*n Variable length ASCII character string (first byte is string length in bytes)
                working_buffer = buffer_remainer[0:1]
                buffer_remainer = buffer_remainer[1:]
                Cn_length, = struct.unpack("%sB" % buffer_endian, working_buffer)
                working_buffer = buffer_remainer[0:Cn_length]
                buffer_remainer = buffer_remainer[Cn_length:]
                retval[index]['Type'] = 'C*n'
                retval[index]['Value'] = working_buffer
                index += 1
            elif local_type == 11: # B*n Variable length binary data string (first byte is string length in bytes)
                working_buffer = buffer_remainer[0:1]
                buffer_remainer = buffer_remainer[1:]
                Bn_length, = struct.unpack("%sB" % buffer_endian, working_buffer)
                working_buffer = buffer_remainer[0:Bn_length]
                buffer_remainer = buffer_remainer[Bn_length:]
                retval[index]['Type'] = 'B*n'
                retval[index]['Value'] = working_buffer
                index += 1
            elif local_type == 12: # D*n Bit encoded data (first two bytes of string are length in bits)
                working_buffer = buffer_remainer[0:2]
                buffer_remainer = buffer_remainer[2:]
                Dn_length = struct.unpack("%sH" % buffer_endian, working_buffer)
                working_buffer = buffer_remainer[0:Dn_length]
                buffer_remainer = buffer_remainer[Dn_length:]
                retval[index]['Type'] = 'D*n'
                retval[index]['Value'] = working_buffer  
                index += 1
            elif local_type == 13: # N*1 Unsigned nibble
                working_buffer = buffer_remainer[0:1]
                buffer_remainer = buffer_remainer[1:]
                retval[index]['Type'] = 'N*1'
                retval[index]['Value'], = struct.unpack("%sB" % buffer_endian, working_buffer) & 0x0F
                index += 1
            else:
                raise STDFError("Vn_decode() : unsupported type '%d' in V*n" % local_type)
        return retval
    
    def __len__(self):
        retval = 0
        for field in self.fields:
            retval += self._type_size(field)
        return retval
    

    def __repr__(self):
        '''
        Method that packs the whole record and returns the packed version.
        '''
        sequence = {}
        header = ''
        body = ''

        # create the sequence order
        for field in self.fields:
            sequence[self.fields[field]['#']] = field
            
        # pack the body
        for item in range(3, len(sequence)):
            body += self._pack_item(sequence[item])
        self._update_rec_len()
        
        # check the body length against the REC_LEN
        if self.get_fields('REC_LEN')[3] != len(body):
            raise STDFError("%s.pack() length error %s != %s" % (self.id, self.get_fields('REC_LEN')[3], len(body)))
        
        # pack the header
        for item in range(0, 3):
            header += self._pack_item(sequence[item])
        
        # assemble the record    
        retval = header + body
        
        if self.local_debug: print("%s.pack()\n   '%s'\n   %s bytes" % (self.id, hexify(retval), len(retval)))
        return retval
        
       
    def __str__(self):
        '''
        Method used by print to print the STDF record.
        '''
        time_fields = ['MOD_TIM', 'SETUP_T', 'START_T', 'FINISH_T']
        sequence = {}
        for field in self.fields:
            sequence[self.fields[field]['#']] = field
        retval = "   %s (%d,%d) @ %s\n" % (self.id, self.get_value('REC_TYP'), self.get_value('REC_SUB'), self.version)
        for field in sorted(sequence):
            retval += "      %s = '%s'" % (sequence[field], self.fields[sequence[field]]['Value'])
            retval += " [%s] (%s)" %  (self.fields[sequence[field]]['Type'], self.fields[sequence[field]]['Text'].strip())
            if self.fields[sequence[field]]['Ref'] != None:
                retval += " -> %s\n" % self.fields[sequence[field]]['Ref']
            if sequence[field] in time_fields:
                retval += " = %s" % DT(float(self.fields[sequence[field]]['Value']))
            retval += "\n"
        return retval
                
###################################################################################################################################################
#TODO: change 'V4' and 'V3' in self.version to 4 and 3 respectively
#TODO: Implement the FPE (Field Present Expression) in all records
#TODO: Impleent support for the FPE in packing/unpacking
#TODO: Run trough all records and set the FPE correct

class ADR(STDR):
    def __init__(self, version=None, endian=None, record=None):
        self.id = ''
        self.local_debug = False
        # Version
        if version==None or version=='V3':
            self.version = 'V3'
            self.info=    '''
?!?
------------------

Function: 
    ?!?

Frequency: 
    * 

Location: 
'''
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' : 'U*2', 'Ref' :      None, 'Value' : None, 'Text' : 'Bytes of data following header                      ', 'Missing' :         None, 'Note' : ''},
                'REC_TYP'  : {'#' :  1, 'Type' : 'U*1', 'Ref' :      None, 'Value' :  220, 'Text' : 'Record type                                         ', 'Missing' :         None, 'Note' : ''},
                'REC_SUB'  : {'#' :  2, 'Type' : 'U*1', 'Ref' :      None, 'Value' :  205, 'Text' : 'Record sub-type                                     ', 'Missing' :         None, 'Note' : ''},
                'CPU_TYPE' : {'#' :  3, 'Type' : 'U1' , 'Ref' :      None, 'Value' : None, 'Text' : '                                                    ', 'Missing' :    sys_cpu(), 'Note' : ''},
                'STDF_VER' : {'#' :  4, 'Type' : 'Cn' , 'Ref' :      None, 'Value' : None, 'Text' : '                                                    ', 'Missing' : self.version, 'Note' : ''},
                'DB_ID'    : {'#' :  5, 'Type' : 'U1' , 'Ref' :      None, 'Value' : None, 'Text' : '                                                    ', 'Missing' :            0, 'Note' : ''},
                'PARA_CNT' : {'#' :  6, 'Type' : 'U2' , 'Ref' :      None, 'Value' : None, 'Text' : '                                                    ', 'Missing' :            0, 'Note' : ''},
                'LOT_FLG'  : {'#' :  7, 'Type' : 'U1' , 'Ref' :      None, 'Value' : None, 'Text' : '                                                    ', 'Missing' :            0, 'Note' : ''},
                'RTST_CNT' : {'#' :  8, 'Type' : 'U2' , 'Ref' :      None, 'Value' : None, 'Text' : '                                                    ', 'Missing' :            0, 'Note' : ''},
                'LOT_TYPE' : {'#' :  9, 'Type' : 'C1' , 'Ref' :      None, 'Value' : None, 'Text' : '                                                    ', 'Missing' :          ' ', 'Note' : ''},
                'RTST_WAF' : {'#' : 10, 'Type' : 'xCn', 'Ref' :'RTST_CNT', 'Value' : None, 'Text' : '                                                    ', 'Missing' :           [], 'Note' : ''},
                'RTST_BIN' : {'#' : 11, 'Type' : 'xU4', 'Ref' :'RTST_CNT', 'Value' : None, 'Text' : '                                                    ', 'Missing' :           [], 'Note' : ''},
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)

class ASR(STDR):
    def __init__(self, version=None, endian=None, record=None):
        self.id = ''
        self.local_debug = False
        # Version
        if version==None or version=='V4':
            self.version = 'V4'
            self.info=    '''
Algorithm Specification Record (V4, Memory:2010.1) 
--------------------------------------------------

Function: 
    This record is used to store the algorithms that are applied during a memory test. Table 11 Algorithm Specification Record (ASR) Record

Frequency: 
    * Once per unique memory test specification.

Location: 
    It can occur after all the Memory Model Records(MMRs) and before any Test specific records 
    e.g. Parametric Test Record (PTR), Functional Test Record (FTRs), Scan Test Record (STR) and Memory Test Record (MTRs).
'''
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' : 'U*2'  , 'Ref' :       None, 'Value' : None, 'Text' : 'Bytes of data following header                      ', 'Missing' : None, 'Note' : ''},
                'REC_TYP'  : {'#' :  1, 'Type' : 'U*1'  , 'Ref' :       None, 'Value' :    0, 'Text' : 'Record type                                         ', 'Missing' : None, 'Note' : ''},
                'REC_SUB'  : {'#' :  2, 'Type' : 'U*1'  , 'Ref' :       None, 'Value' :   20, 'Text' : 'Record sub-type                                     ', 'Missing' : None, 'Note' : ''},
                'ASR_IDX'  : {'#' :  3, 'Type' : 'U*2'  , 'Ref' :       None, 'Value' : None, 'Text' : 'Unique identifier for this ASR record               ', 'Missing' :    0, 'Note' : ''},
                'STRT_IDX' : {'#' :  4, 'Type' : 'U*1'  , 'Ref' :       None, 'Value' : None, 'Text' : 'Cycle Start index flag                              ', 'Missing' :    0, 'Note' : ''},
                'ALGO_CNT' : {'#' :  5, 'Type' : 'U*1'  , 'Ref' :       None, 'Value' : None, 'Text' : 'count (k) of Algorithms descriptions                ', 'Missing' :    0, 'Note' : ''},
                'ALGO_NAM' : {'#' :  6, 'Type' : 'xC*n' , 'Ref' : 'ALGO_CNT', 'Value' : None, 'Text' : 'Array of Names of the Algorithms                    ', 'Missing' :   [], 'Note' : ''},
                'ALGO_LEN' : {'#' :  7, 'Type' : 'xC*n' , 'Ref' : 'ALGO_CNT', 'Value' : None, 'Text' : 'Array of Complexity of algorithm  (e.g., 13N)       ', 'Missing' :   [], 'Note' : ''},
                'FILE_ID'  : {'#' :  8, 'Type' : 'xC*n' , 'Ref' : 'ALGO_CNT', 'Value' : None, 'Text' : 'Array of Name of the file with algorithm description', 'Missing' :   [], 'Note' : ''},
                'CYC_BGN'  : {'#' :  9, 'Type' : 'xU*8' , 'Ref' : 'ALGO_CNT', 'Value' : None, 'Text' : 'Array of Starting cycle number for the Algorithms   ', 'Missing' :   [], 'Note' : ''},
                'CYC_END'  : {'#' : 10, 'Type' : 'xU*8' , 'Ref' : 'ALGO_CNT', 'Value' : None, 'Text' : 'Array of End Cycle number for the algorithm         ', 'Missing' :   [], 'Note' : ''}
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)
            
class ATR(STDR):
    def __init__(self, version=None, endian=None, record = None):
        self.id = 'ATR'
        self.local_debug = False
        # Version
        if version==None or version=='V4':
            self.version = 'V4'
            self.info=    '''
Audit Trail Record 
------------------
    
Function: 
    Used to record any operation that alters the contents of the STDF file. The name of the
    program and all its parameters should be recorded in the ASCII field provided in this
    record. Typically, this record will be used to track filter programs that have been
    applied to the data.
        
Frequency: 
    * Optional 
    * One for each filter or other data transformation program applied to the STDF data.
        
Location: 
    Between the File Attributes Record (FAR) and the Master Information Record (MIR).
    The filter program that writes the altered STDF file must write its ATR immediately
    after the FAR (and hence before any other ATRs that may be in the file). In this way,
    multiple ATRs will be in reverse chronological order.
'''
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' : 'U*2' , 'Ref' : None, 'Value' :   None, 'Text' : 'Bytes of data following header        ', 'Missing' : None, 'Note' : ''},
                'REC_TYP'  : {'#' :  1, 'Type' : 'U*1' , 'Ref' : None, 'Value' :      0, 'Text' : 'Record type                           ', 'Missing' : None, 'Note' : ''},
                'REC_SUB'  : {'#' :  2, 'Type' : 'U*1' , 'Ref' : None, 'Value' :     20, 'Text' : 'Record sub-type                       ', 'Missing' : None, 'Note' : ''},
                'MOD_TIM'  : {'#' :  3, 'Type' : 'U*4' , 'Ref' : None, 'Value' :   None, 'Text' : 'Date & time of STDF file modification ', 'Missing' :    0, 'Note' : ''},
                'CMD_LINE' : {'#' :  4, 'Type' : 'C*n' , 'Ref' : None, 'Value' :   None, 'Text' : 'Command line of program               ', 'Missing' :   '', 'Note' : ''}
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)
            
class BPS(STDR):
    def __init__(self, version=None, endian=None, record=None):
        self. id = 'BPS'
        self.local_debug = False
        # Version
        if version==None or version=='V4' or version=='V3':
            if version==None: self.verson = 'V4'
            else: self.version = version
            self.info = '''
Begin Program Section Record
----------------------------

Function: 
    Marks the beginning of a new program section (or sequencer) in the job plan.
        
Frequency: 
    * Optional on each entry into the program segment.
        
Location: 
    Anywhere after the PIR and before the PRR.
'''    
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' :  'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' : None, 'Note' : ''},
                'REC_TYP'  : {'#' :  1, 'Type' :  'U*1', 'Ref' : None, 'Value' :   20, 'Text' : 'Record type                           ', 'Missing' : None, 'Note' : ''},
                'REC_SUB'  : {'#' :  2, 'Type' :  'U*1', 'Ref' : None, 'Value' :   10, 'Text' : 'Record sub-type                       ', 'Missing' : None, 'Note' : ''},
                'SEQ_NAME' : {'#' :  3, 'Type' :  'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Sequence name                         ', 'Missing' :   '', 'Note' : ''}
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)

class BRR(STDR):
    def __init__(self, version=None, endian=None, record=None):
        self. id = 'BRR'
        self.local_debug = False
        # Version
        if version==None or version=='V3':
            self.version = 'V3'
            self.info = '''
?!?
----------------------------

Function: 
    
        
Frequency: 
    
        
Location: 
    
'''    
            self.fields = {
                'REC_LEN'  : {'#' : 0, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' : None},
                'REC_TYP'  : {'#' : 1, 'Type' : 'U*1', 'Ref' : None, 'Value' :  220, 'Text' : 'Record type                           ', 'Missing' : None},
                'REC_SUB'  : {'#' : 2, 'Type' : 'U*1', 'Ref' : None, 'Value' :  201, 'Text' : 'Record sub-type                       ', 'Missing' : None},
                'RTST_COD' : {'#' : 3, 'Type' : 'C*1', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :  ' '},
                'BIN_CNT'  : {'#' : 4, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :    0},
                'BIN_NUM'  : {'#' : 5, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :    0}
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)

class BSR(STDR):
    def __init__(self, version=None, endian=None, record = None):
        self.id = 'BSR'
        self.local_debug = False
        if version==None or version=='V4':
            self.version = 'V4'
            self.info=    '''
Bit stream Specification Record (V4, Memory:2010.1)
---------------------------------------------------
    
Function: 
    This record is used to enable string bit stream data from the memories. 
    This record defines the format of the bit stream in which the data can be recorded in Memory Test Record (MTR). 
    The bit streams are stored as stream of clusters for compaction. i.e. only the data words that have meaningful 
    information are stored in the stream. Each cluster is defined as the starting address where the meaningful 
    information starts followed by the count of words with meaningful information followed by the words themselves.        

Frequency: 
    Once per memory Algorithm.

Location: 
    It can occur after all the Memory Model Records(MMRs) and before any Test specific records e.g. 
    Parametric Test Record (PTR), Functional Test Record (FTRs), Scan Test Record (STR) and Memory Test Record (MTRs).
'''
            self.fields = {
                'REC_LEN'  : {'#' : 0, 'Type' : 'U*2' , 'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' : None},
                'REC_TYP'  : {'#' : 1, 'Type' : 'U*1' , 'Ref' : None, 'Value' :    1, 'Text' : 'Record type                           ', 'Missing' : None},
                'REC_SUB'  : {'#' : 2, 'Type' : 'U*1' , 'Ref' : None, 'Value' :   97, 'Text' : 'Record sub-type                       ', 'Missing' : None},
                'BSR_IDX'  : {'#' : 3, 'Type' : 'U*2' , 'Ref' : None, 'Value' : None, 'Text' : 'Unique ID for this Bit stream         ', 'Missing' :    0},
                'BIT_TYP'  : {'#' : 4, 'Type' : 'U*1' , 'Ref' : None, 'Value' : None, 'Text' : 'Meaning of bits in the stream         ', 'Missing' :    0},
                'ADDR_SIZ' : {'#' : 5, 'Type' : 'U*1' , 'Ref' : None, 'Value' : None, 'Text' : 'Address field size [1,2,4 or 8]       ', 'Missing' :    0},
                'WC_SIZ'   : {'#' : 6, 'Type' : 'U*1' , 'Ref' : None, 'Value' : None, 'Text' : 'Word Count Field Size [1,2,4 or 8]    ', 'Missing' :    0},
                'WRD_SIZ'  : {'#' : 7, 'Type' : 'U*2' , 'Ref' : None, 'Value' : None, 'Text' : 'Number of bits used in the word field ', 'Missing' :    0}
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)
        
class CDR(STDR):
    def __init__(self, version=None, endian=None, record = None):
        self.id = 'CDR'
        self.local_debug = False
        if version==None or version=='V4':
            self.version = 'V4'
            self.info=    '''
Chain Description Record (V4-2007)
----------------------------------
    
Function: 
    This record contains the description of a scan chain in terms of its input, output, number of cell and clocks. 
    Each CDR record contains description of exactly one scan chain. Each CDR is uniquely identified by an index.            

Frequency: 
    ?!?
    
Location:
    ?!?
'''
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' : 'U*2',  'Ref' : None,       'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' : None},
                'REC_TYP'  : {'#' :  1, 'Type' : 'U*1',  'Ref' : None,       'Value' :    1, 'Text' : 'Record type                           ', 'Missing' : None},
                'REC_SUB'  : {'#' :  2, 'Type' : 'U*1',  'Ref' : None,       'Value' :   94, 'Text' : 'Record sub-type                       ', 'Missing' : None},
                'CONT_FLG' : {'#' :  3, 'Type' : 'B*1',  'Ref' : None,       'Value' : None, 'Text' : 'Continuation CDR record follow (if!=0)', 'Missing' : 0},
                'CDR_INDX' : {'#' :  4, 'Type' : 'U*2',  'Ref' : None,       'Value' : None, 'Text' : 'SCR Index                             ', 'Missing' : 0},
                'CHN_NAM'  : {'#' :  5, 'Type' : 'C*n',  'Ref' : None,       'Value' : None, 'Text' : 'Chain Name                            ', 'Missing' : None},
                'CHN_LEN'  : {'#' :  6, 'Type' : 'U*4',  'Ref' : None,       'Value' : None, 'Text' : 'Chain Length (cells in chain)         ', 'Missing' : 0},
                'SIN_PIN'  : {'#' :  7, 'Type' : 'U*2',  'Ref' : None,       'Value' : None, 'Text' : "PMR index of the chain's Scan In Sig  ", 'Missing' : 0},
                'SOUT_PIN' : {'#' :  8, 'Type' : 'U*2',  'Ref' : None,       'Value' : None, 'Text' : "PMR index of the chain's Scan Out Sig ", 'Missing' : 0},
                'MSTR_CNT' : {'#' :  9, 'Type' : 'U*1',  'Ref' : None,       'Value' : None, 'Text' : 'Count (m) of master clock pins        ', 'Missing' : 0},
                'M_CLKS'   : {'#' : 10, 'Type' : 'xU*2', 'Ref' : 'MSTR_CNT', 'Value' : None, 'Text' : 'Arr of PMR indses for the master clks ', 'Missing' : []},
                'SLAV_CNT' : {'#' : 11, 'Type' : 'U*1',  'Ref' : None,       'Value' : None, 'Text' : 'Count (n) of slave clock pins         ', 'Missing' : 0},
                'S_CLKS'   : {'#' : 12, 'Type' : 'xU*2', 'Ref' : 'SLAV_CNT', 'Value' : None, 'Text' : 'Arr of PMR indxes for the slave clks  ', 'Missing' : []},
                'INV_VAL'  : {'#' : 13, 'Type' : 'U*1',  'Ref' : None,       'Value' : None, 'Text' : '0: No Inversion, 1: Inversion         ', 'Missing' : 0},                                    
                'LST_CNT'  : {'#' : 14, 'Type' : 'U*2',  'Ref' : None,       'Value' : None, 'Text' : 'Count (k) of scan cells               ', 'Missing' : 0},
                'CELL_LST' : {'#' : 15, 'Type' : 'xS*n', 'Ref' : 'LST_CNT',  'Value' : None, 'Text' : 'Array of Scan Cell Names              ', 'Missing' : []},
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)
        
class CNR(STDR):
    def __init__(self, version=None, endian=None, record = None):
        self.id = 'CNR'
        self.local_debug = False
        if version==None or version=='V4':
            self.version = 'V4'
            self.info=    '''
Cell Name Record (V4-2007)
--------------------------
    
Function: 
    This record is used to store the mapping from Chain and Bit position to the Cell/FlipFlop name. 
    A CNR record should be created for each Cell for which a name mapping is required. 
    Typical usage would be to create a record for each failing cell/FlipFlop. 
    A CNR with new mapping for a chain and bit position would override the previous mapping.
            
Frequency: 
        
Location: 
'''
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' : 'U*2' , 'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' : None},
                'REC_TYP'  : {'#' :  1, 'Type' : 'U*1' , 'Ref' : None, 'Value' :    1, 'Text' : 'Record type                           ', 'Missing' : None},
                'REC_SUB'  : {'#' :  2, 'Type' : 'U*1' , 'Ref' : None, 'Value' :   92, 'Text' : 'Record sub-type                       ', 'Missing' : None},
                'CHN_NUM'  : {'#' :  2, 'Type' : 'U*2' , 'Ref' : None, 'Value' : None, 'Text' : 'Chain number. (cfr STR:CHN_NUM)       ', 'Missing' :    0},
                'BIT_POS'  : {'#' :  2, 'Type' : 'U*4' , 'Ref' : None, 'Value' : None, 'Text' : 'Bit position in the chain             ', 'Missing' :    0}, 
                'CELL_NAM' : {'#' :  2, 'Type' : 'S*n' , 'Ref' : None, 'Value' : None, 'Text' : 'Scan Cell Name                        ', 'Missing' :   ''}
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)
        
class DTR(STDR):
    def __init__(self, version=None, endian=None, record=None):
        self.id = 'DTR'
        self.local_debug = False
        # Version
        if version==None or version=='V4' or version=='V3':
            if version==None: self.version = 'V4'
            else: self.version = version
            self.info = '''
Datalog Text Record
-------------------

Function: 
    Contains text information that is to be included in the datalog printout. DTRs may be
    written under the control of a job plan: for example, to highlight unexpected test
    results. They may also be generated by the tester executive software: for example, to
    indicate that the datalog sampling rate has changed. DTRs are placed as comments in
    the datalog listing.

Frequency: 
    * Optional, a test data file may contain any number of DTRs.
        
Location: 
    Anywhere in the data stream after the initial "FAR-(ATRs)-MIR-(RDR)-(SDRs)" sequence.
'''    
            self.fields = {
                'REC_LEN'  : {'#' : 0, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' : None},
                'REC_TYP'  : {'#' : 1, 'Type' : 'U*1', 'Ref' : None, 'Value' :   50, 'Text' : 'Record type                           ', 'Missing' : None},
                'REC_SUB'  : {'#' : 2, 'Type' : 'U*1', 'Ref' : None, 'Value' :   30, 'Text' : 'Record sub-type                       ', 'Missing' : None},
                'TEXT_DAT' : {'#' : 3, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Message                               ', 'Missing' :   ''}
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)

class EPDR(STDR):
    def __init__(self, version=None, endian=None, record=None):
        self.id = 'EPDR'
        self.local_debug = False
        # Version
        if version==None or version=='V3':
            self.version = 'V3'
            self.info = '''
?!?
-------------------

Function: 
    ?!?
Frequency: 
    ?!?
        
Location: 
    ?!?
'''    
            self.fields = {
                'REC_LEN'  : {'#' : 0, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' :    None},
                'REC_TYP'  : {'#' : 1, 'Type' : 'U*1', 'Ref' : None, 'Value' :  220, 'Text' : 'Record type                           ', 'Missing' :    None},
                'REC_SUB'  : {'#' : 2, 'Type' : 'U*1', 'Ref' : None, 'Value' :  206, 'Text' : 'Record sub-type                       ', 'Missing' :    None},
                'TEST_NUM' : {'#' : 3, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :       0},
                'OPT_FLAG' : {'#' : 4, 'Type' : 'B*1', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' : ['0']*8},
                'CAT'      : {'#' : 5, 'Type' : 'C*2', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :    '  '},
                'TARGET'   : {'#' : 6, 'Type' : 'R*4', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :     0.0},
                'SPC_FLAG' : {'#' : 7, 'Type' : 'C*2', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :    '  '},
                'LVL'      : {'#' : 8, 'Type' : 'R*4', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :     0.0},
                'HVL'      : {'#' : 9, 'Type' : 'R*4', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :     0.0},
                'TEST_NAM' : {'#' :10, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :      ''}
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)

class EPS(STDR):
    def __init__(self, version=None, endian=None, record=None):
        self.id = 'EPS'
        self.local_debug = False
        # Version
        if version==None or version=='V4' or version=='V3':
            self.version = version
            self.info = '''
End Program Section Record
--------------------------

Function: 
    Marks the end of the current program section (or sequencer) in the job plan.
        
Frequency: 
    * Optional on each exit from the program segment.
        
Location: 
    Following the corresponding BPS and before the PRR in the data stream.
'''
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' :  'U*2', 'Ref' :         '', 'Value' :      0, 'Text' : 'Bytes of data following header        ', 'Missing' : 'N/A                    '},
                'REC_TYP'  : {'#' :  1, 'Type' :  'U*1', 'Ref' :         '', 'Value' :     20, 'Text' : 'Record type                           ', 'Missing' : '20                     '},
                'REC_SUB'  : {'#' :  2, 'Type' :  'U*1', 'Ref' :         '', 'Value' :     20, 'Text' : 'Record sub-type                       ', 'Missing' : '10                     '}
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)
        
class ETSR(STDR):
    def __init__(self, version=None, endian=None, record=None):
        self.id = 'ETSR'
        self.local_debug = False
        # Version
        if version==None or version=='V3':
            self.version = 'V3'
            self.info = '''
?!?
-------------------

Function: 
    ?!?
Frequency: 
    ?!?
        
Location: 
    ?!?
'''    
            self.fields = {
                'REC_LEN'    : {'#' :  0, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' :    None},
                'REC_TYP'    : {'#' :  1, 'Type' : 'U*1', 'Ref' : None, 'Value' :  220, 'Text' : 'Record type                           ', 'Missing' :    None},
                'REC_SUB'    : {'#' :  2, 'Type' : 'U*1', 'Ref' : None, 'Value' :  203, 'Text' : 'Record sub-type                       ', 'Missing' :    None},
                'TEST_NUM'   : {'#' :  3, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :       0},
                'EXEC_CNT'   : {'#' :  4, 'Type' : 'I*4', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :       0},
                'FAIL_CNT'   : {'#' :  5, 'Type' : 'I*4', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :       0},
                'ALRM_CNT'   : {'#' :  6, 'Type' : 'I*4', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :       0},
                'OPT_FLAG_QU': {'#' :  7, 'Type' : 'B*1', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' : ['0']*8},
                'TEST_05'    : {'#' :  8, 'Type' : 'R*4', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :     0.0},
                'TEST_10'    : {'#' :  9, 'Type' : 'R*4', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :     0.0},
                'TEST_50'    : {'#' : 10, 'Type' : 'R*4', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :     0.0},
                'TEST_90'    : {'#' : 11, 'Type' : 'R*4', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :     0.0},
                'TEST_95'    : {'#' : 12, 'Type' : 'R*4', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :     0.0},
                'OPT_FLAG'   : {'#' : 13, 'Type' : 'B*1', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' : ['0']*8},
                'PAD_BYTE'   : {'#' : 14, 'Type' : 'B*1', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' : ['0']*8},
                'TEST_MIN'   : {'#' : 15, 'Type' : 'R*4', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :     0.0},
                'TEST_MAX'   : {'#' : 16, 'Type' : 'R*4', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :     0.0},
                'TST_MEAN'   : {'#' : 17, 'Type' : 'R*4', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :     0.0},
                'TST_SDEV'   : {'#' : 18, 'Type' : 'R*4', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :     0.0},
                'TST_SUMS'   : {'#' : 19, 'Type' : 'R*4', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :     0.0},
                'TST_SQRS'   : {'#' : 20, 'Type' : 'R*4', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :     0.0},
                'TEST_NAM'   : {'#' : 21, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :      ''},
                'SEQ_NAME'   : {'#' : 22, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :      ''}
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)

class FAR(STDR):
    def __init__(self, version=None, endian=None, record=None):
        self.id = 'FAR'
        self.local_debug = False
        if version==None or version=='V4' or version=='V3':
            if version==None: self.version = 'V4'
            else: self.version = version
            self.info = ''' 
File Attributes Record 
----------------------

Function: 
    Contains the information necessary to determine how to decode the STDF data contained in the file.
                
Frequency:
    * Obligatory
    * One per datastream
                
Location: 
    First record of the STDF file
'''
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' :         None},
                'REC_TYP'  : {'#' :  1, 'Type' : 'U*1', 'Ref' : None, 'Value' :    0, 'Text' : 'Record type                           ', 'Missing' :         None},
                'REC_SUB'  : {'#' :  2, 'Type' : 'U*1', 'Ref' : None, 'Value' :   10, 'Text' : 'Record sub-type                       ', 'Missing' :         None},
                'CPU_TYPE' : {'#' :  3, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'CPU type that wrote this file         ', 'Missing' :    sys_cpu()},
                'STDF_VER' : {'#' :  4, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'STDF version number                   ', 'Missing' : self.version}
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)

class FDR(STDR):
    def __init__(self, version=None, endian=None, record = None):
        self.id = 'FDR'
        self.local_debug = False
        if version==None or version=='V3':
            self.version = 'V3'
            self.info=    '''
Functional Test Description Record
----------------------------------
    
Function: 
    ?!?
        
Frequency: 
    ?!?
    
Location: 
    ?!?
'''
            self.fields = {
                'REC_LEN'  : {'#' : 0, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' :    None},
                'REC_TYP'  : {'#' : 1, 'Type' : 'U*1', 'Ref' : None, 'Value' :   10, 'Text' : 'Record type                           ', 'Missing' :    None},
                'REC_SUB'  : {'#' : 2, 'Type' : 'U*1', 'Ref' : None, 'Value' :   20, 'Text' : 'Record sub-type                       ', 'Missing' :    None},
                'TEST_NUM' : {'#' : 3, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : 'Test number                           ', 'Missing' :       0},
                'DESC_FLG' : {'#' : 4, 'Type' : 'B*1', 'Ref' : None, 'Value' : None, 'Text' : 'Description flags                     ', 'Missing' : ['0']*8},
                'TEST_NAM' : {'#' : 5, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Test name                             ', 'Missing' :      ''},
                'SEQ_NAME' : {'#' : 6, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Sequencer (program segment/flow) name ', 'Missing' :      ''}
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)
        
class FSR(STDR):
    def __init__(self, version=None, endian=None, record = None):
        self.id = 'FSR'
        self.local_debug = False
        if version==None or version == 'V4':
            self.version = 'V4'
            self.info=    '''
Frame Specification Record (V4, Memory:2010.1) 
----------------------------------------------
    
Function:
    Frame Specification Record (FSR) is used to define a frame structure that can be used to store the fail data in a frame format. 
    In most of the embedded memory test architecture available in the industry, the data is communicated from the BIST controllers 
    to ATE in a serial frame format. Each vendor has its own frame format. So to deal with different frame format from various vendors
    the FSR allows encapsulating one or more specific frame definitions used within the STDF file. 
        
Frequency: 
    * Once per memory Algorithm
    
Location:
    It can occur after all the Memory Model Records(MMRs) and before any Test specific records e.g. Parametric Test Record (PTR), 
    Functional Test Record (FTRs), Scan Test Record (STR) and Memory Test Record (MTRs).
'''
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' : None},
                'REC_TYP'  : {'#' :  1, 'Type' : 'U*1', 'Ref' : None, 'Value' :    0, 'Text' : 'Record type                           ', 'Missing' : None},
                'REC_SUB'  : {'#' :  2, 'Type' : 'U*1', 'Ref' : None, 'Value' :   20, 'Text' : 'Record sub-type                       ', 'Missing' : None},
                'BSR_IDX'  : {'#' :  2, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Unique ID this Bit stream spec.       ', 'Missing' :    0},
                'BIT_TYP'  : {'#' :  2, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'Meaning of bits in the stream         ', 'Missing' :    0},
                'ADDR_SIZ' : {'#' :  2, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'Address field size [1,2,4 & 8] are ok ', 'Missing' :    0},
                'WC_SIZ'   : {'#' :  2, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'Word Count Field Size [1,2,4 & 8]     ', 'Missing' :    0},
                'WRD_SIZ'  : {'#' :  2, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Number of bits in word field          ', 'Missing' :    0}        
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)
        
class FTR(STDR):
    def __init__(self, version=None, endian=None, record=None):
        self.id = 'FTR'
        self.local_debug = False
        if version==None or version=='V4':
            self.version = 'V4'
            self.info = '''
Functional Test Record
----------------------

Function: 
    Contains the results of the single execution of a functional test in the test program. The
    first occurrence of this record also establishes the default values for all semi-static
    information about the test. The FTR is related to the Test Synopsis Record (TSR) by test
    number, head number, and site number.
        
Frequency: 
    * Obligatory, one or more for each execution of a functional test.
        
Location: 
    Anywhere in the data stream after the corresponding Part Information Record (PIR)
    and before the corresponding Part Result Record (PRR).    
'''    
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' : 'U*2',  'Ref' :       None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' :    None},
                'REC_TYP'  : {'#' :  1, 'Type' : 'U*1',  'Ref' :       None, 'Value' :   15, 'Text' : 'Record type                           ', 'Missing' :    None},
                'REC_SUB'  : {'#' :  2, 'Type' : 'U*1',  'Ref' :       None, 'Value' :   20, 'Text' : 'Record sub-type                       ', 'Missing' :    None},
                'TEST_NUM' : {'#' :  3, 'Type' : 'U*4',  'Ref' :       None, 'Value' : None, 'Text' : 'Test number                           ', 'Missing' :    None}, # Obligatory!
                'HEAD_NUM' : {'#' :  4, 'Type' : 'U*1',  'Ref' :       None, 'Value' : None, 'Text' : 'Test head number                      ', 'Missing' :       1},
                'SITE_NUM' : {'#' :  5, 'Type' : 'U*1',  'Ref' :       None, 'Value' : None, 'Text' : 'Test site number                      ', 'Missing' :       1},
                'TEST_FLG' : {'#' :  6, 'Type' : 'B*1',  'Ref' :       None, 'Value' : None, 'Text' : 'Test flags (fail, alarm, etc.)        ', 'Missing' : ['0']*8},
                'OPT_FLAG' : {'#' :  7, 'Type' : 'B*1',  'Ref' :       None, 'Value' : None, 'Text' : 'Optional data flag                    ', 'Missing' : ['1']*8},
                'CYCL_CNT' : {'#' :  8, 'Type' : 'U*4',  'Ref' :       None, 'Value' : None, 'Text' : 'Cycle count of vector                 ', 'Missing' :       0}, # OPT_FLAG bit0 = 1
                'REL_VADR' : {'#' :  9, 'Type' : 'U*4',  'Ref' :       None, 'Value' : None, 'Text' : 'Relative vector address               ', 'Missing' :       0}, # OPT_FLAG bit1 = 1
                'REPT_CNT' : {'#' : 10, 'Type' : 'U*4',  'Ref' :       None, 'Value' : None, 'Text' : 'Repeat count of vector                ', 'Missing' :       0}, # OPT_FLAG bit2 = 1
                'NUM_FAIL' : {'#' : 11, 'Type' : 'U*4',  'Ref' :       None, 'Value' : None, 'Text' : 'Number of pins with 1 or more failures', 'Missing' :       0}, # OPT_FLAG bit3 = 1
                'XFAIL_AD' : {'#' : 12, 'Type' : 'I*4',  'Ref' :       None, 'Value' : None, 'Text' : 'X logical device failure address      ', 'Missing' :       0}, # OPT_FLAG bit4 = 1
                'YFAIL_AD' : {'#' : 13, 'Type' : 'I*4',  'Ref' :       None, 'Value' : None, 'Text' : 'Y logical device failure address      ', 'Missing' :       0}, # OPT_FLAG bit4 = 1
                'VECT_OFF' : {'#' : 14, 'Type' : 'I*2',  'Ref' :       None, 'Value' : None, 'Text' : 'Offset from vector of interest        ', 'Missing' :       0}, # OPT_FLAG bit5 = 1
                'RTN_ICNT' : {'#' : 15, 'Type' : 'U*2',  'Ref' :       None, 'Value' : None, 'Text' : 'Count (j) of return data PMR indexes  ', 'Missing' :       0},
                'PGM_ICNT' : {'#' : 16, 'Type' : 'U*2',  'Ref' :       None, 'Value' : None, 'Text' : 'Count (k) of programmed state indexes ', 'Missing' :       0},
                'RTN_INDX' : {'#' : 17, 'Type' : 'xU*2', 'Ref' : 'RTN_ICNT', 'Value' : None, 'Text' : 'Array of j return data PMR indexes    ', 'Missing' :      []}, # RTN_ICNT = 0
                'RTN_STAT' : {'#' : 18, 'Type' : 'xN*1', 'Ref' : 'RTN_ICNT', 'Value' : None, 'Text' : 'Array of j returned states            ', 'Missing' :      []}, # RTN_ICNT = 0
                'PGM_INDX' : {'#' : 19, 'Type' : 'xU*2', 'Ref' : 'PGM_ICNT', 'Value' : None, 'Text' : 'Array of k programmed state indexes   ', 'Missing' :      []}, # PGM_ICNT = 0
                'PGM_STAT' : {'#' : 20, 'Type' : 'xN*1', 'Ref' : 'PGM_ICNT', 'Value' : None, 'Text' : 'Array of k programmed states          ', 'Missing' :      []}, # PGM_ICNT = 0
                'FAIL_PIN' : {'#' : 21, 'Type' : 'D*n',  'Ref' :       None, 'Value' : None, 'Text' : 'Failing pin bitfield                  ', 'Missing' :      []},
                'VECT_NAM' : {'#' : 22, 'Type' : 'C*n',  'Ref' :       None, 'Value' : None, 'Text' : 'Vector module pattern name            ', 'Missing' :      ''},
                'TIME_SET' : {'#' : 23, 'Type' : 'C*n',  'Ref' :       None, 'Value' : None, 'Text' : 'Time set name                         ', 'Missing' :      ''},    
                'OP_CODE'  : {'#' : 24, 'Type' : 'C*n',  'Ref' :       None, 'Value' : None, 'Text' : 'Vector Op Code                        ', 'Missing' :      ''},
                'TEST_TXT' : {'#' : 25, 'Type' : 'C*n',  'Ref' :       None, 'Value' : None, 'Text' : 'Descriptive text or label             ', 'Missing' :      ''},
                'ALARM_ID' : {'#' : 26, 'Type' : 'C*n',  'Ref' :       None, 'Value' : None, 'Text' : 'Name of alarm                         ', 'Missing' :      ''},
                'PROG_TXT' : {'#' : 27, 'Type' : 'C*n',  'Ref' :       None, 'Value' : None, 'Text' : 'Additional programmed information     ', 'Missing' :      ''},
                'RSLT_TXT' : {'#' : 28, 'Type' : 'C*n',  'Ref' :       None, 'Value' : None, 'Text' : 'Additional result information         ', 'Missing' :      ''},
                'PATG_NUM' : {'#' : 29, 'Type' : 'U*1',  'Ref' :       None, 'Value' : None, 'Text' : 'Pattern generator number              ', 'Missing' :    0xFF},
                'SPIN_MAP' : {'#' : 30, 'Type' : 'D*n',  'Ref' :       None, 'Value' : None, 'Text' : 'Bit map of enabled comparators        ', 'Missing' :      []}
            }
        elif version == 'V3':
            self.version = 'V3'
            self.info = '''
Functional Test Record
----------------------

Function: 
    Contains the results of the single execution of a functional test in the test program. The
    first occurrence of this record also establishes the default values for all semi-static
    information about the test. The FTR is related to the Test Synopsis Record (TSR) by test
    number, head number, and site number.
        
Frequency: 
    * Obligatory, one or more for each execution of a functional test.
        
Location: 
    Anywhere in the data stream after the corresponding Part Information Record (PIR)
    and before the corresponding Part Result Record (PRR).    
'''    
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' :    None},
                'REC_TYP'  : {'#' :  1, 'Type' : 'U*1', 'Ref' : None, 'Value' :   15, 'Text' : 'Record type                           ', 'Missing' :    None},
                'REC_SUB'  : {'#' :  2, 'Type' : 'U*1', 'Ref' : None, 'Value' :   20, 'Text' : 'Record sub-type                       ', 'Missing' :    None},
                'TEST_NUM' : {'#' :  3, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :    None}, # Obligatory
                'HEAD_NUM' : {'#' :  4, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :       0},
                'SITE_NUM' : {'#' :  5, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :       0},
                'TEST_FLG' : {'#' :  6, 'Type' : 'B*1', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' : ['0']*8},
                'DESC_FLG' : {'#' :  7, 'Type' : 'B*1', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' : ['0']*8},
                'OPT_FLAG' : {'#' :  8, 'Type' : 'B*1', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' : ['0']*8},
                'TIME_SET' : {'#' :  9, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :       0},
                'VECT_ADR' : {'#' : 10, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :       0},
                'CYCL_CNT' : {'#' : 11, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :       0},
                'REPT_CNT' : {'#' : 12, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :       0},
                'PCP_ADR'  : {'#' : 13, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :       0},
                'NUM_FAIL' : {'#' : 14, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :       0},
                'FAIL_PIN' : {'#' : 15, 'Type' : 'B*n', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :      []},
                'VECT_DAT' : {'#' : 16, 'Type' : 'B*n', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :      []},
                'DEV_DAT'  : {'#' : 17, 'Type' : 'B*n', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :      []},
                'RPIN_MAP' : {'#' : 18, 'Type' : 'B*n', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :      []},
                'TEST_NAM' : {'#' : 19, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :      ''},
                'SEQ_NAME' : {'#' : 20, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :      ''},
                'TEST_TXT' : {'#' : 21, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :      ''}
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)
        
class GDR(STDR):
    def __init__(self, version=None, endian=None, record=None):
        self.id = 'GDR'
        self.local_debug = False
        if version==None or version=='V4' or version=='V3':
            if version==None: self.version='V4'
            else: self.version=version 
            self.info = '''
Generic Data Record
-------------------

Function: 
    Contains information that does not conform to any other record type defined by the
    STDF specification. Such records are intended to be written under the control of job
    plans executing on the tester. This data may be used for any purpose that the user
    desires.
        
Frequency: 
    * Optional, a test data file may contain any number of GDRs.
        
Location: 
    Anywhere in the data stream after the initial "FAR-(ATRs)-MIR-(RDR)-(SDRs)" sequence.
'''
            self.fields = {
                'REC_LEN'  : {'#' : 0, 'Type' :  'U*2', 'Ref' :      None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' : None},
                'REC_TYP'  : {'#' : 1, 'Type' :  'U*1', 'Ref' :      None, 'Value' :   50, 'Text' : 'Record type                           ', 'Missing' : None},
                'REC_SUB'  : {'#' : 2, 'Type' :  'U*1', 'Ref' :      None, 'Value' :   10, 'Text' : 'Record sub-type                       ', 'Missing' : None},
                'FLD_CNT'  : {'#' : 3, 'Type' :  'U*2', 'Ref' :      None, 'Value' : None, 'Text' : 'Count of data fields in record        ', 'Missing' :    0},
                'GEN_DATA' : {'#' : 4, 'Type' : 'xV*n', 'Ref' : 'FLD_CNT', 'Value' : None, 'Text' : 'Data type code and data for one field ', 'Missing' :   []}
            }    
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)

class GTR(STDR):
    def __init__(self, version=None, endian=None, record=None):
        self.id = 'GTR'
        self.local_debug = False
        if version==None or version=='V3':
            self.version='V3'
            self.info = '''
?!?
-------------------

Function: 
        
Frequency: 
        
Location: 
'''
            self.fields = {
                'REC_LEN'   : {'#' : 0, 'Type' : 'U*2',  'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' :               None},
                'REC_TYP'   : {'#' : 1, 'Type' : 'U*1',  'Ref' : None, 'Value' :  220, 'Text' : 'Record type                           ', 'Missing' :               None},
                'REC_SUB'   : {'#' : 2, 'Type' : 'U*1',  'Ref' : None, 'Value' :  204, 'Text' : 'Record sub-type                       ', 'Missing' :               None},
                'TEXT_NAME' : {'#' : 3, 'Type' : 'C*16', 'Ref' : None, 'Value' : None, 'Text' : 'Count of data fields in record        ', 'Missing' : '                '},
                'TEXT_VAL'  : {'#' : 4, 'Type' : 'C*n',  'Ref' : None, 'Value' : None, 'Text' : 'Data type code and data for one field ', 'Missing' :                 ''}
            }    
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)

class HBR(STDR):
    def __init__(self, version=None, endian=None, record = None):
        self.id = 'HBR'
        self.local_debug = False
        if version==None or version == 'V4':
            self.version = 'V4'
            self.info = '''
Hardware Bin Record 
-------------------

Function:
    Stores a count of the parts "physically" placed in a particular bin after testing. (In
    wafer testing, "physical" binning is not an actual transfer of the DUT, but rather is
    represented by a drop of ink or an entry in a wafer map file.) This bin count can be for
    a single test site (when parallel testing) or a total for all test sites. The STDF
    specification also supports a Software Bin Record (SBR) for logical binning categories.
    A part is "physically" placed in a hardware bin after testing. A part can be "logically"
    associated with a software bin during or after testing.
        
Frequency:
    * One per hardware bin for each head/site combination. 
    * One per hardware bin for all heads/sites together ('HEAD_NUM' = 255)
    * May be included to name unused bins.
        
Location: 
    Anywhere in the data stream after the initial "FAR-(ATRs)-MIR-(RDR)-(SDRs)" sequence and before the MRR. 
    When data is being recorded in real time, this record usually appears near the end of the data stream.
'''
            self.fields = {
                'REC_LEN'  : {'#' : 0, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' :  None},
                'REC_TYP'  : {'#' : 1, 'Type' : 'U*1', 'Ref' : None, 'Value' :    1, 'Text' : 'Record type                           ', 'Missing' :  None},
                'REC_SUB'  : {'#' : 2, 'Type' : 'U*1', 'Ref' : None, 'Value' :   40, 'Text' : 'Record sub-type                       ', 'Missing' :  None},
                'HEAD_NUM' : {'#' : 3, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'Test head number                      ', 'Missing' :   255},
                'SITE_NUM' : {'#' : 4, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'Test site number                      ', 'Missing' :   255},
                'HBIN_NUM' : {'#' : 5, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Hardware bin number                   ', 'Missing' : 65535},
                'HBIN_CNT' : {'#' : 6, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : 'Number of parts in bin                ', 'Missing' :     0},
                'HBIN_PF'  : {'#' : 7, 'Type' : 'C*1', 'Ref' : None, 'Value' : None, 'Text' : 'Pass/fail indication (P/F)            ', 'Missing' :   ' '},
                'HBIN_NAM' : {'#' : 8, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Name of hardware bin                  ', 'Missing' :    ''}
            }
        elif version == 'V3':
            self.version = 'V3'
            self.info = '''
Hardware Bin Record 
-------------------

Function:
    Stores a count of the parts "physically" placed in a particular bin after testing. (In
    wafer testing, "physical" binning is not an actual transfer of the DUT, but rather is
    represented by a drop of ink or an entry in a wafer map file.) The STDF specification 
    also supports a Software Bin Record (SBR) for logical binning categories.
    A part is "physically" placed in a hardware bin after testing. A part can be "logically"
    associated with a software bin during or after testing.
        
Frequency:
    * One per hardware bin 
    * May be included to name unused bins.
        
Location: 
    Anywhere in the data stream after the initial "FAR-(ATRs)-MIR-(RDR)-(SDRs)" sequence and before the MRR. 
    When data is being recorded in real time, this record usually appears near the end of the data stream.
'''
            self.fields = {
                'REC_LEN'  : {'#' : 0, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' :  None},
                'REC_TYP'  : {'#' : 1, 'Type' : 'U*1', 'Ref' : None, 'Value' :    1, 'Text' : 'Record type                           ', 'Missing' :  None},
                'REC_SUB'  : {'#' : 2, 'Type' : 'U*1', 'Ref' : None, 'Value' :   40, 'Text' : 'Record sub-type                       ', 'Missing' :  None},
                'HBIN_NUM' : {'#' : 3, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Hardware bin number                   ', 'Missing' : 65535},
                'HBIN_CNT' : {'#' : 4, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : 'Number of parts in bin                ', 'Missing' :     0},
                'HBIN_NAM' : {'#' : 5, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Name of hardware bin                  ', 'Missing' :    ''}
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)

class IDR(STDR):
    def __init__(self, version=None, endian=None, record = None):
        self.id = 'IDR'
        self.local_debug = False
        if version==None or version=='V4':
            self.version = 'V4'
            self.info=    '''
Instance Description Record (V4, Memory:2010.1)
-----------------------------------------------
    
Function: 
    This record is used to store the information for a memory instance within a design. It contains a
    reference to the model records which define the design information for this specific memory instance.
    
Frequency: 
    * Once per memory instance
    
Location:
    It can occur after all the Memory Controller Records(MCRs) and before Memory Model Records (MMRs) 
'''
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' : None},
                'REC_TYP'  : {'#' :  1, 'Type' : 'U*1', 'Ref' : None, 'Value' :    0, 'Text' : 'Record type                           ', 'Missing' : None},
                'REC_SUB'  : {'#' :  2, 'Type' : 'U*1', 'Ref' : None, 'Value' :   20, 'Text' : 'Record sub-type                       ', 'Missing' : None},
                'INST_IDX' : {'#' :  3, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Unique index of this IDR              ', 'Missing' : None}, # Obligatory
                'INST_NAM' : {'#' :  4, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Name of the Instance                  ', 'Missing' :   ''},
                'REF_COD'  : {'#' :  5, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : '0=Wafer Notch based, 1=Pkg ref        ', 'Missing' : None},
                'ORNT_COD' : {'#' :  6, 'Type' : 'C*2', 'Ref' : None, 'Value' : None, 'Text' : 'Orientation of Instance               ', 'Missing' : '  '},
                'MDL_FILE' : {'#' :  7, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Pointer to file describing model      ', 'Missing' :   ''},
                'MDL_REF'  : {'#' :  8, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Reference to the model record         ', 'Missing' : None}
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)

class MCR(STDR):
    def __init__(self, version=None, endian=None, record = None):
        self.id = 'MCR'
        self.local_debug = False
        if version == 'V4':
            self.version = version
            self.info=    '''
Memory Controller Record (V4, Memory:2010.1)
--------------------------------------------
    
Function: 
    This record is used to store information about an embedded memory controller in a design. 
    There is one MCR record in an STDF file for each controller in a design. 
    These records are referenced by the top level Memory Structure Record (MSR) through its CTRL_LST field.
    
Frequency: 
    * Once per controller in the design.
    
Location:
    It can occur after all the Memory Structure Records(MSRs) and before Instance Description Records (IDRs) 
'''
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' : 'U*2' , 'Ref' :       None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' : None},
                'REC_TYP'  : {'#' :  1, 'Type' : 'U*1' , 'Ref' :       None, 'Value' :    1, 'Text' : 'Record type                           ', 'Missing' : None},
                'REC_SUB'  : {'#' :  2, 'Type' : 'U*1' , 'Ref' :       None, 'Value' :  100, 'Text' : 'Record sub-type                       ', 'Missing' : None},
                'CTRL_IDX' : {'#' :  3, 'Type' : 'U*2' , 'Ref' :       None, 'Value' : None, 'Text' : 'Index of this memory controller record', 'Missing' : None},
                'CTRL_NAM' : {'#' :  4, 'Type' : 'C*n' , 'Ref' :       None, 'Value' : None, 'Text' : 'Name of the controller                ', 'Missing' :   ''},
                'MDL_FILE' : {'#' :  5, 'Type' : 'C*n' , 'Ref' :       None, 'Value' : None, 'Text' : 'Pointer to the file describing model  ', 'Missing' :   ''},
                'INST_CNT' : {'#' :  6, 'Type' : 'U*2' , 'Ref' :       None, 'Value' : None, 'Text' : 'Count of INST_INDX array              ', 'Missing' :    0},
                'INST_LST' : {'#' :  7, 'Type' : 'xU*2', 'Ref' : 'INST_CNT', 'Value' : None, 'Text' : 'Array of memory instance indexes      ', 'Missing' :   []}
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)
            
class MIR(STDR):
    def __init__(self, version=None, endian=None, record = None):
        self.id = 'MIR'
        self.local_debug = False
        if version==None or version=='V4':
            self.version ='V4'
            self.info = '''
Master Information Record 
-------------------------

Function: 
    The MIR and the MRR (Master Results Record) contain all the global information that
    is to be stored for a tested lot of parts. Each data stream must have exactly one MIR,
    immediately after the FAR (and the ATRs, if they are used). This will allow any data
    reporting or analysis programs access to this information in the shortest possible
    amount of time.
        
Frequency: 
    * Obligatory 
    * One per data stream.

Location: 
    Immediately after the File Attributes Record (FAR) and the Audit Trail Records (ATR),
    if ATRs are used.    
'''
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' : 'U*2', 'Ref' : None, 'Value' :    0, 'Text' : 'Bytes of data following header        ', 'Missing' :       None},
                'REC_TYP'  : {'#' :  1, 'Type' : 'U*1', 'Ref' : None, 'Value' :    1, 'Text' : 'Record type                           ', 'Missing' :       None},
                'REC_SUB'  : {'#' :  2, 'Type' : 'U*1', 'Ref' : None, 'Value' :   10, 'Text' : 'Record sub-type                       ', 'Missing' :       None},
                'SETUP_T'  : {'#' :  3, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : 'Date and time of job setup            ', 'Missing' :  'START_T'},
                'START_T'  : {'#' :  4, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : 'Date and time first part tested       ', 'Missing' : DT().epoch},
                'STAT_NUM' : {'#' :  5, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'Tester station number                 ', 'Missing' :          0},
                'MODE_COD' : {'#' :  6, 'Type' : 'C*1', 'Ref' : None, 'Value' : None, 'Text' : 'Test mode code : A/M/P/E/M/P/Q/space  ', 'Missing' :        ' '},
                'RTST_COD' : {'#' :  7, 'Type' : 'C*1', 'Ref' : None, 'Value' : None, 'Text' : 'Lot retest code : Y/N/0..9/space      ', 'Missing' :        ' '},
                'PROT_COD' : {'#' :  8, 'Type' : 'C*1', 'Ref' : None, 'Value' : None, 'Text' : 'Data protection code 0..9/A..Z/space  ', 'Missing' :        ' '},
                'BURN_TIM' : {'#' :  9, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Burn-in time (in minutes)             ', 'Missing' :      65535},
                'CMOD_COD' : {'#' : 10, 'Type' : 'C*1', 'Ref' : None, 'Value' : None, 'Text' : 'Command mode code                     ', 'Missing' :        ' '},
                'LOT_ID'   : {'#' : 11, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Lot ID (customer specified)           ', 'Missing' :         ''},
                'PART_TYP' : {'#' : 12, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Part Type (or product ID)             ', 'Missing' :         ''},
                'NODE_NAM' : {'#' : 13, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Name of node that generated data      ', 'Missing' :         ''},
                'TSTR_TYP' : {'#' : 14, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Tester type                           ', 'Missing' :         ''},
                'JOB_NAM'  : {'#' : 15, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Job name (test program name)          ', 'Missing' :         ''},
                'JOB_REV'  : {'#' : 16, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Job (test program) revision number    ', 'Missing' :         ''},
                'SBLOT_ID' : {'#' : 17, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Sublot ID                             ', 'Missing' :         ''},
                'OPER_NAM' : {'#' : 18, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Operator name or ID (at setup time)   ', 'Missing' :         ''},
                'EXEC_TYP' : {'#' : 19, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Tester executive software type        ', 'Missing' :         ''},
                'EXEC_VER' : {'#' : 20, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Tester exec software version number   ', 'Missing' :         ''},
                'TEST_COD' : {'#' : 21, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Test phase or step code               ', 'Missing' :         ''},
                'TST_TEMP' : {'#' : 22, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Test temperature                      ', 'Missing' :         ''},
                'USER_TXT' : {'#' : 23, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Generic user text                     ', 'Missing' :         ''},
                'AUX_FILE' : {'#' : 24, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Name of auxiliary data file           ', 'Missing' :         ''},
                'PKG_TYP'  : {'#' : 25, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Package type                          ', 'Missing' :         ''},
                'FAMLY_ID' : {'#' : 26, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Product family ID                     ', 'Missing' :         ''},
                'DATE_COD' : {'#' : 27, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Date code                             ', 'Missing' :         ''},
                'FACIL_ID' : {'#' : 28, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Test facility ID                      ', 'Missing' :         ''},
                'FLOOR_ID' : {'#' : 29, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Test floor ID                         ', 'Missing' :         ''},
                'PROC_ID'  : {'#' : 30, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Fabrication process ID                ', 'Missing' :         ''},
                'OPER_FRQ' : {'#' : 31, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Operation frequency or step           ', 'Missing' :         ''},
                'SPEC_NAM' : {'#' : 32, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Test specification name               ', 'Missing' :         ''},
                'SPEC_VER' : {'#' : 33, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Test specification version number     ', 'Missing' :         ''},
                'FLOW_ID'  : {'#' : 34, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Test flow ID                          ', 'Missing' :         ''},
                'SETUP_ID' : {'#' : 35, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Test setup ID                         ', 'Missing' :         ''},
                'DSGN_REV' : {'#' : 36, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Device design revision                ', 'Missing' :         ''},
                'ENG_ID'   : {'#' : 37, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Engineering lot ID                    ', 'Missing' :         ''},
                'ROM_COD'  : {'#' : 38, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'ROM code ID                           ', 'Missing' :         ''},
                'SERL_NUM' : {'#' : 39, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Tester serial number                  ', 'Missing' :         ''},
                'SUPR_NAM' : {'#' : 40, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Supervisor name or ID                 ', 'Missing' :         ''}
            }
        elif version == 'V3':
            self.version = 'V3'
            self.info =     '''
Master Information Record 
-------------------------

Function: 
    The MIR and the MRR (Master Results Record) contain all the global information that
    is to be stored for a tested lot of parts. Each data stream must have exactly one MIR,
    immediately after the FAR (and the ATRs, if they are used). This will allow any data
    reporting or analysis programs access to this information in the shortest possible
    amount of time.
        
Frequency: 
    * Obligatory 
    * One per data stream.

Location: 
    In the beginning of the file, or after the File Attributes Record (FAR).
'''
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' : 'U*2', 'Ref' : None, 'Value' :    0, 'Text' : 'Bytes of data following header        ', 'Missing' :         None},
                'REC_TYP'  : {'#' :  1, 'Type' : 'U*1', 'Ref' : None, 'Value' :    1, 'Text' : 'Record type                           ', 'Missing' :         None},
                'REC_SUB'  : {'#' :  2, 'Type' : 'U*1', 'Ref' : None, 'Value' :   10, 'Text' : 'Record sub-type                       ', 'Missing' :         None},
                'CPU_TYPE' : {'#' :  3, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'CPU type that wrote this file         ', 'Missing' :    sys_cpu()},
                'STDF_VER' : {'#' :  4, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'STDF version number                   ', 'Missing' : self.version},
                'MODE_COD' : {'#' :  5, 'Type' : 'C*1', 'Ref' : None, 'Value' : None, 'Text' : 'Test mode code : A/M/P/E/M/P/Q/space  ', 'Missing' :          ' '},
                'STAT_NUM' : {'#' :  6, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'Tester station number                 ', 'Missing' :            0},
                'TEST_COD' : {'#' :  7, 'Type' : 'C*3', 'Ref' : None, 'Value' : None, 'Text' : 'Test phase or step code               ', 'Missing' :        '   '},
                'RTST_COD' : {'#' :  8, 'Type' : 'C*1', 'Ref' : None, 'Value' : None, 'Text' : 'Lot retest code : Y/N/0..9/space      ', 'Missing' :          ' '},
                'PROT_COD' : {'#' :  9, 'Type' : 'C*1', 'Ref' : None, 'Value' : None, 'Text' : 'Data protection code 0..9/A..Z/space  ', 'Missing' :          ' '},
                'CMOD_COD' : {'#' : 10, 'Type' : 'C*1', 'Ref' : None, 'Value' : None, 'Text' : 'Command mode code                     ', 'Missing' :          ' '},
                'SETUP_T'  : {'#' : 11, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : 'Date and time of job setup            ', 'Missing' :    'START_T'},
                'START_T'  : {'#' : 12, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : 'Date and time first part tested       ', 'Missing' :   DT().epoch},
                'LOT_ID'   : {'#' : 13, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Lot ID (customer specified)           ', 'Missing' :           ''},
                'PART_TYP' : {'#' : 14, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Part Type (or product ID)             ', 'Missing' :           ''},
                'JOB_NAM'  : {'#' : 15, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Job name (test program name)          ', 'Missing' :           ''},
                'OPER_NAM' : {'#' : 16, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Operator name or ID (at setup time)   ', 'Missing' :           ''},
                'NODE_NAM' : {'#' : 17, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Name of node that generated data      ', 'Missing' :           ''},
                'TSTR_TYP' : {'#' : 18, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Tester type                           ', 'Missing' :           ''},
                'EXEC_TYP' : {'#' : 19, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Tester executive software type        ', 'Missing' :           ''},
                'SUPR_NAM' : {'#' : 20, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Supervisor name or ID                 ', 'Missing' :           ''},
                'HAND_ID'  : {'#' : 21, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Handler or prober ID                  ', 'Missing' :           ''},
                'SBLOT_ID' : {'#' : 22, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Sublot ID                             ', 'Missing' :           ''},
                'JOB_REV'  : {'#' : 23, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Job (test program) revision number    ', 'Missing' :           ''},
                'PROC_ID'  : {'#' : 24, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Fabrication process ID                ', 'Missing' :           ''},
                'PRB_CARD' : {'#' : 25, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Probe Card ID                         ', 'Missing' :           ''}
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)

class MMR(STDR):
    def __init__(self, version=None, endian=None, record = None):
        self.id = 'MMR'
        self.local_debug = False
        if version==None or version=='V4':
            self.version = 'V4'
            self.info=    '''
Memory Model Record (V4, Memory:2010.1)
---------------------------------------
    
Function: 
    This record is used to store the memory model information in STDF. 
    The record allows storing the logic level information of the model. 
    It does not have any fields to store the physical information except height and width. 
    The physical information can be optionally linked to the record through a reference to the file.

Frequency: 
    Once per memory model.

Location:
    It can occur after all the Instance Description Records(IDRs) and before any Frame Specification Records (FSRs), 
    Bit Stream Specification Records (BSRs) and any Test specific records e.g. Parametric Test Record (PTR), 
    Functional Test Record (FTRs), Scan Test Record (STR) and Memory Test Record (MTRs).
'''
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' : 'U*2',  'Ref' :       None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' : None},
                'REC_TYP'  : {'#' :  1, 'Type' : 'U*1',  'Ref' :       None, 'Value' :    1, 'Text' : 'Record type                           ', 'Missing' : None},
                'REC_SUB'  : {'#' :  2, 'Type' : 'U*1',  'Ref' :       None, 'Value' :   95, 'Text' : 'Record sub-type                       ', 'Missing' : None},
                'ASR_IDX'  : {'#' :  3, 'Type' : 'U*2',  'Ref' :       None, 'Value' : None, 'Text' : 'Unique identifier for this ASR record ', 'Missing' : None},
                'STRT_IDX' : {'#' :  4, 'Type' : 'U*1',  'Ref' :       None, 'Value' : None, 'Text' : 'Cycle Start index flag                ', 'Missing' : None},
                'ALGO_CNT' : {'#' :  5, 'Type' : 'U*1',  'Ref' :       None, 'Value' : None, 'Text' : 'count (k) of Algorithms descriptions  ', 'Missing' :    0},
                'ALGO_NAM' : {'#' :  6, 'Type' : 'xC*n', 'Ref' : 'ALGO_CNT', 'Value' : None, 'Text' : 'Array of Names Name of the Algorithm  ', 'Missing' :   []},
                'ALGO_LEN' : {'#' :  7, 'Type' : 'xC*n', 'Ref' : 'ALGO_CNT', 'Value' : None, 'Text' : 'Array of Complexity of algorithm      ', 'Missing' :   []},
                'FILE_ID'  : {'#' :  8, 'Type' : 'xC*n', 'Ref' : 'ALGO_CNT', 'Value' : None, 'Text' : 'Array of Name of the file with descr. ', 'Missing' :   []},
                'CYC_BGN'  : {'#' :  9, 'Type' : 'xU*8', 'Ref' : 'ALGO_CNT', 'Value' : None, 'Text' : 'Array of Starting cycle number        ', 'Missing' :   []},
                'CYC_END'  : {'#' : 10, 'Type' : 'xU*8', 'Ref' : 'ALGO_CNT', 'Value' : None, 'Text' : 'Array of End Cycle number             ', 'Missing' :   []}
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)

class MPR(STDR):
    def __init__(self, version=None, endian=None, record=None):
        self.id = 'MPR'
        self.local_debug = False
        if version==None or version == 'V4':
            self.version ='V4'
            self.info = '''
Multiple-Result Parametric Record
---------------------------------

Function: 
    Contains the results of a single execution of a parametric test in the test program
    where that test returns multiple values. The first occurrence of this record also
    establishes the default values for all semi-static information about the test, such as
    limits, units, and scaling. The MPR is related to the Test Synopsis Record (TSR) by test
    number, head number, and site number.
        
Frequency: 
    * Obligatory, one per multiple-result parametric test execution on each head/site
        
Location: 
    Anywhere in the data stream after the corresponding Part Information Record (PIR)
    and before the corresponding Part Result Record (PRR).
'''
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' : 'U*2',  'Ref' :       None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' :                                     None},
                'REC_TYP'  : {'#' :  1, 'Type' : 'U*1',  'Ref' :       None, 'Value' :   15, 'Text' : 'Record type                           ', 'Missing' :                                     None},
                'REC_SUB'  : {'#' :  2, 'Type' : 'U*1',  'Ref' :       None, 'Value' :   15, 'Text' : 'Record sub-type                       ', 'Missing' :                                     None},        
                'TEST_NUM' : {'#' :  3, 'Type' : 'U*4',  'Ref' :       None, 'Value' : None, 'Text' : 'Test number                           ', 'Missing' :                                     None},
                'HEAD_NUM' : {'#' :  4, 'Type' : 'U*1',  'Ref' :       None, 'Value' : None, 'Text' : 'Test head number                      ', 'Missing' :                                        1},
                'SITE_NUM' : {'#' :  5, 'Type' : 'U*1',  'Ref' :       None, 'Value' : None, 'Text' : 'Test site number                      ', 'Missing' :                                        1},
                'TEST_FLG' : {'#' :  6, 'Type' : 'B*1',  'Ref' :       None, 'Value' : None, 'Text' : 'Test flags (fail, alarm, etc.)        ', 'Missing' :                                  ['0']*8},
                'PARM_FLG' : {'#' :  7, 'Type' : 'B*1',  'Ref' :       None, 'Value' : None, 'Text' : 'Parametric test flags (drift, etc.)   ', 'Missing' : ['1', '1', '0', '0', '0', '0', '0', '0']}, # 0xC0
                'RTN_ICNT' : {'#' :  8, 'Type' : 'U*2',  'Ref' :       None, 'Value' : None, 'Text' : 'Count (j) of PMR indexes              ', 'Missing' :                                        0},
                'RSLT_CNT' : {'#' :  9, 'Type' : 'U*2',  'Ref' :       None, 'Value' : None, 'Text' : 'Count (k) of returned results         ', 'Missing' :                                        0},
                'RTN_STAT' : {'#' : 10, 'Type' : 'xN*1', 'Ref' : 'RTN_ICNT', 'Value' : None, 'Text' : 'Array of j returned states            ', 'Missing' :                                       []}, # RTN_ICNT = 0
                'RTN_RSLT' : {'#' : 11, 'Type' : 'xR*4', 'Ref' : 'RSLT_CNT', 'Value' : None, 'Text' : 'Array of k returned results           ', 'Missing' :                                       []}, # RSLT_CNT = 0
                'TEST_TXT' : {'#' : 12, 'Type' : 'C*n',  'Ref' :       None, 'Value' : None, 'Text' : 'Descriptive text or label             ', 'Missing' :                                       ''},
                'ALARM_ID' : {'#' : 13, 'Type' : 'C*n',  'Ref' :       None, 'Value' : None, 'Text' : 'Name of alarm                         ', 'Missing' :                                       ''},
                'OPT_FLAG' : {'#' : 14, 'Type' : 'B*1',  'Ref' :       None, 'Value' : None, 'Text' : 'Optional data flag See note           ', 'Missing' : ['0', '0', '0', '0', '0', '0', '1', '0']}, # 0x02
                'RES_SCAL' : {'#' : 15, 'Type' : 'I*1',  'Ref' :       None, 'Value' : None, 'Text' : 'Test result scaling exponent          ', 'Missing' :                                        0}, # OPT_FLAG bit 0 = 1
                'LLM_SCAL' : {'#' : 16, 'Type' : 'I*1',  'Ref' :       None, 'Value' : None, 'Text' : 'Test low limit scaling exponent       ', 'Missing' :                                        0}, # OPT_FLAG bit 4 or 6 = 1
                'HLM_SCAL' : {'#' : 17, 'Type' : 'I*1',  'Ref' :       None, 'Value' : None, 'Text' : 'Test high limit scaling exponent      ', 'Missing' :                                        0}, # OPT_FLAG bit 5 or 7 = 1
                'LO_LIMIT' : {'#' : 18, 'Type' : 'R*4',  'Ref' :       None, 'Value' : None, 'Text' : 'Test low limit value                  ', 'Missing' :                                      0.0}, # OPT_FLAG bit 4 or 6 = 1
                'HI_LIMIT' : {'#' : 19, 'Type' : 'R*4',  'Ref' :       None, 'Value' : None, 'Text' : 'Test high limit value                 ', 'Missing' :                                      0.0}, # OPT_FLAG bit 5 or 7 = 1
                'START_IN' : {'#' : 20, 'Type' : 'R*4',  'Ref' :       None, 'Value' : None, 'Text' : 'Starting input value [condition]      ', 'Missing' :                                      0.0}, # OPT_FLAG bit 1 = 1
                'INCR_IN'  : {'#' : 21, 'Type' : 'R*4',  'Ref' :       None, 'Value' : None, 'Text' : 'Increment of input condition          ', 'Missing' :                                       -1}, # OPT_FLAG bit 1 = 1
                'RTN_INDX' : {'#' : 22, 'Type' : 'xU*2', 'Ref' : 'RTN_ICNT', 'Value' : None, 'Text' : 'Array of j PMR indexes                ', 'Missing' :                                       []}, # RTN_ICNT = 0
                'UNITS'    : {'#' : 23, 'Type' : 'C*n',  'Ref' :       None, 'Value' : None, 'Text' : 'Units of returned results             ', 'Missing' :                                       ''},
                'UNITS_IN' : {'#' : 24, 'Type' : 'C*n',  'Ref' :       None, 'Value' : None, 'Text' : 'Input condition units                 ', 'Missing' :                                       ''},
                'C_RESFMT' : {'#' : 25, 'Type' : 'C*n',  'Ref' :       None, 'Value' : None, 'Text' : 'ANSI C result format string           ', 'Missing' :                                       ''},
                'C_LLMFMT' : {'#' : 26, 'Type' : 'C*n',  'Ref' :       None, 'Value' : None, 'Text' : 'ANSI C low limit format string        ', 'Missing' :                                       ''},
                'C_HLMFMT' : {'#' : 27, 'Type' : 'C*n',  'Ref' :       None, 'Value' : None, 'Text' : 'ANSI C high limit format string       ', 'Missing' :                                       ''},
                'LO_SPEC'  : {'#' : 28, 'Type' : 'R*4',  'Ref' :       None, 'Value' : None, 'Text' : 'Low specification limit value         ', 'Missing' :                                      0.0}, # OPT_FLAG bit 2 = 1
                'HI_SPEC'  : {'#' : 29, 'Type' : 'R*4',  'Ref' :       None, 'Value' : None, 'Text' : 'High specification limit value        ', 'Missing' :                                      0.0}  # OPT_FLAG bit 3 = 1    
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)

class MRR(STDR):
    def __init__(self, version=None, endian=None, record = None):
        self.id = 'MRR'
        self.local_debug = False
        if version==None or version=='V4':
            self.version = 'V4'
            self.info =     '''
Master Results Record 
---------------------

Function: 
    The Master Results Record (MRR) is a logical extension of the Master Information
    Record (MIR). The data can be thought of as belonging with the MIR, but it is not
    available when the tester writes the MIR information. Each data stream must have
    exactly one MRR as the last record in the data stream.
        
Frequency: 
    * Obligatory
    * One per data stream
        
Location: 
    Must be the last record in the data stream.
'''
            self.fields = {
                'REC_LEN'  : {'#' : 0, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' :       None}, 
                'REC_TYP'  : {'#' : 1, 'Type' : 'U*1', 'Ref' : None, 'Value' :    1, 'Text' : 'Record type                           ', 'Missing' :       None},
                'REC_SUB'  : {'#' : 2, 'Type' : 'U*1', 'Ref' : None, 'Value' :   20, 'Text' : 'Record sub-type                       ', 'Missing' :       None},
                'FINISH_T' : {'#' : 3, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : 'Date and time last part tested        ', 'Missing' : DT().epoch},
                'DISP_COD' : {'#' : 4, 'Type' : 'C*1', 'Ref' : None, 'Value' : None, 'Text' : 'Lot disposition code                  ', 'Missing' :        ' '},
                'USR_DESC' : {'#' : 5, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Lot description supplied by user      ', 'Missing' :         ''},
                'EXC_DESC' : {'#' : 6, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Lot description supplied by exec      ', 'Missing' :         ''}
            }
        elif version == 'V3':
            self.version = 'V3'
            self.info =     '''
Master Results Record 
---------------------

Function: 
    The Master Results Record (MRR) is a logical extension of the Master Information
    Record (MIR). The data can be thought of as belonging with the MIR, but it is not
    available when the tester writes the MIR information. Each data stream must have
    exactly one MRR as the last record in the data stream.
        
Frequency: 
    * Obligatory
    * One per data stream
        
Location: 
    Must be the last record in the data stream.
'''
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' :       None}, 
                'REC_TYP'  : {'#' :  1, 'Type' : 'U*1', 'Ref' : None, 'Value' :    1, 'Text' : 'Record type                           ', 'Missing' :       None},
                'REC_SUB'  : {'#' :  2, 'Type' : 'U*1', 'Ref' : None, 'Value' :   20, 'Text' : 'Record sub-type                       ', 'Missing' :       None},
                'FINISH_T' : {'#' :  3, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : 'Date and time last part tested        ', 'Missing' : DT().epoch},
                'PART_CNT' : {'#' :  4, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : 'Number of parts tested                ', 'Missing' :          0},
                'RTST_CNT' : {'#' :  5, 'Type' : 'I*4', 'Ref' : None, 'Value' : None, 'Text' : 'Number of parts retested              ', 'Missing' :          0},
                'ABRT_CNT' : {'#' :  6, 'Type' : 'I*4', 'Ref' : None, 'Value' : None, 'Text' : 'Number of parts aborted               ', 'Missing' :          0},
                'GOOD_CNT' : {'#' :  7, 'Type' : 'I*4', 'Ref' : None, 'Value' : None, 'Text' : 'Number of good parts                  ', 'Missing' :          0},
                'FUNC_CNT' : {'#' :  8, 'Type' : 'I*4', 'Ref' : None, 'Value' : None, 'Text' : 'Number of good functional parts       ', 'Missing' :          0},
                'DISP_COD' : {'#' :  9, 'Type' : 'C*1', 'Ref' : None, 'Value' : None, 'Text' : 'Lot disposition code                  ', 'Missing' :        ' '},
                'USR_DESC' : {'#' : 10, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Lot description supplied by user      ', 'Missing' :         ''},
                'EXC_DESC' : {'#' : 11, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Lot description supplied by exec      ', 'Missing' :         ''}
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)
            
class MSR(STDR):
    def __init__(self, version=None, endian=None, record = None):
        self.id = 'MSR'
        self.local_debug = False
        if version == 'V4':
            self.version = 'V4'
            self.info=    '''
Memory Structure Record (V4, Memory:2010.1)
-------------------------------------------
    
Function: 
    This record is the top level record for storing Memory design information. 
    It supports both the direct access memories as well as the embedded memories controlled by 
    embedded controllers. For embedded memories it contains the references to the controllers 
    and for direct access memories it contains the references to the memory instances.
            
Frequency: 
    * One for each STDF file for a design
    
Location:
    It can occur anytime after Retest Data Record (RDR) if no Site Description Record(s) 
    are present, otherwise after all the SDRs. This record must occur before Memory Controller 
    Records (MCRs) and Instance Description Records (IDRs) 
'''
            self.fields = {
                'REC_LEN'  : {'#' : 0, 'Type' :  'U*2', 'Ref' :       None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' : None},
                'REC_TYP'  : {'#' : 1, 'Type' :  'U*1', 'Ref' :       None, 'Value' :    1, 'Text' : 'Record type                           ', 'Missing' : None},
                'REC_SUB'  : {'#' : 2, 'Type' :  'U*1', 'Ref' :       None, 'Value' :   99, 'Text' : 'Record sub-type                       ', 'Missing' : None},
                'NAME'     : {'#' : 3, 'Type' :  'C*n', 'Ref' :       None, 'Value' : None, 'Text' : 'Name of the design under test         ', 'Missing' :   ''},
                'FILE_NAM' : {'#' : 4, 'Type' :  'C*n', 'Ref' :       None, 'Value' : None, 'Text' : 'Filename containing design information', 'Missing' :   ''},
                'CTRL_CNT' : {'#' : 5, 'Type' :  'U*2', 'Ref' :       None, 'Value' : None, 'Text' : 'Count (k) of controllers in the design', 'Missing' :    0},
                'CTRL_LST' : {'#' : 6, 'Type' : 'xU*2', 'Ref' : 'CTRL_CNT', 'Value' : None, 'Text' : 'Array of controller record indexes    ', 'Missing' :   []},
                'INST_CNT' : {'#' : 7, 'Type' :  'U*2', 'Ref' :       None, 'Value' : None, 'Text' : 'Count(m) of Top level memory instances', 'Missing' :    0},
                'INST_LST' : {'#' : 8, 'Type' : 'xU*2', 'Ref' : 'INST_CNT', 'Value' : None, 'Text' : 'Array of Instance record indexes      ', 'Missing' :   []}
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)
            
class MTR(STDR):
    def __init__(self, version=None, endian=None, record=None,  BSR__ADDR_SIZ=None, BSR__WC_SIZ=None):
        self.id = 'MTR'
        self.local_debug = False
        if version == 'V4':
            self.version = version
            self.info=    '''
Memory Test Record (V4, Memory:2010.1) 
--------------------------------------
    
Function: 
    This is the record is used to store fail data along with capture test conditions and references to test test descriptions. 
    It allows the fail data to be stored in various formats describe below using the field highlighting

Frequency:
    Number of memory tests times records required to log the fails for the test (counting continuation record)
    
Location:    
    It can occur after all the memory design specific records i.e. any Memory Structure Record (MSR),
    any Memory Controller Records (MCRs), any Memory Instance Records (IDRs), any Memory Model Records(MMRs),
    any Algorithms Specification Records (ASRs), any Frame Specification Records (FSRs) and any Bitstream Specificaion Records (BSRs)
'''
            #TODO: Implement "Field Presense Expression" (see PTR record on how)
            self.fields = {
                'REC_LEN'   : {'#' :  0, 'Type' :  'U*2', 'Ref' :                     None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' :    None},
                'REC_TYP'   : {'#' :  1, 'Type' :  'U*1', 'Ref' :                     None, 'Value' :   15, 'Text' : 'Record type                           ', 'Missing' :    None},
                'REC_SUB'   : {'#' :  2, 'Type' :  'U*1', 'Ref' :                     None, 'Value' :   40, 'Text' : 'Record sub-type                       ', 'Missing' :    None},
                'CONT_FLG'  : {'#' :  3, 'Type' :  'B*1', 'Ref' :                     None, 'Value' : None, 'Text' : 'Continuation flag                     ', 'Missing' :    None},
                'TEST_NUM'  : {'#' :  4, 'Type' :  'U*4', 'Ref' :                     None, 'Value' : None, 'Text' : 'Test number                           ', 'Missing' :    None},
                'HEAD_NUM'  : {'#' :  5, 'Type' :  'U*1', 'Ref' :                     None, 'Value' : None, 'Text' : 'Test head number                      ', 'Missing' :       1},
                'SITE_NUM'  : {'#' :  6, 'Type' :  'U*1', 'Ref' :                     None, 'Value' : None, 'Text' : 'Test site number                      ', 'Missing' :       1},
                'ASR_REF'   : {'#' :  7, 'Type' :  'U*2', 'Ref' :                     None, 'Value' : None, 'Text' : 'ASR Index                             ', 'Missing' :    None},
                'TEST_FLG'  : {'#' :  8, 'Type' :  'B*1', 'Ref' :                     None, 'Value' : None, 'Text' : 'Test flags (fail, alarm, etc.)        ', 'Missing' : ['0']*8},
                'LOG_TYP'   : {'#' :  9, 'Type' :  'C*n', 'Ref' :                     None, 'Value' : None, 'Text' : 'User defined description of datalog   ', 'Missing' :      ''},
                'TEST_TXT'  : {'#' : 10, 'Type' :  'C*n', 'Ref' :                     None, 'Value' : None, 'Text' : 'Descriptive text or label             ', 'Missing' :      ''},
                'ALARM_ID'  : {'#' : 11, 'Type' :  'C*n', 'Ref' :                     None, 'Value' : None, 'Text' : 'Name of alarm                         ', 'Missing' :      ''},
                'PROG_TXT'  : {'#' : 12, 'Type' :  'C*n', 'Ref' :                     None, 'Value' : None, 'Text' : 'Additional Programmed information     ', 'Missing' :      ''},
                'RSLT_TXT'  : {'#' : 13, 'Type' :  'C*n', 'Ref' :                     None, 'Value' : None, 'Text' : 'Additional result information         ', 'Missing' :      ''},
                'COND_CNT'  : {'#' : 14, 'Type' :  'U*2', 'Ref' :                     None, 'Value' : None, 'Text' : 'Count (k) of conditions               ', 'Missing' :       0},
                'COND_LST'  : {'#' : 15, 'Type' : 'xC*n', 'Ref' :               'COND_CNT', 'Value' : None, 'Text' : 'Array of Conditions                   ', 'Missing' :      []},
                'CYC_CNT'   : {'#' : 16, 'Type' :  'U*8', 'Ref' :                     None, 'Value' : None, 'Text' : 'Total cycles executed during the test ', 'Missing' :       0},
                'TOTF_CNT'  : {'#' : 17, 'Type' :  'U*8', 'Ref' :                     None, 'Value' : None, 'Text' : 'Total fails during the test           ', 'Missing' :       0},
                'TOTL_CNT'  : {'#' : 18, 'Type' :  'U*8', 'Ref' :                     None, 'Value' : None, 'Text' : 'Total fails during the complete MTR   ', 'Missing' :       0},
                'OVFL_FLG'  : {'#' : 19, 'Type' :  'B*1', 'Ref' :                     None, 'Value' : None, 'Text' : 'Failure Flag                          ', 'Missing' : ['0']*8},
                'FILE_INC'  : {'#' : 20, 'Type' :  'B*1', 'Ref' :                     None, 'Value' : None, 'Text' : 'File incomplete                       ', 'Missing' : ['0']*8},
                'LOG_TYPE'  : {'#' : 21, 'Type' :  'B*1', 'Ref' :                     None, 'Value' : None, 'Text' : 'Type of datalog                       ', 'Missing' : ['0']*8},
                'FDIM_CNT'  : {'#' : 22, 'Type' :  'U*1', 'Ref' :                     None, 'Value' : None, 'Text' : 'Count (m) of FDIM_FNAM and FDIM_FCNT  ', 'Missing' :       0},
                'FDIM_NAM'  : {'#' : 23, 'Type' : 'xC*n', 'Ref' :               'FDIM_CNT', 'Value' : None, 'Text' : 'Array of logged Dim names             ', 'Missing' :      []},
                'FDIM_FCNT' : {'#' : 24, 'Type' : 'xU*8', 'Ref' :               'FDIM_CNT', 'Value' : None, 'Text' : 'Array of failure counts               ', 'Missing' :      []},
                'CYC_BASE'  : {'#' : 25, 'Type' :  'U*8', 'Ref' :                     None, 'Value' : None, 'Text' : 'Cycle offset to CYC_OFST array        ', 'Missing' :       0},
                'CYC_SIZE'  : {'#' : 26, 'Type' :  'U*1', 'Ref' :                     None, 'Value' : None, 'Text' : 'Size (f) of CYC_OFST [1,2,4 or 8 byes]', 'Missing' :       1},
                'PMR_SIZE'  : {'#' : 27, 'Type' :  'U*1', 'Ref' :                     None, 'Value' : None, 'Text' : 'Size (f) of PMR_ARR [1 or 2 bytes]    ', 'Missing' :       1},
                'ROW_SIZE'  : {'#' : 28, 'Type' :  'U*1', 'Ref' :                     None, 'Value' : None, 'Text' : 'Size (f) of ROW_ARR [1,2,4 or 8 bytes]', 'Missing' :       1},
                'COL_SIZE'  : {'#' : 29, 'Type' :  'U*1', 'Ref' :                     None, 'Value' : None, 'Text' : 'Size (f) of COL_ARR [1,2,4 or 8 bytes]', 'Missing' :       1},
                'DLOG_MSK'  : {'#' : 30, 'Type' :  'U*1', 'Ref' :                     None, 'Value' : None, 'Text' : 'Presence indication mask              ', 'Missing' :       0},
                'PMR_CNT'   : {'#' : 31, 'Type' :  'U*4', 'Ref' :                     None, 'Value' : None, 'Text' : 'Count (n) of pins in PMN_ARR          ', 'Missing' :       0},
                'PMR_ARR'   : {'#' : 32, 'Type' : 'xU*f', 'Ref' :  ('PMR_CNT', 'PMR_SIZE'), 'Value' : None, 'Text' : 'Array of PMR indexes for pins         ', 'Missing' :      []},
                'CYCO_CNT'  : {'#' : 33, 'Type' :  'U*4', 'Ref' :                     None, 'Value' : None, 'Text' : 'Count (n) of CYC_OFST array           ', 'Missing' :       0},
                'CYC_OFST'  : {'#' : 34, 'Type' : 'xU*f', 'Ref' : ('CYCO_CNT', 'CYC_SIZE'), 'Value' : None, 'Text' : 'Array of cycle indexes for each fail  ', 'Missing' :      []},
                'ROW_CNT'   : {'#' : 35, 'Type' :  'U*4', 'Ref' :                     None, 'Value' : None, 'Text' : 'Count (d) of ROW_ARR array            ', 'Missing' :       0},
                'ROW_ARR'   : {'#' : 36, 'Type' : 'xU*f', 'Ref' :  ('ROW_CNT', 'ROW_SIZE'), 'Value' : None, 'Text' : 'Array of row addresses for each fail  ', 'Missing' :      []},
                'COL_CNT'   : {'#' : 37, 'Type' :  'U*4', 'Ref' :                     None, 'Value' : None, 'Text' : 'Count (d) of COL_ARR array            ', 'Missing' :       0},
                'COL_ARR'   : {'#' : 38, 'Type' : 'xU*f', 'Ref' :  ('COL_CNT', 'COL_SIZE'), 'Value' : None, 'Text' : 'Array of col addresses for each fail  ', 'Missing' :      []},
                'STEP_CNT'  : {'#' : 39, 'Type' :  'U*4', 'Ref' :                     None, 'Value' : None, 'Text' : 'Count (d) STEP_ARR array              ', 'Missing' :       0},
                'STEP_ARR'  : {'#' : 40, 'Type' : 'xU*1', 'Ref' :               'STEP_CNT', 'Value' : None, 'Text' : 'Array of march steps for each fail    ', 'Missing' :      []},
                'DIM_CNT'   : {'#' : 41, 'Type' :  'U*1', 'Ref' :                     None, 'Value' : None, 'Text' : 'Number (k) of dimensions              ', 'Missing' :       0},
                'DIM_NAMS'  : {'#' : 42, 'Type' : 'xC*n', 'Ref' :                'DIM_CNT', 'Value' : None, 'Text' : 'Names of the dimensions               ', 'Missing' :      []},
                'DIM_DCNT'  : {'#' : 43, 'Type' :  'U*4', 'Ref' :                     None, 'Value' : None, 'Text' : 'Count (n) of DIM_VALS                 ', 'Missing' :       0},
                'DIM_DSIZ'  : {'#' : 44, 'Type' :  'U*1', 'Ref' :                     None, 'Value' : None, 'Text' : 'Size (f) of DIM_VALS [1,2,4or 8 bytes]', 'Missing' :       1},
                'DIM_VALS'  : {'#' : 45, 'Type' : 'xU*f', 'Ref' : ('DIM_DCNT', 'DIM_DSIZ'), 'Value' : None, 'Text' : 'Array of data values for a dimension  ', 'Missing' :      []},
                'TFRM_CNT'  : {'#' : 46, 'Type' :  'U*8', 'Ref' :                     None, 'Value' : None, 'Text' : 'Total frames in frame based logging   ', 'Missing' :       0},
                'TFSG_CNT'  : {'#' : 47, 'Type' :  'U*8', 'Ref' :                     None, 'Value' : None, 'Text' : 'Total segments across all records     ', 'Missing' :       0},
                'LFSG_CNT'  : {'#' : 48, 'Type' :  'U*2', 'Ref' :                     None, 'Value' : None, 'Text' : 'Local number of frame segments        ', 'Missing' :       0},
                'FRM_IDX'   : {'#' : 49, 'Type' :  'U*2', 'Ref' :                     None, 'Value' : None, 'Text' : 'Index of the frame record             ', 'Missing' :       0},
                'FRM_MASK'  : {'#' : 50, 'Type' :  'D*n', 'Ref' :                     None, 'Value' : None, 'Text' : 'Frame presence mask                   ', 'Missing' :      []},
                'FRM_CNT'   : {'#' : 51, 'Type' :  'U*4', 'Ref' :                     None, 'Value' : None, 'Text' : 'Count (q) of frame (curr frame & maks)', 'Missing' :       0},
                'LFBT_CNT'  : {'#' : 52, 'Type' :  'U*4', 'Ref' :                     None, 'Value' : None, 'Text' : 'Count(q) of bits stored in this record', 'Missing' :       0},
                'FRAMES'    : {'#' : 53, 'Type' :  'D*n', 'Ref' :                     None, 'Value' : None, 'Text' : 'Bit encoded data (curr FSR)           ', 'Missing' :      []},
                'TBSG_CNT'  : {'#' : 54, 'Type' :  'U*8', 'Ref' :                     None, 'Value' : None, 'Text' : 'Number of logged bit stream segments  ', 'Missing' :       0},
                'LBSG_CNT'  : {'#' : 55, 'Type' :  'U*2', 'Ref' :                     None, 'Value' : None, 'Text' : '# of bit stream segmnts in this record', 'Missing' :       0},
                'BSR_IDX'   : {'#' : 56, 'Type' :  'U*2', 'Ref' :                     None, 'Value' : None, 'Text' : 'Index of the bit stream record        ', 'Missing' :       0},
                'STRT_ADR'  : {'#' : 57, 'Type' :  'U*f', 'Ref' :            BSR__ADDR_SIZ, 'Value' : None, 'Text' : 'Start row addr in the current segment ', 'Missing' :       1},
                'WORD_CNT'  : {'#' : 58, 'Type' :  'U*f', 'Ref' :              BSR__WC_SIZ, 'Value' : None, 'Text' : 'Word count in current stream segment  ', 'Missing' :       1},
                'WORDS'     : {'#' : 59, 'Type' :  'D*n', 'Ref' :                     None, 'Value' : None, 'Text' : 'Bit encoded data for one or words     ', 'Missing' :      []},
                'TBMP_SIZE' : {'#' : 60, 'Type' :  'U*8', 'Ref' :                     None, 'Value' : None, 'Text' : 'count (k) of CBIT_MAP                 ', 'Missing' :       0},
                'LBMP_SIZE' : {'#' : 61, 'Type' :  'U*2', 'Ref' :                     None, 'Value' : None, 'Text' : 'Bytes from map in the current record  ', 'Missing' :       0},
                'CBIT_MAP'  : {'#' : 62, 'Type' : 'xU*1', 'Ref' :              'TBMP_SIZE', 'Value' : None, 'Text' : 'Compressed bit map                    ', 'Missing' :      []}
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)
            
class NMR(STDR):
    def __init__(self, version=None, endian=None, record = None):
        self.id = 'NMR'
        self.local_debug = False
        if version==None or version=='V4':
            self.version = 'V4'
            self.info=    '''
Name Map Record (V4-2007)
-------------------------
    
Function: 
    This record contains a map of PMR indexes to ATPG signal names. 
    This record is designed to allow preservation of ATPG signal names used in the ATPG files through the datalog output. 
    This record is only required when the standard PMR records do not contain the ATPG signal name.
    
Frequency: 
    ?!?
    
Location: 
    ?!?
    
'''
            self.fields = {
                'REC_LEN'  : {'#' : 0, 'Type' :  'U*2', 'Ref' :       None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' : None},
                'REC_TYP'  : {'#' : 1, 'Type' :  'U*1', 'Ref' :       None, 'Value' :    1, 'Text' : 'Record type                           ', 'Missing' : None},
                'REC_SUB'  : {'#' : 2, 'Type' :  'U*1', 'Ref' :       None, 'Value' :   91, 'Text' : 'Record sub-type                       ', 'Missing' : None},
                'CONT_FLG' : {'#' : 3, 'Type' :  'B*1', 'Ref' :       None, 'Value' : None, 'Text' : 'NMR record(s) following if not 0      ', 'Missing' :    0},
                'TOTM_CNT' : {'#' : 4, 'Type' :  'U*2', 'Ref' :       None, 'Value' : None, 'Text' : 'Count of PMR indexes (=ATPG_NAMes)    ', 'Missing' :    0},
                'LOCM_CNT' : {'#' : 5, 'Type' :  'U*2', 'Ref' :       None, 'Value' : None, 'Text' : 'Count of (k) PMR indexes              ', 'Missing' :    0}, 
                'PMR_INDX' : {'#' : 6, 'Type' : 'xU*2', 'Ref' : 'LOCM_CNT', 'Value' : None, 'Text' : 'Array of PMR indexes                  ', 'Missing' :   []}, 
                'ATPG_NAM' : {'#' : 7, 'Type' : 'xC*n', 'Ref' : 'LOCM_CNT', 'Value' : None, 'Text' : 'Array of ATPG signal names            ', 'Missing' :   []}
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)
            
class PCR(STDR):
    def __init__(self, version=None, endian=None, record = None):
        self.id = 'PCR'
        self.local_debug = False
        if version==None or version=='V4':
            self.version = 'V4'
            self.info =     '''
Part Count Record 
-----------------

Function: 
    Contains the part count totals for one or all test sites. Each data stream must have at
    least one PCR to show the part count.
        
Frequency: 
    * Obligatory.
    * At least one PCR in the file: either one summary PCR for all test sites
      (HEAD_NUM = 255), or one PCR for each head/site combination, or both.

Location: 
    Anywhere in the data stream after the initial "FAR-(ATRs)-MIR-(RDR)-(SDRs)" sequence and before the MRR.
    When data is being recorded in real time, this record will usually appear near the end of the data stream.
'''
            self.fields = {
                'REC_LEN'  : {'#' : 0, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' :        None},
                'REC_TYP'  : {'#' : 1, 'Type' : 'U*1', 'Ref' : None, 'Value' :    1, 'Text' : 'Record type                           ', 'Missing' :        None},
                'REC_SUB'  : {'#' : 2, 'Type' : 'U*1', 'Ref' : None, 'Value' :   30, 'Text' : 'Record sub-type                       ', 'Missing' :        None},
                'HEAD_NUM' : {'#' : 3, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'Test head number                      ', 'Missing' :           0},
                'SITE_NUM' : {'#' : 4, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'Test site number                      ', 'Missing' :           0},
                'PART_CNT' : {'#' : 5, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : 'Number of parts tested                ', 'Missing' :           0},
                'RTST_CNT' : {'#' : 6, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : 'Number of parts retested              ', 'Missing' : 4294967295}, 
                'ABRT_CNT' : {'#' : 7, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : 'Number of aborts during testing       ', 'Missing' : 4294967295},
                'GOOD_CNT' : {'#' : 8, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : 'Number of good (passed) parts tested  ', 'Missing' : 4294967295},
                'FUNC_CNT' : {'#' : 9, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : 'Number of functional parts tested     ', 'Missing' : 4294967295}
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)

class PDR(STDR):
    def __init__(self, version=None, endian=None, record = None):
        self.id = 'PDR'
        self.local_debug = False
        if version==None or version=='V3':
            self.version = 'V3'
            self.info=    '''
Parametric test Description Record 
----------------------------------
    
Function: 
    ?!?
    
Frequency:
    ?!?
        
Location:
    ?!?
'''
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' :      None},
                'REC_TYP'  : {'#' :  1, 'Type' : 'U*1', 'Ref' : None, 'Value' :   10, 'Text' : 'Record type                           ', 'Missing' :      None},
                'REC_SUB'  : {'#' :  2, 'Type' : 'U*1', 'Ref' : None, 'Value' :   10, 'Text' : 'Record sub-type                       ', 'Missing' :      None},
                'TEST_NUM' : {'#' :  3, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :      None},
                'DESC_FLG' : {'#' :  4, 'Type' : 'B*1', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :   ['0']*8},
                'OPT_FLAG' : {'#' :  5, 'Type' : 'B*1', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :   ['0']*8},
                'RES_SCAL' : {'#' :  6, 'Type' : 'I*1', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :         0},
                'UNITS'    : {'#' :  7, 'Type' : 'C*7', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' : '       '},
                'RES_LDIG' : {'#' :  8, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :         0},
                'RES_RDIG' : {'#' :  9, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :         0},
                'LLM_SCAL' : {'#' : 10, 'Type' : 'I*1', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :         0},
                'HLM_SCAL' : {'#' : 11, 'Type' : 'I*1', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :         0},
                'LLM_LDIG' : {'#' : 12, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :         0},
                'LLM_RDIG' : {'#' : 13, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :         0},
                'HLM_LDIG' : {'#' : 14, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :         0},
                'HLM_RDIG' : {'#' : 15, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :         0},
                'LO_LIMIT' : {'#' : 16, 'Type' : 'R*4', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :       0.0},
                'HI_LIMIT' : {'#' : 17, 'Type' : 'R*4', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :       0.0},
                'TEST_NAM' : {'#' : 18, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :        ''},
                'SEQ_NAME' : {'#' : 19, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'Missing' :        ''}
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)
            
class PGR(STDR):
    def __init__(self, version=None, endian=None, record = None):
        self.id = 'PGR'
        self.local_debug = False
        if version==None or version=='V4':
            self.version = 'V4'
            self.info = '''
Pin Group Record
----------------

Function: 
    Associates a name with a group of pins.
        
Frequency:
    * Optional 
    * One per pin group defined in the test program.
       
Location: 
    After all the PMRs whose PMR index values are listed in the PMR_INDX array of this
    record; and before the first PLR that uses this record's GRP_INDX value.
'''
            self.fields = {
                'REC_LEN'  : {'#' : 0, 'Type' :  'U*2', 'Ref' :       None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' : None},
                'REC_TYP'  : {'#' : 1, 'Type' :  'U*1', 'Ref' :       None, 'Value' :    1, 'Text' : 'Record type                           ', 'Missing' : None},
                'REC_SUB'  : {'#' : 2, 'Type' :  'U*1', 'Ref' :       None, 'Value' :   62, 'Text' : 'Record sub-type                       ', 'Missing' : None},
                'GRP_INDX' : {'#' : 3, 'Type' :  'U*2', 'Ref' :       None, 'Value' : None, 'Text' : 'Unique index associated with pin group', 'Missing' :    0},
                'GRP_NAM'  : {'#' : 4, 'Type' :  'C*n', 'Ref' :       None, 'Value' : None, 'Text' : 'Name of pin group                     ', 'Missing' :   ''},
                'INDX_CNT' : {'#' : 5, 'Type' :  'U*2', 'Ref' :       None, 'Value' : None, 'Text' : 'Count (k) of PMR indexes              ', 'Missing' :    0},
                'PMR_INDX' : {'#' : 6, 'Type' : 'xU*2', 'Ref' : 'INDX_CNT', 'Value' : None, 'Text' : 'Array of indexes for pins in the group', 'Missing' :   []}
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)
    
class PIR(STDR):
    def __init__(self, version=None, endian=None, record = None):
        self.id = 'PIR'
        self.local_debug = False
        if version==None or version=='V4':
            self.version = 'V4'
            self.info = '''
Part Information Record
-----------------------

Function: 
    Acts as a marker to indicate where testing of a particular part begins for each part
    tested by the test program. The PIR and the Part Results Record (PRR) bracket all the
    stored information pertaining to one tested part.
        
Frequency: 
    * Obligatory
    * One per part tested.
        
Location: 
    Anywhere in the data stream after the initial sequence "FAR-(ATRs)-MIR-(RDR)-(SDRs)", and before the corresponding PRR.
    Sent before testing each part.
'''
            self.fields = {
                'REC_LEN'  : {'#' : 0, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' : None},
                'REC_TYP'  : {'#' : 1, 'Type' : 'U*1', 'Ref' : None, 'Value' :    5, 'Text' : 'Record type                           ', 'Missing' : None},
                'REC_SUB'  : {'#' : 2, 'Type' : 'U*1', 'Ref' : None, 'Value' :   10, 'Text' : 'Record sub-type                       ', 'Missing' : None},
                'HEAD_NUM' : {'#' : 3, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'Test head number                      ', 'Missing' :    1},
                'SITE_NUM' : {'#' : 4, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'Test site number                      ', 'Missing' :    1}
            }
        elif version=='V3':
            self.version = 'V3'
            self.info = '''
Part Information Record
-----------------------

Function: 
    Acts as a marker to indicate where testing of a particular part begins for each part
    tested by the test program. The PIR and the Part Results Record (PRR) bracket all the
    stored information pertaining to one tested part.
        
Frequency: 
    * Obligatory
    * One per part tested.
        
Location: 
    Anywhere in the data stream after the initial sequence "FAR-(ATRs)-MIR-(RDR)-(SDRs)", and before the corresponding PRR.
    Sent before testing each part.
'''
            self.fields = {
                'REC_LEN'  : {'#' : 0, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' : None},
                'REC_TYP'  : {'#' : 1, 'Type' : 'U*1', 'Ref' : None, 'Value' :    5, 'Text' : 'Record type                           ', 'Missing' : None},
                'REC_SUB'  : {'#' : 2, 'Type' : 'U*1', 'Ref' : None, 'Value' :   10, 'Text' : 'Record sub-type                       ', 'Missing' : None},
                'HEAD_NUM' : {'#' : 3, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'Test head number                      ', 'Missing' :    1},
                'SITE_NUM' : {'#' : 4, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'Test site number                      ', 'Missing' :    1},
                'X_COORD'  : {'#' : 5, 'Type' : 'I*2', 'Ref' : None, 'Value' : None, 'Text' : 'Wafer X coordinate                    ', 'Missing' :    0},
                'Y_COORD'  : {'#' : 6, 'Type' : 'I*2', 'Ref' : None, 'Value' : None, 'Text' : 'Wafer Y coordinate                    ', 'Missing' :    0},
                'PART_ID'  : {'#' : 7, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Part Identification                   ', 'Missing' :   ''},
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)
        
class PLR(STDR):
    def __init__(self, version=None, endian=None, record = None):
        self.id = 'PLR'
        self.local_debug = False
        if version==None or version=='V4':
            self.version = 'V4'
            self.info = '''
Pin List Record
---------------

Function: 
    Defines the current display radix and operating mode for a pin or pin group.

Frequency:
    * Optional
    * One or more whenever the usage of a pin or pin group changes in the test program.
        
Location: 
    After all the PMRs and PGRs whose PMR index values and pin group index values are
    listed in the GRP_INDX array of this record; and before the first FTR that references pins
    or pin groups whose modes are defined in this record.
'''
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' :  'U*2', 'Ref' :       None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' : None},
                'REC_TYP'  : {'#' :  1, 'Type' :  'U*1', 'Ref' :       None, 'Value' :    1, 'Text' : 'Record type                           ', 'Missing' : None},
                'REC_SUB'  : {'#' :  2, 'Type' :  'U*1', 'Ref' :       None, 'Value' :   63, 'Text' : 'Record sub-type                       ', 'Missing' : None},
                'GRP_CNT'  : {'#' :  3, 'Type' :  'U*2', 'Ref' :       None, 'Value' : None, 'Text' : 'Count (k) of pins or pin groups       ', 'Missing' :    0},
                'GRP_INDX' : {'#' :  4, 'Type' : 'xU*2', 'Ref' :  'GRP_CNT', 'Value' : None, 'Text' : 'Array of pin or pin group indexes     ', 'Missing' :   []},
                'GRP_MODE' : {'#' :  5, 'Type' : 'xU*2', 'Ref' :  'GRP_CNT', 'Value' : None, 'Text' : 'Operating mode of pin group           ', 'Missing' :   []},
                'GRP_RADX' : {'#' :  6, 'Type' : 'xU*1', 'Ref' :  'GRP_CNT', 'Value' : None, 'Text' : 'Display radix of pin group            ', 'Missing' :   []},
                'PGM_CHAR' : {'#' :  7, 'Type' : 'xC*n', 'Ref' :  'GRP_CNT', 'Value' : None, 'Text' : 'Program state encoding characters     ', 'Missing' :   []},
                'RTN_CHAR' : {'#' :  8, 'Type' : 'xC*n', 'Ref' :  'GRP_CNT', 'Value' : None, 'Text' : 'Return state encoding characters      ', 'Missing' :   []},
                'PGM_CHAL' : {'#' :  9, 'Type' : 'xC*n', 'Ref' :  'GRP_CNT', 'Value' : None, 'Text' : 'Program state encoding characters     ', 'Missing' :   []},
                'RTN_CHAL' : {'#' : 10, 'Type' : 'xC*n', 'Ref' :  'GRP_CNT', 'Value' : None, 'Text' : 'Return state encoding characters      ', 'Missing' :   []}
            }    
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)

class PMR(STDR):
    def __init__(self, version=None, endian=None, record = None):
        self.id = 'PMR'
        self.local_debug = False
        if version==None or version=='V4':
            self.version = 'V4'
            self.info =     '''
Pin Map Record
--------------

Function: 
    Provides indexing of tester channel names, and maps them to physical and logical pin
    names. Each PMR defines the information for a single channel/pin combination.

Frequency:
    * Optional
    * One per channel/pin combination used in the test program.
    * Reuse of a PMR index number is not permitted.
        
Location: 
    After the initial "FAR-(ATRs)-MIR-(RDR)-(SDRs)" sequence and before the first PGR, PLR, 
    FTR, or MPR that uses this record's PMR_INDX value.
'''
            self.fields = {
                'REC_LEN'  : {'#' : 0, 'Type' :  'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' : None},
                'REC_TYP'  : {'#' : 1, 'Type' :  'U*1', 'Ref' : None, 'Value' :    1, 'Text' : 'Record type                           ', 'Missing' : None},
                'REC_SUB'  : {'#' : 2, 'Type' :  'U*1', 'Ref' : None, 'Value' :   60, 'Text' : 'Record sub-type                       ', 'Missing' : None},
                'PMR_INDX' : {'#' : 3, 'Type' :  'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Unique index associated with pin      ', 'Missing' :    0},
                'CHAN_TYP' : {'#' : 4, 'Type' :  'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Channel type                          ', 'Missing' :    0},
                'CHAN_NAM' : {'#' : 5, 'Type' :  'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Channel name                          ', 'Missing' :   ''},
                'PHY_NAM'  : {'#' : 6, 'Type' :  'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Physical name of pin                  ', 'Missing' :   ''},
                'LOG_NAM'  : {'#' : 7, 'Type' :  'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Logical name of pin                   ', 'Missing' :   ''},
                'HEAD_NUM' : {'#' : 8, 'Type' :  'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'Head number associated with channel   ', 'Missing' :    1},
                'SITE_NUM' : {'#' : 9, 'Type' :  'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'Site number associated with channel   ', 'Missing' :    1}
            }
        elif version=='V3':
            self.version = 'V3'
            self.info =     '''
Pin Map Record
--------------

Function: 
    Provides indexing of tester channel names, and maps them to physical and logical pin
    names. Each PMR defines the information for a single channel/pin combination.

Frequency:
    * Optional
    * One per channel/pin combination used in the test program.
    * Reuse of a PMR index number is not permitted.
        
Location: 
    After the initial "FAR-(ATRs)-MIR-(RDR)-(SDRs)" sequence and before the first PGR, PLR, 
    FTR, or MPR that uses this record's PMR_INDX value.
'''
            self.fields = {
                'REC_LEN'  : {'#' : 0, 'Type' :  'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' : None},
                'REC_TYP'  : {'#' : 1, 'Type' :  'U*1', 'Ref' : None, 'Value' :    1, 'Text' : 'Record type                           ', 'Missing' : None},
                'REC_SUB'  : {'#' : 2, 'Type' :  'U*1', 'Ref' : None, 'Value' :   63, 'Text' : 'Record sub-type                       ', 'Missing' : None},
            }
            raise STDFError("%s object for STDF '%s' is not yet implemented" % (self.id, self.version))
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)

class PRR(STDR):
    def __init__(self, version=None, endian=None, record=None):
        self.id = 'PRR'
        self.local_debug = False
        if version==None or version=='V4':
            self.version = 'V4'
            self.info = '''
Part Results Record
-------------------

Function: 
    Contains the result information relating to each part tested by the test program. The
    PRR and the Part Information Record (PIR) bracket all the stored information
    pertaining to one tested part.
        
Frequency: 
    * Obligatory 
    * One per part tested.
        
Location: 
    Anywhere in the data stream after the corresponding PIR and before the MRR.
    Sent after completion of testing each part.
'''    
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' :                                     None},
                'REC_TYP'  : {'#' :  1, 'Type' : 'U*1', 'Ref' : None, 'Value' :    5, 'Text' : 'Record type                           ', 'Missing' :                                     None},
                'REC_SUB'  : {'#' :  2, 'Type' : 'U*1', 'Ref' : None, 'Value' :   20, 'Text' : 'Record sub-type                       ', 'Missing' :                                     None},
                'HEAD_NUM' : {'#' :  3, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'Test head number                      ', 'Missing' :                                        1},
                'SITE_NUM' : {'#' :  4, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'Test site number                      ', 'Missing' :                                        1},
                'PART_FLG' : {'#' :  5, 'Type' : 'B*1', 'Ref' : None, 'Value' : None, 'Text' : 'Part information flag                 ', 'Missing' : ['0', '0', '0', '1', '0', '0', '0', '1']},
                'NUM_TEST' : {'#' :  6, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Number of tests executed              ', 'Missing' :                                        0},
                'HARD_BIN' : {'#' :  7, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Hardware bin number                   ', 'Missing' :                                        0},
                'SOFT_BIN' : {'#' :  8, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Software bin number                   ', 'Missing' :                                    65535},
                'X_COORD'  : {'#' :  9, 'Type' : 'I*2', 'Ref' : None, 'Value' : None, 'Text' : '(Wafer) X coordinate                  ', 'Missing' :                                   -32768},
                'Y_COORD'  : {'#' : 10, 'Type' : 'I*2', 'Ref' : None, 'Value' : None, 'Text' : '(Wafer) Y coordinate                  ', 'Missing' :                                   -32768},
                'TEST_T'   : {'#' : 11, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : 'Elapsed test time in milliseconds     ', 'Missing' :                                        0},
                'PART_ID'  : {'#' : 12, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Part identification                   ', 'Missing' :                                       ''},
                'PART_TXT' : {'#' : 13, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Part description text                 ', 'Missing' :                                       ''},
                'PART_FIX' : {'#' : 14, 'Type' : 'B*n', 'Ref' : None, 'Value' : None, 'Text' : 'Part repair information               ', 'Missing' :                                       []}
            }
        elif version == 'V3':
            self.version = 'V3'
            self.info = '''
Part Results Record
-------------------

Function: 
    Contains the result information relating to each part tested by the test program. The
    PRR and the Part Information Record (PIR) bracket all the stored information
    pertaining to one tested part.
        
Frequency: 
    * Obligatory 
    * One per part tested.
        
Location: 
    Anywhere in the data stream after the corresponding PIR and before the MRR.
    Sent after completion of testing each part.
'''    
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' :                                     None},
                'REC_TYP'  : {'#' :  1, 'Type' : 'U*1', 'Ref' : None, 'Value' :    5, 'Text' : 'Record type                           ', 'Missing' :                                     None},
                'REC_SUB'  : {'#' :  2, 'Type' : 'U*1', 'Ref' : None, 'Value' :   20, 'Text' : 'Record sub-type                       ', 'Missing' :                                     None},
                'HEAD_NUM' : {'#' :  3, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'Test head number                      ', 'Missing' :                                        1},
                'SITE_NUM' : {'#' :  4, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'Test site number                      ', 'Missing' :                                        1},
                'NUM_TEST' : {'#' :  5, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Number of tests executed              ', 'Missing' :                                        0},
                'HARD_BIN' : {'#' :  6, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Hardware bin number                   ', 'Missing' :                                        0},
                'SOFT_BIN' : {'#' :  7, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Software bin number                   ', 'Missing' :                                    65535},
                'PART_FLG' : {'#' :  8, 'Type' : 'B*1', 'Ref' : None, 'Value' : None, 'Text' : 'Part information flag                 ', 'Missing' : ['0', '0', '0', '0', '0', '0', '0', '1']},
                'PAD_BYTE' : {'#' :  9, 'Type' : 'B*1', 'Ref' : None, 'Value' : None, 'Text' : 'pad byte                              ', 'Missing' :                                  ['0']*8},
                'X_COORD'  : {'#' : 10, 'Type' : 'I*2', 'Ref' : None, 'Value' : None, 'Text' : '(Wafer) X coordinate                  ', 'Missing' :                                   -32768},
                'Y_COORD'  : {'#' : 11, 'Type' : 'I*2', 'Ref' : None, 'Value' : None, 'Text' : '(Wafer) Y coordinate                  ', 'Missing' :                                   -32768},
                'PART_ID'  : {'#' : 12, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Part identification                   ', 'Missing' :                                       ''},
                'PART_TXT' : {'#' : 13, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Part description text                 ', 'Missing' :                                       ''},
                'PART_FIX' : {'#' : 14, 'Type' : 'B*n', 'Ref' : None, 'Value' : None, 'Text' : 'Part repair information               ', 'Missing' :                                       []}
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)

class PSR(STDR):
    def __init__(self, version=None, endian=None, record = None):
        self.id = 'PSR'
        self.local_debug = False
        if version==None or version=='V4':
            self.version = 'V4'
            self.info=    '''
Pattern Sequence Record (V4-2007) 
---------------------------------
    
Function: 
    PSR record contains the information on the pattern profile for a specific executed scan test 
    as part of the Test Identification information. In particular it implements the Test Pattern 
    Map data object in the data model. It specifies how the patterns for that test were constructed. 
    There will be a PSR record for each scan test in a test program. A PSR is referenced by the STR 
    (Scan Test Record) using its PSR_INDX field
        
Frequency: 
    ?!?
        
Location:
    ?!? 
'''
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' : 'U*2', 'Ref' :       None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' :    None},
                'REC_TYP'  : {'#' :  1, 'Type' : 'U*1', 'Ref' :       None, 'Value' :    1, 'Text' : 'Record type                           ', 'Missing' :    None},
                'REC_SUB'  : {'#' :  2, 'Type' : 'U*1', 'Ref' :       None, 'Value' :   90, 'Text' : 'Record sub-type                       ', 'Missing' :    None},
                'CONT_FLG' : {'#' :  3, 'Type' : 'B*1', 'Ref' :       None, 'Value' : None, 'Text' : 'PSR record(s) to follow if not 0      ', 'Missing' : ['0']*8},
                'PSR_INDX' : {'#' :  4, 'Type' : 'U*2', 'Ref' :       None, 'Value' : None, 'Text' : 'PSR Record Index (used by STR records)', 'Missing' :    None},
                'PSR_NAM'  : {'#' :  5, 'Type' : 'C*n', 'Ref' :       None, 'Value' : None, 'Text' : 'Symbolic name of PSR record           ', 'Missing' :      ''},
                'OPT_FLG'  : {'#' :  6, 'Type' : 'B*1', 'Ref' :       None, 'Value' : None, 'Text' : 'Options Flag                          ', 'Missing' :    None},
                'TOTP_CNT' : {'#' :  7, 'Type' : 'U*2', 'Ref' :       None, 'Value' : None, 'Text' : 'Count of sets in the complete data set', 'Missing' :       1},
                'LOCP_CNT' : {'#' :  8, 'Type' : 'U*2', 'Ref' :       None, 'Value' : None, 'Text' : 'Count (k) of sets in this record      ', 'Missing' :       0},
                'PAT_BGN'  : {'#' :  9, 'Type' :'xU*8', 'Ref' : 'LOCP_CNT', 'Value' : None, 'Text' : "Array of Cycle #'s patterns begins on ", 'Missing' :      []},
                'PAT_END'  : {'#' : 10, 'Type' :'xU*8', 'Ref' : 'LOCP_CNT', 'Value' : None, 'Text' : "Array of Cycle #'s patterns stops at  ", 'Missing' :      []},
                'PAT_FILE' : {'#' : 11, 'Type' :'xC*n', 'Ref' : 'LOCP_CNT', 'Value' : None, 'Text' : 'Array of Pattern File Names           ', 'Missing' :      []},
                'PAT_LBL'  : {'#' : 12, 'Type' :'xC*n', 'Ref' : 'LOCP_CNT', 'Value' : None, 'Text' : 'Optional pattern symbolic name        ', 'Missing' :      []},
                'FILE_UID' : {'#' : 13, 'Type' :'xC*n', 'Ref' : 'LOCP_CNT', 'Value' : None, 'Text' : 'Optional array of file identifier code', 'Missing' :      []},
                'ATPG_DSC' : {'#' : 14, 'Type' :'xC*n', 'Ref' : 'LOCP_CNT', 'Value' : None, 'Text' : 'Optional array of ATPG information    ', 'Missing' :      []},
                'SRC_ID'   : {'#' : 15, 'Type' :'xC*n', 'Ref' : 'LOCP_CNT', 'Value' : None, 'Text' : 'Optional array of PatternInSrcFileID  ', 'Missing' :      []}
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)
            
class PTR(STDR):
    def __init__(self, version=None, endian=None, record=None):
        self.id = 'PTR'
        self.local_debug = False
        if version==None or version == 'V4':
            self.version = 'V4'
            self.info = '''
Parametric Test Record
----------------------

Function:
    Contains the results of a single execution of a parametric test in the test program. The
    first occurrence of this record also establishes the default values for all semi-static
    information about the test, such as limits, units, and scaling. The PTR is related to the
    Test Synopsis Record (TSR) by test number, head number, and site number.
    
Frequency: 
    * Obligatory, one per parametric test execution on each head/site
        
Location: 
    Under normal circumstances, the PTR can appear anywhere in the data stream after
    the corresponding Part Information Record (PIR) and before the corresponding Part
    Result Record (PRR).
    In addition, to facilitate conversion from STDF V3, if the first PTR for a test contains
    default information only (no test results), it may appear anywhere after the initial
    "FAR-(ATRs)-MIR-(RDR)-(SDRs)" sequence, and before the first corresponding PTR, but need not appear
    between a PIR and PRR.
'''
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'FPE' : None,                                     'Missing' : None   },
                'REC_TYP'  : {'#' :  1, 'Type' : 'U*1', 'Ref' : None, 'Value' :   15, 'Text' : 'Record type                           ', 'FPE' : None,                                     'Missing' : None   },
                'REC_SUB'  : {'#' :  2, 'Type' : 'U*1', 'Ref' : None, 'Value' :   10, 'Text' : 'Record sub-type                       ', 'FPE' : None,                                     'Missing' : None   },        
                'TEST_NUM' : {'#' :  3, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : 'Test number                           ', 'FPE' : None,                                     'Missing' : None   },
                'HEAD_NUM' : {'#' :  4, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'Test head number                      ', 'FPE' : None,                                     'Missing' : 1      },
                'SITE_NUM' : {'#' :  5, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'Test site number                      ', 'FPE' : None,                                     'Missing' : 1      },
                'TEST_FLG' : {'#' :  6, 'Type' : 'B*1', 'Ref' : None, 'Value' : None, 'Text' : 'Test flags (fail, alarm, etc.)        ', 'FPE' : None,                                     'Missing' : ['0']*8},
                'PARM_FLG' : {'#' :  7, 'Type' : 'B*1', 'Ref' : None, 'Value' : None, 'Text' : 'Parametric test flags (drift, etc.)   ', 'FPE' : None,                                     'Missing' : ['0']*8},
                'RESULT'   : {'#' :  8, 'Type' : 'R*4', 'Ref' : None, 'Value' : None, 'Text' : 'Test result                           ', 'FPE' : None,                                     'Missing' : 0.0    },
                'TEST_TXT' : {'#' :  9, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Test description text or label        ', 'FPE' : None,                                     'Missing' : ''     },
                'ALARM_ID' : {'#' : 10, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Name of alarm                         ', 'FPE' : None,                                     'Missing' : ''     },
                'OPT_FLAG' : {'#' : 11, 'Type' : 'B*1', 'Ref' : None, 'Value' : None, 'Text' : 'Optional data flag                    ', 'FPE' : "self.fields['OPT_FLAG']['Value']!=None", 'Missing' : 255    }, #TODO: Needs some more work
                'RES_SCAL' : {'#' : 12, 'Type' : 'I*1', 'Ref' : None, 'Value' : None, 'Text' : 'Test results scaling exponent         ', 'FPE' : "self.fields['OPT_FLAG']['Value']!=None", 'Missing' : 0      },
                'LLM_SCAL' : {'#' : 13, 'Type' : 'I*1', 'Ref' : None, 'Value' : None, 'Text' : 'Low limit scaling exponent            ', 'FPE' : "self.fields['OPT_FLAG']['Value']!=None", 'Missing' : 0      },
                'HLM_SCAL' : {'#' : 14, 'Type' : 'I*1', 'Ref' : None, 'Value' : None, 'Text' : 'High limit scaling exponent           ', 'FPE' : "self.fields['OPT_FLAG']['Value']!=None", 'Missing' : 0      },
                'LO_LIMIT' : {'#' : 15, 'Type' : 'R*4', 'Ref' : None, 'Value' : None, 'Text' : 'Low test limit value                  ', 'FPE' : "self.fields['OPT_FLAG']['Value']!=None", 'Missing' : 0.0    },
                'HI_LIMIT' : {'#' : 16, 'Type' : 'R*4', 'Ref' : None, 'Value' : None, 'Text' : 'High test limit value                 ', 'FPE' : "self.fields['OPT_FLAG']['Value']!=None", 'Missing' : 0.0    },
                'UNITS'    : {'#' : 17, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Test units                            ', 'FPE' : "self.fields['OPT_FLAG']['Value']!=None", 'Missing' : ''     },
                'C_RESFMT' : {'#' : 18, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'ANSI C result format string           ', 'FPE' : "self.fields['OPT_FLAG']['Value']!=None", 'Missing' : ''     },
                'C_LLMFMT' : {'#' : 19, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'ANSI C low limit format string        ', 'FPE' : "self.fields['OPT_FLAG']['Value']!=None", 'Missing' : ''     },
                'C_HLMFMT' : {'#' : 20, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'ANSI C high limit format string       ', 'FPE' : "self.fields['OPT_FLAG']['Value']!=None", 'Missing' : ''     },
                'LO_SPEC'  : {'#' : 21, 'Type' : 'R*4', 'Ref' : None, 'Value' : None, 'Text' : 'Low specification limit value         ', 'FPE' : "self.fields['OPT_FLAG']['Value']!=None", 'Missing' : 0.0    },
                'HI_SPEC'  : {'#' : 22, 'Type' : 'R*4', 'Ref' : None, 'Value' : None, 'Text' : 'High specification limit value        ', 'FPE' : "self.fields['OPT_FLAG']['Value']!=None", 'Missing' : 0.0    }
            }
        elif version == 'V3':
            self.version ='V3'
            self.info = '''
Parametric Test Record
----------------------

Function:
    Contains the results of a single execution of a parametric test in the test program. The
    first occurrence of this record also establishes the default values for all semi-static
    information about the test, such as limits, units, and scaling. The PTR is related to the
    Test Synopsis Record (TSR) by test number, head number, and site number.
    
Frequency: 
    * Obligatory, one per parametric test execution on each head/site
        
Location: 
    Under normal circumstances, the PTR can appear anywhere in the data stream after
    the corresponding Part Information Record (PIR) and before the corresponding Part
    Result Record (PRR).
    In addition, to facilitate conversion from STDF V3, if the first PTR for a test contains
    default information only (no test results), it may appear anywhere after the initial
    "FAR-(ATRs)-MIR-(RDR)-(SDRs)" sequence, and before the first corresponding PTR, but need not appear
    between a PIR and PRR.
'''
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'FPE' : None, 'Missing' : None     },
                'REC_TYP'  : {'#' :  1, 'Type' : 'U*1', 'Ref' : None, 'Value' :   15, 'Text' : 'Record type                           ', 'FPE' : None, 'Missing' : None     },
                'REC_SUB'  : {'#' :  2, 'Type' : 'U*1', 'Ref' : None, 'Value' :   10, 'Text' : 'Record sub-type                       ', 'FPE' : None, 'Missing' : None     },        
                'TEST_NUM' : {'#' :  3, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : 'Test number                           ', 'FPE' : None, 'Missing' : None     },
                'HEAD_NUM' : {'#' :  4, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'Test head number                      ', 'FPE' : None, 'Missing' : 1        },
                'SITE_NUM' : {'#' :  5, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'Test site number                      ', 'FPE' : None, 'Missing' : 1        },
                'TEST_FLG' : {'#' :  6, 'Type' : 'B*1', 'Ref' : None, 'Value' : None, 'Text' : 'Test flags (fail, alarm, etc.)        ', 'FPE' : None, 'Missing' : ['0']*8  },
                'PARM_FLG' : {'#' :  7, 'Type' : 'B*1', 'Ref' : None, 'Value' : None, 'Text' : 'Parametric test flags (drift, etc.)   ', 'FPE' : None, 'Missing' : ['0']*8  },
                'RESULT'   : {'#' :  8, 'Type' : 'R*4', 'Ref' : None, 'Value' : None, 'Text' : 'Test result                           ', 'FPE' : None, 'Missing' : 0.0      },
                'OPT_FLAG' : {'#' :  9, 'Type' : 'B*1', 'Ref' : None, 'Value' : None, 'Text' : 'Optional data flag                    ', 'FPE' : None, 'Missing' : ['0']*8  },
                'RES_SCAL' : {'#' : 10, 'Type' : 'I*1', 'Ref' : None, 'Value' : None, 'Text' : 'Test results scaling exponent         ', 'FPE' : None, 'Missing' : 0        },
                'RES_LDIG' : {'#' : 11, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'FPE' : None, 'Missing' : 0        },
                'RES_RDIG' : {'#' : 12, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'FPE' : None, 'Missing' : 0        },
                'DESC_FLG' : {'#' : 13, 'Type' : 'B*1', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'FPE' : None, 'Missing' : ['0']*8  },
                'UNITS'    : {'#' : 14, 'Type' : 'C*7', 'Ref' : None, 'Value' : None, 'Text' : 'Test units                            ', 'FPE' : None, 'Missing' : '       '},
                'LLM_SCAL' : {'#' : 15, 'Type' : 'I*1', 'Ref' : None, 'Value' : None, 'Text' : 'Low limit scaling exponent            ', 'FPE' : None, 'Missing' : 0        },
                'HLM_SCAL' : {'#' : 16, 'Type' : 'I*1', 'Ref' : None, 'Value' : None, 'Text' : 'High limit scaling exponent           ', 'FPE' : None, 'Missing' : 0        },
                'LLM_LDIG' : {'#' : 17, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'FPE' : None, 'Missing' : 0        },
                'LLM_RDIG' : {'#' : 18, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'FPE' : None, 'Missing' : 0        },
                'HLM_LDIG' : {'#' : 19, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'FPE' : None, 'Missing' : 0        },
                'HLM_RDIG' : {'#' : 20, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'FPE' : None, 'Missing' : 0        },
                'LO_LIMIT' : {'#' : 21, 'Type' : 'R*4', 'Ref' : None, 'Value' : None, 'Text' : 'Low test limit value                  ', 'FPE' : None, 'Missing' : 0.0      },
                'HI_LIMIT' : {'#' : 22, 'Type' : 'R*4', 'Ref' : None, 'Value' : None, 'Text' : 'High test limit value                 ', 'FPE' : None, 'Missing' : 0.0      },
                'TEST_NAM' : {'#' : 23, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'FPE' : None, 'Missing' : ''       },
                'SEQ_NAME' : {'#' : 24, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : '                                      ', 'FPE' : None, 'Missing' : ''       },
                'TEST_TXT' : {'#' : 25, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Test description text or label        ', 'FPE' : None, 'Missing' : ''       }
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)
        
class RDR(STDR):
    def __init__(self, version=None, endian=None, record=None):
        self.id = 'RDR'
        self.local_debug = False
        if version==None or version == 'V4':
            self.version = 'V4'
            self.info = '''
Retest Data Record
------------------

Function: 
    Signals that the data in this STDF file is for retested parts. The data in this record,
    combined with information in the MIR, tells data filtering programs what data to
    replace when processing retest data.
        
Frequency: 
    * Obligatory if a lot is retested. (not if a device is binned in the reteset bin) 
    * One per data stream.
        
Location: 
    If this record is used, it must appear immediately after theMaster Information Record (MIR).
'''
            self.fields = {
                'REC_LEN'  : {'#' : 0, 'Type' :  'U*2', 'Ref' : None,       'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' : None},
                'REC_TYP'  : {'#' : 1, 'Type' :  'U*1', 'Ref' : None,       'Value' :    1, 'Text' : 'Record type                           ', 'Missing' : None},
                'REC_SUB'  : {'#' : 2, 'Type' :  'U*1', 'Ref' : None,       'Value' :   70, 'Text' : 'Record sub-type                       ', 'Missing' : None},
                'NUM_BINS' : {'#' : 3, 'Type' :  'U*2', 'Ref' : None,       'Value' : None, 'Text' : 'Number (k) of bins being retested     ', 'Missing' : 0   },
                'RTST_BIN' : {'#' : 4, 'Type' : 'xU*2', 'Ref' : 'NUM_BINS', 'Value' : None, 'Text' : 'Array of retest bin numbers           ', 'Missing' : []  }
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)

class RR1(STDR):
    def __init__(self, version=None, endian=None, record=None):
        self.id = 'RR1'
        raise STDFError("%s object creation error : reserved object", self.id)

class RR2(STDR):
    def __init__(self, version=None, endian=None, record=None):
        self.id = 'RR2'
        raise STDFError("%s object creation error : reserved object", self.id)

class SBR(STDR):
    def __init__(self, version=None, endian=None, record=None):
        self.id = 'SBR'
        self.local_debug = False
        if version==None or version=='V4':
            self.version = 'V4'
            self.info = '''
Software Bin Record
-------------------

Function: 
    Stores a count of the parts associated with a particular logical bin after testing. This
    bin count can be for a single test site (when parallel testing) or a total for all test sites.
    The STDF specification also supports a Hardware Bin Record (HBR) for actual physical
    binning. A part is "physically" placed in a hardware bin after testing. A part can be
    "logically" associated with a software bin during or after testing.
        
Frequency: 
    * Obligatory
    * One per software bin for each head/site combination 
    * One per software bin for all head/site combinations together ('HEAD_NUM' = 255)
    * May be included to name unused bins.
        
Location: 
    Anywhere in the data stream after the initial "FAR-(ATRs)-MIR-(RDR)-(SDRs)" sequence and before the MRR. 
    When data is being recorded in real time, this record usually appears near the end of the data stream.
'''
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' :  'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' : None},
                'REC_TYP'  : {'#' :  1, 'Type' :  'U*1', 'Ref' : None, 'Value' :    1, 'Text' : 'Record type                           ', 'Missing' : None},
                'REC_SUB'  : {'#' :  2, 'Type' :  'U*1', 'Ref' : None, 'Value' :   50, 'Text' : 'Record sub-type                       ', 'Missing' : None},
                'HEAD_NUM' : {'#' :  3, 'Type' :  'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'Test head number (255 = summary)      ', 'Missing' : 1   },
                'SITE_NUM' : {'#' :  4, 'Type' :  'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'Test site number                      ', 'Missing' : 1   },
                'SBIN_NUM' : {'#' :  5, 'Type' :  'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Software bin number                   ', 'Missing' : 0   },
                'SBIN_CNT' : {'#' :  6, 'Type' :  'U*4', 'Ref' : None, 'Value' : None, 'Text' : 'Number of parts in bin                ', 'Missing' : 0   },
                'SBIN_PF'  : {'#' :  7, 'Type' :  'C*1', 'Ref' : None, 'Value' : None, 'Text' : 'Pass/fail indication (P/F)            ', 'Missing' : ' ' },
                'SBIN_NAM' : {'#' :  8, 'Type' :  'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Name of software bin                  ', 'Missing' : ''  } 
            }
        elif version=='V3':
            self.version = 'V3'
            self.info = '''
Software Bin Record
-------------------

Function: 
    Stores a count of the parts associated with a particular logical bin after testing. This
    bin count can be for a single test site (when parallel testing) or a total for all test sites.
    The STDF specification also supports a Hardware Bin Record (HBR) for actual physical
    binning. A part is "physically" placed in a hardware bin after testing. A part can be
    "logically" associated with a software bin during or after testing.
        
Frequency: 
    * Obligatory
    * One per software bin for each head/site combination 
    * One per software bin for all head/site combinations together ('HEAD_NUM' = 255)
    * May be included to name unused bins.
        
Location: 
    Anywhere in the data stream after the initial "FAR-(ATRs)-MIR-(RDR)-(SDRs)" sequence and before the MRR. 
    When data is being recorded in real time, this record usually appears near the end of the data stream.
'''
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' : None},
                'REC_TYP'  : {'#' :  1, 'Type' : 'U*1', 'Ref' : None, 'Value' :    1, 'Text' : 'Record type                           ', 'Missing' : None},
                'REC_SUB'  : {'#' :  2, 'Type' : 'U*1', 'Ref' : None, 'Value' :   50, 'Text' : 'Record sub-type                       ', 'Missing' : None},
                'SBIN_NUM' : {'#' :  3, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Software bin number                   ', 'Missing' : 0   },
                'SBIN_CNT' : {'#' :  4, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : 'Number of parts in bin                ', 'Missing' : 0   },
                'SBIN_NAM' : {'#' :  5, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Name of software bin                  ', 'Missing' : ''  }
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)

class SCR(STDR):
    def __init__(self, version=None, endian=None, record = None):
        self.id = 'SCR'
        self.local_debug = False
        if version == 'V3':
            self.version = 'V3'
            self.info=    '''
Site specific part Count Record (V3+)
-------------------------------------
    
Function: 
    ?!?
    
Frequency: 
    ?!?
        
Location: 
    ?!?
'''
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' : None},
                'REC_TYP'  : {'#' :  1, 'Type' : 'U*1', 'Ref' : None, 'Value' :   25, 'Text' : 'Record type                           ', 'Missing' : None},
                'REC_SUB'  : {'#' :  2, 'Type' : 'U*1', 'Ref' : None, 'Value' :   40, 'Text' : 'Record sub-type                       ', 'Missing' : None},
                'REC_LEN'  : {'#' :  2, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' : None},
                'REC_TYP'  : {'#' :  2, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'Record type (25)                      ', 'Missing' : None},
                'REC_SUB'  : {'#' :  2, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'Record sub-type (40)                  ', 'Missing' : None},
                'HEAD_NUM' : {'#' :  2, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'Test head number                      ', 'Missing' : None},
                'SITE_NUM' : {'#' :  2, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'Test site number                      ', 'Missing' : None}, 
                'FINISH_T' : {'#' :  2, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : 'Date/time last part tested at site    ', 'Missing' : 0   },
                'PART_CNT' : {'#' :  2, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : 'Number of parts tested                ', 'Missing' : 0   },
                'RTST_CNT' : {'#' :  2, 'Type' : 'I*4', 'Ref' : None, 'Value' : None, 'Text' : 'Number of parts retested              ', 'Missing' : -1  },
                'ABRT_CNT' : {'#' :  2, 'Type' : 'I*4', 'Ref' : None, 'Value' : None, 'Text' : 'Number of aborts during testing       ', 'Missing' : -1  },
                'GOOD_CNT' : {'#' :  2, 'Type' : 'I*4', 'Ref' : None, 'Value' : None, 'Text' : 'Number of good (passed) parts tested  ', 'Missing' : -1  },
                'FUNC_CNT' : {'#' :  2, 'Type' : 'I*4', 'Ref' : None, 'Value' : None, 'Text' : 'Number of functional parts tested     ', 'Missing' : -1  }
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)
            
class SDR(STDR):
    def __init__(self, version=None, endian=None, record = None):
        self.id = 'SDR'
        self.local_debug = False
        if version==None or version == 'V4':
            self.version = 'V4'
            self.info = '''
Site Description Record
-----------------------

Function: 
    Contains the configuration information for one or more test sites, connected to one test
    head, that compose a site group.
        
Frequency: 
    * Optional
    * One for each site or group of sites that is differently configured.

Location: 
    Immediately after the MIR and RDR (if an RDR is used).
'''
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' : 'U*2',  'Ref' : None,       'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' : None},
                'REC_TYP'  : {'#' :  1, 'Type' : 'U*1',  'Ref' : None,       'Value' :    1, 'Text' : 'Record type                           ', 'Missing' : None},
                'REC_SUB'  : {'#' :  2, 'Type' : 'U*1',  'Ref' : None,       'Value' :   80, 'Text' : 'Record sub-type                       ', 'Missing' : None},        
                'HEAD_NUM' : {'#' :  3, 'Type' : 'U*1',  'Ref' : None,       'Value' : None, 'Text' : 'Test head number                      ', 'Missing' : 1   },
                'SITE_GRP' : {'#' :  4, 'Type' : 'U*1',  'Ref' : None,       'Value' : None, 'Text' : 'Site group number                     ', 'Missing' : 1   },
                'SITE_CNT' : {'#' :  5, 'Type' : 'U*1',  'Ref' : None,       'Value' : None, 'Text' : 'Number (k) of test sites in site group', 'Missing' : 1   },
                'SITE_NUM' : {'#' :  6, 'Type' : 'xU*1', 'Ref' : 'SITE_CNT', 'Value' : None, 'Text' : 'Array of k test site numbers          ', 'Missing' : [1] },
                'HAND_TYP' : {'#' :  7, 'Type' : 'C*n',  'Ref' : None,       'Value' : None, 'Text' : 'Handler or prober type                ', 'Missing' : ''  },
                'HAND_ID'  : {'#' :  8, 'Type' : 'C*n',  'Ref' : None,       'Value' : None, 'Text' : 'Handler or prober ID                  ', 'Missing' : ''  },
                'CARD_TYP' : {'#' :  9, 'Type' : 'C*n',  'Ref' : None,       'Value' : None, 'Text' : 'Probe card type                       ', 'Missing' : ''  },
                'CARD_ID'  : {'#' : 10, 'Type' : 'C*n',  'Ref' : None,       'Value' : None, 'Text' : 'Probe card ID                         ', 'Missing' : ''  },
                'LOAD_TYP' : {'#' : 11, 'Type' : 'C*n',  'Ref' : None,       'Value' : None, 'Text' : 'Load board type                       ', 'Missing' : ''  },
                'LOAD_ID'  : {'#' : 12, 'Type' : 'C*n',  'Ref' : None,       'Value' : None, 'Text' : 'Load board ID                         ', 'Missing' : ''  },
                'DIB_TYP'  : {'#' : 13, 'Type' : 'C*n',  'Ref' : None,       'Value' : None, 'Text' : 'DIB (aka load-) board type            ', 'Missing' : ''  },
                'DIB_ID'   : {'#' : 14, 'Type' : 'C*n',  'Ref' : None,       'Value' : None, 'Text' : 'DIB (aka load-) board ID              ', 'Missing' : ''  },
                'CABL_TYP' : {'#' : 15, 'Type' : 'C*n',  'Ref' : None,       'Value' : None, 'Text' : 'Interface cable type                  ', 'Missing' : ''  },
                'CABL_ID'  : {'#' : 16, 'Type' : 'C*n',  'Ref' : None,       'Value' : None, 'Text' : 'Interface cable ID                    ', 'Missing' : ''  },
                'CONT_TYP' : {'#' : 17, 'Type' : 'C*n',  'Ref' : None,       'Value' : None, 'Text' : 'Handler contactor type                ', 'Missing' : ''  },
                'CONT_ID'  : {'#' : 18, 'Type' : 'C*n',  'Ref' : None,       'Value' : None, 'Text' : 'Handler contactor ID                  ', 'Missing' : ''  },
                'LASR_TYP' : {'#' : 19, 'Type' : 'C*n',  'Ref' : None,       'Value' : None, 'Text' : 'Laser type                            ', 'Missing' : ''  },
                'LASR_ID'  : {'#' : 20, 'Type' : 'C*n',  'Ref' : None,       'Value' : None, 'Text' : 'Laser ID                              ', 'Missing' : ''  },
                'EXTR_TYP' : {'#' : 21, 'Type' : 'C*n',  'Ref' : None,       'Value' : None, 'Text' : 'Extra equipment type                  ', 'Missing' : ''  },
                'EXTR_ID'  : {'#' : 22, 'Type' : 'C*n',  'Ref' : None,       'Value' : None, 'Text' : 'Extra equipment ID                    ', 'Missing' : ''  }
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)

class SHB(STDR):
    def __init__(self, version=None, endian=None, record = None):
        self.id = 'SHB'
        self.local_debug = False
        if version==None or version == 'V3':
            self.version = 'V3'
            self.info = '''
Site specific Hardware bin Record (V3+)
---------------------------------------

Function:
    Stores a count of the parts tested at one test site that are physically placed in a particular bin after testing.
    The SHB stores site specific information, that is, information generated at one site of the tester. 
    It is therefore a subset of the Hardware Bin Record (HBR), which collects information from all the sites of a tester.
    The STDF specification also supports a site specific Software Bin Record (SSB), for logical binning categories. 
    The part is actually placed in a hardware bin after testing. A part can be logically associated with a software bin during or after testing.
        
Frequency: 
    ?!?
    
Location: 
    ?!?
'''
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' : 'U*2',  'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' : None},
                'REC_TYP'  : {'#' :  1, 'Type' : 'U*1',  'Ref' : None, 'Value' :   25, 'Text' : 'Record type                           ', 'Missing' : None},
                'REC_SUB'  : {'#' :  2, 'Type' : 'U*1',  'Ref' : None, 'Value' :   10, 'Text' : 'Record sub-type                       ', 'Missing' : None},        
                'HEAD_NUM' : {'#' :  3, 'Type' : 'U*1',  'Ref' : None, 'Value' : None, 'Text' : 'Test head number                      ', 'Missing' : 1   },
                'SITE_NUM' : {'#' :  4, 'Type' : 'U*1',  'Ref' : None, 'Value' : None, 'Text' : 'Test site number                      ', 'Missing' : 1   },
                'HBIN_NUM' : {'#' :  5, 'Type' : 'U*2',  'Ref' : None, 'Value' : None, 'Text' : 'Hardware bin number                   ', 'Missing' : None},
                'HBIN_CNT' : {'#' :  6, 'Type' : 'U*4',  'Ref' : None, 'Value' : None, 'Text' : 'Number of parts in bin                ', 'Missing' : 0   },
                'HBIN_NAM' : {'#' :  7, 'Type' : 'C*n',  'Ref' : None, 'Value' : None, 'Text' : 'Name of hardware bin                  ', 'Missing' : ''  }
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)
    
class SSB(STDR):
    def __init__(self, version=None, endian=None, record = None):
        self.id = 'SSB'
        self.local_debug = False
        if version==None or version == 'V3':
            self.version = 'V3'
            self.info = '''
Site specific Software Bin record (V3+)
---------------------------------------

Function:
    Stores a count of the parts tested at one test site that are associated with a particular logical bin after testing.
    The SSB stores site specific information, that is, information generated at one site of the tester. 
    It is therefore a subset of the Software Bin Record (SBR), which collects information from all the sites of a tester.
    The STDF specification also supports a site specific Hardware Bin Record (SHB), for physical binning categories.
    The part is actually placed in a hardware bin after testing. A part can be logically associated with a software bin during or after testing.
        
Frequency: 
    ?!?
    
Location: 
    ?!?
'''
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' : 'U*2',  'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' : None},
                'REC_TYP'  : {'#' :  1, 'Type' : 'U*1',  'Ref' : None, 'Value' :   25, 'Text' : 'Record type                           ', 'Missing' : None},
                'REC_SUB'  : {'#' :  2, 'Type' : 'U*1',  'Ref' : None, 'Value' :   20, 'Text' : 'Record sub-type                       ', 'Missing' : None},        
                'HEAD_NUM' : {'#' :  3, 'Type' : 'U*1',  'Ref' : None, 'Value' : None, 'Text' : 'Test head number                      ', 'Missing' : 1   },
                'SITE_NUM' : {'#' :  4, 'Type' : 'U*1',  'Ref' : None, 'Value' : None, 'Text' : 'Test site number                      ', 'Missing' : 1   },
                'SBIN_NUM' : {'#' :  5, 'Type' : 'U*2',  'Ref' : None, 'Value' : None, 'Text' : 'Hardware bin number                   ', 'Missing' : None},
                'SBIN_CNT' : {'#' :  6, 'Type' : 'U*4',  'Ref' : None, 'Value' : None, 'Text' : 'Number of parts in bin                ', 'Missing' : 0   },
                'SBIN_NAM' : {'#' :  7, 'Type' : 'C*n',  'Ref' : None, 'Value' : None, 'Text' : 'Name of hardware bin                  ', 'Missing' : ''  }
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)

class SSR(STDR):
    def __init__(self, version=None, endian=None, record = None):
        self.id = 'SSR'
        self.local_debug = False
        if version==None or version == 'V4':
            self.version = 'V4'
            self.info=    '''
Scan Structure Record 
---------------------
    
Function: 
    This record contains the Scan Structure information normally found in a STIL file. 
    The SSR is a top level Scan Structure record that contains an array of indexes to CDR 
    (Chain Description Record) records which contain the chain information.
        
Frequency: 
    ?!?
        
Location:
    ?!?
'''
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' : 'U*2',  'Ref' : None,      'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' : None},
                'REC_TYP'  : {'#' :  1, 'Type' : 'U*1',  'Ref' : None,      'Value' :    1, 'Text' : 'Record type                           ', 'Missing' : None},
                'REC_SUB'  : {'#' :  2, 'Type' : 'U*1',  'Ref' : None,      'Value' :   93, 'Text' : 'Record sub-type                       ', 'Missing' : None},
                'SSR_NAM'  : {'#' :  3, 'Type' : 'C*n',  'Ref' : None,      'Value' : None, 'Text' : 'Name of the STIL Scan Structure       ', 'Missing' : ''  },
                'CHN_CNT'  : {'#' :  4, 'Type' : 'U*2',  'Ref' : None,      'Value' : None, 'Text' : 'Count (k) of number of Chains         ', 'Missing' : 0   },
                'CHN_LIST' : {'#' :  5, 'Type' : 'xU*2', 'Ref' : 'CHN_CNT', 'Value' : None, 'Text' : 'Array of CDR Indexes                  ', 'Missing' : []  }
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)
            
class STR(STDR):
    def __init__(self, version=None, endian=None, record = None):
        self.id = 'STR'
        self.local_debug = False
        if version==None or version=='V4':
            self.version = 'V4'
            self.info=    '''
Record 
------------------
    
Function: 
    It contains all or some of the results of the single execution of a scan test in the test program. 
    It is intended to contain all of the individual pin/cycle failures that are detected in a single test execution. 
    If there are more failures than can be contained in a single record, then the record may be followed by additional continuation STR records.
        
Frequency: 
    ?!?
    
Location:
    ?!?
'''
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' : 'U*2',  'Ref' : None,                     'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' : None   },
                'REC_TYP'  : {'#' :  1, 'Type' : 'U*1',  'Ref' : None,                     'Value' :   15, 'Text' : 'Record type                           ', 'Missing' : None   },
                'REC_SUB'  : {'#' :  2, 'Type' : 'U*1',  'Ref' : None,                     'Value' :   30, 'Text' : 'Record sub-type                       ', 'Missing' : None   },
                'CONT_FLG' : {'#' :  3, 'Type' : 'B*1',  'Ref' : None,                     'Value' : None, 'Text' : 'Continuation STRs follow (if not 0)   ', 'Missing' : 0      },
                'TEST_NUM' : {'#' :  4, 'Type' : 'U*4',  'Ref' : None,                     'Value' : None, 'Text' : 'Test number                           ', 'Missing' : None   },
                'HEAD_NUM' : {'#' :  5, 'Type' : 'U*1',  'Ref' : None,                     'Value' : None, 'Text' : 'Test head number                      ', 'Missing' : 1      },
                'SITE_NUM' : {'#' :  6, 'Type' : 'U*1',  'Ref' : None,                     'Value' : None, 'Text' : 'Test site number                      ', 'Missing' : 1      },
                'PSR_REF'  : {'#' :  7, 'Type' : 'U*2',  'Ref' : None,                     'Value' : None, 'Text' : 'PSR Index (Pattern Sequence Record)   ', 'Missing' : 0      },
                'TEST_FLG' : {'#' :  8, 'Type' : 'B*1',  'Ref' : None,                     'Value' : None, 'Text' : 'Test flags (fail, alarm, etc.)        ', 'Missing' : ['0']*8},
                'LOG_TYP'  : {'#' :  9, 'Type' : 'C*n',  'Ref' : None,                     'Value' : None, 'Text' : 'User defined description of datalog   ', 'Missing' : ''     },
                'TEST_TXT' : {'#' : 10, 'Type' : 'C*n',  'Ref' : None,                     'Value' : None, 'Text' : 'Descriptive text or label             ', 'Missing' : ''     },
                'ALARM_ID' : {'#' : 11, 'Type' : 'C*n',  'Ref' : None,                     'Value' : None, 'Text' : 'Name of alarm                         ', 'Missing' : ''     },
                'PROG_TXT' : {'#' : 12, 'Type' : 'C*n',  'Ref' : None,                     'Value' : None, 'Text' : 'Additional Programmed information     ', 'Missing' : ''     },
                'RSLT_TXT' : {'#' : 13, 'Type' : 'C*n',  'Ref' : None,                     'Value' : None, 'Text' : 'Additional result information         ', 'Missing' : ''     },
                'Z_VAL'    : {'#' : 14, 'Type' : 'U*1',  'Ref' : None,                     'Value' : None, 'Text' : 'Z Handling Flag                       ', 'Missing' : 0      },
                'FMU_FLG'  : {'#' : 15, 'Type' : 'B*1',  'Ref' : None,                     'Value' : None, 'Text' : 'MASK_MAP & FAL_MAP field status       ', 'Missing' : ['0']*8},
                'MASK_MAP' : {'#' : 16, 'Type' : 'D*n',  'Ref' : None,                     'Value' : None, 'Text' : 'Bit map of Globally Masked Pins       ', 'Missing' : []     },
                'FAL_MAP'  : {'#' : 17, 'Type' : 'D*n',  'Ref' : None,                     'Value' : None, 'Text' : 'Bit map of failures after buffer full ', 'Missing' : []     },
                'CYC_CNT'  : {'#' : 18, 'Type' : 'U*8',  'Ref' : None,                     'Value' : None, 'Text' : 'Total cycles executed in test         ', 'Missing' : 0      },
                'TOTF_CNT' : {'#' : 19, 'Type' : 'U*4',  'Ref' : None,                     'Value' : None, 'Text' : 'Total failures (pin x cycle) detected ', 'Missing' : 0      },
                'TOTL_CNT' : {'#' : 20, 'Type' : 'U*4',  'Ref' : None,                     'Value' : None, 'Text' : "Total fails logged across all STR's   ", 'Missing' : 0      },
                'CYC_BASE' : {'#' : 21, 'Type' : 'U*8',  'Ref' : None,                     'Value' : None, 'Text' : 'Cycle offset to apply to CYCL_NUM arr ', 'Missing' : 0      },
                'BIT_BASE' : {'#' : 22, 'Type' : 'U*4',  'Ref' : None,                     'Value' : None, 'Text' : 'Offset to apply to BIT_POS array      ', 'Missing' : 0      },
                'COND_CNT' : {'#' : 23, 'Type' : 'U*2',  'Ref' : None,                     'Value' : None, 'Text' : 'Count (g) of Test Conditions+opt spec ', 'Missing' : 0      },
                'LIM_CNT'  : {'#' : 24, 'Type' : 'U*2',  'Ref' : None,                     'Value' : None, 'Text' : 'Count (j) of LIM Arrays in cur. rec.  ', 'Missing' : 0      }, # 1 = global
                'CYC_SIZE' : {'#' : 25, 'Type' : 'U*1',  'Ref' : None,                     'Value' : None, 'Text' : 'Size (f) [1,2,4 or 8] of  CYC_OFST    ', 'Missing' : 1      },
                'PMR_SIZE' : {'#' : 26, 'Type' : 'U*1',  'Ref' : None,                     'Value' : None, 'Text' : 'Size (f) [1 or 2] of PMR_INDX         ', 'Missing' : 1      },
                'CHN_SIZE' : {'#' : 27, 'Type' : 'U*1',  'Ref' : None,                     'Value' : None, 'Text' : 'Size (f) [1, 2 or 4] of CHN_NUM       ', 'Missing' : 1      },
                'PAT_SIZE' : {'#' : 28, 'Type' : 'U*1',  'Ref' : None,                     'Value' : None, 'Text' : 'Size (f) [1,2, or 4] of PAT_NUM       ', 'Missing' : 1      },
                'BIT_SIZE' : {'#' : 29, 'Type' : 'U*1',  'Ref' : None,                     'Value' : None, 'Text' : 'Size (f) [1,2, or 4] of BIT_POS       ', 'Missing' : 1      },
                'U1_SIZE'  : {'#' : 30, 'Type' : 'U*1',  'Ref' : None,                     'Value' : None, 'Text' : 'Size (f) [1,2,4 or 8] of USR1         ', 'Missing' : 1      },
                'U2_SIZE'  : {'#' : 31, 'Type' : 'U*1',  'Ref' : None,                     'Value' : None, 'Text' : 'Size (f) [1,2,4 or 8] of USR2         ', 'Missing' : 1      },
                'U3_SIZE'  : {'#' : 32, 'Type' : 'U*1',  'Ref' : None,                     'Value' : None, 'Text' : 'Size (f) [1,2,4 or 8] of USR3         ', 'Missing' : 1      },
                'UTX_SIZE' : {'#' : 33, 'Type' : 'U*1',  'Ref' : None,                     'Value' : None, 'Text' : 'Size (f) of each string in USER_TXT   ', 'Missing' : 0      },
                'CAP_BGN'  : {'#' : 34, 'Type' : 'U*2',  'Ref' : None,                     'Value' : None, 'Text' : 'Offset to BIT_POS to get capture cycls', 'Missing' : 0      },
                'LIM_INDX' : {'#' : 35, 'Type' : 'xU*2', 'Ref' : 'LIM_CNT',                'Value' : None, 'Text' : 'Array of PMR unique limit specs       ', 'Missing' : []     },
                'LIM_SPEC' : {'#' : 36, 'Type' : 'xU*4', 'Ref' : 'LIM_CNT',                'Value' : None, 'Text' : "Array of fail datalog limits for PMR's", 'Missing' : []     },
                'COND_LST' : {'#' : 37, 'Type' : 'xC*n', 'Ref' : 'COND_CNT',               'Value' : None, 'Text' : 'Array of test condition (Name=value)  ', 'Missing' : []     },
                'CYC_CNT'  : {'#' : 38, 'Type' : 'U*2',  'Ref' : None,                     'Value' : None, 'Text' : 'Count (k) of entries in CYC_OFST array', 'Missing' : 0      },
                'CYC_OFST' : {'#' : 39, 'Type' : 'xU*f', 'Ref' : ('CYC_CNT', 'CYC_SIZE'),  'Value' : None, 'Text' : 'Array of cycle nrs relat to CYC_BASE  ', 'Missing' : []     },
                'PMR_CNT'  : {'#' : 40, 'Type' : 'U*2',  'Ref' : None,                     'Value' : None, 'Text' : 'Count (k) of entries in the PMR_INDX  ', 'Missing' : 0      },
                'PMR_INDX' : {'#' : 41, 'Type' : 'xU*f', 'Ref' : ('PMR_CNT', 'PMR_SIZE'),  'Value' : None, 'Text' : 'Array of PMR Indexes (All Formats)    ', 'Missing' : []     },
                'CHN_CNT'  : {'#' : 42, 'Type' : 'U*2',  'Ref' : None,                     'Value' : None, 'Text' : 'Count (k) of entries in the CHN_NUM   ', 'Missing' : 0      },
                'CHN_NUM'  : {'#' : 43, 'Type' : 'xU*f', 'Ref' : ('CHN_CNT', 'CHN_SIZE'),  'Value' : None, 'Text' : 'Array of Chain No for FF Name Mapping ', 'Missing' : []     },
                'EXP_CNT'  : {'#' : 44, 'Type' : 'U*2',  'Ref' : None,                     'Value' : None, 'Text' : 'Count (k) of EXP_DATA array entries   ', 'Missing' : 0      },
                'EXP_DATA' : {'#' : 45, 'Type' : 'xU*1', 'Ref' : 'EXP_CNT',                'Value' : None, 'Text' : 'Array of expected vector data         ', 'Missing' : []     },
                'CAP_CNT'  : {'#' : 46, 'Type' : 'U*2',  'Ref' : None,                     'Value' : None, 'Text' : 'Count (k) of CAP_DATA array entries   ', 'Missing' : 0      },
                'CAP_DATA' : {'#' : 47, 'Type' : 'xU*1', 'Ref' : 'CAP_CNT',                'Value' : None, 'Text' : 'Array of captured data                ', 'Missing' : []     },
                'NEW_CNT'  : {'#' : 48, 'Type' : 'U*2',  'Ref' : None,                     'Value' : None, 'Text' : 'Count (k) of NEW_DATA array entries   ', 'Missing' : 0      },
                'NEW_DATA' : {'#' : 49, 'Type' : 'xU*1', 'Ref' : 'NEW_CNT',                'Value' : None, 'Text' : 'Array of new vector data              ', 'Missing' : []     },
                'PAT_CNT'  : {'#' : 50, 'Type' : 'U*2',  'Ref' : None,                     'Value' : None, 'Text' : 'Count (k) of PAT_NUM array entries    ', 'Missing' : 0      },
                'PAT_NUM'  : {'#' : 51, 'Type' : 'xU*f', 'Ref' : ('PAT_CNT', 'PAT_SIZE'),  'Value' : None, 'Text' : 'Array of pattern # (Ptn/Chn/Bit fmt)  ', 'Missing' : []     },
                'BPOS_CNT' : {'#' : 52, 'Type' : 'U*2',  'Ref' : None,                     'Value' : None, 'Text' : 'Count (k) of BIT_POS array entries    ', 'Missing' : 0      },
                'BIT_POS'  : {'#' : 53, 'Type' : 'xU*f', 'Ref' : ('BPOS_CNT', 'BIT_SIZE'), 'Value' : None, 'Text' : 'Array of chain bit (Ptn/Chn/Bit fmt)  ', 'Missing' : []     },
                'USR1_CNT' : {'#' : 54, 'Type' : 'U*2',  'Ref' : None,                     'Value' : None, 'Text' : 'Count (k) of USR1 array entries       ', 'Missing' : 0      },
                'USR1'     : {'#' : 55, 'Type' : 'xU*f', 'Ref' : ('USR1_CNT', 'U1_SIZE'),  'Value' : None, 'Text' : 'Array of logged fail                  ', 'Missing' : []     },
                'USR2_CNT' : {'#' : 56, 'Type' : 'U*2',  'Ref' : None,                     'Value' : None, 'Text' : 'Count (k) of USR2 array entries       ', 'Missing' : 0      },
                'USR2'     : {'#' : 57, 'Type' : 'xU*f', 'Ref' : ('USR2_CNT', 'U2_SIZE'),  'Value' : None, 'Text' : 'Array of logged fail                  ', 'Missing' : []     },
                'USR3_CNT' : {'#' : 58, 'Type' : 'U*2',  'Ref' : None,                     'Value' : None, 'Text' : 'Count (k) of USR3 array entries       ', 'Missing' : 0      },
                'USR3'     : {'#' : 59, 'Type' : 'xU*f', 'Ref' : ('USR3_CNT', 'U3_SIZE'),  'Value' : None, 'Text' : 'Array of logged fail                  ', 'Missing' : []     },
                'TXT_CNT'  : {'#' : 60, 'Type' : 'U*2',  'Ref' : None,                     'Value' : None, 'Text' : 'Count (k) of USER_TXT array entries   ', 'Missing' : 0      },
                'USER_TXT' : {'#' : 61, 'Type' : 'xC*f', 'Ref' : ('TXT_CNT', 'UTX_SIZE'),  'Value' : None, 'Text' : 'Array of logged fail                  ', 'Missing' : []     }
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)
            
class STS(STDR):
    def __init__(self, version=None, endian=None, record = None):
        self.id = 'STS'
        self.local_debug = False
        if version==None or version=='V3':
            self.version = 'V3'
            self.info=    '''
Site specific Test Synopsis record (V3+)
----------------------------------------
    
Function: 
    Contains the test execution and failure counts at one test site for one parametric or functional test in the test plan. 
    The STS stores site specific information, that is, information generated at one site of the tester. 
    It is therefore a subset of the Test Synopsis Record (TSR), which collects information from all the sites of a tester.
    
Frequency: 
    ?!?
    
Location:
    ?!?
'''
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' : 'U*2',  'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' : None   },
                'REC_TYP'  : {'#' :  1, 'Type' : 'U*1',  'Ref' : None, 'Value' :   25, 'Text' : 'Record type                           ', 'Missing' : None   },
                'REC_SUB'  : {'#' :  2, 'Type' : 'U*1',  'Ref' : None, 'Value' :   30, 'Text' : 'Record sub-type                       ', 'Missing' : None   },
                'HEAD_NUM' : {'#' :  3, 'Type' : 'U*1',  'Ref' : None, 'Value' : None, 'Text' : 'Test head number                      ', 'Missing' : 1      },
                'SITE_NUM' : {'#' :  4, 'Type' : 'U*1',  'Ref' : None, 'Value' : None, 'Text' : 'Test site number                      ', 'Missing' : 1      },
                'TEST_NUM' : {'#' :  5, 'Type' : 'U*4',  'Ref' : None, 'Value' : None, 'Text' : 'Test number                           ', 'Missing' : None   },
                'EXEC_CNT' : {'#' :  6, 'Type' : 'I*4',  'Ref' : None, 'Value' : None, 'Text' : 'Number of test executions             ', 'Missing' : -1     },
                'FAIL_CNT' : {'#' :  7, 'Type' : 'I*4',  'Ref' : None, 'Value' : None, 'Text' : 'Number of test failures               ', 'Missing' : -1     },
                'ALRM_CNT' : {'#' :  8, 'Type' : 'I*4',  'Ref' : None, 'Value' : None, 'Text' : 'Number of alarmed tests               ', 'Missing' : -1     },
                'OPT_FLAG' : {'#' :  9, 'Type' : 'B*1',  'Ref' : None, 'Value' : None, 'Text' : 'Optional Data Flag                    ', 'Missing' : ['1']*8},
                'PAD_BYTE' : {'#' : 10, 'Type' : 'B*1',  'Ref' : None, 'Value' : None, 'Text' : 'Reserved for future use               ', 'Missing' : ['0']*8},
                'TEST_MIN' : {'#' : 11, 'Type' : 'R*4',  'Ref' : None, 'Value' : None, 'Text' : 'Lowest test result value              ', 'Missing' : 0.0    },
                'TEST_MAX' : {'#' : 12, 'Type' : 'R*4',  'Ref' : None, 'Value' : None, 'Text' : 'Highest test result value             ', 'Missing' : 0.0    },
                'TST_MEAN' : {'#' : 13, 'Type' : 'R*4',  'Ref' : None, 'Value' : None, 'Text' : 'Mean of test result values            ', 'Missing' : 0.0    },
                'TST_SDEV' : {'#' : 14, 'Type' : 'R*4',  'Ref' : None, 'Value' : None, 'Text' : 'Standard Deviation of test values     ', 'Missing' : 0.0    },
                'TST_SUMS' : {'#' : 15, 'Type' : 'R*4',  'Ref' : None, 'Value' : None, 'Text' : 'Sum of test result values             ', 'Missing' : 0.0    },
                'TST_SQRS' : {'#' : 16, 'Type' : 'R*4',  'Ref' : None, 'Value' : None, 'Text' : 'Sum of Squares of test result values  ', 'Missing' : 0.0    },
                'TEST_NAM' : {'#' : 17, 'Type' : 'C*n',  'Ref' : None, 'Value' : None, 'Text' : 'Test Name length                      ', 'Missing' : ''     },
                'SEQ_NAME' : {'#' : 18, 'Type' : 'C*n',  'Ref' : None, 'Value' : None, 'Text' : 'Sequencer (program segment) name      ', 'Missing' : ''     },
                'TEST_LBL' : {'#' : 19, 'Type' : 'C*n',  'Ref' : None, 'Value' : None, 'Text' : 'Test text or label                    ', 'Missing' : ''     }
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)
            
class TSR(STDR):
    def __init__(self, version=None, endian=None, record=None):
        self.id = 'TSR'
        self.local_debug = False
        if version==None or version=='V4':
            self.version = 'V4'
            self.info = '''
Test Synopsis Record
--------------------

Function: 
    Contains the test execution and failure counts for one parametric or functional test in
    the test program. Also contains static information, such as test name. The TSR is
    related to the Functional Test Record (FTR), the Parametric Test Record (PTR), and the
    Multiple Parametric Test Record (MPR) by test number, head number, and site
    number.
        
Frequency: 
    * Obligatory, one for each test executed in the test program per Head and site.
    * Optional summary per test head and/or test site.
    * May optionally be used to identify unexecuted tests.
        
Location: 
    Anywhere in the data stream after the initial sequence (see page 14) and before the MRR.
    When test data is being generated in real-time, these records will appear after the last PRR.
'''
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' : None       },
                'REC_TYP'  : {'#' :  1, 'Type' : 'U*1', 'Ref' : None, 'Value' :   10, 'Text' : 'Record type                           ', 'Missing' : None       },
                'REC_SUB'  : {'#' :  2, 'Type' : 'U*1', 'Ref' : None, 'Value' :   30, 'Text' : 'Record sub-type                       ', 'Missing' : None       },
                'HEAD_NUM' : {'#' :  3, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'Test head number                      ', 'Missing' : 255        },
                'SITE_NUM' : {'#' :  4, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'Test site number                      ', 'Missing' : 255        },
                'TEST_TYP' : {'#' :  5, 'Type' : 'C*1', 'Ref' : None, 'Value' : None, 'Text' : 'Test type [P/F/space]                 ', 'Missing' : ' '        },
                'TEST_NUM' : {'#' :  6, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : 'Test number                           ', 'Missing' : None       },
                'EXEC_CNT' : {'#' :  7, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : 'Number of test executions             ', 'Missing' : 4294967295},
                'FAIL_CNT' : {'#' :  8, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : 'Number of test failures               ', 'Missing' : 4294967295},
                'ALRM_CNT' : {'#' :  9, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : 'Number of alarmed tests               ', 'Missing' : 4294967295},
                'TEST_NAM' : {'#' : 10, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Test name                             ', 'Missing' : ''         },
                'SEQ_NAME' : {'#' : 11, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Sequencer (program segment/flow) name ', 'Missing' : ''         },
                'TEST_LBL' : {'#' : 12, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Test label or text                    ', 'Missing' : ''         },
                'OPT_FLAG' : {'#' : 13, 'Type' : 'B*1', 'Ref' : None, 'Value' : None, 'Text' : 'Optional data flag See note           ', 'Missing' : ['1']*8    },
                'TEST_TIM' : {'#' : 14, 'Type' : 'R*4', 'Ref' : None, 'Value' : None, 'Text' : 'Average test execution time in seconds', 'Missing' : 0.0        },
                'TEST_MIN' : {'#' : 15, 'Type' : 'R*4', 'Ref' : None, 'Value' : None, 'Text' : 'Lowest test result value              ', 'Missing' : 0.0        },
                'TEST_MAX' : {'#' : 16, 'Type' : 'R*4', 'Ref' : None, 'Value' : None, 'Text' : 'Highest test result value             ', 'Missing' : 0.0        },
                'TST_SUMS' : {'#' : 17, 'Type' : 'R*4', 'Ref' : None, 'Value' : None, 'Text' : 'Sum of test result values             ', 'Missing' : 0.0        },
                'TST_SQRS' : {'#' : 18, 'Type' : 'R*4', 'Ref' : None, 'Value' : None, 'Text' : 'Sum of squares of test result values  ', 'Missing' : 0.0        }
            }
        elif version == 'V3':
            self.version = 'V3'
            self.info = '''
Test Synopsis Record
--------------------

Function: 
    Contains the test execution and failure counts for one parametric or functional test in
    the test program. Also contains static information, such as test name. The TSR is
    related to the Functional Test Record (FTR), the Parametric Test Record (PTR), and the
    Multiple Parametric Test Record (MPR) by test number, head number, and site
    number.
        
Frequency: 
    * Obligatory, one for each test executed in the test program per Head and site.
    * Optional summary per test head and/or test site.
    * May optionally be used to identify unexecuted tests.
        
Location: 
    Anywhere in the data stream after the initial sequence (see page 14) and before the MRR.
    When test data is being generated in real-time, these records will appear after the last PRR.
'''
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' : None       },
                'REC_TYP'  : {'#' :  1, 'Type' : 'U*1', 'Ref' : None, 'Value' :   10, 'Text' : 'Record type                           ', 'Missing' : None       },
                'REC_SUB'  : {'#' :  2, 'Type' : 'U*1', 'Ref' : None, 'Value' :   30, 'Text' : 'Record sub-type                       ', 'Missing' : None       },
                'TEST_NUM' : {'#' :  3, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : 'Test number                           ', 'Missing' : None       },
                'EXEC_CNT' : {'#' :  4, 'Type' : 'I*4', 'Ref' : None, 'Value' : None, 'Text' : 'Number of test executions             ', 'Missing' : 4294967295},
                'FAIL_CNT' : {'#' :  5, 'Type' : 'I*4', 'Ref' : None, 'Value' : None, 'Text' : 'Number of test failures               ', 'Missing' : 4294967295},
                'ALRM_CNT' : {'#' :  6, 'Type' : 'I*4', 'Ref' : None, 'Value' : None, 'Text' : 'Number of alarmed tests               ', 'Missing' : 4294967295},
                'OPT_FLAG' : {'#' :  7, 'Type' : 'B*1', 'Ref' : None, 'Value' : None, 'Text' : 'Optional data flag See note           ', 'Missing' : ['1']*8    },
                'PAD_BYTE' : {'#' :  8, 'Type' : 'B*1', 'Ref' : None, 'Value' : None, 'Text' : 'Padding byte                          ', 'Missing' : ['0']*8    },
                'TEST_MIN' : {'#' :  9, 'Type' : 'R*4', 'Ref' : None, 'Value' : None, 'Text' : 'Lowest test result value              ', 'Missing' : 0.0        },
                'TEST_MAX' : {'#' : 10, 'Type' : 'R*4', 'Ref' : None, 'Value' : None, 'Text' : 'Highest test result value             ', 'Missing' : 0.0        },
                'TST_MEAN' : {'#' : 11, 'Type' : 'R*4', 'Ref' : None, 'Value' : None, 'Text' : 'Mean of test result values            ', 'Missing' : 0.0        },
                'TST_SDEV' : {'#' : 12, 'Type' : 'R*4', 'Ref' : None, 'Value' : None, 'Text' : 'Standard Deviation of test results    ', 'Missing' : 0.0        },
                'TST_SUMS' : {'#' : 13, 'Type' : 'R*4', 'Ref' : None, 'Value' : None, 'Text' : 'Sum of test result values             ', 'Missing' : 0.0        },
                'TST_SQRS' : {'#' : 14, 'Type' : 'R*4', 'Ref' : None, 'Value' : None, 'Text' : 'Sum of squares of test result values  ', 'Missing' : 0.0        },
                'TEST_NAM' : {'#' : 15, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Test name                             ', 'Missing' : ''         },
                'SEQ_NAME' : {'#' : 16, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Sequence name                         ', 'Missing' : ''         },
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)

class VUR(STDR):
    def __init__(self, version=None, endian=None, record = None):
        self.id = 'VUR'
        self.local_debug = False
        if version==None or version=='V4':
            self.version = 'V4'
            self.info=    '''
Version Update Record 
---------------------
    
Function: 
    Version update Record is used to identify the updates over version V4. 
    Presence of this record indicates that the file may contain records defined by the new standard. 

Frequency: 
    * One for each extension to STDF V4 used.
    
Location:
    Just before the MIR
'''
            self.fields = {
                'REC_LEN'  : {'#' : 0, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' : None},
                'REC_TYP'  : {'#' : 1, 'Type' : 'U*1', 'Ref' : None, 'Value' :    0, 'Text' : 'Record type                           ', 'Missing' : None},
                'REC_SUB'  : {'#' : 2, 'Type' : 'U*1', 'Ref' : None, 'Value' :   30, 'Text' : 'Record sub-type                       ', 'Missing' : None},
                'UPD_NAM'  : {'#' : 3, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Update Version Name                   ', 'Missing' : ''  }
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)

class WCR(STDR):
    def __init__(self, version=None, endian=None, record=None):
        self.id = 'WCR'
        self.local_debug = False
        if version==None or version=='V4' or version=='V3':
            if version==None: self.version='V4'
            else: self.version = version
            self.info = '''
Wafer Configuration Record
--------------------------

Function: 
    Contains the configuration information for the wafers tested by the job plan. The
    WCR provides the dimensions and orientation information for all wafers and dice
    in the lot. This record is used only when testing at wafer probe time.
        
Frequency: 
    * Obligatory for Wafer sort
    * One per STDF file
        
Location:
    Anywhere in the data stream after the initial "FAR-(ATRs)-MIR-(RDR)-(SDRs)" sequence, and before the MRR.
'''
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' : None  },
                'REC_TYP'  : {'#' :  1, 'Type' : 'U*1', 'Ref' : None, 'Value' :    2, 'Text' : 'Record type                           ', 'Missing' : None  },
                'REC_SUB'  : {'#' :  2, 'Type' : 'U*1', 'Ref' : None, 'Value' :   30, 'Text' : 'Record sub-type                       ', 'Missing' : None  },        
                'WAFR_SIZ' : {'#' :  3, 'Type' : 'R*4', 'Ref' : None, 'Value' : None, 'Text' : 'Diameter of wafer in WF_UNITS         ', 'Missing' : 0.0   },
                'DIE_HT'   : {'#' :  4, 'Type' : 'R*4', 'Ref' : None, 'Value' : None, 'Text' : 'Height of die in WF_UNITS             ', 'Missing' : 0.0   },
                'DIE_WID'  : {'#' :  5, 'Type' : 'R*4', 'Ref' : None, 'Value' : None, 'Text' : 'Width of die in WF_UNITS              ', 'Missing' : 0.0   },
                'WF_UNITS' : {'#' :  6, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'Units for wafer and die dimensions    ', 'Missing' : 0     }, # 0=?/1=Inch/2=cm/3=mm/4=mils
                'WF_FLAT'  : {'#' :  7, 'Type' : 'C*1', 'Ref' : None, 'Value' : None, 'Text' : 'Orientation of wafer flat (U/D/L/R)   ', 'Missing' : ' '   },
                'CENTER_X' : {'#' :  8, 'Type' : 'I*2', 'Ref' : None, 'Value' : None, 'Text' : 'X coordinate of center die on wafer   ', 'Missing' : -32768},  
                'CENTER_Y' : {'#' :  9, 'Type' : 'I*2', 'Ref' : None, 'Value' : None, 'Text' : 'Y coordinate of center die on wafer   ', 'Missing' : -32768},
                'POS_X'    : {'#' : 10, 'Type' : 'C*1', 'Ref' : None, 'Value' : None, 'Text' : 'Positive X direction of wafer (L/R)   ', 'Missing' : ' '   },
                'POS_Y'    : {'#' : 11, 'Type' : 'C*1', 'Ref' : None, 'Value' : None, 'Text' : 'Positive Y direction of wafer (U/D)   ', 'Missing' : ' '   }
            }        
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)
        
class WIR(STDR):
    def __init__(self, version=None, endian=None, record=None):
        self.id = 'WIR'
        self.local_debug = False
        if version==None or version=='V4':
            self.version = 'V4'
            self.info = '''
Wafer Information Record
------------------------

Function: 
    Acts mainly as a marker to indicate where testing of a particular wafer begins for each
    wafer tested by the job plan. The WIR and the Wafer Results Record (WRR) bracket all
    the stored information pertaining to one tested wafer. This record is used only when
    testing at wafer probe. A WIR/WRR pair will have the same HEAD_NUM and SITE_GRP values.
        
Frequency: 
    * Obligatory for Wafer sort
    * One per wafer tested.
        
Location: 
    Anywhere in the data stream after the initial sequence (see page 14) and before the MRR.
    Sent before testing each wafer.
'''
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' : None},
                'REC_TYP'  : {'#' :  1, 'Type' : 'U*1', 'Ref' : None, 'Value' :    2, 'Text' : 'Record type                           ', 'Missing' : None},
                'REC_SUB'  : {'#' :  2, 'Type' : 'U*1', 'Ref' : None, 'Value' :   10, 'Text' : 'Record sub-type                       ', 'Missing' : None},        
                'HEAD_NUM' : {'#' :  3, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'Test head number                      ', 'Missing' : 1   },
                'SITE_GRP' : {'#' :  4, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'Site group number                     ', 'Missing' : 255 },
                'START_T'  : {'#' :  5, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : 'Date and time first part tested       ', 'Missing' : 0   },
                'WAFER_ID' : {'#' :  6, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Wafer ID                              ', 'Missing' : ''  }
            }
        elif version == 'V3':
            self.version = 'V3'
            self.info = '''
Wafer Information Record
------------------------

Function: 
    Acts mainly as a marker to indicate where testing of a particular wafer begins for each
    wafer tested by the job plan. The WIR and the Wafer Results Record (WRR) bracket all
    the stored information pertaining to one tested wafer. This record is used only when
    testing at wafer probe. A WIR/WRR pair will have the same HEAD_NUM and SITE_GRP values.
        
Frequency: 
    * Obligatory for Wafer sort
    * One per wafer tested.
        
Location: 
    Anywhere in the data stream after the initial sequence (see page 14) and before the MRR.
    Sent before testing each wafer.
'''
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' : None   },
                'REC_TYP'  : {'#' :  1, 'Type' : 'U*1', 'Ref' : None, 'Value' :    2, 'Text' : 'Record type                           ', 'Missing' : None   },
                'REC_SUB'  : {'#' :  2, 'Type' : 'U*1', 'Ref' : None, 'Value' :   10, 'Text' : 'Record sub-type                       ', 'Missing' : None   },        
                'HEAD_NUM' : {'#' :  3, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'Test head number                      ', 'Missing' : 1      },
                'PAD_BYTE' : {'#' :  4, 'Type' : 'B*1', 'Ref' : None, 'Value' : None, 'Text' : 'Pad byte                              ', 'Missing' : ['0']*8},
                'START_T'  : {'#' :  5, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : 'Date and time first part tested       ', 'Missing' : 0      },
                'WAFER_ID' : {'#' :  6, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Wafer ID                              ', 'Missing' : ''     }
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)
        
class WRR(STDR):
    def __init__(self, version=None, endian=None, record=None):
        self.id = 'WRR'
        self.local_debug = False
        if version==None or version=='V4':
            self.version = 'V4'
            self.info = '''
Wafer Results Record
--------------------

Function: 
    Contains the result information relating to each wafer tested by the job plan. The WRR
    and the Wafer Information Record (WIR) bracket all the stored information pertaining
    to one tested wafer. This record is used only when testing at wafer probe time. A
    WIR/WRR pair will have the same HEAD_NUM and SITE_GRP values.
        
Frequency: 
    * Obligatory for Wafer sort
    * One per wafer tested.
        
Location:
    Anywhere in the data stream after the corresponding WIR.
    Sent after testing each wafer.
'''
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' : None      },
                'REC_TYP'  : {'#' :  1, 'Type' : 'U*1', 'Ref' : None, 'Value' :    2, 'Text' : 'Record type                           ', 'Missing' : None      },
                'REC_SUB'  : {'#' :  2, 'Type' : 'U*1', 'Ref' : None, 'Value' :   20, 'Text' : 'Record sub-type                       ', 'Missing' : None      },        
                'HEAD_NUM' : {'#' :  3, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'Test head number                      ', 'Missing' : 255       },
                'SITE_GRP' : {'#' :  4, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'Site group number                     ', 'Missing' : 255       },
                'FINISH_T' : {'#' :  5, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : 'Date and time last part tested        ', 'Missing' : 0         },
                'PART_CNT' : {'#' :  6, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : 'Number of parts tested                ', 'Missing' : 0         },
                'RTST_CNT' : {'#' :  7, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : 'Number of parts retested              ', 'Missing' : 4294967295},
                'ABRT_CNT' : {'#' :  8, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : 'Number of aborts during testing       ', 'Missing' : 4294967295},
                'GOOD_CNT' : {'#' :  9, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : 'Number of good (passed) parts tested  ', 'Missing' : 4294967295},
                'FUNC_CNT' : {'#' : 10, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : 'Number of functional parts tested     ', 'Missing' : 4294967295},
                'WAFER_ID' : {'#' : 11, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Wafer ID                              ', 'Missing' : ''        },
                'FABWF_ID' : {'#' : 12, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Fab wafer ID                          ', 'Missing' : ''        },
                'FRAME_ID' : {'#' : 13, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Wafer frame ID                        ', 'Missing' : ''        },
                'MASK_ID'  : {'#' : 14, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Wafer mask ID                         ', 'Missing' : ''        },
                'USR_DESC' : {'#' : 15, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Wafer description supplied by user    ', 'Missing' : ''        },
                'EXC_DESC' : {'#' : 16, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Wafer description supplied by exec    ', 'Missing' : ''        }
            }            
        elif version == 'V3':
            self.version = 'V3'
            self.info = '''
Wafer Results Record
--------------------

Function: 
    Contains the result information relating to each wafer tested by the job plan. The WRR
    and the Wafer Information Record (WIR) bracket all the stored information pertaining
    to one tested wafer. This record is used only when testing at wafer probe time. A
    WIR/WRR pair will have the same HEAD_NUM and SITE_GRP values.
        
Frequency: 
    * Obligatory for Wafer sort
    * One per wafer tested.
        
Location:
    Anywhere in the data stream after the corresponding WIR.
    Sent after testing each wafer.
'''
            self.fields = {
                'REC_LEN'  : {'#' :  0, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' : None      },
                'REC_TYP'  : {'#' :  1, 'Type' : 'U*1', 'Ref' : None, 'Value' :    2, 'Text' : 'Record type                           ', 'Missing' : None      },
                'REC_SUB'  : {'#' :  2, 'Type' : 'U*1', 'Ref' : None, 'Value' :   20, 'Text' : 'Record sub-type                       ', 'Missing' : None      },        
                'FINISH_T' : {'#' :  3, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : 'Date and time last part tested        ', 'Missing' : 0         },
                'HEAD_NUM' : {'#' :  4, 'Type' : 'U*1', 'Ref' : None, 'Value' : None, 'Text' : 'Test head number                      ', 'Missing' : 255       },
                'PAD_BYTE' : {'#' :  5, 'Type' : 'B*1', 'Ref' : None, 'Value' : None, 'Text' : 'Test head number                      ', 'Missing' : ['0']*8   },
                'PART_CNT' : {'#' :  6, 'Type' : 'U*4', 'Ref' : None, 'Value' : None, 'Text' : 'Number of parts tested                ', 'Missing' : 0         },
                'RTST_CNT' : {'#' :  7, 'Type' : 'I*4', 'Ref' : None, 'Value' : None, 'Text' : 'Number of retests done                ', 'Missing' : 0         },
                'ABRT_CNT' : {'#' :  8, 'Type' : 'I*4', 'Ref' : None, 'Value' : None, 'Text' : 'Number of aborts during testing       ', 'Missing' : 0         },
                'GOOD_CNT' : {'#' :  9, 'Type' : 'I*4', 'Ref' : None, 'Value' : None, 'Text' : 'Number of good (passed) parts tested  ', 'Missing' : 0         },
                'FUNC_CNT' : {'#' : 10, 'Type' : 'I*4', 'Ref' : None, 'Value' : None, 'Text' : 'Number of functional parts tested     ', 'Missing' : 0         },
                'WAFER_ID' : {'#' : 11, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Wafer ID                              ', 'Missing' : ''        },
                'HAND_ID'  : {'#' : 12, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Handler (Prober) ID                   ', 'Missing' : ''        },
                'PRB_CARD' : {'#' : 13, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Probe Card ID                         ', 'Missing' : ''        },
                'USR_DESC' : {'#' : 14, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Wafer description supplied by user    ', 'Missing' : ''        },
                'EXC_DESC' : {'#' : 15, 'Type' : 'C*n', 'Ref' : None, 'Value' : None, 'Text' : 'Wafer description supplied by exec    ', 'Missing' : ''        }
            }            
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)

class WTR(STDR): 
    def __init__(self, version=None, endian=None, record = None):
        self.id = 'WTR'
        self.local_debug = False
        if version==None or version=='V3':
            self.version = 'V3'
            self.info=    '''
?!?
----------------------------------------
    
Function: 
    ?!?
    
Frequency: 
    ?!?
    
Location:
    ?!?
'''
            self.fields = {
                'REC_LEN'   : {'#' : 0, 'Type' : 'U*2', 'Ref' : None, 'Value' : None, 'Text' : 'Bytes of data following header        ', 'Missing' : None},
                'REC_TYP'   : {'#' : 1, 'Type' : 'U*1', 'Ref' : None, 'Value' :  220, 'Text' : 'Record type                           ', 'Missing' : None},
                'REC_SUB'   : {'#' : 2, 'Type' : 'U*1', 'Ref' : None, 'Value' :  202, 'Text' : 'Record sub-type                       ', 'Missing' : None},
                'TEST_TYPE' : {'#' : 3, 'Type' : 'C*1', 'Ref' : None, 'value' : None, 'Text' : '                                      ', 'Missing' : ' ' }
            }
        else:
            raise STDFError("%s object creation error: unsupported version '%s'" % (self.id, version))
        self._default_init(endian, record)

def hexify(input):
    '''
    This function returns the hexified version of input
    
    the input can be a byte array or a string, but the output is always a string.
    '''
    retval = ''
    if isinstance(input, bytes):
        for b in range(len(input)):
            retval += hex(input[b]).upper().replace('0X', '0x')
    elif isinstance(input, str):
        for i in input:
            retval += hex(ord(i)).upper().replace('0X', '0x')
    else:
        raise Exception("input type needs to be bytes or str.")
    return retval

def sys_endian():
    '''
    This function determines the endian of the running system.
    '''
    if sys.byteorder == 'little':
        return '<'
    return '>'

def sys_cpu():
    if sys_endian=='<':
        return 2
    return 1

def is_odd(Number):
    '''
    This function will return True if the Number is odd, False otherwise    
    '''
    if ((Number % 2) == 1):
        return True
    return False

def is_even(Number):
    '''
    This function will return True if the Number is EVEN, False otherwise.
    '''
    if ((Number % 2) == 1):
        return False
    return True

def read_record(fd, RHF):
    '''
    This method will read one record from fd (at the current fp) with record header format RHF, and return the raw record
    '''
    header = fd.read(4)
    REC_LEN, REC_TYP, REC_SUB = struct.unpack(RHF, header)
    footer = fd.read(REC_LEN)
    return REC_LEN, REC_TYP, REC_SUB, header+footer
    
def read_indexed_record(fd, fp, RHF):
    fd.seek(fp)
    header = fd.read(4)
    REC_LEN, REC_TYP, REC_SUB = struct.unpack(RHF, header)
    footer = fd.read(REC_LEN)
    return REC_LEN, REC_TYP, REC_SUB, header+footer

class records_from_file(object):
    '''
    Generator class to run over the records in FileName.
    The return values are 4-fold : REC_LEN, REC_TYP, REC_SUB and REC 
    REC is the complete record (including REC_LEN, REC_TYP & REC_SUB)
    if unpack indicates if REC is to be the raw record or the unpacked object.
    of_interest can be a list of records to return. By default of_interest is void
    meaning all records (of FileName's STDF Version) are used.
    '''
    debug = False
    
    def __init__(self, FileName, unpack=False, of_interest=None):
        if self.debug: print("initializing 'records_from_file")
        if isinstance(FileName, str):
            self.keep_open = False
            if not os.path.exists(FileName): 
                STDFError("'%s' does not exist")
            self.endian = get_STDF_setup_from_file(FileName)[0]
            self.version = 'V%s' % struct.unpack('B', get_bytes_from_file(FileName, 5, 1))
            self.fd = open(FileName, 'rb')
        elif isinstance(FileName, io.IOBase):
            self.keep_open = True
            self.fd = FileName
            ptr = self.fd.tell()
            self.fd.seek(4)
            buff = self.fd.read(2)
            CPU_TYPE = struct.unpack('B', buff[0])[0]
            STDF_VER = struct.unpack('B', buff[1])[0]
            if CPU_TYPE == 1: self.endian = '>'
            elif CPU_TYPE == 2: self.endian = '<'
            else: self.endian = '?'
            self.version = 'V%s' % STDF_VER
            self.fd.seek(ptr)
        else:
            STDFError("'%s' is not a string or an open file descriptor")
        self.unpack = unpack
        self.fmt = '%sHBB' % self.endian
        TS2ID = ts_to_id(self.version)
        if of_interest==None:
            self.records_of_interest = TS2ID
        elif isinstance(of_interest, list):
            ID2TS = id_to_ts(self.version)
            tmp_list = []
            for item in of_interest:
                if isinstance(item, str):
                    if item in ID2TS:
                        if ID2TS[item] not in tmp_list:
                            tmp_list.append(ID2TS[item])
                elif isinstance(item, tuple) and len(item)==2:
                    if item in TS2ID:
                        if item not in tmp_list:
                            tmp_list.append(item)
            self.records_of_interest = tmp_list
        else:
            raise STDFError("objects_from_file(%s, %s) : Unsupported of_interest" % (FileName, of_interest))
        
    def __del__(self):
        if not self.keep_open:
            self.fd.close()
        
    def __iter__(self):
        return self
    
    def __next__(self):
        while self.fd!=None:
            header = self.fd.read(4)
            if len(header)!=4:
                raise StopIteration
            else:
                REC_LEN, REC_TYP, REC_SUB = struct.unpack(self.fmt, header)
                footer = self.fd.read(REC_LEN)
                if (REC_TYP, REC_SUB) in self.records_of_interest:
                    if len(footer)!=REC_LEN:
                        raise StopIteration()
                    else:
                        if self.unpack:
                            return REC_LEN, REC_TYP, REC_SUB, create_record_object(self.version, self.endian, (REC_TYP, REC_SUB), header+footer)
                        else:
                            return REC_LEN, REC_TYP, REC_SUB, header+footer

def objects_from_indexed_file(FileName, index, records_of_interest=None):
    '''
     This is a Generator of records (not in order!) 
    '''
    if not isinstance(FileName, str): STDFError("'%s' is not a string.")
    if not os.path.exists(FileName): STDFError("'%s' does not exist")
    endian = get_STDF_setup_from_file(FileName)[0]
    RLF = '%sH' % endian
    version = 'V%s' % struct.unpack('B', get_bytes_from_file(FileName, 5, 1))
    fd = open(FileName, 'rb')
    
    ALL = list(id_to_ts(version).keys())
    if records_of_interest==None:
        roi = ALL
    elif isinstance(records_of_interest, list):
        roi = []
        for item in records_of_interest:
            if isinstance(item, str):
                if (item in ALL) and (item not in roi):
                    roi.append(item)
    else:
        raise STDFError("objects_from_indexed_file(%s, index, records_of_interest) : Unsupported records_of_interest" % (FileName, records_of_interest))
    for REC_ID in roi:
        if REC_ID in index:
            for fp in index[REC_ID]:
                OBJ = create_record_object(version, endian, REC_ID, get_record_from_file_at_position(fd, fp, RLF))
                yield OBJ

class xrecords_from_file(object):
    '''
    This is a *FAST* iterator class that returns the next record from an STDF file each time it is called.
    It is fast because it doesn't check versions, extensions and it doesn't unpack the record and skips unknown records.
    '''
 
    def __init__(self, FileName, of_interest=None):
        #TODO: add a record_list of records to return
        if isinstance(FileName, str):
            try:
                stdf_file = File(FileName)
            except:
                raise StopIteration
            self.fd = stdf_file.open()
        elif isinstance(FileName, File):
            stdf_file = FileName
            self.fd = FileName.open()
        else:
            raise STDFError("records_from_file(%s) : Unsupported 'FileName'" % FileName)
        self.endian = stdf_file.endian
        self.version = stdf_file.version
        TS2ID = ts_to_id(self.version)
        if of_interest==None:
            self.of_interest = list(TS2ID.keys())
        elif isinstance(of_interest, list):
            ID2TS = id_to_ts(self.version)
            tmp_list = []
            for item in of_interest:
                if isinstance(item, str):
                    if item in ID2TS:
                        if ID2TS[item] not in tmp_list:
                            tmp_list.append(ID2TS[item])
                elif isinstance(item, tuple) and len(item)==2:
                    if item in TS2ID:
                        if item not in tmp_list:
                            tmp_list.append(item)
            self.of_interest = tmp_list
        else:
            raise STDFError("records_from_file(%s, %s) : Unsupported of_interest" % (FileName, of_interest))
            
    def __del__(self):
        self.fd.close()
        
    def __iter__(self):
        return self
    
    def __next__(self):
        while self.fd!=None:
            while True:
                header = self.fd.read(4)
                if len(header)!=4:
                    raise StopIteration
                REC_LEN, REC_TYP, REC_SUB = struct.unpack('HBB', header)
                footer = self.fd.read(REC_LEN)
                if len(footer)!=REC_LEN:
                    raise StopIteration
                if (REC_TYP, REC_SUB) in self.of_interest:
                    return REC_LEN, REC_TYP, REC_SUB, header+footer

class xobjects_from_file(object):
    '''
    This is an iterator class that returns the next object (unpacked) from an STDF file.
    It will take care of versions and extensions, and unrecognized records will simply be skipped.
    '''
    def __init__(self, FileName, of_interest=None): 
        if isinstance(FileName, str):
            try:
                stdf_file = File(FileName)
            except:
                raise STDFError("objects_from_file(%s, %s) : File doesn't exist" % (FileName, of_interest))
            self.fd = stdf_file.open()
        elif isinstance(FileName, File):
            self.fd = FileName.open()
        else:
            raise STDFError("objects_from_file(%s) : Unsupported 'FileName'" % FileName)
        self.endian = stdf_file.endian
        self.version = stdf_file.version
        TS2ID = ts_to_id(self.version)
        if of_interest==None:
            of_interest = TS2ID
        elif isinstance(of_interest, list):
            ID2TS = id_to_ts(self.version)
            tmp_list = []
            for item in of_interest:
                if isinstance(item, str):
                    if item in ID2TS:
                        if ID2TS[item] not in tmp_list:
                            tmp_list.append(ID2TS[item])
                elif isinstance(item, tuple) and len(item)==2:
                    if item in TS2ID:
                        if item not in tmp_list:
                            tmp_list.append(item)
            of_interest = tmp_list
        else:
            raise STDFError("objects_from_file(%s, %s) : Unsupported of_interest" % (FileName, of_interest))
        self.of_interest = of_interest
        self.fmt = '%sHBB' % self.endian
        
    def __del__(self):
        self.fd.close()
    
    def __iter__(self):
        return self
    
    def __next__(self):
        while True:
            header = self.fd.read(4)
            if len(header)!=4:
                raise StopIteration
            else:
                REC_LEN, REC_TYP, REC_SUB = struct.unpack(self.fmt, header)
                footer = self.fd.read(REC_LEN)
                if len(footer)!=REC_LEN:
                    raise StopIteration
                else:
                    record = header + footer
                    if (REC_TYP, REC_SUB) in self.of_interest:
                        recobj = create_record_object(self.version, self.endian, (REC_TYP, REC_SUB), record)
                        return (recobj)


# class open(object):
#     '''
#     file opener that opens an STDF file transparently (gzipped or not)
#     '''
#     def __init__(self, fname):
#         f = open(fname)
#         # Read magic number (the first 2 bytes) and rewind.
#         magic_number = f.read(2)
#         f.seek(0)
#         # Encapsulated 'self.f' is a file or a GzipFile.
#         if magic_number == '\x1f\x8b':
#             self.f = gzip.GzipFile(fileobj=f)
#         else:
#             self.f = f
# 
#         # Define '__enter__' and '__exit__' to use in 'with' blocks. 
#         def __enter__(self):
#             return self
#         def __exit__(self, type, value, traceback):
#             try:
#                 self.f.fileobj.close()
#             except AttributeError:
#                 pass
#             finally:
#                 self.f.close()
# 
#         # Reproduce the interface of an open file by encapsulation.
#         def __getattr__(self, name):
#             return getattr(self.f, name)
#         def __iter__(self):
#             return iter(self.f)
#         def next(self):
#             return next(self.f)



def create_record_object(Version, Endian, REC_ID, REC=None):
    '''  
    This function will create and return the appropriate Object for REC
    based on REC_ID. REC_ID can be a 2-element tuple or a string.
    If REC is not None, then the record will also be unpacked.
    '''
    retval = None
    REC_TYP=-1
    REC_SUB=-1
    if Version not in supported().versions():
        raise STDFError("Unsupported STDF Version : %s" % Version)
    if Endian not in ['<', '>']:
        raise STDFError("Unsupported Endian : '%s'" % Endian)
    if isinstance(REC_ID, tuple) and len(REC_ID)==2:
        TS2ID = ts_to_id(Version)
        if (REC_ID[0], REC_ID[1]) in TS2ID:
            REC_TYP = REC_ID[0]
            REC_SUB = REC_ID[1]
            REC_ID = TS2ID[(REC_TYP, REC_SUB)]
    elif isinstance(REC_ID, str):
        ID2TS = id_to_ts(Version)
        if REC_ID in ID2TS:
            (REC_TYP, REC_SUB) = ID2TS[REC_ID]
    else:
        raise STDFError("Unsupported REC_ID : %s" % REC_ID)

    if REC_TYP!=-1 and REC_SUB!=-1:
        if REC_ID == 'PTR': retval = PTR(Version, Endian, REC)
        elif REC_ID == 'FTR': retval = FTR(Version, Endian, REC)
        elif REC_ID == 'MPR': retval = MPR(Version, Endian, REC)
        elif REC_ID == 'STR': retval = STR(Version, Endian, REC)
        elif REC_ID == 'MTR': retval = MTR(Version, Endian, REC)
        elif REC_ID == 'PIR': retval = PIR(Version, Endian, REC)
        elif REC_ID == 'PRR': retval = PRR(Version, Endian, REC)
        elif REC_ID == 'FAR': retval = FAR(Version, Endian, REC)
        elif REC_ID == 'ATR': retval = ATR(Version, Endian, REC)
        elif REC_ID == 'VUR': retval = VUR(Version, Endian, REC)
        elif REC_ID == 'MIR': retval = MIR(Version, Endian, REC)
        elif REC_ID == 'MRR': retval = MRR(Version, Endian, REC)
        elif REC_ID == 'WCR': retval = WCR(Version, Endian, REC)
        elif REC_ID == 'WIR': retval = WIR(Version, Endian, REC)
        elif REC_ID == 'WRR': retval = WRR(Version, Endian, REC)
        elif REC_ID == 'ADR': retval = ADR(Version, Endian, REC)
        elif REC_ID == 'ASR': retval = ASR(Version, Endian, REC)
        elif REC_ID == 'BPS': retval = BPS(Version, Endian, REC)
        elif REC_ID == 'BRR': retval = BRR(Version, Endian, REC)
        elif REC_ID == 'BSR': retval = BSR(Version, Endian, REC)
        elif REC_ID == 'CNR': retval = CNR(Version, Endian, REC)
        elif REC_ID == 'DTR': retval = DTR(Version, Endian, REC)
        elif REC_ID == 'EPDR': retval = EPDR(Version, Endian, REC)
        elif REC_ID == 'EPS': retval = EPS(Version, Endian, REC)
        elif REC_ID == 'ETSR': retval = ETSR(Version, Endian, REC)
        elif REC_ID == 'FDR': retval = FDR(Version, Endian, REC)
        elif REC_ID == 'FSR': retval = FSR(Version, Endian, REC)
        elif REC_ID == 'GDR': retval = GDR(Version, Endian, REC)
        elif REC_ID == 'GTR': retval = GTR(Version, Endian, REC)
        elif REC_ID == 'HBR': retval = HBR(Version, Endian, REC)
        elif REC_ID == 'IDR': retval = IDR(Version, Endian, REC)
        elif REC_ID == 'MCR': retval = MCR(Version, Endian, REC)
        elif REC_ID == 'MMR': retval = MMR(Version, Endian, REC)
        elif REC_ID == 'MSR': retval = MSR(Version, Endian, REC)
        elif REC_ID == 'NMR': retval = NMR(Version, Endian, REC)
        elif REC_ID == 'PCR': retval = PCR(Version, Endian, REC)
        elif REC_ID == 'PDR': retval = PDR(Version, Endian, REC)
        elif REC_ID == 'PGR': retval = PGR(Version, Endian, REC)
        elif REC_ID == 'PLR': retval = PLR(Version, Endian, REC)
        elif REC_ID == 'PMR': retval = PMR(Version, Endian, REC)
        elif REC_ID == 'PSR': retval = PSR(Version, Endian, REC)
        elif REC_ID == 'RDR': retval = RDR(Version, Endian, REC)
        elif REC_ID == 'SBR': retval = SBR(Version, Endian, REC)
        elif REC_ID == 'SCR': retval = SCR(Version, Endian, REC)
        elif REC_ID == 'SDR': retval = SDR(Version, Endian, REC)
        elif REC_ID == 'SHB': retval = SHB(Version, Endian, REC)
        elif REC_ID == 'SSB': retval = SSB(Version, Endian, REC)
        elif REC_ID == 'SSR': retval = SSR(Version, Endian, REC)
        elif REC_ID == 'STS': retval = STS(Version, Endian, REC)
        elif REC_ID == 'TSR': retval = TSR(Version, Endian, REC)
        elif REC_ID == 'WTR': retval = WTR(Version, Endian, REC)
        elif REC_ID == 'RR1': retval = RR1(Version, Endian, REC) # can not be reached because of -1
        elif REC_ID == 'RR2': retval = RR2(Version, Endian, REC) # can not be reached because of -1
    return retval

def wafer_map(data, parameter=None):
    '''
    data is a pandas data frame, it has at least 5 columns ('X_COORD', 'Y_COORD', 'LOT_ID', 'WAFER_ID' and the parameter)
    If the parameter is not named the following order of 'parameters' will be used :
        'HARD_BIN'
        'SOFT_BIN'
        'PART_PF'
    
    '''
    pass
    

    
def get_bytes_from_file(FileName, Offset, Number):
    '''
    This function will return 'Number' bytes starting after 'Offset' from 'FileName'
    '''
    if not isinstance(FileName, str): STDFError("'%s' is not a string")
    if not isinstance(Offset, int): STDFError("Offset is not an integer")
    if not isinstance(Number, int): STDFError("Number is not an integer")
    if not os.path.exists(FileName): STDFError("'%s' does not exist")
    if guess_type(FileName)[1]=='gzip':
        raise NotImplemented("Not yet implemented")
    else:
        with open(FileName, 'rb') as fd:
            fd.seek(Offset)
            retval = fd.read(Number)
    return retval

def get_record_from_file_at_position(fd, offset, REC_LEN_FMT):
    fd.seek(offset)
    header = fd.read(4)
    REC_LEN = struct.unpack(REC_LEN_FMT, header[:2])[0]
    footer = fd.read(REC_LEN)
    return header+footer
    
def get_STDF_setup_from_file(FileName):
    '''
    This function will determine the endian and the version of a given STDF file
    it must *NOT* be guaranteed that FileName exists or is an STDF File.
    '''    
    endian = None
    version = None
    if os.path.exists(FileName) and os.path.isfile(FileName):
        if '.stdf' in magicnumber.extension_from_magic_number_in_file(FileName):
            CPU_TYP, STDF_VER = struct.unpack('BB', get_bytes_from_file(FileName, 4, 2))
            if CPU_TYP == 1: endian = '>'
            elif CPU_TYP == 2: endian = '<'
            else: endian = '?'
            version = "V%s" % STDF_VER
    return endian, version

def get_MIR_from_file(FileName):
    '''
    This function will just get the MIR (near the start of the file) from the FileName and return it.
    it must *NOT* be guaranteed that FileName exists or is an STDF File.
    '''
    endian, version = get_STDF_setup_from_file(FileName)
    mir = None
    if endian!=None and version!=None: # file exists and is an STDF file
        for record in xrecords_from_file(FileName):
            _, REC_TYP, REC_SUB, REC = record
            if (REC_TYP, REC_SUB) == (1, 10):
                mir = MIR(version, endian, REC)
                break
    return mir

def get_partcount_from_file(FileName):
    '''
    This function will return the number of parts contained in FileName.
    it must *NOT* be guaranteed that FileName exists or is an STDF File.
    '''
    
def save_STDF_index(FileName, index):
    '''
    '''
    if os.path.exists(FileName) and os.path.isfile(FileName):
        Path, Name = os.path.split(FileName)
        Base, Ext = os.path.splitext(Name)
        if Ext in ['.stdf', '.pbz2']:
            pickle_file = os.path.join(Path, "%s.pbz2" % Base)
        else:
            raise Exception("FileName should have '.stdf' or '.pbz2' extension")
        with bz2.open(pickle_file, 'wb') as fd:
            pickle.dump(index, fd)
        

def load_STDF(FileName, progress=False):
    '''
    This function will retrun a dictionary of dictionaries as follows
    
        {'version' : xxx,
         'endian' : xxx,
         'records' : { REC_NAM : [offset, ... 
         'indexes' : { offset : bytearray of the record ...
         'parts' : {part# : [offset, offset, offset, ...
    
    if however, next to FileName a file exists witht the same name, but with the .pickle extension,
    *AND* that file is younger than FileName, then this file is loaded.
    '''
    retval = {}
    Path, File = os.path.split(FileName)
    Name, _ = os.path.splitext(File)
    pickle_file = os.path.join(Path, "%s.pbz2" % Name)
    if os.path.exists(pickle_file) and os.path.isfile(pickle_file):
        if os.path.getmtime(FileName) < os.path.getmtime(pickle_file):
            print("Loading STDF index file '%s.pickle' ... ", end='')
            with bz2.open(pickle_file, 'rb') as fd:
                retval = pickle.load(fd)
            print("Done.")
            return retval
    offset = 0
    if os.path.exists(FileName) and os.path.isfile(FileName):
        endian, version = get_STDF_setup_from_file(FileName)
        retval['version'] = version
        retval['endian'] = endian
        retval['records'] = {}
        retval['indexes'] = {}
        retval['parts'] = {}
        PIP = {} # parts in process
        PN = 1
        TS2ID = ts_to_id()
        if progress:
            description = "Indexing STDF file '%s'" % os.path.split(FileName)[1]
            t = tqdm(total=os.stat(FileName)[6], ascii=True, disable=not progress, desc=description, leave=False, unit='b')
        for _, REC_TYP, REC_SUB, REC in xrecords_from_file(FileName):
            REC_ID = TS2ID[(REC_TYP, REC_SUB)]
            REC_LEN = len(REC)
            if REC_ID not in retval['records']: retval['records'][REC_ID] = [] 
            retval['indexes'][offset] = REC
            retval['records'][REC_ID].append(offset)
            if REC_ID in ['PIR', 'PRR', 'PTR', 'FTR', 'MPR']:
                if REC_ID == 'PIR':
                    pir = PIR(retval['version'], retval['endian'], REC)
                    pir_HEAD_NUM = pir.get_value('HEAD_NUM')
                    pir_SITE_NUM = pir.get_value('SITE_NUM')
                    if (pir_HEAD_NUM, pir_SITE_NUM) in PIP:
                        raise Exception("One should not be able to reach this point !")
                    PIP[(pir_HEAD_NUM, pir_SITE_NUM)] = PN
                    retval['parts'][PN]=[]
                    retval['parts'][PN].append(offset)
                    PN+=1  
                elif REC_ID == 'PRR':
                    prr = PRR(retval['version'], retval['endian'], REC)
                    prr_HEAD_NUM = prr.get_value('HEAD_NUM') 
                    prr_SITE_NUM = prr.get_value('SITE_NUM')
                    if (prr_HEAD_NUM, prr_SITE_NUM) not in PIP:
                        raise Exception("One should not be able to reach this point!")
                    pn = PIP[(prr_HEAD_NUM, prr_SITE_NUM)]
                    retval['parts'][pn].append(offset)
                    del PIP[(prr_HEAD_NUM, prr_SITE_NUM)]
                elif REC_ID == 'PTR':
                    ptr = PTR(retval['version'], retval['endian'], REC)
                    ptr_HEAD_NUM = ptr.get_value('HEAD_NUM') 
                    ptr_SITE_NUM = ptr.get_value('SITE_NUM')
                    if (ptr_HEAD_NUM, ptr_SITE_NUM) not in PIP:
                        raise Exception("One should not be able to reach this point!")
                    pn = PIP[(ptr_HEAD_NUM, ptr_SITE_NUM)]
                    retval['parts'][pn].append(offset)
                elif REC_ID == 'FTR':
                    ftr = FTR(retval['version'], retval['endian'], REC)
                    ftr_HEAD_NUM = ftr.get_value('HEAD_NUM') 
                    ftr_SITE_NUM = ftr.get_value('SITE_NUM')
                    if (ftr_HEAD_NUM, ftr_SITE_NUM) not in PIP:
                        raise Exception("One should not be able to reach this point!")
                    pn = PIP[(ftr_HEAD_NUM, ftr_SITE_NUM)]
                    retval['parts'][pn].append(offset)
                elif REC_ID == 'MPR':
                    mpr = MPR(retval['version'], retval['endian'], REC)
                    mpr_HEAD_NUM = mpr.get_value('HEAD_NUM') 
                    mpr_SITE_NUM = mpr.get_value('SITE_NUM')
                    if (mpr_HEAD_NUM, mpr_SITE_NUM) not in PIP:
                        raise Exception("One should not be able to reach this point!")
                    pn = PIP[(mpr_HEAD_NUM, mpr_SITE_NUM)]
                    retval['parts'][pn].append(offset)
                else:
                    raise Exception("One should not be able to reach this point! (%s)" % REC_ID)
            if progress: t.update(REC_LEN)
            offset += REC_LEN
        if progress: t.close()
    return retval

def measurements_df_from_index(index, progress=False):
    '''
    '''
    idx = list(index['parts'])
    columns = ['PART_TYP', 'TST_TEMP', 'LOT_ID', 'MODE_COD', 'NODE_NAM', 'X_COORD', 'Y_COORD', 'TEST_T', 'PART_ID', 'SOFT_BIN', 'HARD_BIN', 'HEAD_NUM', 'SITE_NUM', 'NUM_TEST']
    
def get_tests_from_index(index, progress=False):
    retval = {'PTR' : {}, 'FTR' : {}, 'MPR' : {}, '?' : {}}
    
    
    for tsr_offset in index['records']['TSR']:
        tsr = TSR(index['version'], index['endian'], index['indexes'][tsr_offset])
     
def get_df_stup_from_index(index, progress=False):
    '''
    '''
    
    
    
       
def TS_from_record(record):
    '''
    given an STDF record (bytearray), extract the REC_TYP and REC_SUB
    '''
    return struct.unpack("BB", record[2:4])

if __name__ == '__main__':
    FN = r'C:\Users\hoeren\eclipse-workspace\ATE\resources\stdf\Micronas\HVCF\IFLEX-14_1_XEHVCF4310WTJ3_272_F1N_R_806265.000_1_jul24_03_01.stdf'

