'''
Created on Aug 15, 2019

@author: hoeren
'''
import os, struct

from ATE.Data.Formats.STDF.records import __latest_STDF_version__, FileNameDefinitions
FileNameDefinition = FileNameDefinitions[__latest_STDF_version__]

from ATE.utils.magicnumber import is_compressed_file, extension_from_magic_number_in_file
from ATE.utils.compression import supported_compressions, supported_compressions_extensions, default_compression


def isWS(FileName, progress=False):
    '''
    This function returns True if the given (compressed) FileName is made during Wafer Sort, False otherwise.
    The only reliable way to determine if the data is generated during Wafer Sort is to look for the presense of 'WIR'.
    This function might take a while on big files, so if progress=True, a progress bar is displayed.
    '''
    #TODO: Implement
    return True

def isFT(FileName, progress=False):
    '''
    This function returns True if the given (compressed) FileName is made during Final Test, False otherwhise.
    The only reliable way to determine if the date is generated dureing Final Test is to look for the absense of 'WIR'.
    This function might take a while on big files, so if progress=True, a progress bar is displayed.
    '''
    return not isWS(FileName, progress)


def get_mir(FileName):
    '''
    This function will return the Master Information Record of FileName.
    If FileName is not a (compressed) STDF file, an empty MIR is returned. 
    '''
    with open(FileName, 'rb', roi=['MIR']) as reader:
        for mir in reader:
            return mir
    
def is_STDF(FileName):
    '''
    This function will read the first 4 bytes of a file, and see if byte 3 == 0 and byte 4 ==10
    (that is the magic number of an STDF file) if so return True, False otherwise.
    
    Note, it is checked if the file is compressed (only supports gzip, bz2 and lzma), if so,
    the uncompressed file is examined.
    '''
    if is_compressed_file(FileName, ['.gz', '.xz', '.bz2']):
        extension = extension_from_magic_number_in_file(FileName)[0]
        if extension == '.gz':
            import gzip
            with gzip.open(FileName, 'rb') as fd:
                FAR = fd.read(4)
                REC_TYP, REC_SUB = struct.unpack('BB', FAR[2:4])
                if REC_TYP == 0 and REC_SUB == 10:
                    return True
                else:
                    return False
        elif extension == '.bz2':
            import bz2
            with bz2.open(FileName, 'rb') as fd:
                FAR = fd.read(4)
                REC_TYP, REC_SUB = struct.unpack('BB', FAR[2:4])
                if REC_TYP == 0 and REC_SUB == 10:
                    return True
                else:
                    return False
        elif extension == '.xz':
            import lzma
            with lzma.open(FileName, 'rb') as fd:
                FAR = fd.read(4)
                REC_TYP, REC_SUB = struct.unpack('BB', FAR[2:4])
                if REC_TYP == 0 and REC_SUB == 10:
                    return True
                else:
                    return False
        else:
            raise Exception("Shouldn't reach this point (%s)" % extension)
    else:
        with open(FileName, 'rb') as fd:
            FAR = fd.read(4)
            REC_TYP, REC_SUB = struct.unpack('BB', FAR[2:4])
            if REC_TYP == 0 and REC_SUB == 10:
                return True
            else:
                return False

# def FAR_info_from_file(FileName):
#     '''
#     The FAR is the first record (6 bytes) of an STDF file.
# 
#     Note: if FileName is a compressed STDF, then this function will read INSIDE the decomressed version.
#     '''
#     if is_compressed_file(FileName, ['.gz', '.xz', '.bz2']):
#         extension = extension_from_magic_number_in_file(FileName)
#         if extension == '.gz':
#             import gzip
#             with gzip.open(FileName, 'rb') as fd:
#                 FAR = fd.read(6)
#                 REC_TYP, REC_SUB = struct.unpack('BB', FAR[2:4])
#                 if REC_TYP == 0 and REC_SUB == 10:
#                     return struct.unpack('BB', FAR[4,6])
#                 else:
#                     return None, None
#         elif extension == '.bz2':
#             import bz2
#             with bz2.open(FileName, 'rb') as fd:
#                 FAR = fd.read(6)
#                 REC_TYP, REC_SUB = struct.unpack('BB', FAR[2:4])
#                 if REC_TYP == 0 and REC_SUB == 10:
#                     return struct.unpack('BB', FAR[4,6])
#                 else:
#                     return None, None
#         elif extension == '.xz':
#             import lzma
#             with lzma.open(FileName, 'rb') as fd:
#                 FAR = fd.read(6)
#                 REC_TYP, REC_SUB = struct.unpack('BB', FAR[2:4])
#                 if REC_TYP == 0 and REC_SUB == 10:
#                     return struct.unpack('BB', FAR[4,6])
#                 else:
#                     return None, None
#         else:
#             raise Exception("Shouldn't reach this poin")
#     else:
#         with open(FileName, 'rb') as fd:
#             FAR = fd.read(6)
#             REC_TYP, REC_SUB = struct.unpack('BB', FAR[2:4])
#             if REC_TYP == 0 and REC_SUB == 10:
#                 return struct.unpack('BB', FAR[4,6])
#             else:
#                 return None, None
#     
#     struct.unpack('BB', FAR[2:4])
#     
#     
#     return CPU_TYP, STDF_VER
   
   
    

