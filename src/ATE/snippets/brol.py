'''
Created on Sep 13, 2019

@author: hoeren
'''
from ATE.Data.Formats import STDF


if __name__ == '__main__':
    files = STDF.get_stdf_zx_files(STDF.samples)
    mir = STDF.get_MIR_from_file(files[10])
    print(mir)
