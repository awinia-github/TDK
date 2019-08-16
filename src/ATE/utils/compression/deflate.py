'''
Created on Aug 14, 2019

@author: hoeren
'''
import os, sys, tqdm
import gzip, bz2, lzma

from ATE.utils import DT
from ATE.utils.hashing import file_contents_hash
from ATE.utils.compression import supported_compressions, default_compression

def deflate(FileNames, compression=default_compression, progress=True, bs=128*1024, use_hash=False):
    '''
    compresses all give 'FileNames' 
    
    TODO: add the hashing possibility
    '''
    def comp(FileName, compression='lzma', annotation='', bs=128*1024, progress=False, indent=0, callback=None):
        lbl = "Compressing %s : '%s' with %s" % (annotation, os.path.split(FileName)[1], compression)
        ttl = os.stat(FileName)[6]
        dt = DT(FileName)
        pb = tqdm.tqdm(total=ttl, desc=lbl, unit='B', unit_scale=True, leave=False, disable=not progress, position=indent)
        ext = supported_compressions[compression]
        if compression=='lzma':
            with open(FileName, 'rb') as fdi, lzma.open(FileName+ext, 'wb') as fdo:
                chunk = fdi.read(bs)
                while len(chunk) == bs:
                    fdo.write(chunk)
                    pb.update(bs)
                    if progress and callback!=None: callback(bs)
                    chunk = fdi.read(bs)
                fdo.write(chunk)
                pb.update(bs)
                if progress and callback!=None: callback(bs)
            os.utime(FileName+ext, times=(dt.epoch, dt.epoch))
        elif compression=='bz2':
            with open(FileName, 'rb') as fdi, bz2.open(FileName+ext, 'wb') as fdo:
                chunk = fdi.read(bs)
                while len(chunk) == bs:
                    fdo.write(chunk)
                    pb.update(bs)
                    if progress and callback!=None: callback(bs)
                    chunk = fdi.read(bs)
                fdo.write(chunk)
                pb.update(bs)
                if progress and callback!=None: callback(bs)
            os.utime(FileName+ext, times=(dt.epoch, dt.epoch))
        elif compression=='gzip':
            with open(FileName, 'rb') as fdi, gzip.open(FileName+ext, 'wb') as fdo:
                chunk = fdi.read(bs)
                while len(chunk) == bs:
                    fdo.write(chunk)
                    pb.update(bs)
                    if progress and callback!=None: callback(bs)
                    chunk = fdi.read(bs)
                fdo.write(chunk)
                pb.update(bs)
                if progress and callback!=None: callback(bs)
            os.utime(FileName+ext, times=(dt.epoch, dt.epoch))
        else:
            raise Exception("Supported but un-implemented compression '%s'" % compression)
        pb.close()
    
    if compression not in supported_compressions:
        raise Exception("don't know how to handle '%s' compression" % compression)
        
    if isinstance(FileNames, str): # single file
        comp(FileNames, progress=progress)
    if isinstance(FileNames, list): # multiple files
        label = "%s progress of %d files" % (compression, len(FileNames))
        total = 0
        for FileName in FileNames:
            total+=os.stat(FileName)[6]
        tpb = tqdm.tqdm(total=total, desc=label, unit='B', unit_scale=True, leave=False, disable=not progress)
        for FileNumber, FileName in enumerate(FileNames):
            annotation = 'file %s/%s' % (FileNumber+1, len(FileNames))
            comp(FileName, annotation = annotation, progress=progress, indent=1, callback=tpb.update)
        tpb.close()

if __name__ == '__main__':
    from ATE.scripts.python import stdf_resources, stdf_files
    deflate(stdf_files, compression='gzip') # gzip
    deflate(stdf_files, compression='bz2') # bz2
    deflate(stdf_files) # lzma, default
