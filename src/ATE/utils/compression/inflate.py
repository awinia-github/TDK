'''
Created on Aug 14, 2019

@author: hoeren
'''
import os, sys, tqdm
import gzip, bz2, lzma

from ATE.utils import DT
from ATE.utils.compression import supported_compressions, supported_compressions_extensions, default_compression
from ATE.utils.magicnumber import extension_from_magic_number_in_file
from ATE.Data.Formats.STDF.quick import is_supported_compressed_STDF_file
    


def inflate(FileNames, compression=default_compression, progress=True, bs=128*1024):
    '''
    de-compress *ALL* given FileNames
    '''
    def decomp(FileName, compression='lzma', annotation='', bs=128*1024, progress=False, indent=0, callback=None):
        pass



def get_deflated_file_size(FileName):
    '''
    This function returns the (deflated) file size of FileName.
    
    if FileName is a compressed file, but not supported, -1 is returned.
    if FileName is not (recognized) as a compressed file, the filesize is returned.
    '''
    # tip, open, seek to end and tell


    
if __name__ == '__main__':
    from ATE import package_root

    stdf_resources_path = os.path.normpath(os.path.join(package_root, r'./../../resources/stdf'))
    if not os.path.exists(stdf_resources_path) or not os.path.isdir(stdf_resources_path):
        raise Exception("'%s' is not valid.")

    FileNames = []
    for root, _, files in os.walk(stdf_resources_path):
        for file in files:
            if not file.startswith('.'):
                FileNames.append(os.path.join(root, file))

    for FileName in FileNames:
        print(FileName)
