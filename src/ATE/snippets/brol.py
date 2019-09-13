'''
Created on Sep 13, 2019

@author: hoeren
'''
from ATE.Data.Formats.STDF.utils import index_from_STDF
from ATE.Data.Formats.STDF import get_stdf_zx_files, samples

if __name__ == '__main__':
    stdf_xz_files = get_stdf_zx_files(samples)

#     my_mir = STDF.utils.MIR_from_file(stdf_xz_files[6])
#     print(my_mir)
    
    index = index_from_STDF(stdf_xz_files[6])
    print(index)