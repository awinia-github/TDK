'''
Created on Aug 16, 2019

@author: hoeren
'''
import os

def reset(path=None, verbose=False):
    '''
    
    '''
    if path==None:
        metis_path = os.environ['METIS']
    elif isinstance(path, str):
        if os.path.exists(path) and os.path.isdir(path):
            metis_path = path
        else:
            raise Exception("Directory '%s' doesn't exist" % path)
    else:
        raise Exception("Can not interpret '%s'" % path)
    
    if verbose: print("Resetting '%s' ... " % metis_path, end='')
    if verbose: print("Done.")

def clean(path=None, verbose=False):
    '''
    
    '''
    if path==None:
        metis_path = os.environ['METIS']
    elif isinstance(path, str):
        if os.path.exists(path) and os.path.isdir(path):
            metis_path = path
        else:
            raise Exception("Directory '%s' doesn't exist" % path)
    else:
        raise Exception("Can not interpret '%s'" % path)
    
    if verbose: print("Cleaning '%s' ... " % metis_path, end='')
    if verbose: print("Done.")
    
if __name__ == '__main__':
    from myconsole import metis_path
    reset(path=metis_path, verbose=True)
    clean(path=metis_path, verbose=True)
    