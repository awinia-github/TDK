'''
Created on Aug 16, 2019

@author: hoeren
'''
import pickle

def readPickle(FileName):
    '''
    This method will read a pickled object in FileName and return it.
    '''
    retval = {}
    with open(FileName, 'rb') as fd:
        retval = pickle.load(fd)
    return retval
    
def writePickle(FileName, Obj):
    '''
    This method will write the Obj in a pickle FileName.
    if FileName already exists, it will be overwritten.
    '''
    with open(FileName, 'wb') as fd:
        pickle.dump(Obj, fd)

if __name__ == '__main__':
    pass