def MIR_from_file(FileName):
    '''
    '''
    

def TS_from_record(record):
    '''
    given an STDF record (bytearray), extract the REC_TYP and REC_SUB
    Note: This will work on *ALL* records.
    '''
    return struct.unpack("BB", record[2:4])

def HS_from_record(record):
    '''
    given and STDF record (bytearray), extract the HEAD_NUM and SITE_NUM 
    Note : HEAD_NUM and SITE_NUM are not always located at the same (byte) offset.

                REC_TYP   REC_SUB   HEAD_NUM   SITE_NUM
           PCR      1        30        4          5
           HBR      1        40        4          5
           SBR      1        50        4          5 
           PMR      1        60     variable   variable <-- will not support here
           SDR      1        80        4        array   <-- will not support here
           WIR      2        10        4          /     <-- will not support here
           WRR      2        20        4          /     <-- will not support here   
           PIR      5        10        4          5
           PRR      5        20        4          5
           TSR      10       30        4          5
           PTR      15       10        9          10    < most likely
           MPR      15       15        9          10    < most likely
           FTR      15       20        9          10    < most likely
           
    '''
    REC_TYP, REC_SUB = TS_from_record(record)
    HEAD_NUM = 0
    SITE_NUM = 0
    if REC_TYP == 15:
        if REC_SUB in [10, 15, 20]:
            HEAD_NUM, SITE_NUM = struct.unpack("BB", record[8:10])
    elif REC_TYP == 5:
        if REC_SUB in [10, 20, 30]:
            HEAD_NUM, SITE_NUM = struct.unpack("BB", record[4:6])
    elif REC_TYP == 1:
        if REC_SUB in [30, 40, 50]:
            HEAD_NUM, SITE_NUM = struct.unpack("BB", record[4:6])
    return HEAD_NUM, SITE_NUM
            
def N_from_record(record, endian):
    '''
    given a PTR, MPR or FTR record, extract the test Number.
    Note: TEST_NUM is for these records always located on offset 4..7
    '''
    REC_TYP, REC_SUB = TS_from_record(record)
    
def endian_from_file(FileName):
    '''
    '''

def is_supported_compressed_STDF_file(FileName):
    '''
    Returns True if FileName is a supported compressed file, False otherwise
    '''
    if not is_STDF(FileName): return False
    ext = extension_from_magic_number_in_file(FileName, supported_compressions_extensions)
    if len(ext)!=1: return False
    return True

class records_from_file(object):
    '''
    This is a *QUICK* iterator class that returns the next record from an STDF file each time it is called.
    It is fast because it doesn't check versions, extensions and it doesn't unpack the record and skips unknown records.
    '''
    def __init__(self, FileName):
        self.fd = None
        if not isinstance(FileName, str): return
        if not os.path.exists(FileName): return
        if not os.path.isfile(FileName): return
        if not is_STDF(FileName): return
        if is_supported_compressed_STDF_file(FileName):
            ext = extension_from_magic_number_in_file(FileName)
            if len(ext)!=1: return
            compression = supported_compressions_extensions[ext[0]]
            if compression=='lzma':
                import lzma
                self.fd = lzma.open(FileName, 'rb')
            elif compression=='bz2':
                import bz2
                self.fd = bz2.open(FileName, 'rb')
            elif compression=='gzip':
                import gzip
                self.fd = gzip.open(FileName, 'rb')
            else:
                raise Exception("the %s compression is supported but not fully implemented." % compression)
        else:
            self.fd = open(FileName, 'rb')
        buff = self.fd.read(6)
        CPU_TYPE, STDF_VER = struct.unpack('BB', buff[4:])
        if CPU_TYPE == 1: self.endian = '>'
        elif CPU_TYPE == 2: self.endian = '<'
        else: self.endian = '?'
        self.version = 'V%s' % STDF_VER
        self.fd.seek(0)
        self.unpack_fmt = '%sHBB' % self.endian
        
    def __del__(self):
        if self.fd != None:
            self.fd.close()
        
    def __iter__(self):
        return self
    
    def __next__(self):
        while self.fd!=None:
            while True:
                header = self.fd.read(4)
                if len(header)!=4:
                    raise StopIteration
                REC_LEN, REC_TYP, REC_SUB = struct.unpack(self.unpack_fmt, header)
                footer = self.fd.read(REC_LEN)
                if len(footer)!=REC_LEN:
                    raise StopIteration
                return REC_LEN, REC_TYP, REC_SUB, header+footer

if __name__ == '__main__':
#     FileName = r'C:\Users\hoeren\eclipse-workspace\SCT\resources\stdf\test.stdf'
    FileName = r'C:\Users\hoeren\eclipse-workspace\SCT\resources\stdf\FLEX08_1_IDHVCF4A10W_270_P1N_R_806511.001_05_jul31_21_35.stdf.xz'
    
    for REC_LEN, REC_TYP, REC_SUB, REC in records_from_file(FileName):
        print(REC_LEN, REC_TYP, REC_SUB, REC)
    