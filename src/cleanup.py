'''
Created on Aug 16, 2019

@author: hoeren
'''
import os, shutil

from SpyderConsole import project_root

files_to_keep = ['.gitignore']
dirs_not_to_keep = ['__pycache__']

def clean_files(verbose=False):
    '''
    remove all files starting with '.' (except those in 'files_to_keep') from the project tree
    '''
    files_to_remove = []
    for root, _, files in os.walk(project_root):
        for file in files:
            if file.startswith('.') and file not in files_to_keep:
                file_to_remove = os.path.join(root, file)
                if verbose: print("   Staging '%s' for deletion." % file_to_remove)
                files_to_remove.append(file_to_remove)
    for file in files_to_remove:
        if os.path.exists(file):
            if verbose: print("   Removing '%s' ... " % file, end = '')
            os.unlink(file)
            if verbose: print("Done.")

def clean_dirs(verbose=False):
    '''
    remove the superfluous directories in 'dirs_not_to_keep'
    '''
    dirs_to_remove = []
    for root, dirs, _ in os.walk(project_root):
        for Dir in dirs:
            if Dir in dirs_not_to_keep:
                dir_to_remove = os.path.join(root, Dir)
                if verbose: print("   Staging tree '%s' for deletion." % dir_to_remove)
                dirs_to_remove.append(dir_to_remove)
    for Dir in dirs_to_remove:
        if verbose: print("   Removing tree '%s' ... " % Dir, end = '')
        shutil.rmtree(Dir)
        if verbose: print("Done.")
    
if __name__ == '__main__':
    print('Cleaning Files:')
    clean_files(True)
    print('Cleaning Directories:')
    clean_dirs(True)